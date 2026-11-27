"""Run every Exercise-1 experiment and regenerate all numbers and charts.

Usage (from the exercise folder)::

    python code/run_experiments.py

Outputs
-------
* ``output/scenario_<name>.txt``  — full Gantt + metric table per scenario
* ``output/experiments.json``     — machine-readable metrics for the reports
* ``output/experiments_summary.txt`` — the table pasted into the reports
* ``diagrams/chart_*.png``        — every data chart used in the reports
* ``diagrams/gantt_<name>.png``   — Gantt chart per scenario

Nothing in this file invents numbers: every value written out is produced by
``lottery.simulate_full`` from the JSON scenarios (or the inline scenario
definitions documented beside each experiment).
"""
from __future__ import annotations

import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import matplotlib                                            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

from lottery import (simulate_full, metrics_full, format_gantt, format_table,  # noqa: E402
                     plot_gantt, load_config, measured_shares, DEFAULT_SEED)

OUT = os.path.join(ROOT, "output")
FIG = os.path.join(ROOT, "diagrams")
SCN = os.path.join(HERE, "scenarios")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.35,
                     "grid.linestyle": ":", "axes.axisbelow": True})


def _load(name):
    with open(os.path.join(SCN, name), encoding="utf-8") as f:
        return json.load(f)


def run_scenario_file(name, **over):
    spec = _load(name)
    procs, quantum, seed, compensation, currencies, horizon = load_config(spec)
    quantum = over.get("quantum", quantum)
    seed = over.get("seed", seed)
    compensation = over.get("compensation", compensation)
    horizon = over.get("horizon", horizon)
    plist, gantt, st, log = simulate_full(procs, quantum, seed, compensation=compensation,
                                          currencies=currencies, horizon=horizon)
    rows, summary = metrics_full(plist, st, seed, gantt, log)
    return rows, summary, gantt, plist, log


def write_scenario_report(name, tag=None, **over):
    rows, summary, gantt, plist, log = run_scenario_file(name, **over)
    tag = tag or name.replace(".json", "")
    txt = [f"scenario: {name}"]
    if over:
        txt.append(f"overrides: {json.dumps(over, sort_keys=True)}")
    txt.append("")
    # very long traces are summarized; metrics below are computed from the full run
    if len(gantt) > 180:
        head = gantt[:60]
        tail = gantt[-60:]
        body = "  ".join(f"{s}-{e}:{n}" for s, e, n in head) + "  ...  " + \
               "  ".join(f"{s}-{e}:{n}" for s, e, n in tail)
        txt.append(f"(trace truncated: {len(gantt)} segments shown as first 60 + last 60)")
        txt.append(body)
    else:
        txt.append(format_gantt(gantt))
    txt.append("")
    txt.append(format_table(rows, summary))
    path = os.path.join(OUT, f"scenario_{tag}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt) + "\n")
    title = f"Lottery Scheduling Gantt — {tag}"
    plot_gantt(gantt, os.path.join(FIG, f"gantt_{tag}.png"), title=title)
    return rows, summary


# --------------------------------------------------------------------------
# Experiments
# --------------------------------------------------------------------------

def exp_basic_scenarios():
    results = {}
    for fname in ("baseline.json", "fair.json", "dominance.json", "compensation.json", "transfer.json", "currencies.json"):
        name = fname.replace(".json", "")
        rows, summary = write_scenario_report(fname, tag=name)
        results[name] = summary
    return results


def exp_seed_sweep(seeds=50, horizon=600):
    """Steady-state shares across 50 seeds (5/3/2 tickets, 1500-tick horizons)."""
    procs = [
        {"pid": "T5", "arrival": 0, "burst": 10**9, "tickets": 5},
        {"pid": "T3", "arrival": 0, "burst": 10**9, "tickets": 3},
        {"pid": "T2", "arrival": 0, "burst": 10**9, "tickets": 2},
    ]
    shares = []
    for seed in range(seeds):
        _, gantt, _, _ = simulate_full(procs, 1, seed=seed, horizon=horizon)
        measured = measured_shares(gantt)
        total = sum(measured.values())
        shares.append({pid: measured[pid] / total for pid in ("T5", "T3", "T2")})
    stats = {pid: {"mean": statistics.fmean(s[pid] for s in shares),
                   "stdev": statistics.stdev(s[pid] for s in shares)}
             for pid in ("T5", "T3", "T2")}
    fig, ax = plt.subplots(figsize=(9, 4.2))
    pids = ["T5", "T3", "T2"]
    means = [stats[p]["mean"] for p in pids]
    stds = [stats[p]["stdev"] for p in pids]
    targets = [0.5, 0.3, 0.2]
    x = range(3)
    ax.bar([i - 0.2 for i in x], means, width=0.36, yerr=stds, capsize=5,
           color="#2F5496", label=f"observed mean (±1σ, {seeds} seeds)")
    ax.bar([i + 0.2 for i in x], targets, width=0.36,
           color="#C00000", alpha=0.75, label="ticket fraction (expected)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{p}\n({t})" for p, t in zip(pids, ["5/10", "3/10", "2/10"])])
    ax.set_ylabel("CPU share of a 600-tick horizon")
    ax.set_title(f"Steady-state share vs ticket fraction — {seeds} seeds, horizon 600")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_seed_sweep.png"), dpi=160)
    plt.close(fig)
    return stats


def exp_convergence(horizon=1500):
    """Cumulative tick share over time for the 5/3/2 trio (single seeded run)."""
    procs = [
        {"pid": "T5", "arrival": 0, "burst": 10**9, "tickets": 5},
        {"pid": "T3", "arrival": 0, "burst": 10**9, "tickets": 3},
        {"pid": "T2", "arrival": 0, "burst": 10**9, "tickets": 2},
    ]
    _, gantt, _, _ = simulate_full(procs, 1, seed=31415, horizon=horizon)
    cum = {"T5": 0, "T3": 0, "T2": 0}
    traj = {"T5": [], "T3": [], "T2": []}
    total = 0
    for s, e, label in gantt:
        if label == "IDLE":
            continue
        cum[label] += e - s
        total += e - s
        for pid in traj:
            traj[pid].append(cum[pid] / total)
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    colors_ = {"T5": "#2F5496", "T3": "#C00000", "T2": "#1E6B3C"}
    for pid, target in (("T5", 0.5), ("T3", 0.3), ("T2", 0.2)):
        ax.plot(traj[pid], color=colors_[pid], label=f"{pid} (ticket fraction {target})")
        ax.axhline(target, color=colors_[pid], linestyle="--", alpha=0.45)
    ax.set_xlabel("ticks elapsed (quantum = 1)")
    ax.set_ylabel("cumulative CPU share")
    ax.set_title("Convergence of observed share to ticket fraction (seed 31415)")
    ax.legend(loc="center right")
    ax.set_ylim(0.1, 0.65)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_convergence.png"), dpi=160)
    plt.close(fig)
    final = {pid: traj[pid][-1] for pid in traj}
    return final


def exp_quantum_sweep():
    """Context switches / response / throughput vs quantum on the baseline set."""
    spec = _load("baseline.json")
    quantums = [1, 2, 3, 4, 6, 8]
    rows_out = []
    for q in quantums:
        procs, _, seed, comp, curr, _ = load_config(spec)
        plist, gantt, st, log = simulate_full(procs, q, seed, compensation=comp, currencies=curr)
        rows, summary = metrics_full(plist, st, seed, gantt, log)
        rows_out.append({"quantum": q,
                         "context_switches": summary["context_switches"],
                         "dispatches": summary["dispatches"],
                         "avg_response": summary["avg_response"],
                         "avg_turnaround": summary["avg_turnaround"],
                         "preemptions": summary["preemptions"]})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    axes[0].plot([r["quantum"] for r in rows_out],
                 [r["context_switches"] for r in rows_out],
                 marker="o", color="#2F5496", label="context switches")
    axes[0].plot([r["quantum"] for r in rows_out],
                 [r["dispatches"] for r in rows_out],
                 marker="s", color="#C00000", label="dispatches")
    axes[0].set_xlabel("time quantum (ticks)")
    axes[0].set_ylabel("count over the run")
    axes[0].set_title("Scheduling overhead vs quantum")
    axes[0].legend()
    axes[1].plot([r["quantum"] for r in rows_out],
                 [r["avg_response"] for r in rows_out],
                 marker="o", color="#1E6B3C", label="avg response")
    axes[1].plot([r["quantum"] for r in rows_out],
                 [r["avg_turnaround"] for r in rows_out],
                 marker="s", color="#7B2FBE", label="avg turnaround")
    axes[1].set_xlabel("time quantum (ticks)")
    axes[1].set_ylabel("ticks")
    axes[1].set_title("Response / turnaround vs quantum")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_quantum_sweep.png"), dpi=160)
    plt.close(fig)
    return rows_out


def exp_compensation():
    """IO-bound process allocation with and without compensation tickets."""
    procs = [
        {"pid": "IO", "arrival": 0, "burst": 10**9, "tickets": 10, "io_every": 2, "io_len": 3},
        {"pid": "CPU1", "arrival": 0, "burst": 10**9, "tickets": 10},
        {"pid": "CPU2", "arrival": 0, "burst": 10**9, "tickets": 10},
    ]
    out = {}
    for comp in (False, True):
        _, gantt, st, log = simulate_full(procs, 4, seed=2024,
                                          compensation=comp, horizon=2000)
        measured = measured_shares(gantt)
        total = sum(measured.values())
        decisions = {}
        for e in log:
            decisions[e["winner"]] = decisions.get(e["winner"], 0) + 1
        out["compensation" if comp else "no_compensation"] = {
            "tick_share_io": measured["IO"] / total,
            "tick_share_cpu1": measured["CPU1"] / total,
            "tick_share_cpu2": measured["CPU2"] / total,
            "decisions_io": decisions.get("IO", 0),
            "grants": st.compensation_grants,
        }
    fig, ax = plt.subplots(figsize=(9, 4.0))
    labels = ["IO (I/O-bound)", "CPU1 (CPU-bound)", "CPU2 (CPU-bound)"]
    no_comp = [out["no_compensation"]["tick_share_io"], out["no_compensation"]["tick_share_cpu1"], out["no_compensation"]["tick_share_cpu2"]]
    comp = [out["compensation"]["tick_share_io"], out["compensation"]["tick_share_cpu1"], out["compensation"]["tick_share_cpu2"]]
    x = range(3)
    ax.bar([i - 0.2 for i in x], no_comp, width=0.36, color="#8EA9DB", label="compensation off")
    ax.bar([i + 0.2 for i in x], comp, width=0.36, color="#2F5496", label="compensation on")
    ax.set_ylabel("share of busy ticks (horizon 2000)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("Compensation tickets rebalance an I/O-bound process (10:10:10 tickets)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_compensation.png"), dpi=160)
    plt.close(fig)
    return out


def exp_ticket_sweep():
    """Observed decision share as a function of ticket count (steady state)."""
    ticket_counts = [1, 2, 3, 5, 8, 12]
    observed = []
    for k in ticket_counts:
        procs = [{"pid": "TARGET", "arrival": 0, "burst": 10**9, "tickets": k}]
        procs += [{"pid": f"F{i}", "arrival": 0, "burst": 10**9, "tickets": 10} for i in range(3)]
        _, gantt, _, _ = simulate_full(procs, 1, seed=2718, horizon=900)
        measured = measured_shares(gantt)
        total = sum(measured.values())
        observed.append(measured["TARGET"] / total)
    ideal = [k / (k + 30) for k in ticket_counts]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(ticket_counts, ideal, "--o", color="#C00000", label="ideal: t / (t + 30)")
    ax.plot(ticket_counts, observed, "-s", color="#2F5496", label="observed (seed 2718, horizon 900)")
    ax.set_xlabel("tickets held by one process (others hold 10 each)")
    ax.set_ylabel("observed CPU share")
    ax.set_title("Ticket-count sweep — share of the lottery pool")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_ticket_sweep.png"), dpi=160)
    plt.close(fig)
    return {"ticket_counts": ticket_counts, "observed": observed, "ideal": ideal}


def chart_scenarios(results):
    names = ["baseline", "fair", "dominance", "transfer", "currencies"]
    waits = [results[n]["avg_waiting"] for n in names]
    tats = [results[n]["avg_turnaround"] for n in names]
    resps = [results[n]["avg_response"] for n in names]
    x = range(len(names))
    width = 0.27
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar([i - width for i in x], waits, width, color="#2F5496", label="avg waiting")
    ax.bar(list(x), tats, width, color="#C00000", label="avg turnaround")
    ax.bar([i + width for i in x], resps, width, color="#1E6B3C", label="avg response")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel("ticks")
    ax.set_title("Scenario metrics (all terminating workloads)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_scenarios.png"), dpi=160)
    plt.close(fig)


def chart_share_error(results):
    names = ["baseline", "fair", "dominance", "transfer", "currencies"]
    errs = [results[n]["avg_share_error"] for n in names]
    mx = [results[n]["max_share_error"] for n in names]
    x = range(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.0))
    ax.bar([i - 0.2 for i in x], errs, width=0.36, color="#2F5496", label="avg |share error|")
    ax.bar([i + 0.2 for i in x], mx, width=0.36, color="#C00000", label="max |share error|")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel("|observed share − ticket fraction|")
    ax.set_title("Share error of terminating scenarios (burst-bound totals)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "chart_share_error.png"), dpi=160)
    plt.close(fig)


def main():
    experiments = {}

    basic = exp_basic_scenarios()
    experiments["basic"] = basic

    print("running seed sweep (50 seeds × horizon 600)…")
    experiments["seed_sweep"] = exp_seed_sweep(50, 600)

    print("running convergence trace…")
    experiments["convergence_final"] = exp_convergence(1500)

    print("running quantum sweep…")
    experiments["quantum_sweep"] = exp_quantum_sweep()

    print("running compensation experiment…")
    experiments["compensation"] = exp_compensation()

    print("running ticket sweep…")
    experiments["ticket_sweep"] = exp_ticket_sweep()

    chart_scenarios(basic)
    chart_share_error(basic)

    # experiments.json (strip nothing — it is plain JSON already)
    with open(os.path.join(OUT, "experiments.json"), "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=2, default=str)

    # human-readable summary
    lines = ["Exercise 1 — Lottery Scheduling: experiment summary",
             "=" * 58, "",
             "Scenario results (terminating workloads):"]
    for name, s in basic.items():
        aw = s["avg_waiting"]
        at = s["avg_turnaround"]
        ar = s["avg_response"]
        lines.append(f"  {name:14s}  avg wait {(f'{aw:6.2f}' if aw is not None else '   n/a')}"
                     f"  avg TAT {(f'{at:6.2f}' if at is not None else '   n/a')}  avg resp {(f'{ar:6.2f}' if ar is not None else '   n/a')}"
                     f"  ctx {s['context_switches']:3d}  share err {s['avg_share_error']:.4f}")
    lines.append("")
    lines.append("Steady state (50 seeds, horizon 600):")
    for pid, s in experiments["seed_sweep"].items():
        lines.append(f"  {pid}: mean {s['mean']:.4f}  stdev {s['stdev']:.4f}")
    lines.append("")
    lines.append(f"Convergence final shares (1500-tick run): {experiments['convergence_final']}")
    lines.append("")
    lines.append("Quantum sweep:")
    for r in experiments["quantum_sweep"]:
        lines.append(f"  q={r['quantum']}: ctx {r['context_switches']:3d}  dispatches {r['dispatches']:3d}"
                     f"  avg resp {r['avg_response']:.2f}  avg TAT {r['avg_turnaround']:.2f}")
    lines.append("")
    lines.append("Compensation (horizon 2000):")
    for k, v in experiments["compensation"].items():
        lines.append(f"  {k}: IO tick share {v['tick_share_io']:.4f}  grants {v['grants']}  IO decisions {v['decisions_io']}")
    lines.append("")
    lines.append("Ticket sweep (t vs 30 held by others, horizon 900):")
    ts = experiments["ticket_sweep"]
    for k, obs, ideal in zip(ts["ticket_counts"], ts["observed"], ts["ideal"]):
        lines.append(f"  t={k:2d}: observed {obs:.4f}   ideal {ideal:.4f}")
    with open(os.path.join(OUT, "experiments_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
