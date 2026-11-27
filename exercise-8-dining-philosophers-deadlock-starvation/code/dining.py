#!/usr/bin/env python3
"""Dining Philosophers: deadlock witness, resource hierarchy, and fair monitor."""
from __future__ import annotations

import argparse
import json
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path


def conflicts(left: int, right: int, count: int) -> bool:
    """True when two philosophers need at least one common fork."""
    return left == right or (left - right) % count in (1, count - 1)


def detect_deadlock_cycle(count: int = 5, timeout: float = 0.08) -> dict:
    """Construct the circular-wait pattern, then release cleanly on timeout.

    Each philosopher first takes its left fork, synchronizes at a barrier, and
    then asks for its right fork. In the constructed state all left forks are
    held, so every right-fork request is blocked. Timeouts are used only to
    collect a finite witness and clean up; they are not the deadlock solution.
    """
    if count < 3 or timeout <= 0:
        raise ValueError("count must be >= 3 and timeout must be positive")
    forks = [threading.Lock() for _ in range(count)]
    barrier = threading.Barrier(count)
    # Do not release any left fork until every right-fork request has timed out
    # or completed; otherwise the first timeout could let a neighbour acquire.
    outcomes_barrier = threading.Barrier(count)
    outcomes: list[dict] = [{} for _ in range(count)]

    def philosopher(index: int) -> None:
        left = index
        right = (index + 1) % count
        forks[left].acquire()
        try:
            barrier.wait(timeout=2)
            acquired = forks[right].acquire(timeout=timeout)
            outcomes[index] = {
                "philosopher": index,
                "holds_left_fork": True,
                "acquired_right_fork": acquired,
            }
            if acquired:
                forks[right].release()
            # All requests observe the same circular-wait state before cleanup.
            outcomes_barrier.wait(timeout=2)
        except threading.BrokenBarrierError:
            outcomes[index] = {
                "philosopher": index,
                "holds_left_fork": True,
                "acquired_right_fork": False,
                "barrier_broken": True,
            }
        finally:
            forks[left].release()

    threads = [
        threading.Thread(target=philosopher, args=(i,), daemon=True, name=f"P{i}")
        for i in range(count)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout + 3)
    if any(thread.is_alive() for thread in threads):
        raise TimeoutError("deadlock witness threads failed to clean up")
    return {
        "philosophers": count,
        "timeout_seconds": timeout,
        "outcomes": outcomes,
        "deadlock_witness": (
            len(outcomes) == count
            and all(row.get("holds_left_fork") and not row.get("acquired_right_fork")
                    for row in outcomes)
        ),
        "explanation": (
            "Every philosopher held one fork and waited for the next fork in a "
            "cycle. The timeout lets the demonstration terminate after recording "
            "the deadlock state; a real deadlock would wait indefinitely."
        ),
    }


def run_resource_hierarchy(count: int = 5, meals: int = 20) -> dict:
    """Break circular wait by acquiring fork locks in a global numeric order."""
    if count < 3 or meals <= 0:
        raise ValueError("count must be >= 3 and meals must be positive")
    forks = [threading.Lock() for _ in range(count)]
    completed = [0] * count
    errors: list[str] = []

    def philosopher(index: int) -> None:
        left, right = index, (index + 1) % count
        first, second = sorted((left, right))
        for _ in range(meals):
            try:
                with forks[first]:
                    with forks[second]:
                        time.sleep(0.00005)
                        completed[index] += 1
            except Exception as exc:  # pragma: no cover
                errors.append(f"P{index}: {exc!r}")
                return

    threads = [threading.Thread(target=philosopher, args=(i,), name=f"P{i}")
               for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    alive = [t.name for t in threads if t.is_alive()]
    if alive:
        raise TimeoutError(f"resource-hierarchy threads stuck: {alive}")
    return {
        "solution": "resource-hierarchy",
        "philosophers": count,
        "meals_per_philosopher": meals,
        "completed_meals": completed,
        "all_meals_completed": all(value == meals for value in completed),
        "errors": errors,
        "deadlock_argument": (
            "Every fork is acquired in increasing numeric order. A cycle in the "
            "wait-for graph would require a strictly increasing sequence of fork "
            "numbers to return to its starting fork, which is impossible."
        ),
        "starvation_note": (
            "A global lock order eliminates circular wait, but Python Lock does "
            "not promise FIFO acquisition; starvation freedom is not claimed."
        ),
    }


class FairDiningMonitor:
    """A monitor that preserves FIFO order among requests sharing a fork.

    A request may pass older queued requests only when they are non-conflicting.
    This allows non-neighbouring philosophers to eat concurrently while a
    conflicting later request cannot overtake an earlier one.
    """

    def __init__(self, count: int = 5):
        if count < 3:
            raise ValueError("count must be >= 3")
        self.count = count
        self._condition = threading.Condition()
        self._queue: deque[int] = deque()
        self._eating: set[int] = set()
        self.entry_log: list[int] = []
        self.max_eating = 0
        self.violations: list[str] = []

    @property
    def waiting_count(self) -> int:
        with self._condition:
            return len(self._queue)

    def acquire(self, philosopher: int) -> float:
        if not 0 <= philosopher < self.count:
            raise ValueError("invalid philosopher index")
        with self._condition:
            self._queue.append(philosopher)
            started = time.perf_counter()
            while True:
                active_conflict = any(
                    conflicts(philosopher, active, self.count)
                    for active in self._eating
                )
                earlier_conflict = False
                for earlier in self._queue:
                    if earlier == philosopher:
                        break
                    if conflicts(philosopher, earlier, self.count):
                        earlier_conflict = True
                        break
                if not active_conflict and not earlier_conflict:
                    break
                self._condition.wait()
            self._queue.remove(philosopher)
            if any(conflicts(philosopher, active, self.count) for active in self._eating):
                self.violations.append("conflicting philosophers entered together")
            self._eating.add(philosopher)
            self.entry_log.append(philosopher)
            self.max_eating = max(self.max_eating, len(self._eating))
            return time.perf_counter() - started

    def release(self, philosopher: int) -> None:
        with self._condition:
            if philosopher not in self._eating:
                raise RuntimeError("philosopher is not eating")
            self._eating.remove(philosopher)
            self._condition.notify_all()


def run_fair_monitor(count: int = 5, meals: int = 20) -> dict:
    """Run finite meals under the fair monitor and return safety/fairness evidence."""
    if meals <= 0:
        raise ValueError("meals must be positive")
    monitor = FairDiningMonitor(count)
    completed = [0] * count
    wait_samples: list[float] = []
    sample_lock = threading.Lock()

    def philosopher(index: int) -> None:
        for _ in range(meals):
            waited = monitor.acquire(index)
            try:
                with sample_lock:
                    wait_samples.append(waited)
                time.sleep(0.00005)
                completed[index] += 1
            finally:
                monitor.release(index)

    threads = [threading.Thread(target=philosopher, args=(i,), name=f"P{i}")
               for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    alive = [t.name for t in threads if t.is_alive()]
    if alive:
        raise TimeoutError(f"fair-monitor threads stuck: {alive}")
    return {
        "solution": "fair-monitor",
        "philosophers": count,
        "meals_per_philosopher": meals,
        "completed_meals": completed,
        "all_meals_completed": all(value == meals for value in completed),
        "max_simultaneous_eaters": monitor.max_eating,
        "theoretical_max_simultaneous_eaters": count // 2,
        "mutual_exclusion_verified": not monitor.violations,
        "violations": monitor.violations,
        "entry_log": monitor.entry_log,
        "mean_wait_ms": (sum(wait_samples) / len(wait_samples) * 1000
                         if wait_samples else 0.0),
        "fairness_argument": (
            "A request is never passed by an earlier queued request that shares "
            "a fork. With finite eating intervals and fair OS thread scheduling, "
            "each philosopher's finite set of conflicting predecessors leaves."
        ),
        "assumption": "Fairness is conditional on finite critical sections and OS thread scheduling.",
    }


def run_all() -> dict:
    return {
        "deadlock_demo": detect_deadlock_cycle(),
        "resource_hierarchy": run_resource_hierarchy(),
        "fair_monitor": run_fair_monitor(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "output")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = run_all()
    target = args.output / "dining_philosophers_results.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
