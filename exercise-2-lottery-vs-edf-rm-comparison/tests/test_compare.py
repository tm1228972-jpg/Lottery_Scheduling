"""Exercise 2 tests: comparator semantics, head-to-head policy expectations."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import compare  # noqa: E402

SETS = {p.stem: compare.load_tasks(p) for p in (ROOT / "scenarios").glob("*.json")}
HORIZONS = {k: v[1] for k, v in SETS.items()}
TASKS = {k: v[0] for k, v in SETS.items()}


def test_utilization_and_bound():
    assert compare.utilization(TASKS["set_a_harmonic"]) == pytest.approx(0.75)
    assert compare.utilization(TASKS["set_b_edf_yes_rm_no"]) == pytest.approx(0.9722, abs=1e-3)
    assert compare.rm_utilization_bound(3) == pytest.approx(0.7798, abs=1e-3)
    assert compare.rm_utilization_bound(4) == pytest.approx(0.7568, abs=1e-3)


def test_rta_results():
    ordered = sorted(TASKS["set_b_edf_yes_rm_no"], key=lambda t: (t.period, t.pid))
    assert compare.rm_response_time(TASKS["set_b_edf_yes_rm_no"], 0) == 1
    assert compare.rm_response_time(TASKS["set_b_edf_yes_rm_no"], 1) == 2
    assert compare.rm_response_time(TASKS["set_b_edf_yes_rm_no"], 2) == 3
    assert compare.rm_response_time(TASKS["set_b_edf_yes_rm_no"], 3) is None  # unschedulable under RM
    for name, exp in [("set_a_harmonic", [1, 3, 4]), ("set_d_mixed", [1, 2, 10])]:
        ordered = sorted(TASKS[name], key=lambda t: (t.period, t.pid))
        got = [compare.rm_response_time(TASKS[name], i) for i in range(len(ordered))]
        assert got == exp


def test_edf_feasibility_rule():
    assert compare.edf_feasibility_utilization(TASKS["set_a_harmonic"]) is True
    assert compare.edf_feasibility_utilization(TASKS["set_b_edf_yes_rm_no"]) is True
    assert compare.edf_feasibility_utilization(TASKS["set_c_overloaded"]) is False


def test_cdf_gap_free_gantt():
    for policy in ("lottery", "rm", "edf"):
        jobs, gantt, st = compare.simulate_policy(TASKS["set_a_harmonic"], policy, 60, seed=7)
        t = 0
        for s, e, _ in gantt:
            assert s == t
            t = e
        assert t == 60
        assert st.busy + st.idle == 60


def test_rm_edf_zero_misses_when_feasible():
    # set_b is the deliberately EDF-feasible-but-RM-unschedulable case: EDF must be clean,
    # RM is allowed (expected, in fact) to miss. Everything else must be clean for both.
    for name, horizon in HORIZONS.items():
        for policy in ("rm", "edf"):
            if name == "set_c_overloaded":
                continue
            if name == "set_b_edf_yes_rm_no" and policy == "rm":
                continue
            jobs, gantt, st = compare.simulate_policy(TASKS[name], policy, horizon, seed=20261127)
            unfinished = sum(1 for j in jobs if j.finish is None)
            assert st.missed + unfinished == 0, (name, policy)


def test_set_b_edf_zero_rm_misses():
    jobs, gantt, st_e = compare.simulate_policy(TASKS["set_b_edf_yes_rm_no"], "edf", 72, seed=20261127)
    jobs, gantt, st_r = compare.simulate_policy(TASKS["set_b_edf_yes_rm_no"], "rm", 72, seed=20261127)
    assert st_e.missed == 0
    assert st_r.missed > 0


def test_rm_beats_lottery_on_set_d():
    horizon = HORIZONS["set_d_mixed"]
    lottery_misses, rt_misses = [], []
    for seed in range(10):
        _, _, st_l = compare.simulate_policy(TASKS["set_d_mixed"], "lottery", horizon, seed=seed)
        _, _, st_r = compare.simulate_policy(TASKS["set_d_mixed"], "rm", horizon, seed=seed)
        lottery_misses.append(st_l.missed)
        rt_misses.append(st_r.missed)
    assert sum(lottery_misses) > 0
    assert sum(rt_misses) == 0


def test_overloaded_edf_graceful():
    horizon = HORIZONS["set_c_overloaded"]
    _, _, st_e = compare.simulate_policy(TASKS["set_c_overloaded"], "edf", horizon, seed=20261127)
    _, _, st_r = compare.simulate_policy(TASKS["set_c_overloaded"], "rm", horizon, seed=20261127)
    _, _, st_l = compare.simulate_policy(TASKS["set_c_overloaded"], "lottery", horizon, seed=20261127)
    # EDF is optimal on a uniprocessor: no policy can have strictly fewer missed jobs... EDF
    # should never miss more than RM here.
    assert st_e.missed <= st_r.missed
    assert st_e.missed <= st_l.missed


def test_determinism():
    for policy in ("lottery", "rm", "edf"):
        a = compare.simulate_policy(TASKS["set_d_mixed"], policy, 66, seed=99)
        b = compare.simulate_policy(TASKS["set_d_mixed"], policy, 66, seed=99)
        assert a[1] == b[1]


def test_invalid_policy_rejected():
    with pytest.raises(compare.InputError):
        compare.simulate_policy(TASKS["set_a_harmonic"], "rr", 10)


def test_invalid_task_rejected():
    with pytest.raises(compare.InputError):
        compare.validate_tasks([{"pid": "X", "burst": 0, "period": 5}])


def test_summary_schema():
    tasks = TASKS["set_a_harmonic"]
    jobs, gantt, st = compare.simulate_policy(tasks, "edf", 60, seed=1)
    s = compare.summarize(jobs, st, tasks, 60, 1)
    for key in ("policy", "utilization", "deadline_misses", "jobs_completed", "per_task", "avg_response", "context_switches", "dispatches"):
        assert key in s
    for pid, pt in s["per_task"].items():
        assert {"ticket_fraction", "cpu_share", "share_error", "deadline_misses"} <= set(pt)
