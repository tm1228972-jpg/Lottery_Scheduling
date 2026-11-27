"""Core tests for the lottery scheduling simulator."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import lottery  # noqa: E402


BASELINE = [
    {"pid": "P1", "arrival": 0, "burst": 5, "tickets": 5},
    {"pid": "P2", "arrival": 1, "burst": 4, "tickets": 3},
    {"pid": "P3", "arrival": 2, "burst": 3, "tickets": 2},
    {"pid": "P4", "arrival": 3, "burst": 2, "tickets": 4},
    {"pid": "P5", "arrival": 4, "burst": 1, "tickets": 1},
]


def run(procs, quantum=2, seed=20250927, **kw):
    return lottery.simulate_full(procs, quantum, seed, **kw)


# --------------------------------------------------------------------------
# Determinism and basic sanity
# --------------------------------------------------------------------------

def test_same_seed_same_gantt():
    _, g1, _, _ = run(BASELINE, seed=42)
    _, g2, _, _ = run(BASELINE, seed=42)
    assert g1 == g2


def test_different_seeds_usually_differ():
    _, g1, _, _ = run(BASELINE, seed=1)
    _, g2, _, _ = run(BASELINE, seed=2)
    assert g1 != g2  # 15 ticks with different seeds: different interleavings


def test_every_process_finishes():
    plist, gantt, st, _ = run(BASELINE, seed=42)
    assert all(p.finish is not None for p in plist)
    assert all(p.remaining == 0 for p in plist)


def test_timeline_is_contiguous_and_covers_makespan():
    _, gantt, st, _ = run(BASELINE, seed=42)
    cursor = 0
    for s, e, _label in gantt:
        assert s == cursor
        assert e > s
        cursor = e
    assert st.total_time == cursor


def test_total_busy_equals_total_burst():
    plist, gantt, st, _ = run(BASELINE, seed=42)
    assert st.busy_time == sum(p.burst for p in plist)
    assert st.busy_time == st.total_time  # no idle ticks in this workload


def test_metrics_identities():
    plist, gantt, st, _ = run(BASELINE, seed=42)
    rows, summary = lottery.metrics_full(plist, st, 42, gantt)
    for p, r in zip(sorted(plist, key=lambda p: p.pid), sorted(rows, key=lambda r: r["pid"])):
        assert r["turnaround"] == r["finish"] - r["arrival"]
        assert r["waiting"] == r["turnaround"] - r["burst"]
        assert r["response"] == r["finish"] - r["arrival"] - (r["turnaround"] - r["burst"]) \
            or r["response"] <= r["turnaround"]
    assert summary["avg_turnaround"] == pytest.approx(
        sum(r["turnaround"] for r in rows) / len(rows))


# --------------------------------------------------------------------------
# Lottery semantics
# --------------------------------------------------------------------------

def test_draw_winner_respects_ticket_weights():
    rng = lottery.random.Random(7)
    pool = {"high": 90.0, "low": 10.0}
    wins = {"high": 0, "low": 0}
    for _ in range(2000):
        wins[lottery.draw_winner(pool, rng)] += 1
    assert wins["high"] > wins["low"] * 5


def test_steady_state_share_tracks_ticket_fraction():
    procs = [
        {"pid": "T5", "arrival": 0, "burst": 10**9, "tickets": 5},
        {"pid": "T3", "arrival": 0, "burst": 10**9, "tickets": 3},
        {"pid": "T2", "arrival": 0, "burst": 10**9, "tickets": 2},
    ]
    plist, gantt, st, log = run(procs, quantum=1, seed=31415, horizon=1500)
    rows, summary = lottery.metrics_full(plist, st, 31415, gantt, log)
    frac = {r["pid"]: r["cpu_share"] for r in rows}
    assert abs(frac["T5"] - 0.5) < 0.05
    assert abs(frac["T3"] - 0.3) < 0.05
    assert abs(frac["T2"] - 0.2) < 0.05
    assert summary["completed"] == 0


def test_zero_ticket_pool_cannot_win_draw():
    pool = {"a": 0.0, "b": 0.0}
    assert lottery.draw_winner(pool, lottery.random.Random(1)) is None


def test_blocked_process_is_not_in_pool():
    procs = [
        {"pid": "IO", "arrival": 0, "burst": 4, "tickets": 10, "io_every": 1, "io_len": 2},
        {"pid": "CPU", "arrival": 0, "burst": 4, "tickets": 10},
    ]
    plist, gantt, st, log = run(procs, quantum=2, seed=5, compensation=False)
    # during IO's blocking windows only CPU may be drawn
    for entry in log:
        if "IO" not in str(entry["pool"]):
            assert entry["winner"] == "CPU"


# --------------------------------------------------------------------------
# Validation and CLI errors
# --------------------------------------------------------------------------

def test_validation_rejects_zero_tickets():
    with pytest.raises(lottery.InputError):
        lottery.validate([{"pid": "P", "arrival": 0, "burst": 1, "tickets": 0}])


def test_validation_rejects_duplicate_pid():
    with pytest.raises(lottery.InputError):
        lottery.validate([{"pid": "P", "arrival": 0, "burst": 1, "tickets": 1},
                          {"pid": "P", "arrival": 0, "burst": 1, "tickets": 1}])


def test_validation_rejects_negative_arrival():
    with pytest.raises(lottery.InputError):
        lottery.validate([{"pid": "P", "arrival": -1, "burst": 1, "tickets": 1}])


def test_validation_rejects_unknown_transfer_target():
    with pytest.raises(lottery.InputError):
        lottery.validate([{"pid": "P", "arrival": 0, "burst": 1, "tickets": 1,
                           "transfers": [{"start": 0, "end": 1, "tickets": 1, "target": "X"}]}])


def test_cli_exit_code_on_invalid_scenario(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"processes": [{"pid": "P", "arrival": 0, "burst": 1, "tickets": 0}]}))
    rc = lottery.main([str(bad)])
    assert rc == 2


def test_cli_writes_csv_and_json(tmp_path):
    csv_p = tmp_path / "out.csv"
    json_p = tmp_path / "out.json"
    scen = tmp_path / "s.json"
    scen.write_text(json.dumps({"quantum": 2, "seed": 42, "processes": BASELINE}))
    rc = lottery.main([str(scen), "--csv", str(csv_p), "--json", str(json_p), "--quiet"])
    assert rc == 0
    assert "pid,arrival,burst" in csv_p.read_text()
    data = json.loads(json_p.read_text())
    assert data["summary"]["draws"] > 0
    assert len(data["rows"]) == len(BASELINE)


def test_cli_scenario_files_run():
    for name in ("baseline", "fair", "dominance", "compensation", "transfer", "currencies"):
        rc = lottery.main([str(ROOT / "code" / "scenarios" / f"{name}.json"), "--quiet"])
        assert rc == 0, name


def test_invalid_scenarios_fail_with_code_2():
    for name in ("invalid_tickets", "invalid_missing_field", "invalid_transfer_target"):
        rc = lottery.main([str(ROOT / "code" / "scenarios" / f"{name}.json")])
        assert rc == 2, name
