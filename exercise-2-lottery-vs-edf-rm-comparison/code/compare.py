#!/usr/bin/env python3
"""Exercise 2 — Lottery Scheduling vs EDF/RM, head-to-head on periodic real-time workloads.

Models periodic tasks (arrival offset 0, deadline == period) under three policies:
  * lottery  — ticket-weighted randomized proportional share (from Exercise 1),
  * rm       — Rate Monotonic fixed-priority (shorter period => higher priority),
  * edf      — dynamic earliest-deadline-first.

Outputs machine-readable metrics (JSON) and human-readable traces/Gantt per run.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_SEED = 20261127


class InputError(ValueError):
    pass


@dataclass
class Task:
    pid: str
    burst: int
    period: int
    deadline: int
    tickets: int

    def __post_init__(self):
        if self.burst <= 0 or self.period <= 0 or self.deadline <= 0 or self.tickets <= 0:
            raise InputError(f"task {self.pid}: burst/period/deadline/tickets must be >= 1")


@dataclass
class JobStats:
    pid: str
    release: int
    deadline: int
    start: Optional[int] = None
    finish: Optional[int] = None
    executed: int = 0

    @property
    def response(self):
        return None if self.start is None else self.start - self.release

    @property
    def turnaround(self):
        return None if self.finish is None else self.finish - self.release

    @property
    def tardiness(self):
        return None if self.finish is None else max(0, self.finish - self.deadline)

    @property
    def missed(self):
        return self.finish is None or self.finish > self.deadline


@dataclass
class Stats:
    policy: str = ""
    busy: int = 0
    idle: int = 0
    dispatches: int = 0
    context_switches: int = 0
    completed: int = 0
    missed: int = 0
    max_tardiness: int = 0
    total_response: int = 0
    response_n: int = 0


def validate_tasks(spec) -> list:
    tasks = []
    seen = set()
    for raw in spec:
        try:
            t = Task(pid=str(raw["pid"]), burst=int(raw["burst"]),
                     period=int(raw["period"]), deadline=int(raw.get("deadline", raw["period"])),
                     tickets=int(raw.get("tickets", 1)))
        except KeyError as e:
            raise InputError(f"missing field {e} in {raw!r}") from None
        if t.pid in seen:
            raise InputError(f"duplicate pid {t.pid}")
        seen.add(t.pid)
        tasks.append(t)
    if not tasks:
        raise InputError("empty task set")
    return tasks


def utilization(tasks) -> float:
    return sum(t.burst / t.period for t in tasks)


def rm_utilization_bound(n: int) -> float:
    return n * (2 ** (1.0 / n) - 1.0)


def rm_response_time(tasks, idx: int) -> Optional[int]:
    """Worst-case response time of task idx under RM (Audsley). None => unbounded/unschedulable."""
    ordered = sorted(tasks, key=lambda t: (t.period, t.pid))
    me = ordered[idx]
    r = me.burst
    for _ in range(10000):
        interference = sum(
            math.ceil(r / hp.period) * hp.burst
            for k, hp in enumerate(ordered)
            if k < idx
        )
        r_new = me.burst + interference
        if r_new > me.deadline:
            return None
        if r_new == r:
            return r
        r = r_new
    return None


def edf_feasibility_utilization(tasks) -> bool:
    """Sufficient condition (and necessary when D == T): U <= 1."""
    return utilization(tasks) <= 1.0 + 1e-12


def simulate_policy(tasks, policy: str, horizon: int, seed: int = DEFAULT_SEED,
                    quantum: int = 1):
    """Simulate repeated release of tasks over [0, horizon). Fully preemptive.

    RM/EDF re-evaluate eligibility every tick and preempt immediately on a
    higher-priority (earlier-deadline / shorter-period) arrival. Lottery
    re-decides only when the current job finishes or the quantum expires.

    Returns (jobs, gantt, stats). Deadline miss: finish > deadline (or
    unfinished at horizon).
    """
    rng = random.Random(seed)
    if policy not in ("lottery", "rm", "edf"):
        raise InputError(f"unknown policy {policy}")
    jobs: list[JobStats] = []
    gantt: list[tuple[int, int, str]] = []
    st = Stats(policy=policy)

    burst_of = {t.pid: t for t in tasks}

    def ready_jobs(t):
        return [j for j in jobs if j.release <= t and j.executed < burst_of[j.pid].burst]

    releases = []
    for task in tasks:
        k = 0
        while k * task.period < horizon:
            releases.append((k * task.period, task))
            k += 1
    releases.sort(key=lambda x: (x[0], x[1].pid))

    def release_jobs(t):
        while releases and releases[0][0] <= t:
            rel_t, task = releases.pop(0)
            jobs.append(JobStats(pid=task.pid, release=rel_t, deadline=rel_t + task.deadline))

    current: Optional[JobStats] = None
    slice_left = 0
    t = 0

    def note(seg):
        if gantt and gantt[-1][2] == seg[2] and gantt[-1][1] == seg[0]:
            gantt[-1] = (gantt[-1][0], seg[1], seg[2])
        else:
            gantt.append(seg)

    while t < horizon:
        release_jobs(t)
        ready = ready_jobs(t)

        if not ready:
            nxt = horizon
            if releases:
                nxt = min(nxt, releases[0][0])
            st.idle += nxt - t
            note((t, nxt, "IDLE"))
            current = None
            t = nxt
            continue

        if policy == "lottery":
            need_pick = current is None or current not in ready or slice_left == 0
            if need_pick:
                total = sum(burst_of[j.pid].tickets for j in ready)
                draw = rng.uniform(0, total)
                acc = 0.0
                chosen = ready[-1]
                for j in ready:
                    acc += burst_of[j.pid].tickets
                    if draw < acc:
                        chosen = j
                        break
                if current is not None and chosen.pid != current.pid:
                    st.context_switches += 1
                st.dispatches += 1  # every lottery decision is a dispatch
                if chosen.start is None:
                    chosen.start = t
                current = chosen
                slice_left = quantum
        else:  # preemptive rm/edf: re-pick every tick
            if policy == "rm":
                chosen = min(ready, key=lambda j: (burst_of[j.pid].period, j.release, j.pid))
            else:
                chosen = min(ready, key=lambda j: (j.deadline, j.release, j.pid))
            if chosen is not current:
                if current is not None:
                    st.context_switches += 1
                st.dispatches += 1
                if chosen.start is None:
                    chosen.start = t
                current = chosen

        current.executed += 1
        slice_left -= 1
        st.busy += 1
        note((t, t + 1, current.pid))
        t += 1

        if current.executed >= burst_of[current.pid].burst:
            current.finish = t
            st.completed += 1
            st.total_response += (current.start - current.release)
            st.response_n += 1
            if t > current.deadline:
                st.missed += 1
                st.max_tardiness = max(st.max_tardiness, t - current.deadline)
            current = None

    return jobs, gantt, st


def summarize(jobs, st: Stats, tasks, horizon: int, seed: int):
    per_task = {}
    for task in tasks:
        js = [j for j in jobs if j.pid == task.pid and j.finish is not None]
        executed = sum(j.executed for j in jobs if j.pid == task.pid)
        share = executed / max(st.busy, 1)
        frac = task.tickets / sum(x.tickets for x in tasks)
        misses = sum(1 for j in js if j.finish > j.deadline) + sum(
            1 for j in jobs if j.pid == task.pid and j.finish is None)
        responses = [j.start - j.release for j in js if j.start is not None]
        per_task[task.pid] = {
            "jobs_released": len([j for j in jobs if j.pid == task.pid]),
            "jobs_completed": len(js),
            "tickets": task.tickets,
            "ticket_fraction": frac,
            "cpu_ticks": executed,
            "cpu_share": share,
            "share_error": abs(share - frac),
            "deadline_misses": misses,
            "avg_response": (sum(responses) / len(responses)) if responses else None,
            "max_response": max(responses) if responses else None,
        }
    total_jobs = len(jobs)
    unfinished = sum(1 for j in jobs if j.finish is None)
    misses = st.missed + unfinished
    return {
        "policy": st.policy,
        "seed": seed,
        "horizon": horizon,
        "utilization": utilization(tasks),
        "rm_bound_3_required_note": f"n(2^(1/n)-1) for n={len(tasks)} is {rm_utilization_bound(len(tasks)):.4f}",
        "busy": st.busy,
        "idle": st.idle,
        "dispatches": st.dispatches,
        "context_switches": st.context_switches,
        "jobs_released": total_jobs,
        "jobs_completed": st.completed,
        "deadline_misses": misses,
        "max_tardiness": st.max_tardiness,
        "avg_response": (st.total_response / st.response_n) if st.response_n else None,
        "per_task": per_task,
    }


def load_tasks(path: str):
    with open(path) as f:
        spec = json.load(f)
    return validate_tasks(spec["tasks"]), int(spec.get("horizon", 60)), spec.get("runs")


def format_gantt(gantt) -> str:
    labels = [f"{s}-{e}:{n}" for s, e, n in gantt]
    line = "  ".join(labels)
    width = 96
    out, cur = [], ""
    for tok in line.split("  "):
        if len(cur) + len(tok) + 2 > width:
            out.append(cur)
            cur = tok
        else:
            cur = f"{cur}  {tok}".strip()
    if cur:
        out.append(cur)
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lottery vs EDF/RM comparator")
    ap.add_argument("scenario", help="scenario JSON (tasks, horizon, optional runs)")
    ap.add_argument("--policy", choices=["lottery", "rm", "edf", "all"], default="all")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--gantt", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    tasks, horizon, runs = load_tasks(a.scenario)
    policies = ["lottery", "rm", "edf"] if a.policy == "all" else [a.policy]
    results = {}
    for policy in policies:
        jobs, gantt, st = simulate_policy(tasks, policy, horizon, seed=a.seed)
        results[policy] = (jobs, gantt, st, summarize(jobs, st, tasks, horizon, a.seed))
    for policy in policies:
        jobs, gantt, st, summary = results[policy]
        if not a.quiet:
            print(f"=== policy: {policy}  horizon={horizon}  seed={a.seed} ===")
            if a.gantt:
                print(format_gantt(gantt))
            print(json.dumps(summary, indent=2))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump({p: results[p][3] for p in policies}, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
