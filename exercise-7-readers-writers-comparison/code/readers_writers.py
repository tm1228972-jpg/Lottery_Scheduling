#!/usr/bin/env python3
"""Compare reader-preference, writer-preference, and FIFO-fair read/write locks."""
from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Waiter:
    request_id: int
    kind: str


class ReaderWriterLock:
    """Read/write lock with three explicit admission policies.

    reader: readers may pass waiting writers (writer starvation is possible).
    writer: new readers wait while any writer is queued (reader starvation is
            possible under a continuing stream of writers).
    fair: requests queue in arrival order; consecutive head readers may batch,
          but a later reader cannot pass a waiting writer.
    """

    def __init__(self, policy: str = "fair"):
        if policy not in {"reader", "writer", "fair"}:
            raise ValueError("policy must be reader, writer, or fair")
        self.policy = policy
        self._condition = threading.Condition()
        self._queue: deque[Waiter] = deque()
        self._next_id = 0
        self._active_readers = 0
        self._active_writer = False
        self._waiting_writers = 0
        self.peak_readers = 0
        self.write_entries = 0
        self.read_entries = 0

    @property
    def waiting_count(self) -> int:
        with self._condition:
            return len(self._queue)

    def _request(self, kind: str) -> Waiter:
        req = Waiter(self._next_id, kind)
        self._next_id += 1
        return req

    def acquire_read(self) -> float:
        with self._condition:
            req = self._request("R")
            if self.policy == "fair":
                self._queue.append(req)
            started = time.perf_counter()
            while not self._can_read(req):
                self._condition.wait()
            if self.policy == "fair":
                self._queue.remove(req)
            self._active_readers += 1
            self.peak_readers = max(self.peak_readers, self._active_readers)
            self.read_entries += 1
            self._condition.notify_all()
            return time.perf_counter() - started

    def release_read(self) -> None:
        with self._condition:
            if self._active_readers <= 0:
                raise RuntimeError("release_read without a matching acquire_read")
            self._active_readers -= 1
            self._condition.notify_all()

    def acquire_write(self) -> float:
        with self._condition:
            req = self._request("W")
            self._waiting_writers += 1
            if self.policy == "fair":
                self._queue.append(req)
            started = time.perf_counter()
            while not self._can_write(req):
                self._condition.wait()
            if self.policy == "fair":
                self._queue.remove(req)
            self._waiting_writers -= 1
            self._active_writer = True
            self.write_entries += 1
            return time.perf_counter() - started

    def release_write(self) -> None:
        with self._condition:
            if not self._active_writer:
                raise RuntimeError("release_write without a matching acquire_write")
            self._active_writer = False
            self._condition.notify_all()

    def _can_read(self, req: Waiter) -> bool:
        if self._active_writer:
            return False
        if self.policy == "reader":
            return True
        if self.policy == "writer":
            return self._waiting_writers == 0
        for queued in self._queue:
            if queued is req:
                return True
            if queued.kind == "W":
                return False
        return False

    def _can_write(self, req: Waiter) -> bool:
        if self._active_writer or self._active_readers:
            return False
        if self.policy == "fair":
            return bool(self._queue) and self._queue[0] is req
        return True

    @contextmanager
    def read_lock(self) -> Iterator[float]:
        waited = self.acquire_read()
        try:
            yield waited
        finally:
            self.release_read()

    @contextmanager
    def write_lock(self) -> Iterator[float]:
        waited = self.acquire_write()
        try:
            yield waited
        finally:
            self.release_write()


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * p)))
    return ordered[index]


def run_benchmark(policy: str, readers: int = 6, writers: int = 2,
                  operations: int = 80, seed_delay: float = 0.0002) -> dict:
    lock = ReaderWriterLock(policy)
    payload = {"version": 0}
    wait_readers: list[float] = []
    wait_writers: list[float] = []
    sample_lock = threading.Lock()
    errors: list[str] = []

    def reader_task() -> None:
        for _ in range(operations):
            with lock.read_lock() as waited:
                with sample_lock:
                    wait_readers.append(waited)
                    observed = payload["version"]
                time.sleep(seed_delay)
                if observed < 0:
                    errors.append("impossible negative version")

    def writer_task() -> None:
        for _ in range(max(1, operations // 4)):
            with lock.write_lock() as waited:
                with sample_lock:
                    wait_writers.append(waited)
                    payload["version"] += 1
                time.sleep(seed_delay * 1.5)

    threads = [threading.Thread(target=reader_task) for _ in range(readers)]
    threads += [threading.Thread(target=writer_task) for _ in range(writers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    alive = [thread.name for thread in threads if thread.is_alive()]
    if alive:
        raise TimeoutError(f"threads did not finish: {alive}")
    if errors:
        raise RuntimeError("; ".join(errors))

    def stats(values: list[float]) -> dict:
        return {
            "samples": len(values),
            "mean_ms": statistics.fmean(values) * 1000 if values else 0.0,
            "p50_ms": percentile(values, 0.50) * 1000,
            "p95_ms": percentile(values, 0.95) * 1000,
            "max_ms": max(values, default=0.0) * 1000,
        }

    return {
        "policy": policy,
        "configuration": {
            "readers": readers, "writers": writers, "reader_operations": operations,
            "writer_operations_per_thread": max(1, operations // 4),
        },
        "reader_wait": stats(wait_readers),
        "writer_wait": stats(wait_writers),
        "final_version": payload["version"],
        "peak_simultaneous_readers": lock.peak_readers,
        "read_entries": lock.read_entries,
        "write_entries": lock.write_entries,
        "errors": errors,
        "note": "Observed host-thread timing is an experiment, not a scheduler-independent guarantee.",
    }


def run_all() -> dict:
    return {
        "method": "Concurrent CPython threads; same operation counts and critical-section duration per policy.",
        "policies": {
            name: run_benchmark(name)
            for name in ("reader", "writer", "fair")
        },
        "conclusion_guard": (
            "Reader priority can starve writers; writer priority can starve readers; "
            "the fair queue avoids bypass under the stated finite-critical-section assumption."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "output")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = run_all()
    (args.output / "readers_writers_results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
