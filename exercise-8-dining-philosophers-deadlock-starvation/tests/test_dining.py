import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from dining import (
    FairDiningMonitor,
    detect_deadlock_cycle,
    run_fair_monitor,
    run_resource_hierarchy,
)


def test_constructed_circular_wait_is_detected_and_cleaned_up():
    result = detect_deadlock_cycle(count=5, timeout=0.03)
    assert result["deadlock_witness"] is True
    assert all(not row["acquired_right_fork"] for row in result["outcomes"])


def test_global_fork_order_completes_without_deadlock():
    result = run_resource_hierarchy(count=5, meals=8)
    assert result["all_meals_completed"] is True
    assert result["completed_meals"] == [8] * 5


def test_fair_monitor_preserves_nonconflicting_concurrency_and_safety():
    result = run_fair_monitor(count=5, meals=8)
    assert result["all_meals_completed"] is True
    assert result["mutual_exclusion_verified"] is True
    assert result["max_simultaneous_eaters"] <= 2
    assert len(result["entry_log"]) == 40


def test_fair_monitor_does_not_let_later_conflicting_request_overtake():
    monitor = FairDiningMonitor(5)
    monitor.acquire(0)  # keep P0 eating; P1 conflicts with P0, P2 does not
    p1_entered = threading.Event()
    p1_release = threading.Event()
    p2_entered = threading.Event()

    def p1():
        monitor.acquire(1)
        p1_entered.set()
        p1_release.wait(timeout=2)
        monitor.release(1)

    def p2():
        monitor.acquire(2)
        p2_entered.set()
        monitor.release(2)

    first = threading.Thread(target=p1)
    first.start()
    deadline = time.monotonic() + 1
    while monitor.waiting_count < 1 and time.monotonic() < deadline:
        time.sleep(0.001)
    assert monitor.waiting_count == 1

    second = threading.Thread(target=p2)
    second.start()
    deadline = time.monotonic() + 1
    while monitor.waiting_count < 2 and time.monotonic() < deadline:
        time.sleep(0.001)
    assert monitor.waiting_count == 2

    monitor.release(0)
    assert p1_entered.wait(1)
    assert not p2_entered.wait(0.05)
    p1_release.set()
    assert p2_entered.wait(1)
    first.join(timeout=1)
    second.join(timeout=1)
    assert not first.is_alive() and not second.is_alive()


def test_monitor_rejects_invalid_philosopher():
    monitor = FairDiningMonitor(5)
    try:
        monitor.acquire(5)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid index must be rejected")
