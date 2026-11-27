#!/usr/bin/env python3
"""Reproducible comparison of randomized lottery and deterministic stride shares."""
from __future__ import annotations

import json
import random
from pathlib import Path


DEFAULT_TICKETS = {"P1": 5, "P2": 3, "P3": 2}


def lottery_counts(tickets: dict[str, int], decisions: int, seed: int) -> dict[str, int]:
    if not tickets or any(t <= 0 for t in tickets.values()):
        raise ValueError("tickets must be positive")
    rng = random.Random(seed)
    names = list(tickets)
    total = sum(tickets.values())
    counts = {name: 0 for name in names}
    for _ in range(decisions):
        draw = rng.randint(1, total)
        cumulative = 0
        for name in names:
            cumulative += tickets[name]
            if draw <= cumulative:
                counts[name] += 1
                break
    return counts


def stride_counts(tickets: dict[str, int], decisions: int,
                  stride_constant: int = 1_000_000) -> dict[str, int]:
    if not tickets or any(t <= 0 for t in tickets.values()):
        raise ValueError("tickets must be positive")
    names = list(tickets)
    strides = {name: stride_constant / tickets[name] for name in names}
    passes = {name: 0.0 for name in names}
    counts = {name: 0 for name in names}
    for _ in range(decisions):
        winner = min(names, key=lambda name: (passes[name], names.index(name)))
        counts[winner] += 1
        passes[winner] += strides[winner]
    return counts


def shares(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    return {name: count / total if total else 0.0 for name, count in counts.items()}


def run_experiment(decisions: int = 10_000, seeds: int = 50) -> dict:
    tickets = DEFAULT_TICKETS.copy()
    total_tickets = sum(tickets.values())
    target = {name: value / total_tickets for name, value in tickets.items()}
    lottery_rows = []
    for seed in range(seeds):
        observed = shares(lottery_counts(tickets, decisions, seed))
        lottery_rows.append({
            "seed": seed,
            "shares": observed,
            "max_absolute_share_error": max(abs(observed[n] - target[n]) for n in tickets),
        })
    stride_observed = shares(stride_counts(tickets, decisions))
    lottery_errors = [row["max_absolute_share_error"] for row in lottery_rows]
    return {
        "workload": {"tickets": tickets, "decisions_per_run": decisions, "seeds": seeds},
        "target_shares": target,
        "lottery": {
            "mean_max_absolute_share_error": sum(lottery_errors) / len(lottery_errors),
            "worst_max_absolute_share_error": max(lottery_errors),
            "runs": lottery_rows,
        },
        "stride": {
            "observed_shares": stride_observed,
            "max_absolute_share_error": max(abs(stride_observed[n] - target[n]) for n in tickets),
        },
        "scope_note": (
            "This is a single-CPU, always-runnable, equal-quantum allocation model. "
            "It does not measure wall-clock latency, cache effects, or a production kernel."
        ),
    }


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "output"
    output.mkdir(parents=True, exist_ok=True)
    result = run_experiment()
    (output / "scheduler_comparison.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "workload": result["workload"],
        "lottery_mean_error": result["lottery"]["mean_max_absolute_share_error"],
        "lottery_worst_error": result["lottery"]["worst_max_absolute_share_error"],
        "stride_error": result["stride"]["max_absolute_share_error"],
    }, indent=2))


if __name__ == "__main__":
    main()
