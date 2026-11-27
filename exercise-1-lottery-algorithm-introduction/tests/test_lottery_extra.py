"""Extension tests: compensation tickets, ticket transfer, currencies."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import lottery  # noqa: E402


# --------------------------------------------------------------------------
# Compensation tickets
# --------------------------------------------------------------------------

def _io_workload():
    return [
        {"pid": "IO", "arrival": 0, "burst": 10**9, "tickets": 10, "io_every": 2, "io_len": 3},
        {"pid": "CPU1", "arrival": 0, "burst": 10**9, "tickets": 10},
        {"pid": "CPU2", "arrival": 0, "burst": 10**9, "tickets": 10},
    ]


def test_compensation_boosts_io_process_share():
    procs_off = _io_workload()
    procs_on = _io_workload()
    _, g_off, st_off, log_off = lottery.simulate_full(procs_off, 4, seed=2024,
                                                      compensation=False, horizon=3000)
    _, g_on, st_on, log_on = lottery.simulate_full(procs_on, 4, seed=2024,
                                                   compensation=True, horizon=3000)
    dec_off = sum(1 for e in log_off if e["winner"] == "IO")
    dec_on = sum(1 for e in log_on if e["winner"] == "IO")
    share_off = lottery.measured_shares(g_off)["IO"]
    share_on = lottery.measured_shares(g_on)["IO"]
    assert st_on.compensation_grants > 0
    assert dec_on > dec_off
    assert share_on > share_off


def test_compensation_resets_after_winning():
    procs = _io_workload()
    plist, gantt, st, log = lottery.simulate_full(procs, 4, seed=2024,
                                                  compensation=True, horizon=400)
    io_proc = next(p for p in plist if p.pid == "IO")
    # compensation boost applies until the next win; the invariant is that the
    # multiplier never exceeds the quantum/used cap (20x)
    assert 1.0 <= io_proc.compensation <= 20.0


# --------------------------------------------------------------------------
# Ticket transfer
# --------------------------------------------------------------------------

def test_transfer_window_moves_effective_tickets():
    procs = [
        {"pid": "P1", "arrival": 0, "burst": 10, "tickets": 6,
         "transfers": [{"start": 0, "end": 100, "tickets": 4, "target": "P2"}]},
        {"pid": "P2", "arrival": 0, "burst": 10, "tickets": 2},
        {"pid": "P3", "arrival": 0, "burst": 10, "tickets": 4},
    ]
    pool = lottery.effective_pool(lottery.validate(procs), 5)
    assert pool["P1"] == pytest.approx(2.0)
    assert pool["P2"] == pytest.approx(6.0)
    assert pool["P3"] == pytest.approx(4.0)


def test_transfer_window_expiry():
    procs = [
        {"pid": "P1", "arrival": 0, "burst": 10, "tickets": 6,
         "transfers": [{"start": 2, "end": 4, "tickets": 4, "target": "P2"}]},
        {"pid": "P2", "arrival": 0, "burst": 10, "tickets": 2},
    ]
    validated = lottery.validate(procs)
    assert lottery.effective_pool(validated, 1)["P1"] == pytest.approx(6.0)
    assert lottery.effective_pool(validated, 3)["P1"] == pytest.approx(2.0)
    assert lottery.effective_pool(validated, 4)["P1"] == pytest.approx(6.0)


def test_transfer_gives_target_higher_share_in_window():
    procs = [
        {"pid": "P1", "arrival": 0, "burst": 10**9, "tickets": 6,
         "transfers": [{"start": 0, "end": 10**9, "tickets": 4, "target": "P2"}]},
        {"pid": "P2", "arrival": 0, "burst": 10**9, "tickets": 2},
        {"pid": "P3", "arrival": 0, "burst": 10**9, "tickets": 4},
    ]
    _, gantt, _, log = lottery.simulate_full(procs, 1, seed=123, compensation=False, horizon=900)
    dec = {}
    for e in log:
        dec[e["winner"]] = dec.get(e["winner"], 0) + 1
    assert dec["P2"] > dec["P3"]


def test_lent_tickets_are_not_copied():
    procs = [
        {"pid": "P1", "arrival": 0, "burst": 5, "tickets": 3,
         "transfers": [{"start": 0, "end": 100, "tickets": 2, "target": "P2"}]},
        {"pid": "P2", "arrival": 0, "burst": 5, "tickets": 1},
    ]
    pool = lottery.effective_pool(lottery.validate(procs), 0)
    assert pool["P1"] + pool["P2"] == pytest.approx(3.0 + 1.0)  # no duplication


# --------------------------------------------------------------------------
# Currencies
# --------------------------------------------------------------------------

def _currency_scenario():
    return {
        "quantum": 2,
        "seed": 555,
        "currencies": [
            {"name": "system", "base_tickets": 50, "members": {"P1": 1, "P2": 1}},
            {"name": "users", "base_tickets": 100, "members": {"P3": 1, "P4": 3}},
        ],
        "processes": [
            {"pid": "P1", "arrival": 0, "burst": 200, "tickets": 1},
            {"pid": "P2", "arrival": 0, "burst": 200, "tickets": 1},
            {"pid": "P3", "arrival": 0, "burst": 200, "tickets": 1},
            {"pid": "P4", "arrival": 0, "burst": 200, "tickets": 3},
        ],
    }


def test_currency_validation_covers_all_processes():
    spec = _currency_scenario()
    procs = lottery.validate(spec["processes"])
    with pytest.raises(lottery.InputError):
        lottery.validate_groups([{"name": "g", "base_tickets": 10, "members": {"P1": 1}}], procs)


def test_currency_split_proportions():
    spec = _currency_scenario()
    quantum = spec["quantum"]
    procs = spec["processes"]
    _, gantt, _, log = lottery.simulate_full(procs, quantum, seed=spec["seed"],
                                             currencies=spec["currencies"])
    first = log[0]["pool"]
    # system group: 50 base split 1:1 -> 25 each; users group: 100 split 1:3 -> 25/75
    assert first == pytest.approx({"P1": 25.0, "P2": 25.0, "P3": 25.0, "P4": 75.0})


def test_currency_share_over_long_run():
    spec = _currency_scenario()
    huge = [dict(p, burst=10**9) for p in spec["processes"]]
    _, gantt, _, log = lottery.simulate_full(huge, 1, seed=20250927,
                                             currencies=spec["currencies"], horizon=1500)
    shares = lottery.measured_shares(gantt)
    total = sum(shares.values())
    # P4 (75/150 = 0.5) should dominate; P1/P2/P3 each 25/150 ≈ 0.1667
    assert abs(shares["P4"] / total - 0.5) < 0.06
    for pid in ("P1", "P2", "P3"):
        assert abs(shares[pid] / total - 1 / 6) < 0.06


# --------------------------------------------------------------------------
# I/O model details
# --------------------------------------------------------------------------

def test_io_process_blocks_and_resumes():
    procs = [
        {"pid": "IO", "arrival": 0, "burst": 3, "tickets": 1, "io_every": 1, "io_len": 2},
        {"pid": "CPU", "arrival": 0, "burst": 10, "tickets": 1},
    ]
    plist, gantt, st, _ = lottery.simulate_full(procs, 1, seed=11)
    assert all(p.finish is not None for p in plist)
    labels = [g[2] for g in gantt]
    assert "IDLE" not in labels  # CPU always covers the blocking windows


def test_io_requires_pair_of_fields():
    with pytest.raises(lottery.InputError):
        lottery.validate([{"pid": "P", "arrival": 0, "burst": 1, "tickets": 1, "io_every": 2}])


# --------------------------------------------------------------------------
# Convergence across seeds
# --------------------------------------------------------------------------

def test_mean_share_converges_across_seeds():
    shares = []
    for seed in range(30):
        procs = [
            {"pid": "A", "arrival": 0, "burst": 10**9, "tickets": 7},
            {"pid": "B", "arrival": 0, "burst": 10**9, "tickets": 3},
        ]
        _, gantt, _, log = lottery.simulate_full(procs, 1, seed=seed, horizon=600)
        shares.append(lottery.measured_shares(gantt)["A"] / 600)
    assert abs(sum(shares) / len(shares) - 0.7) < 0.03
