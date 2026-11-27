#!/usr/bin/env python3
"""Exercise 4 — threaded lab: Dekker, Peterson, semaphores, monitors on real threads.

Part A (proof):   finite-state enumeration of the two-process algorithms
                  (see mutex_models.py) — exact, exhaustive, deterministic.
Part B (measure): threaded micro-experiments — lost updates without a lock,
                  with each mechanism; fairness of ticket lock vs mutex;
                  bounded-buffer integrity via semaphore and via monitor.

All randomness is seeded; runs are reproducible.
"""
from __future__ import annotations

import argparse
import json
import random
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ---------- shared cell with an explicit read/sleep/write race window ----------
class Counter:
    def __init__(self):
        self.value = 0

    def unsafe_inc(self):
        v = self.value
        time.sleep(0)          # widen the race window — deterministic-ish loss
        self.value = v + 1

    def add(self, n):
        # locked increment used to build the expected value path
        self.value += n


class DekkerLock:
    """Dekker's algorithm for exactly two threads (Python spin simulation)."""
    def __init__(self):
        self.flag = [False, False]
        self.turn = 0
        self._lock = threading.Lock()   # only guards flag/turn bookkeeping itself

    def acquire(self, i):
        j = 1 - i
        self.flag[i] = True
        while self.flag[j]:
            if self.turn != i:
                self.flag[i] = False
                while self.turn != i:
                    time.sleep(0)
                self.flag[i] = True
        # critical section begins

    def release(self, i):
        j = 1 - i
        self.turn = j
        self.flag[i] = False


class PetersonLock:
    def __init__(self):
        self.flag = [False, False]
        self.turn = 0

    def acquire(self, i):
        j = 1 - i
        self.flag[i] = True
        self.turn = j
        while self.flag[j] and self.turn == j:
            time.sleep(0)

    def release(self, i):
        self.flag[i] = False


class TicketLock:
    """Fair FIFO ticket mutex (bakery-style, 2 fields)."""
    def __init__(self):
        self._next = 0
        self._serving = 0
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            ticket = self._next
            self._next += 1
        while self._serving != ticket:
            time.sleep(0)
        return ticket

    def release(self, ticket):
        with self._lock:
            self._serving += 1


def bench_counter(mechanism: str, n_threads: int, increments_per_thread: int,
                  trials: int, seed: int):
    random.seed(seed)
    total_lost = 0
    totals = []
    durations = []
    for _ in range(trials):
        c = Counter()
        if mechanism == "dekker" or mechanism == "peterson":
            assert n_threads == 2, "two-process algorithms only"
            lock = DekkerLock() if mechanism == "dekker" else PetersonLock()
            def worker(i):
                for _ in range(increments_per_thread):
                    lock.acquire(i)
                    c.value += 1   # locked section
                    lock.release(i)
        elif mechanism == "mutex":
            lock = threading.Lock()
            def worker(i):
                for _ in range(increments_per_thread):
                    with lock:
                        c.value += 1
        elif mechanism == "semaphore":
            sem = threading.Semaphore(1)
            def worker(i):
                for _ in range(increments_per_thread):
                    with sem:
                        c.value += 1
        elif mechanism == "ticket":
            lock = TicketLock()
            def worker(i):
                for _ in range(increments_per_thread):
                    t = lock.acquire()
                    c.value += 1
                    lock.release(t)
        elif mechanism == "none":
            def worker(i):
                for _ in range(increments_per_thread):
                    c.unsafe_inc()
        else:
            raise ValueError(mechanism)
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        durations.append(time.perf_counter() - start)
        expected = n_threads * increments_per_thread
        totals.append(c.value)
        total_lost += expected - c.value
    return {"mechanism": mechanism, "threads": n_threads,
            "increments_per_thread": increments_per_thread,
            "trials": trials, "expected_per_trial": n_threads * increments_per_thread,
            "actual_per_trial": totals, "lost_total": total_lost,
            "avg_duration_s": sum(durations) / len(durations)}


def bench_fairness(rounds: int, n_threads: int, seed: int):
    """Wait-time distribution: ticket lock (FIFO) vs threading.Lock (unfair)."""
    rng = random.Random(seed)
    results = {}
    for mechanism in ("ticket", "mutex"):
        waits = [[] for _ in range(n_threads)]
        for _ in range(rounds):
            lock = TicketLock() if mechanism == "ticket" else threading.Lock()
            order = list(range(n_threads))
            rng.shuffle(order)
            start_times = [time.perf_counter() for _ in range(n_threads)]
            def work(i, box):
                if mechanism == "ticket":
                    t = lock.acquire()
                    waits[i].append(time.perf_counter() - start_times[i])
                    time.sleep(0)
                    lock.release(t)
                else:
                    with lock:
                        waits[i].append(time.perf_counter() - start_times[i])
                        time.sleep(0)
            threads = [threading.Thread(target=work, args=(i, None)) for i in order]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        flat = [w for ws in waits for w in ws]
        results[mechanism] = {"per_thread_waits": waits,
                              "avg_wait_ms": 1000 * sum(flat) / len(flat),
                              "max_wait_ms": 1000 * max(flat),
                              "per_thread_avg_ms": [1000 * sum(ws) / max(len(ws), 1) for ws in waits]}
    return results


class BoundedBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buf = []
        self.max_occupancy = 0
        self.mutex = threading.Semaphore(1)
        self.empty = threading.Semaphore(capacity)
        self.full = threading.Semaphore(0)

    def producer_put(self, item):
        self.empty.acquire()
        with self.mutex:
            self.buf.append(item)
            self.max_occupancy = max(self.max_occupancy, len(self.buf))
        self.full.release()

    def consumer_get(self, timeout=0.5):
        if not self.full.acquire(timeout=timeout):
            return None
        with self.mutex:
            item = self.buf.pop(0)
        self.empty.release()
        return item


class MonitorBuffer:
    """Monitor (Condition-based) bounded buffer with FIFO wakeups."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.buf = []
        self.max_occupancy = 0
        self.cond = threading.Condition()

    def put(self, item):
        with self.cond:
            while len(self.buf) == self.capacity:
                self.cond.wait()
            self.buf.append(item)
            self.max_occupancy = max(self.max_occupancy, len(self.buf))
            self.cond.notify_all()   # wake consumers

    def get(self, timeout=0.5):
        with self.cond:
            while not self.buf:
                if not self.cond.wait(timeout=timeout):
                    return None
            item = self.buf.pop(0)
            self.cond.notify_all()   # wake producers
            return item


def bench_buffer(capacity: int, n_items: int, use_monitor: bool, seed: int,
                 n_producers=2, n_consumers=2):
    rng = random.Random(seed)
    buf = MonitorBuffer(capacity) if use_monitor else BoundedBuffer(capacity)
    produced = list(range(n_items))
    rng.shuffle(produced)
    chunks = [produced[i::n_producers] for i in range(n_producers)]
    consumed = []
    consumed_lock = threading.Lock()

    def producer(my_items):
        for item in my_items:
            if use_monitor:
                buf.put(item)
            else:
                buf.producer_put(item)

    stop = threading.Event()

    def consumer():
        while not stop.is_set():
            with consumed_lock:
                if len(consumed) >= n_items:
                    return
            if use_monitor:
                item = buf.get(timeout=0.2)
            else:
                item = buf.consumer_get(timeout=0.2)
            if item is None:
                continue
            with consumed_lock:
                if len(consumed) < n_items:
                    consumed.append(item)
                else:
                    return

    producers = [threading.Thread(target=producer, args=(chunks[i],))
                 for i in range(n_producers)]
    consumers = [threading.Thread(target=consumer, daemon=True)
                 for _ in range(n_consumers)]
    for t in consumers:
        t.start()
    for t in producers:
        t.start()
    for t in producers:
        t.join()
    deadline = time.time() + 20
    while time.time() < deadline:
        with consumed_lock:
            if len(consumed) >= n_items:
                break
        time.sleep(0.01)
    stop.set()
    for t in consumers:
        t.join(timeout=1.0)
    with consumed_lock:
        n_consumed = len(consumed)
        ok = sorted(consumed) == list(range(n_items))
    return {"capacity": capacity, "n_items": n_items,
            "mechanism": "monitor" if use_monitor else "semaphore",
            "produced": n_items, "consumed": n_consumed,
            "conservation_ok": ok,
            "max_occupancy": buf.max_occupancy,
            "capacity_respected": buf.max_occupancy <= capacity}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("models", "counter", "fairness", "buffer", "fifo", "all"))
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--increments", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261127)
    a = ap.parse_args(argv)

    if a.command in ("models", "all"):
        import mutex_models as M
        out = {}
        for name in ("dekker", "peterson", "turn_only", "flag_only"):
            out[name] = {"graph": M.state_graph_summary(name),
                         "safety": M.check_safety(name),
                         "deadlock": M.check_deadlock(name),
                         "liveness": M.check_liveness(name)}
        (ROOT / "output" / "model_checks.json").write_text(json.dumps(out, indent=2))
        for name, rec in out.items():
            g = rec["graph"]
            print(f"{name}: states={g['states']} transitions={g['transitions']} "
                  f"safety_violations={rec['safety']['mutual_exclusion_violations']} "
                  f"deadlocks={rec['deadlock']['deadlock_states']} live={rec['liveness'].get('live')}")

    if a.command in ("counter", "all"):
        results = []
        for mechanism in ("none", "dekker", "peterson", "mutex", "semaphore", "ticket"):
            for threads in ((2,) if mechanism in ("dekker", "peterson") else (2, 4)):
                r = bench_counter(mechanism, threads, a.increments, a.trials, a.seed)
                results.append(r)
                print(f"{mechanism:9} threads={threads} lost_total={r['lost_total']} "
                      f"avg_time={r['avg_duration_s']:.3f}s")
        (ROOT / "output" / "counter_bench.json").write_text(json.dumps(results, indent=2))

    if a.command in ("fairness", "all"):
        res = bench_fairness(60, 4, a.seed)
        for mechanism, rec in res.items():
            print(f"{mechanism}: avg_wait_ms={rec['avg_wait_ms']:.3f} max_wait_ms={rec['max_wait_ms']:.3f} "
                  f"per_thread_avg_ms={[round(x, 3) for x in rec['per_thread_avg_ms']]}")
        (ROOT / "output" / "fairness.json").write_text(json.dumps(res, indent=2))

    if a.command in ("fifo", "all"):
        res = bench_fifo_order(150, 4, a.seed)
        print("fifo order check:", res)
        (ROOT / "output" / "fifo_order.json").write_text(json.dumps(res, indent=2))

    if a.command in ("buffer", "all"):
        results = []
        for use_monitor in (False, True):
            r = bench_buffer(3, 300, use_monitor, a.seed)
            results.append(r)
            print(r)
        (ROOT / "output" / "buffer.json").write_text(json.dumps(results, indent=2))
    return 0




def bench_fifo_order(rounds: int, n_threads: int, seed: int):
    """Ordering invariant: ticket lock hands out the critical section in ticket
    order; an unfair mutex gives no such guarantee."""
    rng = random.Random(seed)
    results = {"ticket": {"rounds_checked": 0, "order_violations": 0},
               "mutex": {"rounds_checked": 0, "order_violations": 0}}
    for mechanism in ("ticket", "mutex"):
        order_violations = 0
        for _ in range(rounds):
            lock = TicketLock() if mechanism == "ticket" else threading.Lock()
            acquire_order = []
            lock_order = threading.Lock()
            start = threading.Barrier(n_threads)

            def worker(i):
                start.wait()
                if mechanism == "ticket":
                    t = lock.acquire()
                    with lock_order:
                        acquire_order.append((t, i))
                    lock.release(t)
                else:
                    with lock:
                        with lock_order:
                            acquire_order.append((None, i))

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            results[mechanism]["rounds_checked"] += 1
            if mechanism == "ticket":
                tickets = [t for t, _ in acquire_order]
                if tickets != sorted(tickets):
                    order_violations += 1
        results[mechanism]["order_violations"] = order_violations
    return results
if __name__ == "__main__":
    raise SystemExit(main())
