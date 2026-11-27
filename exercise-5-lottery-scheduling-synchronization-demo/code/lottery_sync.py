#!/usr/bin/env python3
"""Threaded, weighted lottery mutex: a runnable synchronization demonstration."""
from __future__ import annotations

import argparse
import json
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Request:
    request_id: int
    process: str
    tickets: int


class LotteryMutex:
    """A mutual-exclusion lock that lotteries among currently waiting requests.

    A winner owns the critical section until release(). Ticket weights affect
    the probability of receiving the next lock grant. This models the
    lock/resource-allocation extension discussed by Waldspurger and Weihl;
    it is not a replacement for an operating-system CPU scheduler.
    """

    def __init__(self, seed: int = 20261127, grant_limit: int = 1000):
        if grant_limit <= 0:
            raise ValueError("grant_limit must be positive")
        self._condition = threading.Condition()
        self._rng = random.Random(seed)
        self._grant_limit = grant_limit
        self._next_request_id = 0
        self._waiters: list[Request] = []
        self._owner: Optional[Request] = None
        self._closed = False
        self.draws: list[dict] = []

    def _choose_next(self) -> None:
        if self._owner is not None or not self._waiters or self._closed:
            return
        total = sum(req.tickets for req in self._waiters)
        winning_ticket = self._rng.randint(1, total)
        cumulative = 0
        winner = None
        for req in self._waiters:
            cumulative += req.tickets
            if winning_ticket <= cumulative:
                winner = req
                break
        assert winner is not None
        self._waiters.remove(winner)
        self._owner = winner
        self.draws.append({
            "decision": len(self.draws) + 1,
            "process": winner.process,
            "tickets": winner.tickets,
            "total_waiting_tickets": total,
            "winning_ticket": winning_ticket,
        })

    def acquire(self, process: str, tickets: int) -> Optional[Request]:
        if tickets <= 0:
            raise ValueError("tickets must be positive")
        with self._condition:
            if self._closed:
                return None
            req = Request(self._next_request_id, process, tickets)
            self._next_request_id += 1
            self._waiters.append(req)
            self._choose_next()
            while self._owner is not req and not self._closed:
                self._condition.wait()
            return req if self._owner is req else None

    def release(self, request: Request) -> None:
        with self._condition:
            if self._owner is not request:
                raise RuntimeError("only the current owner may release the lottery mutex")
            self._owner = None
            if len(self.draws) >= self._grant_limit:
                self._closed = True
                self._waiters.clear()
            else:
                self._choose_next()
            self._condition.notify_all()


def simulate_lottery(tickets: dict[str, int], decisions: int, seed: int) -> list[dict]:
    """Pure deterministic reference trace with every process continuously runnable."""
    if not tickets or any(value <= 0 for value in tickets.values()):
        raise ValueError("tickets must be a non-empty mapping of positive integers")
    if decisions < 0:
        raise ValueError("decisions must be non-negative")
    rng = random.Random(seed)
    names = list(tickets)
    total = sum(tickets.values())
    trace = []
    for decision in range(1, decisions + 1):
        draw = rng.randint(1, total)
        cumulative = 0
        winner = names[-1]
        for name in names:
            cumulative += tickets[name]
            if draw <= cumulative:
                winner = name
                break
        trace.append({
            "decision": decision,
            "process": winner,
            "tickets": tickets[winner],
            "total_waiting_tickets": total,
            "winning_ticket": draw,
        })
    return trace


def run_demo(decisions: int = 3000, seed: int = 20261127) -> dict:
    """Run real Python threads contending for one weighted synchronization lock."""
    if decisions <= 0:
        raise ValueError("decisions must be positive")
    ticket_map = {"P1": 5, "P2": 3, "P3": 2}
    mutex = LotteryMutex(seed=seed, grant_limit=decisions)
    # The lottery mutex itself must protect this state; no second mutex should
    # mask a broken ownership invariant in the demonstration.
    state = {"counter": 0, "active": 0, "max_active": 0}
    errors: list[str] = []

    def worker(name: str, weight: int) -> None:
        while True:
            request = mutex.acquire(name, weight)
            if request is None:
                return
            try:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
                old_value = state["counter"]
                time.sleep(0.00002)
                state["counter"] = old_value + 1
                state["active"] -= 1
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                errors.append(f"{name}: {exc!r}")
                raise
            finally:
                mutex.release(request)

    threads = [
        threading.Thread(target=worker, args=(name, weight), name=f"worker-{name}")
        for name, weight in ticket_map.items()
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    alive = [thread.name for thread in threads if thread.is_alive()]
    if alive:
        raise TimeoutError(f"workers did not terminate: {alive}")
    if errors:
        raise RuntimeError("; ".join(errors))

    counts = {name: 0 for name in ticket_map}
    for draw in mutex.draws:
        counts[draw["process"]] += 1
    total_tickets = sum(ticket_map.values())
    observed = {name: counts[name] / decisions for name in ticket_map}
    expected = {name: ticket_map[name] / total_tickets for name in ticket_map}
    return {
        "seed": seed,
        "decisions": decisions,
        "tickets": ticket_map,
        "counts": counts,
        "expected_shares": expected,
        "observed_shares": observed,
        "absolute_share_error": {
            name: abs(observed[name] - expected[name]) for name in ticket_map
        },
        "protected_counter": state["counter"],
        "max_simultaneous_critical_sections": state["max_active"],
        "mutual_exclusion_verified": state["max_active"] == 1,
        "errors": errors,
        "draws": mutex.draws,
        "interpretation": (
            "Weighted grants to a shared critical section. This demonstrates "
            "lottery-based lock/resource arbitration, not a kernel CPU scheduler."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20261127)
    parser.add_argument("--output", type=Path, default=Path(__file__).parents[1] / "output")
    args = parser.parse_args()
    result = run_demo(args.decisions, args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "lottery_sync_results.json").write_text(
        json.dumps({k: v for k, v in result.items() if k != "draws"}, indent=2),
        encoding="utf-8",
    )
    (args.output / "lottery_sync_trace.json").write_text(
        json.dumps(result["draws"], indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "draws"}, indent=2))


if __name__ == "__main__":
    main()
