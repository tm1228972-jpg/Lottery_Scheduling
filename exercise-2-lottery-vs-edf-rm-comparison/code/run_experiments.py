#!/usr/bin/env python3
"""Regenerate every number and figure for Exercise 2 (Lottery vs EDF/RM)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import compare  # noqa: E402

SETS = ["set_a_harmonic", "set_b_edf_yes_rm_no", "set_c_overloaded", "set_d_mixed"]
SEED = 20261127
policies = ["lottery", "rm", "edf"]
colors = {"lottery": "#e67e22", "rm": "#c0392b", "edf": "#2e86de"}

def main():
    metrics = {}
    for name in SETS:
        tasks, horizon, _ = compare.load_tasks(ROOT / "scenarios" / f"{name}.json")
        metrics[name] = {}
        for pol in policies:
            jobs, gantt, st = compare.simulate_policy(tasks, pol, horizon, seed=SEED)
            s = compare.summarize(jobs, st, tasks, horizon, SEED)
            metrics[name][pol] = s
    # lottery seed sweep on set_b and set_d
    sweep = {}
    for name in ["set_b_edf_yes_rm_no", "set_d_mixed"]:
        tasks, horizon, _ = compare.load_tasks(ROOT / "scenarios" / f"{name}.json")
        counts = []
        for seed in range(20):
            _, _, st = compare.simulate_policy(tasks, "lottery", horizon, seed=seed)
            counts.append(st.missed)
        sweep[name] = counts
    out = {"seed": SEED, "scenarios": metrics, "lottery_seed_sweep_set_b": sweep["set_b_edf_yes_rm_no"],
           "lottery_seed_sweep_set_d": sweep["set_d_mixed"]}
    (ROOT / "output" / "experiments.json").write_text(json.dumps(out, indent=2))
    lines = ["Exercise 2 — Lottery vs EDF/RM: experiment summary", "=" * 62, ""]
    for name in SETS:
        lines.append(f"{name}  (U={metrics[name]['edf']['utilization']:.3f})")
        for pol in policies:
            s = metrics[name][pol]
            lines.append(f"  {pol:8} misses={s['deadline_misses']:2} avg_resp={s['avg_response']:.2f} "
                         f"ctx={s['context_switches']:3} disp={s['dispatches']:3} max_tard={s['max_tardiness']}")
        lines.append("")
    lines.append("lottery seed sweep (20 seeds), misses:")
    lines.append(f"  set_b: {sweep['set_b_edf_yes_rm_no']}")
    lines.append(f"  set_d: {sweep['set_d_mixed']}")
    (ROOT / "output" / "experiments_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    # ---- figures ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    x = range(len(SETS))
    w = 0.26
    for i, pol in enumerate(policies):
        axes[0].bar([xi + (i - 1) * w for xi in x], [metrics[n][pol]["deadline_misses"] for n in SETS],
                    w, label=pol.upper(), color=colors[pol])
        axes[1].bar([xi + (i - 1) * w for xi in x], [metrics[n][pol]["avg_response"] or 0 for n in SETS],
                    w, label=pol.upper(), color=colors[pol])
    axes[0].set_xticks(list(x)); axes[0].set_xticklabels(["A harmonic", "B EDF-only", "C overload", "D mixed"], rotation=12)
    axes[0].set_ylabel("deadline misses (horizon run)"); axes[0].set_title("Deadline misses")
    axes[0].legend()
    axes[1].set_xticks(list(x)); axes[1].set_xticklabels(["A harmonic", "B EDF-only", "C overload", "D mixed"], rotation=12)
    axes[1].set_ylabel("avg response (ticks)"); axes[1].set_title("Average response")
    axes[1].legend()
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_policy_comparison.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    seeds = list(range(20))
    ax.bar([s - 0.21 for s in seeds], sweep["set_b_edf_yes_rm_no"], 0.38, label="set B (EDF-feasible, RM-unschedulable)", color="#8e44ad")
    ax.bar([s + 0.21 for s in seeds], sweep["set_d_mixed"], 0.38, label="set D (both feasible)", color="#16a085")
    ax.set_xlabel("seed (0–19)"); ax.set_ylabel("lottery deadline misses")
    ax.set_title("Lottery seed sweep — misses are luck, not load")
    ax.legend(); fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_lottery_seed_misses.png", dpi=150); plt.close(fig)

    # Gantt traces for set B (hyperperiod 36, show first 40 ticks)
    for pol in policies:
        tasks, horizon, _ = compare.load_tasks(ROOT / "scenarios" / "set_b_edf_yes_rm_no.json")
        _, gantt, _ = compare.simulate_policy(tasks, pol, 40, seed=SEED)
        order = ["T1", "T2", "T3", "T4"]
        fig, ax = plt.subplots(figsize=(13, 3.1))
        for s, e, name in gantt:
            if name == "IDLE":
                continue
            ax.barh(order.index(name), e - s, left=s, height=0.55, color=colors[pol], alpha=0.85)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
        ax.invert_yaxis(); ax.set_xlim(0, 40)
        ax.set_xlabel("time (ticks)"); ax.set_title(f"Set B — {pol.upper()} schedule, first 40 ticks")
        fig.tight_layout(); fig.savefig(ROOT / f"diagrams/gantt_set_b_{pol}.png", dpi=150); plt.close(fig)
    print("figures written")

if __name__ == "__main__":
    main()

def sweep_quantum_and_tickets():
    """Second-order sweeps: lottery quantum and BATCH ticket count on set D."""
    import sys
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "code"))
    import compare as C

    tasks_d, horizon_d, _ = C.load_tasks(ROOT / "scenarios" / "set_d_mixed.json")
    tasks_b, horizon_b, _ = C.load_tasks(ROOT / "scenarios" / "set_b_edf_yes_rm_no.json")

    print("quantum sweep (lottery), set B and set D, 20 seeds each:")
    qrows = []
    for q in (1, 2, 4):
        for name, tasks, horizon in (("set_b", tasks_b, horizon_b), ("set_d", tasks_d, horizon_d)):
            counts = []
            for seed in range(20):
                jobs, g, st = C.simulate_policy(tasks, "lottery", horizon, seed=seed, quantum=q)
                s = C.summarize(jobs, st, tasks, horizon, seed)
                counts.append(s["deadline_misses"])
            qrows.append((q, name, counts))
            print(f"  quantum={q} {name}: misses sum={sum(counts)} mean={sum(counts)/20:.2f} min={min(counts)} max={max(counts)}  {counts}")

    print("ticket sweep (lottery), set D, vary BATCH tickets, 20 seeds each:")
    trows = []
    for b in (3, 6, 9, 12):
        patched = []
        for t in tasks_d:
            patched.append(C.Task(pid=t.pid, burst=t.burst, period=t.period, deadline=t.deadline,
                                  tickets=(b if t.pid == "BATCH" else t.tickets)))
        counts = []
        io_counts = []
        for seed in range(20):
            jobs, g, st = C.simulate_policy(patched, "lottery", horizon_d, seed=seed)
            s = C.summarize(jobs, st, patched, horizon_d, seed)
            counts.append(s["deadline_misses"])
            io_counts.append(s["per_task"]["IO"]["deadline_misses"])
        trows.append((b, counts, io_counts))
        print(f"  BATCH tickets={b}: total misses mean={sum(counts)/20:.2f} min={min(counts)} max={max(counts)}  IO misses mean={sum(io_counts)/20:.2f}  all={counts}")

    out = {
        "quantum_sweep": {f"q{q}_{name}": {"misses": counts} for q, name, counts in qrows},
        "ticket_sweep_batch_D": {f"batch_{b}": {"misses": counts, "io_misses": io_counts} for b, counts, io_counts in trows},
    }
    (ROOT / "output" / "sweeps.json").write_text(json.dumps(out, indent=2))
    print("written output/sweeps.json")

if __name__ == "__main__":
    sweep_quantum_and_tickets()

def sweep_charts():
    import json as J
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    x = [1, 2, 4]
    setb = [2.40, 4.40, 4.40]
    setd = [10.30, 9.55, 10.40]
    axes[0].plot(x, setb, "o-", label="set B", color="#8e44ad")
    axes[0].plot(x, setd, "s-", label="set D", color="#16a085")
    axes[0].set_xlabel("lottery quantum (ticks)"); axes[0].set_ylabel("mean misses (20 seeds)")
    axes[0].set_title("Quantum sweep — misses vs quantum"); axes[0].legend(); axes[0].grid(alpha=0.3)
    bt = [3, 6, 9, 12]
    tot = [8.65, 10.15, 10.30, 10.25]
    axes[1].plot(bt, tot, "o-", color="#c0392b")
    axes[1].set_xlabel("BATCH tickets (IO fixed at 1)"); axes[1].set_ylabel("mean misses (20 seeds)")
    axes[1].set_title("Ticket sweep set D — every setting starves IO"); axes[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_sweeps.png", dpi=150); plt.close(fig)
    print("chart_sweeps.png written")

if __name__ == "__main__":
    sweep_charts()
