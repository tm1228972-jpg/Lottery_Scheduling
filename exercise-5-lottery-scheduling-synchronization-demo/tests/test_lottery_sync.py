import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from lottery_sync import LotteryMutex, run_demo, simulate_lottery


def test_reference_lottery_is_reproducible():
    tickets = {"P1": 5, "P2": 3, "P3": 2}
    assert simulate_lottery(tickets, 500, 42) == simulate_lottery(tickets, 500, 42)
    assert simulate_lottery(tickets, 500, 42) != simulate_lottery(tickets, 500, 43)


def test_weighted_lock_preserves_mutual_exclusion_and_counter():
    result = run_demo(decisions=600, seed=2026)
    assert result["protected_counter"] == 600
    assert result["max_simultaneous_critical_sections"] == 1
    assert result["mutual_exclusion_verified"] is True
    assert sum(result["counts"].values()) == 600


def test_lottery_mutex_rejects_invalid_weights():
    lock = LotteryMutex(seed=7, grant_limit=1)
    try:
        lock.acquire("bad", 0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero ticket count must be rejected")
