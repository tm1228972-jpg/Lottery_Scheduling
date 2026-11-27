"""Exercise 3 tests — hand procedure vs machine trace."""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import manual_rm_edf as M  # noqa: E402

SC = {p.stem: p for p in (ROOT / "scenarios").glob("*.json")}


def test_scenarios_load():
    assert set(SC) == {"ex3_1_trivial_two_task", "ex3_2_bound_beaten", "ex3_3_edf_not_rm",
                       "ex3_4_constrained_deadlines", "ex3_5_overload"}
    for p in SC.values():
        raw, tasks, horizon = M.load_scenario(p)
        assert horizon > 0 and tasks


def test_utilization_exact():
    _, t1, _ = M.load_scenario(SC["ex3_1_trivial_two_task"])
    _, t2, _ = M.load_scenario(SC["ex3_2_bound_beaten"])
    _, t3, _ = M.load_scenario(SC["ex3_3_edf_not_rm"])
    _, t4, _ = M.load_scenario(SC["ex3_4_constrained_deadlines"])
    _, t5, _ = M.load_scenario(SC["ex3_5_overload"])
    assert M.utilization(t1) == pytest.approx(2/5 + 1/7)
    assert M.utilization(t2) == pytest.approx(2/5 + 1/8 + 3/10)
    assert M.utilization(t3) == pytest.approx(1/4 + 2/5 + 2/7)
    assert M.utilization(t4) == pytest.approx(2/7 + 2/9)
    assert M.utilization(t5) == pytest.approx(2/5 + 2/6 + 2/7)


def test_hyperperiod():
    for name, expect in [("ex3_1_trivial_two_task", 35), ("ex3_2_bound_beaten", 40),
                         ("ex3_3_edf_not_rm", 140), ("ex3_4_constrained_deadlines", 63),
                         ("ex3_5_overload", 210)]:
        _, tasks, _ = M.load_scenario(SC[name])
        assert M.hyperperiod(tasks) == expect


def test_rm_bound_values():
    assert M.rm_utilization_bound(2) == pytest.approx(2 * (2 ** 0.5 - 1))
    assert M.rm_utilization_bound(3) == pytest.approx(0.7798, abs=1e-4)


def test_rta_fixed_points():
    _, t2, _ = M.load_scenario(SC["ex3_2_bound_beaten"])
    _, t3, _ = M.load_scenario(SC["ex3_3_edf_not_rm"])
    o2 = M.ordered_rm(t2)
    o3 = M.ordered_rm(t3)
    assert M.rta_iterations(t2, 0)[0] == 2
    assert M.rta_iterations(t2, 1)[0] == 3
    assert M.rta_iterations(t2, 2)[0] == 8     # above bound, still schedulable
    assert M.rta_iterations(t3, 0)[0] == 1
    assert M.rta_iterations(t3, 1)[0] == 3
    assert M.rta_iterations(t3, 2)[0] is None  # RTA diverges on T3


def test_rta_iteration_sequence_shape():
    _, t3, _ = M.load_scenario(SC["ex3_3_edf_not_rm"])
    r, seq = M.rta_iterations(t3, 2)
    assert r is None
    assert seq[0] == 2 and seq[-1] > 7


def test_demand_bound_constrained():
    _, t4, _ = M.load_scenario(SC["ex3_4_constrained_deadlines"])
    H, rows, ok = M.edf_demand_bound(t4)
    assert H == 63
    assert ok
    for t, dbf in rows:
        assert dbf <= t


def test_gantt_gap_free_and_accounting():
    for p in SC.values():
        _, tasks, horizon = M.load_scenario(p)
        for policy in ("rm", "edf"):
            jobs, gantt, st = M.simulate(tasks, policy, horizon)
            covered, cur = 0, 0
            for s, e, pid in gantt:
                assert s == cur, (p, policy, gantt)
                cur = e
                covered += e - s
            assert covered == horizon
            assert st.busy + st.idle == horizon


def test_ex3_3_rm_misses_exactly_one_edf_zero():
    _, tasks, horizon = M.load_scenario(SC["ex3_3_edf_not_rm"])
    jobs_r, _, _ = M.simulate(tasks, "rm", horizon)
    jobs_e, _, _ = M.simulate(tasks, "edf", horizon)
    late_r = [j for j in jobs_r if j.finish is not None and j.finish > j.deadline]
    assert [j.pid for j in late_r] == ["T3"]
    unf_r = sum(1 for j in jobs_r if j.finish is None)
    assert unf_r == 0
    assert all(j.finish is not None and j.finish <= j.deadline for j in jobs_e)


def test_ex3_2_above_bound_but_zero_misses():
    _, tasks, horizon = M.load_scenario(SC["ex3_2_bound_beaten"])
    assert M.utilization(tasks) > M.rm_utilization_bound(3)
    for policy in ("rm", "edf"):
        jobs, _, _ = M.simulate(tasks, policy, horizon)
        assert all(j.finish is not None and j.finish <= j.deadline for j in jobs)


def test_ex3_5_overload_edf_least_damage():
    _, tasks, horizon = M.load_scenario(SC["ex3_5_overload"])
    jobs_r, _, _ = M.simulate(tasks, "rm", horizon)
    jobs_e, _, _ = M.simulate(tasks, "edf", horizon)
    s_r = M.misses_summary(jobs_r)
    s_e = M.misses_summary(jobs_e)
    assert s_e["deadline_misses"] < s_r["deadline_misses"]
    assert s_e["deadline_misses"] == 1
    assert s_e["late_completed"] == 0


def test_determinism_double_run():
    for p in SC.values():
        _, tasks, horizon = M.load_scenario(p)
        for policy in ("rm", "edf"):
            _, g1, _ = M.simulate(tasks, policy, horizon)
            _, g2, _ = M.simulate(tasks, policy, horizon)
            assert g1 == g2


def test_metrics_schema():
    m = json.loads((ROOT / "output" / "metrics.json").read_text())
    assert set(m) == set(SC)
    for name, rec in m.items():
        for key in ("utilization", "hyperperiod", "rm_bound", "rta", "edf_demand_bound_ok", "rm", "edf"):
            assert key in rec, (name, key)
        for policy in ("rm", "edf"):
            for key in ("deadline_misses", "late_completed", "unfinished", "jobs_released",
                        "jobs_completed", "avg_response", "max_tardiness", "dispatches", "context_switches"):
                assert key in rec[policy], (name, policy, key)


def test_demand_bound_file_has_no_violations_ex3_4():
    text = (ROOT / "output" / "ex3_4_constrained_deadlines_demand_bound.txt").read_text()
    assert "VIOLATION" not in text
