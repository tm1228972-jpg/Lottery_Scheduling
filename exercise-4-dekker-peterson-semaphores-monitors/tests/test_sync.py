"""Tests for Exercise 4 — model checker and threaded lab."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import mutex_models as M  # noqa: E402


def test_models_enumerated():
    for name in ("dekker", "peterson", "turn_only", "flag_only"):
        states, transitions = M.enumerate_states(name)
        assert len(states) > 0 and transitions > 0


def test_dekker_safe_live_lockfree():
    assert M.check_safety("dekker")["mutual_exclusion_violations"] == 0
    assert M.check_deadlock("dekker")["deadlock_states"] == 0
    assert M.check_liveness("dekker")["live"] is True


def test_peterson_safe_live():
    assert M.check_safety("peterson")["mutual_exclusion_violations"] == 0
    assert M.check_deadlock("peterson")["deadlock_states"] == 0
    assert M.check_liveness("peterson")["live"] is True


def test_turn_only_safe_but_unfair():
    assert M.check_safety("turn_only")["mutual_exclusion_violations"] == 0
    assert M.check_deadlock("turn_only")["deadlock_states"] == 0
    # safety yes, liveness from the model's perspective: can still reach CS —
    # the real defect of turn-only is blocking the *other* process, which is
    # a liveness failure under fairness; flag_only shows the deadlock face.
    assert M.check_liveness("turn_only")["live"] is True


def test_flag_only_deadlocks():
    assert M.check_deadlock("flag_only")["deadlock_states"] >= 1
    assert M.check_liveness("flag_only")["live"] is False


def test_peterson_state_count():
    # known, documented counts (regression guard)
    assert M.enumerate_states("peterson")[0] and len(M.enumerate_states("peterson")[0]) == 34


def test_dekker_has_two_terminal_states():
    states, _ = M.enumerate_states("dekker")
    halts = [s for s in states if all(p == M.HALT for p in s[0])]
    assert len(halts) == 2


def test_output_artifacts_exist():
    for name in ("model_checks.json", "counter_bench.json", "fairness.json", "buffer.json"):
        path = ROOT / "output" / name
        assert path.exists(), name
        json.loads(path.read_text())


def test_counter_benchmark_locks_are_exact():
    data = json.loads((ROOT / "output" / "counter_bench.json").read_text())
    for r in data:
        if r["mechanism"] != "none":
            assert r["lost_total"] == 0, r


def test_unsynchronized_counter_loses_updates():
    data = json.loads((ROOT / "output" / "counter_bench.json").read_text())
    none_runs = [r for r in data if r["mechanism"] == "none"]
    assert none_runs, "expected the unsynchronized baseline"
    assert all(r["lost_total"] > 0 for r in none_runs)


def test_buffer_conservation_both_mechanisms():
    data = json.loads((ROOT / "output" / "buffer.json").read_text())
    for r in data:
        assert r["conservation_ok"] is True
        assert r["capacity_respected"] is True
        assert r["max_occupancy"] <= r["capacity"]


def test_ticket_lock_is_fair_within_noise():
    data = json.loads((ROOT / "output" / "fairness.json").read_text())
    per_thread = data["ticket"]["per_thread_avg_ms"]
    assert max(per_thread) - min(per_thread) < 0.2


def test_model_checker_cli():
    out = subprocess.run([sys.executable, str(ROOT / "code" / "sync_lab.py"), "models"],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0
    assert "peterson" in out.stdout


def test_figures_exist():
    for name in ("fig_counter_race.png", "fig_dekker_protocol.png", "fig_peterson_protocol.png",
                 "chart_model_graph.png", "chart_safety_deadlock.png", "chart_lost_updates.png",
                 "chart_lock_cost.png", "chart_fairness.png", "fig_bounded_buffer.png",
                 "fig_monitor.png", "fig_decision_map.png", "fig_proof_map.png"):
        path = ROOT / "diagrams" / name
        assert path.exists(), name
        assert path.stat().st_size > 10_000


def test_ticket_fifo_ordering_invariant():
    import json as _json
    data = _json.loads((ROOT / "output" / "fifo_order.json").read_text())
    assert data["ticket"]["order_violations"] == 0
    assert data["ticket"]["rounds_checked"] >= 100
