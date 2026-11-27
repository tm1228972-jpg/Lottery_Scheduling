"""Lottery Scheduling simulator — discrete, integer time.

Exercise 1 deliverable: a *runnable* model of Lottery Scheduling, the
probabilistic proportional-share algorithm of Waldspurger and Weihl (OSDI '94).

Model
-----
* Every runnable process owns **tickets**.  At each scheduling decision the
  scheduler draws one ticket uniformly at random; the process whose ticket
  interval contains the winning number receives the CPU for one **quantum**
  (or until it finishes / blocks).
* Runnable = arrived and not finished and not blocked.  Blocked and finished
  tickets are *not* in the pool, so a blocked process cannot win draws.
* Discrete integer ticks.  This is a **model** of the algorithm; it is not a
  kernel scheduler and it does not measure real wall-clock time.

Documented extensions (Waldspurger & Weihl, and Waldspurger's thesis)
---------------------------------------------------------------------
* ``compensation`` — when a process blocks before its quantum is exhausted it is
  temporarily granted extra tickets equal to ``quantum / used`` until it next
  wins a draw.  This compensates I/O-bound clients that voluntarily forfeit the
  remainder of their slice.
* ``transfers`` — *timed ticket transfer windows*: a process lends tickets to
  another process during an explicit ``[start, end)`` window (communicated
  donation, e.g. while acting on behalf of another client).
* ``currencies`` — hierarchical *ticket currencies*: groups of processes own a
  base-currency allocation; inside a group, tickets are denominated in the
  group's private currency and converted with the group's exchange rate.

Everything is seeded and therefore reproducible: every experiment in this
folder prints the seed it used.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

POLICY_NAME = "LOTTERY"
DEFAULT_SEED = 20250927


class InputError(ValueError):
    """Raised for invalid user input."""


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    tickets: int
    quantum_used: int = 0                  # ticks consumed in the current slice
    remaining: int = field(init=False)
    first_start: Optional[int] = None
    finish: Optional[int] = None
    blocked_until: int = 0
    io_every: Optional[int] = None         # extension: I/O-bound behaviour
    io_len: Optional[int] = None
    cpu_since_block: int = 0
    compensation: float = 1.0              # extension: compensation multiplier
    transfers: List[dict] = field(default_factory=list)
    home_tickets: int = field(init=False)

    def __post_init__(self):
        self.remaining = self.burst
        self.home_tickets = self.tickets

@dataclass
class Stats:
    total_time: int = 0
    busy_time: int = 0
    idle_time: int = 0
    context_switches: int = 0      # switches between two different processes
    switches_total: int = 0        # any change of the running entity (incl. idle)
    dispatches: int = 0            # times a process was dispatched
    preemptions: int = 0           # a running process was removed while unfinished
    draws: int = 0                 # lottery draws performed
    compensation_grants: int = 0   # times a compensation boost was applied
    transfers_applied: int = 0     # transfer windows that affected the pool
    max_wait: int = 0


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate(procs: List[dict]) -> List[Process]:
    if not isinstance(procs, list) or not procs:
        raise InputError("at least one process is required")
    out, seen = [], set()
    for i, p in enumerate(procs):
        if not isinstance(p, dict):
            raise InputError(f"process #{i + 1}: expected an object, got {type(p).__name__}")
        try:
            pid = str(p["pid"])
            arrival = int(p["arrival"])
            burst = int(p["burst"])
            tickets = int(p["tickets"])
        except KeyError as e:
            raise InputError(f"process #{i + 1}: missing field {e}")
        except (TypeError, ValueError) as e:
            raise InputError(f"process #{i + 1}: non-integer field ({e})")
        if not pid:
            raise InputError(f"process #{i + 1}: pid must be a non-empty string")
        if pid in seen:
            raise InputError(f"duplicate pid {pid}")
        if arrival < 0:
            raise InputError(f"{pid}: arrival must be >= 0")
        if burst <= 0:
            raise InputError(f"{pid}: burst must be > 0")
        if tickets <= 0:
            raise InputError(f"{pid}: tickets must be > 0")
        io_every = p.get("io_every")
        io_len = p.get("io_len")
        if (io_every is None) != (io_len is None):
            raise InputError(f"{pid}: io_every and io_len must be given together")
        if io_every is not None:
            io_every, io_len = int(io_every), int(io_len)
            if io_every <= 0 or io_len <= 0:
                raise InputError(f"{pid}: io_every and io_len must be > 0")
        transfers = p.get("transfers", [])
        parsed_transfers = []
        for tr in transfers:
            try:
                start, end = int(tr["start"]), int(tr["end"])
                amount = int(tr["tickets"])
                target = str(tr["target"])
            except KeyError as e:
                raise InputError(f"{pid}: transfer missing field {e}")
            if start < 0 or end <= start:
                raise InputError(f"{pid}: transfer window must satisfy 0 <= start < end")
            if amount <= 0:
                raise InputError(f"{pid}: transfer amount must be > 0")
            parsed_transfers.append({"start": start, "end": end, "tickets": amount, "target": target})
        seen.add(pid)
        out.append(Process(pid, arrival, burst, tickets,
                           io_every=io_every, io_len=io_len,
                           transfers=parsed_transfers))
    # cross-check transfer targets
    for p in out:
        for tr in p.transfers:
            if tr["target"] not in seen:
                raise InputError(f"{p.pid}: transfer target {tr['target']!r} is not a known pid")
            if tr["target"] == p.pid:
                raise InputError(f"{p.pid}: a process cannot transfer tickets to itself")
    return out


def validate_groups(groups: List[dict], procs: List[Process]) -> List[dict]:
    """Validate the optional hierarchical currency description."""
    if not groups:
        return []
    if not isinstance(groups, list):
        raise InputError("'currencies' must be a list of groups")
    pids = {p.pid for p in procs}
    total_base = 0
    out = []
    seen_members = set()
    for i, g in enumerate(groups):
        if not isinstance(g, dict):
            raise InputError(f"currency group #{i + 1}: expected an object")
        try:
            name = str(g["name"])
            base = int(g["base_tickets"])
            members = g["members"]
        except KeyError as e:
            raise InputError(f"currency group #{i + 1}: missing field {e}")
        if base <= 0:
            raise InputError(f"currency group {name}: base_tickets must be > 0")
        if not isinstance(members, dict) or not members:
            raise InputError(f"currency group {name}: 'members' must map pid -> currency tickets")
        member_total = 0
        parsed_members = {}
        for pid, cur in members.items():
            pid = str(pid)
            cur = int(cur)
            if pid not in pids:
                raise InputError(f"currency group {name}: unknown pid {pid!r}")
            if cur <= 0:
                raise InputError(f"currency group {name}: tickets for {pid} must be > 0")
            if pid in seen_members:
                raise InputError(f"pid {pid} appears in more than one currency group")
            seen_members.add(pid)
            parsed_members[pid] = cur
            member_total += cur
        total_base += base
        out.append({"name": name, "base_tickets": base,
                    "members": parsed_members, "member_total": member_total})
    if seen_members != pids:
        missing = sorted(pids - seen_members)
        raise InputError(f"currency groups must cover every process; missing {missing}")
    return out


def effective_pool(processes: List[Process], t: int) -> Dict[str, float]:
    """Effective tickets per runnable process at time ``t`` (pre-currency)."""
    pool = {}
    boosts: Dict[str, float] = {}
    for p in processes:
        for tr in p.transfers:
            if tr["start"] <= t < tr["end"]:
                boosts[tr["target"]] = boosts.get(tr["target"], 0.0) + tr["tickets"]
    for p in processes:
        if not is_runnable(p, t):
            continue
        eff = float(p.tickets) * p.compensation
        lent = sum(tr["tickets"] for tr in p.transfers
                   if tr["start"] <= t < tr["end"])
        eff = max(eff - lent, 0.0)
        eff += boosts.get(p.pid, 0.0)
        pool[p.pid] = eff
    return pool


def is_runnable(p: Process, t: int) -> bool:
    return p.arrival <= t < (p.finish if p.finish is not None else math.inf) and p.remaining > 0 and p.blocked_until <= t


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

def draw_winner(pool: Dict[str, float], rng: random.Random) -> Optional[str]:
    """Draw one winning ticket from ``pool``; returns the pid or None."""
    total = sum(pool.values())
    if total <= 0:
        return None
    ticket = rng.uniform(0, total)
    cumulative = 0.0
    for pid, eff in pool.items():
        cumulative += eff
        if ticket < cumulative:
            return pid
    return next(reversed(pool))  # floating-point safety net


def simulate_full(procs: List[dict], quantum: int = 2, seed: int = DEFAULT_SEED,
                  compensation: bool = False, currencies: Optional[List[dict]] = None,
                  max_ticks: int = 1_000_000, horizon: Optional[int] = None):
    """Run the simulation.

    Returns ``(process_list, gantt, stats)`` where ``gantt`` is a list of
    ``(start, end, label)`` intervals (``IDLE`` for idle ticks).
    """
    if quantum <= 0:
        raise InputError("quantum must be > 0")
    plist = validate(procs)
    groups = validate_groups(currencies or [], plist)
    by_pid = {p.pid: p for p in plist}
    rng = random.Random(seed)

    st = Stats()
    gantt: List[Tuple[int, int, str]] = []
    pending = sorted(plist, key=lambda p: (p.arrival, p.pid))
    t = 0
    current: Optional[Process] = None
    slice_left = 0
    done = 0
    decision_log: List[dict] = []

    def note(seg):
        if gantt and gantt[-1][2] == seg[2] and gantt[-1][1] == seg[0]:
            gantt[-1] = (gantt[-1][0], seg[1], seg[2])
        else:
            gantt.append(seg)

    while done < len(plist) and (horizon is None or t < horizon):
        if t > max_ticks:
            raise InputError("simulation did not terminate (max_ticks exceeded)")
        runnable = [p for p in plist if is_runnable(p, t) and p.remaining > 0]

        if current is None:
            if not runnable:
                # jump to the next event
                future = [p.arrival for p in plist if p.arrival > t]
                future += [p.blocked_until for p in plist if p.blocked_until > t]
                if not future:
                    break
                nxt = min(future)
                if nxt > t:
                    st.idle_time += nxt - t
                    st.total_time += nxt - t
                    note((t, nxt, "IDLE"))
                t = nxt
                continue
            pool = effective_pool(plist, t)
            pool = {pid: eff for pid, eff in pool.items() if eff > 0}
            if currencies:
                # hierarchical currency: each group splits its base-ticket
                # allocation between members in proportion to the *effective*
                # local (private-currency) tickets, so compensation and
                # transferred tickets still count inside the group
                converted = {}
                for g in groups:
                    members = [pid for pid in g["members"] if pid in pool]
                    local_total = sum(pool[pid] for pid in members)
                    if local_total <= 0:
                        continue
                    for pid in members:
                        converted[pid] = g["base_tickets"] * (pool[pid] / local_total)
                pool = converted
            winner = draw_winner(pool, rng)
            st.draws += 1
            if winner is None:
                t += 1
                continue
            current = by_pid[winner]
            current.quantum_used = 0
            slice_left = min(quantum, current.remaining)
            st.dispatches += 1
            if current.first_start is None:
                current.first_start = t
            # winning a draw cancels the outstanding compensation boost
            if compensation and current.compensation != 1.0:
                current.compensation = 1.0
            decision_log.append({"t": t, "pool": dict(pool), "winner": winner,
                                 "draw": st.draws})

        # run one tick
        current.remaining -= 1
        current.quantum_used += 1
        current.cpu_since_block += 1
        st.busy_time += 1
        st.total_time += 1
        slice_left -= 1
        note((t, t + 1, current.pid))
        t += 1

        # I/O blocking (extension)
        blocked_now = False
        if current.io_every and current.remaining > 0 and current.cpu_since_block >= current.io_every:
            blocked_now = True

        if current.remaining == 0:
            current.finish = t
            done += 1
            prev = current
            current = None
        elif blocked_now:
            used = current.quantum_used
            current.blocked_until = t + current.io_len
            current.cpu_since_block = 0
            if compensation and used < quantum:
                current.compensation = min(quantum / max(used, 1), 20.0)
                st.compensation_grants += 1
            prev = current
            current = None
        elif slice_left == 0:
            prev = current
            current = None  # quantum expired; it re-enters the pool next decision
        else:
            prev = None

        if prev is not None and prev.remaining > 0:
            st.preemptions += 1

    # context switches between consecutive different segments
    st.context_switches = sum(1 for a, b in zip(gantt, gantt[1:])
                              if a[2] != b[2] and a[2] != "IDLE" and b[2] != "IDLE")
    st.switches_total = sum(1 for a, b in zip(gantt, gantt[1:]) if a[2] != b[2])
    st.max_wait = max(((p.first_start or 0) - p.arrival for p in plist), default=0)
    return plist, gantt, st, decision_log


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def metrics_full(plist: List[Process], st: Stats, seed: int = DEFAULT_SEED,
                 gantt: Optional[List[Tuple[int, int, str]]] = None,
                 decision_log: Optional[List[dict]] = None):
    rows = []
    total_ticket_share = sum(p.home_tickets for p in plist)
    measured = measured_shares(gantt) if gantt else {}
    measured_total = sum(measured.values())
    decisions: Dict[str, int] = {}
    if decision_log:
        for entry in decision_log:
            decisions[entry["winner"]] = decisions.get(entry["winner"], 0) + 1
    total_decisions = sum(decisions.values())
    for p in plist:
        done_p = p.finish is not None
        finish = p.finish if done_p else None
        tat = (finish - p.arrival) if done_p else None
        wait = (tat - p.burst) if done_p else None
        resp = ((p.first_start if p.first_start is not None else finish) - p.arrival) if (done_p or p.first_start is not None) else None
        if measured_total:
            ticks_share = measured.get(p.pid, 0) / measured_total
        else:
            ticks_share = p.burst / sum(q.burst for q in plist)
        if total_decisions:
            decision_share = decisions.get(p.pid, 0) / total_decisions
        else:
            decision_share = 0.0
        ticket_frac = p.home_tickets / total_ticket_share
        rows.append({
            "pid": p.pid,
            "arrival": p.arrival,
            "burst": p.burst,
            "tickets": p.home_tickets,
            "finish": finish,
            "waiting": wait,
            "turnaround": tat,
            "response": resp,
            "cpu_share": ticks_share,
            "decisions": decisions.get(p.pid, 0),
            "decision_share": decision_share,
            "ticket_fraction": ticket_frac,
            "share_error": abs(ticks_share - ticket_frac),
        })
    n = len(rows)
    summary_completed = sum(1 for r in rows if r["finish"] is not None)
    def _avg(key):
        vals = [r[key] for r in rows if r[key] is not None]
        return sum(vals) / len(vals) if vals else None
    completed = sum(1 for r in rows if r["finish"] is not None)
    summary = {
        "avg_waiting": _avg("waiting"),
        "avg_turnaround": _avg("turnaround"),
        "avg_response": _avg("response"),
        "completed": summary_completed,
        "avg_share_error": sum(r["share_error"] for r in rows) / n,
        "max_share_error": max(r["share_error"] for r in rows),
        "total_time": st.total_time,
        "busy": st.busy_time,
        "idle": st.total_time - st.busy_time,
        "utilization": (st.busy_time / st.total_time) if st.total_time else 0.0,
        "throughput": summary_completed / st.total_time if st.total_time else 0.0,
        "context_switches": st.context_switches,
        "switches_total": st.switches_total,
        "dispatches": st.dispatches,
        "preemptions": st.preemptions,
        "draws": st.draws,
        "compensation_grants": st.compensation_grants,
        "seed": seed,
    }
    return rows, summary


def measured_shares(gantt) -> Dict[str, int]:
    share: Dict[str, int] = {}
    for s, e, label in gantt:
        if label == "IDLE":
            continue
        share[label] = share.get(label, 0) + (e - s)
    return share


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def format_gantt(gantt) -> str:
    bar = "|" + "|".join(f" {n} ".center(max(len(n) + 2, 2 * (e - s)))
                         for s, e, n in gantt) + "|"
    return bar + "\n" + "  ".join(f"{s}-{e}:{n}" for s, e, n in gantt)


def format_table(rows, summary) -> str:
    def _c(v, w, fmt="{:.0f}"):
        return (fmt.format(v) if v is not None else "—").rjust(w)
    w_pid = max(6, max(len(str(r["pid"])) for r in rows) + 1)
    w_burst = max(6, max(len(str(r["burst"])) for r in rows) + 1)
    head = (f"{'PID':<{w_pid}}{'Arr':>5}{'Burst':>{w_burst}}{'Tickets':>8}{'Fin':>6}"
            f"{'Wait':>6}{'TAT':>6}{'Resp':>6}{'Tick%':>8}{'Decis':>8}{'|Err|':>9}")
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(f"{r['pid']:<{w_pid}}{r['arrival']:>5}{r['burst']:>{w_burst}}{r['tickets']:>8}"
                     f"{_c(r['finish'], 6)}{_c(r['waiting'], 6)}{_c(r['turnaround'], 6)}"
                     f"{_c(r['response'], 6)}"
                     f"{r['cpu_share']:>8.3f}{r['decision_share']:>8.3f}{r['share_error']:>9.4f}")
    lines.append("-" * len(head))
    for label, key in (("avg waiting   ", "avg_waiting"),
                       ("avg turnaround", "avg_turnaround"),
                       ("avg response  ", "avg_response")):
        v = summary[key]
        lines.append(f"{label}= {v:.2f}" if v is not None else f"{label}= n/a (unfinished)")
    lines.append(f"avg share err = {summary['avg_share_error']:.4f}   max = {summary['max_share_error']:.4f}")
    lines.append(f"total time    = {summary['total_time']}   busy = {summary['busy']}   idle = {summary['idle']}")
    lines.append(f"CPU utilization = {summary['utilization'] * 100:.2f}%")
    lines.append(f"throughput    = {summary['throughput']:.4f} proc/tick")
    lines.append(f"context switches (proc->proc) = {summary['context_switches']}"
                 f"   dispatches = {summary['dispatches']}"
                 f"   total switches = {summary['switches_total']}")
    lines.append(f"preemptions = {summary['preemptions']}   draws = {summary['draws']}"
                 f"   compensation grants = {summary['compensation_grants']}")
    return "\n".join(lines)


def to_csv(rows) -> str:
    keys = ["pid", "arrival", "burst", "tickets", "finish", "waiting", "turnaround",
            "response", "cpu_share", "decisions", "decision_share", "ticket_fraction", "share_error"]
    out = [",".join(keys)]
    for r in rows:
        cells = []
        for k in keys:
            v = r[k]
            cells.append("" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v)))
        out.append(",".join(cells))
    return "\n".join(out)


def plot_gantt(gantt, path: str, title: str = "Lottery Scheduling Gantt chart"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = sorted({n for _, _, n in gantt if n != "IDLE"})
    cmap = plt.get_cmap("tab20")
    colors_ = {n: cmap(i % 20) for i, n in enumerate(names)}
    fig, ax = plt.subplots(figsize=(10, 0.9 + 0.42 * len(names)))
    for s, e, n in gantt:
        if n == "IDLE":
            ax.barh(len(names), e - s, left=s, color="#d9d9d9", edgecolor="black", hatch="//")
        else:
            ax.barh(names.index(n), e - s, left=s, color=colors_[n], edgecolor="black")
    ax.set_yticks(list(range(len(names))) + ([len(names)] if any(n == "IDLE" for _, _, n in gantt) else []))
    ax.set_yticklabels(names + (["IDLE"] if any(n == "IDLE" for _, _, n in gantt) else []))
    ax.set_xlabel("time (ticks)")
    ax.set_title(title)
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Input handling
# --------------------------------------------------------------------------

def load_config(spec: dict):
    if "processes" not in spec:
        raise InputError("scenario must define 'processes'")
    quantum = int(spec.get("quantum", 2))
    seed = int(spec.get("seed", DEFAULT_SEED))
    compensation = bool(spec.get("compensation", False))
    currencies = spec.get("currencies")
    horizon = spec.get("horizon")
    horizon = int(horizon) if horizon is not None else None
    return spec["processes"], quantum, seed, compensation, currencies, horizon


def interactive_input() -> dict:
    def ask_int(prompt, minimum=None):
        while True:
            raw = input(prompt).strip()
            try:
                v = int(raw)
            except ValueError:
                print("  ! please enter an integer")
                continue
            if minimum is not None and v < minimum:
                print(f"  ! value must be >= {minimum}")
                continue
            return v

    n = ask_int("number of processes: ", 1)
    procs = []
    for i in range(n):
        print(f"process {i + 1}:")
        pid = input("  pid: ").strip() or f"P{i + 1}"
        arrival = ask_int("  arrival: ", 0)
        burst = ask_int("  burst: ", 1)
        tickets = ask_int("  tickets: ", 1)
        procs.append({"pid": pid, "arrival": arrival, "burst": burst, "tickets": tickets})
    quantum = ask_int("time quantum (ticks): ", 1)
    seed = ask_int("seed: ", 0)
    return {"processes": procs, "quantum": quantum, "seed": seed}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Lottery Scheduling simulator")
    ap.add_argument("input", nargs="?", help="JSON scenario file ('-' for stdin)")
    ap.add_argument("--interactive", action="store_true", help="enter the scenario by hand")
    ap.add_argument("--png", help="write a Gantt chart PNG to this path")
    ap.add_argument("--csv", help="write the per-process table to this CSV path")
    ap.add_argument("--json", dest="json_out", help="write metrics as JSON to this path")
    ap.add_argument("--seed", type=int, default=None, help="override the RNG seed")
    ap.add_argument("--quantum", type=int, default=None, help="override the time quantum")
    ap.add_argument("--horizon", type=int, default=None, help="stop after this many ticks (bounded-horizon mode)")
    ap.add_argument("--compensation", action="store_true", help="enable compensation tickets")
    ap.add_argument("--quiet", action="store_true", help="print only the metrics table")
    a = ap.parse_args(argv)

    try:
        if a.interactive:
            spec = interactive_input()
        else:
            if not a.input:
                raise InputError("no input file given (use a path, '-' for stdin, or --interactive)")
            raw = sys.stdin.read() if a.input == "-" else open(a.input, encoding="utf-8").read()
            try:
                spec = json.loads(raw)
            except json.JSONDecodeError as e:
                raise InputError(f"invalid JSON: {e}")
        procs, quantum, seed, compensation, currencies, horizon = load_config(spec)
        if a.seed is not None:
            seed = a.seed
        if a.quantum is not None:
            quantum = a.quantum
        if a.compensation:
            compensation = True
        if a.horizon is not None:
            horizon = a.horizon
        plist, gantt, st, decision_log = simulate_full(procs, quantum, seed,
                                                       compensation=compensation,
                                                       currencies=currencies,
                                                       horizon=horizon)
    except (OSError, KeyError, InputError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    rows, summary = metrics_full(plist, st, seed, gantt, decision_log)

    if not a.quiet:
        print(format_gantt(gantt))
        print()
    print(format_table(rows, summary))
    if a.png:
        plot_gantt(gantt, a.png)
    if a.csv:
        with open(a.csv, "w", encoding="utf-8", newline="") as f:
            f.write(to_csv(rows) + "\n")
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump({"rows": rows, "summary": summary,
                       "gantt": [list(g) for g in gantt],
                       "decisions": decision_log}, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
