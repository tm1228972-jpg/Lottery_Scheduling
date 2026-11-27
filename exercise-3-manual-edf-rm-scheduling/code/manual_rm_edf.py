#!/usr/bin/env python3
"""Exercise 3 — Manual EDF/RM scheduling, worked by hand and verified by machine.

Every scenario in scenarios/ is small enough to schedule by hand. This program
produces BOTH the paper-style artifacts (iteration sequences, tick-by-tick
manual tables, deadline ledgers) and the machine-verified ones (gantt traces,
metrics, assertions). Nothing in the report is typed by hand; the "hand" tables
are computed by exactly the rules a student would apply with a pencil.

Policies (identical preemptive semantics to Exercise 2):
  rm  — min by (period, release, pid), re-picked every tick, preempts immediately
  edf — min by (absolute deadline, release, pid), re-picked every tick
D == T except in the constrained-deadline scenario (ex3_4).
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from math import gcd
from pathlib import Path

DEFAULT_SEED = 20261127  # unused for deterministic RM/EDF; kept for interface symmetry


class InputError(ValueError):
    pass


@dataclass
class Task:
    pid: str
    burst: int
    period: int
    deadline: int  # relative

    def __post_init__(self):
        if min(self.burst, self.period, self.deadline) < 1:
            raise InputError(f"task {self.pid}: burst/period/deadline must be >= 1")
        if self.deadline > self.period:
            raise InputError(f"task {self.pid}: this exercise uses D <= T (constrained or implicit)")


@dataclass
class Job:
    pid: str
    release: int
    deadline: int  # absolute
    executed: int = 0
    start: int | None = None
    finish: int | None = None

    @property
    def remaining(self):
        return self.burst_c - self.executed

    @property
    def burst_c_pid(self):
        return self.pid


@dataclass
class Stats:
    policy: str = ""
    busy: int = 0
    idle: int = 0
    dispatches: int = 0
    context_switches: int = 0
    completed: int = 0
    missed: int = 0          # completed-and-late
    max_tardiness: int = 0
    response_total: int = 0
    response_n: int = 0


def load_scenario(path):
    raw = json.loads(Path(path).read_text())
    name = raw.get("name") or Path(path).stem
    tasks = []
    for t in raw["tasks"]:
        tasks.append(Task(pid=str(t["pid"]), burst=int(t["burst"]),
                          period=int(t["period"]), deadline=int(t.get("deadline", t["period"]))))
    return raw, tasks, int(raw["horizon"])


def lcm(a, b):
    return a * b // gcd(a, b)


def hyperperiod(tasks):
    h = 1
    for t in tasks:
        h = lcm(h, t.period)
    return h


def utilization(tasks) -> float:
    return sum(t.burst / t.period for t in tasks)


def rm_utilization_bound(n: int) -> float:
    return n * (2 ** (1.0 / n) - 1.0)


def ordered_rm(tasks):
    """RM priority order: shorter period first, pid breaks ties."""
    return sorted(tasks, key=lambda t: (t.period, t.pid))


def rta_iterations(tasks, idx):
    """Audsley response-time iteration, with the full r-sequence returned."""
    ts = ordered_rm(tasks)
    me = ts[idx]
    r = me.burst
    seq = [r]
    for _ in range(10000):
        interference = sum(math.ceil(r / hp.period) * hp.burst
                           for k, hp in enumerate(ts) if k < idx)
        r_new = me.burst + interference
        if r_new > me.deadline:
            seq.append(r_new)
            return None, seq
        if r_new == r:
            return r, seq
        r = r_new
        seq.append(r)
    return None, seq


def edf_demand_bound(tasks):
    """dbf(t) over (0, H]; feasibility iff dbf(t) <= t everywhere. H = max(hyperperiod, max deadline)."""
    H = max(hyperperiod(tasks), max(t.deadline for t in tasks))
    rows = []
    ok = True
    for t in range(0, H + 1):
        dbf = 0
        for task in tasks:
            if t >= task.deadline:
                dbf += (math.floor((t - task.deadline) / task.period) + 1) * task.burst
        rows.append((t, dbf))
        if dbf > t:
            ok = False
    return H, rows, ok


def simulate(tasks, policy: str, horizon: int):
    if policy not in ("rm", "edf"):
        raise InputError(f"unknown policy {policy}")
    releases = []
    for task in tasks:
        k = 0
        while k * task.period < horizon:
            releases.append((k * task.period, task))
            k += 1
    releases.sort(key=lambda x: (x[0], x[1].pid))

    jobs: list[Job] = []
    gantt: list[tuple[int, int, str]] = []
    st = Stats(policy=policy)
    t = 0
    cur: Job | None = None

    def release_jobs(now):
        while releases and releases[0][0] <= now:
            rel_t, task = releases.pop(0)
            jobs.append(Job(pid=task.pid, release=rel_t, deadline=rel_t + task.deadline))

    def note(seg):
        if gantt and gantt[-1][2] == seg[2] and gantt[-1][1] == seg[0]:
            gantt[-1] = (gantt[-1][0], seg[1], seg[2])
        else:
            gantt.append(seg)

    burst_of = {t2.pid: t2 for t2 in tasks}

    def ready():
        return [j for j in jobs if j.release <= t and j.executed < burst_of[j.pid].burst]

    while t < horizon:
        release_jobs(t)
        rd = ready()
        if not rd:
            nxt = horizon
            if releases:
                nxt = min(nxt, releases[0][0])
            st.idle += nxt - t
            note((t, nxt, "IDLE"))
            cur = None
            t = nxt
            continue
        if policy == "rm":
            chosen = min(rd, key=lambda j: (burst_of[j.pid].period, j.release, j.pid))
        else:
            chosen = min(rd, key=lambda j: (j.deadline, j.release, j.pid))
        if chosen is not cur:
            if cur is not None:
                st.context_switches += 1
            st.dispatches += 1
            if chosen.start is None:
                chosen.start = t
            cur = chosen
        cur.executed += 1
        st.busy += 1
        note((t, t + 1, cur.pid))
        t += 1
        if cur.executed >= burst_of[cur.pid].burst:
            cur.finish = t
            st.completed += 1
            st.response_total += cur.start - cur.release
            st.response_n += 1
            if t > cur.deadline:
                st.missed += 1
                st.max_tardiness = max(st.max_tardiness, t - cur.deadline)
            cur = None
    return jobs, gantt, st


def misses_summary(jobs):
    rel = sum(1 for _ in jobs)
    late = sum(1 for j in jobs if j.finish is not None and j.finish > j.deadline)
    unf = sum(1 for j in jobs if j.finish is None)
    return {"jobs_released": rel, "deadline_misses": late + unf,
            "late_completed": late, "unfinished": unf,
            "jobs_completed": sum(1 for j in jobs if j.finish is not None)}


def manual_table(tasks, policy: str, n_ticks: int):
    """Paper-style rows: t | releases | chosen | running-bursts | next-deadline | remark."""
    burst_of = {t.pid: t for t in tasks}
    releases = []
    for task in tasks:
        k = 0
        while k * task.period < n_ticks:
            releases.append((k * task.period, task))
            k += 1
    releases.sort(key=lambda x: (x[0], x[1].pid))
    jobs = []
    rows = []
    cur = None
    for t in range(n_ticks):
        rel_now = [task.pid for rt, task in releases if rt == t]
        while releases and releases[0][0] == t:
            rel_t, task = releases.pop(0)
            jobs.append(Job(pid=task.pid, release=rel_t, deadline=rel_t + task.deadline))
        rd = [j for j in jobs if j.release <= t and j.executed < burst_of[j.pid].burst]
        if not rd:
            rows.append({"t": t, "released": rel_now, "chosen": "—", "remaining": {}, "remark": "idle: nothing ready"})
            continue
        if policy == "rm":
            chosen = min(rd, key=lambda j: (burst_of[j.pid].period, j.release, j.pid))
        else:
            chosen = min(rd, key=lambda j: (j.deadline, j.release, j.pid))
        before = {j.pid: burst_of[j.pid].burst - j.executed for j in rd}
        chosen.executed += 1
        if chosen.start is None:
            chosen.start = t
        if chosen.executed >= burst_of[chosen.pid].burst:
            chosen.finish = t + 1
        remark_bits = []
        if rel_now:
            remark_bits.append("+" + ",".join(rel_now) + " released")
        task = burst_of[chosen.pid]
        if chosen.executed == task.burst:
            remark_bits.append(f"{chosen.pid} done @ t={chosen.finish}, deadline {chosen.deadline}"
                                + (" MISS" if chosen.finish > chosen.deadline else " ok"))
        remaining = {j.pid: burst_of[j.pid].burst - j.executed for j in rd}
        rows.append({"t": t, "released": rel_now, "chosen": chosen.pid,
                     "remaining": remaining,
                     "remark": "; ".join(remark_bits) or "run"})
    return rows


def format_manual_table(rows):
    out = [" t | released | pick | remaining after tick | remark", "---+----------+------+-----------------------+------------------------------"]
    for r in rows:
        rel = ",".join(r["released"]) or "·"
        rem = " ".join(f"{k}:{v}" for k, v in sorted(r["remaining"].items())) or "·"
        out.append(f"{r['t']:2} | {rel:8} | {r['chosen']:4} | {rem:21} | {r['remark']}")
    return "\n".join(out)


def format_gantt(gantt):
    parts, line = [], ""
    for s, e, pid in gantt:
        seg = f"{s}-{e}:{pid}"
        if len(line) + len(seg) + 2 > 78:
            parts.append(line.rstrip())
            line = ""
        line += seg + "  "
    if line.strip():
        parts.append(line.rstrip())
    return "\n".join(parts)


def full_analysis(path):
    raw, tasks, horizon = load_scenario(path)
    order = ordered_rm(tasks)
    H = hyperperiod(tasks)
    u = utilization(tasks)
    bound = rm_utilization_bound(len(tasks))
    rta = []
    for i, t in enumerate(order):
        r, seq = rta_iterations(tasks, i)
        rta.append({"pid": t.pid, "r": r, "seq": seq, "deadline": t.deadline})
    _, dbf_rows, edf_ok = edf_demand_bound(tasks)
    result = {
        "name": raw.get("name"), "title": raw.get("title"), "horizon": horizon,
        "hyperperiod": H, "utilization": u, "rm_bound": bound, "n_tasks": len(tasks),
        "rta": rta, "edf_demand_bound_ok": edf_ok,
        "tasks": [{"pid": t.pid, "burst": t.burst, "period": t.period, "deadline": t.deadline}
                  for t in tasks],
    }
    for policy in ("rm", "edf"):
        jobs, gantt, st = simulate(tasks, policy, horizon)
        summ = misses_summary(jobs)
        summ.update({"dispatches": st.dispatches, "context_switches": st.context_switches,
                     "busy": st.busy, "idle": st.idle,
                     "avg_response": (st.response_total / st.response_n) if st.response_n else None,
                     "max_tardiness": st.max_tardiness})
        result[policy] = summ
        result[policy + "_gantt"] = gantt
    return result, tasks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scenario", nargs="?", help="scenario JSON")
    ap.add_argument("--all", action="store_true", help="analyze every scenario in scenarios/ and write output/metrics.json")
    ap.add_argument("--table", type=int, default=0, help="print manual table for N ticks (default 0 = off)")
    ap.add_argument("--policy", choices=("rm", "edf"), default="rm")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args(argv)

    if a.all:
        here = Path(__file__).resolve().parents[1]
        metrics = {}
        for spath in sorted((here / "scenarios").glob("*.json")):
            result, _ = full_analysis(spath)
            metrics[result["name"]] = {k: v for k, v in result.items() if not k.endswith("_gantt")}
            print(f"== {result['name']}: U={result['utilization']:.4f} H={result['hyperperiod']} "
                  f"rm_misses={result['rm']['deadline_misses']} edf_misses={result['edf']['deadline_misses']}")
        target = Path(a.json_out) if a.json_out else here / "output" / "metrics.json"
        target.write_text(json.dumps(metrics, indent=2))
        print("wrote", target)
        return 0

    if not a.scenario:
        ap.error("scenario required (or --all)")
    result, tasks = full_analysis(a.scenario)
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_gantt")}, indent=2, ensure_ascii=False))
    if a.table:
        rows = manual_table(tasks, a.policy, a.table)
        print(format_manual_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
