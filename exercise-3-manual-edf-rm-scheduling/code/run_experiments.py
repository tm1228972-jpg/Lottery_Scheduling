#!/usr/bin/env python3
"""Regenerate every artifact quoted in the Exercise 3 report."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import manual_rm_edf as M  # noqa: E402

EXAMPLES = ["ex3_1_trivial_two_task", "ex3_2_bound_beaten", "ex3_3_edf_not_rm",
            "ex3_4_constrained_deadlines", "ex3_5_overload"]
colors = {"rm": "#c0392b", "edf": "#2e86de"}

def main():
    metrics = {}
    for name in EXAMPLES:
        path = ROOT / "scenarios" / f"{name}.json"
        raw, tasks, horizon = M.load_scenario(path)
        result, _ = M.full_analysis(path)
        metrics[name] = {k: v for k, v in result.items() if not k.endswith("_gantt")}
        order = M.ordered_rm(tasks)
        # --- text artifacts ---
        for policy in ("rm", "edf"):
            jobs, gantt, st = M.simulate(tasks, policy, horizon)
            lines = [f"{name} — policy {policy} — horizon {horizon}",
                     f"dispatches={st.dispatches} ctx={st.context_switches} busy={st.busy} idle={st.idle} completed={st.completed}",
                     "=" * 76, M.format_gantt(gantt)]
            (ROOT / "output" / f"{name}_{policy}.txt").write_text("\n".join(lines) + "\n")
        rta_lines = [f"{name} — RM response-time analysis (period order)", "=" * 60]
        for i, t in enumerate(order):
            r, seq = M.rta_iterations(tasks, i)
            rta_lines.append(f"{t.pid} (C={t.burst},T={t.period},D={t.deadline}): seq={seq} -> R={r}")
        (ROOT / "output" / f"{name}_rta.txt").write_text("\n".join(rta_lines) + "\n")
        # manual table (first min(60, horizon) ticks)
        tab_len = min(60, horizon)
        for policy in ("rm", "edf"):
            rows = M.manual_table(tasks, policy, tab_len)
            (ROOT / "output" / f"{name}_{policy}_manual_first{tab_len}.txt").write_text(
                M.format_manual_table(rows) + "\n")
        # demand-bound table only meaningful for constrained deadlines; dump anyway
        H, rows, ok = M.edf_demand_bound(tasks)
        (ROOT / "output" / f"{name}_demand_bound.txt").write_text(
            f"{name} — dbf(t), H={H}, feasible={ok}\n" +
            "\n".join(f"t={t} dbf={d}{'  <-- VIOLATION' if d > t else ''}" for t, d in rows) + "\n")
    (ROOT / "output" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print((ROOT / "output" / "metrics.json").read_text()[:200], "...")

    # --- figures ---
    for name in EXAMPLES:
        raw, tasks, horizon = M.load_scenario(ROOT / "scenarios" / f"{name}.json")
        order = [t.pid for t in tasks]
        for policy in ("rm", "edf"):
            jobs, gantt, st = M.simulate(tasks, policy, horizon)
            show_h = min(horizon, 63)
            fig, ax = plt.subplots(figsize=(13, 2.3 + 0.35 * len(order)))
            for s, e, pid in gantt:
                if s >= show_h:
                    break
                if pid == "IDLE":
                    continue
                ax.barh(order.index(pid), e - s, left=s, height=0.55, color=colors[policy], alpha=0.85)
            ax.set_yticks(range(len(order))); ax.set_yticklabels(order)
            ax.invert_yaxis(); ax.set_xlim(0, show_h)
            ax.set_xlabel("time (ticks)")
            ax.set_title(f"{name} — {policy.upper()} schedule, first {show_h} ticks")
            fig.tight_layout()
            fig.savefig(ROOT / f"diagrams/gantt_{name}_{policy}.png", dpi=150)
            plt.close(fig)

    # utilization vs bound
    fig, ax = plt.subplots(figsize=(11, 4.4))
    xs = range(len(EXAMPLES))
    us = [metrics[n]["utilization"] for n in EXAMPLES]
    bounds = [metrics[n]["rm_bound"] for n in EXAMPLES]
    ax.bar([x - 0.21 for x in xs], us, 0.38, label="U", color="#16a085")
    ax.bar([x + 0.21 for x in xs], bounds, 0.38, label="RM bound n(2^{1/n}-1)", color="#8e44ad")
    ax.axhline(1.0, color="#c0392b", lw=1.2, ls="--", label="U = 1 (EDF feasibility edge)")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["Ex3-1\n2 tasks", "Ex3-2\n3 tasks", "Ex3-3\n3 tasks", "Ex3-4\n2 tasks", "Ex3-5\n3 tasks"])
    ax.set_ylabel("utilization")
    ax.set_title("Utilization vs Liu-Layland bound per example")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_utilization_bound.png", dpi=150); plt.close(fig)

    # misses summary
    fig, ax = plt.subplots(figsize=(11, 4.2))
    rm_m = [metrics[n]["rm"]["deadline_misses"] for n in EXAMPLES]
    edf_m = [metrics[n]["edf"]["deadline_misses"] for n in EXAMPLES]
    ax.bar([x - 0.21 for x in xs], rm_m, 0.38, label="RM", color=colors["rm"])
    ax.bar([x + 0.21 for x in xs], edf_m, 0.38, label="EDF", color=colors["edf"])
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["Ex3-1", "Ex3-2", "Ex3-3", "Ex3-4", "Ex3-5"])
    ax.set_ylabel("deadline misses (full horizon)")
    ax.set_title("Deadline misses per example and policy")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_misses.png", dpi=150); plt.close(fig)

    # demand-bound curve for Ex3-4 (constrained deadlines)
    raw, tasks, horizon = M.load_scenario(ROOT / "scenarios" / "ex3_4_constrained_deadlines.json")
    H, rows, ok = M.edf_demand_bound(tasks)
    ts = [r[0] for r in rows]
    dbfs = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(ts, dbfs, color="#8e44ad", lw=1.6, marker=".", ms=3, label="dbf(t)")
    ax.plot(ts, ts, color="#2e86de", lw=1.4, ls="--", label="t (demand must not exceed t)")
    ax.set_xlabel("t"); ax.set_ylabel("demand bound (ticks of work)")
    ax.set_title("Ex3-4 constrained deadlines — demand-bound test, H = 63 (feasible)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/chart_dbf_ex3_4.png", dpi=150); plt.close(fig)

    # method flowchart
    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.axis("off")
    steps = [
        ("1. Collect tasks", "C_i, T_i, D_i (+ tickets if proportional-share)"),
        ("2. Order for RM", "by (period, pid) — shortest period = highest priority"),
        ("3. Admission test RM", "bound n(2^{1/n}-1) → if exceeded, Audsley RTA"),
        ("4. Admission test EDF", "D == T: U ≤ 1   ·   D < T: demand-bound dbf(t) ≤ t ∀t ≤ H"),
        ("5. Tick-by-tick table", "release jobs; pick min (period | abs-deadline); preempt now"),
        ("6. Ledger", "start/finish vs deadline per job; misses; response times"),
        ("7. Verify", "hand table == machine trace; gantt gap-free; busy+idle == H"),
    ]
    y = 0.97
    for title, body in steps:
        ax.add_patch(mpatches.FancyArrowPatch((0.06, y - 0.045), (0.06, y - 0.115),
                                              arrowstyle="-|>", mutation_scale=14, color="#2c3e50",
                                              linewidth=1.6)) if title != steps[0][0] else None
        ax.add_patch(mpatches.FancyBboxPatch((0.09, y - 0.10), 0.84, 0.085,
                                             boxstyle="round,pad=0.008",
                                             linewidth=1.4, edgecolor="#2c3e50", facecolor="#ecf0f1"))
        ax.text(0.115, y - 0.038, title, fontsize=11, fontweight="bold", color="#2c3e50", va="center")
        ax.text(0.115, y - 0.075, body, fontsize=8.5, color="#34495e", va="center")
        y -= 0.135
    fig.tight_layout(); fig.savefig(ROOT / "diagrams/fig_manual_method.png", dpi=150); plt.close(fig)
    print("figures written")

if __name__ == "__main__":
    main()
