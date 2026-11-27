#!/usr/bin/env python3
"""Regenerate every figure quoted in the Exercise 4 report."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagrams"
DIAG.mkdir(exist_ok=True)

INK = "#1b2a3a"
ACC = "#2e86de"
RED = "#c0392b"
GRN = "#1e8449"
GOLD = "#b7950b"
BG = "#fdfdfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "figure.facecolor": BG,
    "savefig.facecolor": BG,
    "figure.dpi": 160,
})

def save(fig, name):
    fig.savefig(DIAG / name, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)

def load(name):
    return json.loads((ROOT / "output" / name).read_text())

mc = load("model_checks.json")
cb = load("counter_bench.json")
fn = load("fairness.json")
bb = load("buffer.json")

# ---------- Fig 1: lost-update race schematic ----------
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.axis("off")
ax.set_title("The lost-update race window (read-modify-write is not atomic)", fontsize=13, fontweight="bold", color=INK)
lanes = [("Thread 0", 0.78), ("Thread 1", 0.30)]
for name, y in lanes:
    ax.axhline(y, color=INK, lw=1.2, alpha=0.35)
    ax.text(0.005, y + 0.028, name, fontsize=11, fontweight="bold", color=INK, va="center")
ax.text(0.16, 0.86, "load counter (= 41)", fontsize=10, color=INK)
ax.text(0.40, 0.86, "add 1", fontsize=10, color=INK)
ax.text(0.62, 0.86, "store 42", fontsize=10, color=GRN, fontweight="bold")
ax.text(0.16, 0.38, "load counter (= 41)", fontsize=10, color=INK)
ax.text(0.40, 0.38, "add 1", fontsize=10, color=INK)
ax.text(0.62, 0.38, "store 42", fontsize=10, color=RED, fontweight="bold")
ax.annotate("both read 41 → both store 42 → one increment vanishes", xy=(0.62, 0.34), xytext=(0.30, 0.08),
            fontsize=10, color=RED, arrowprops=dict(arrowstyle="-|>", color=RED))
ax.set_xlim(0, 1.05); ax.set_ylim(0, 1)
save(fig, "fig_counter_race.png")

# ---------- Fig 2: Dekker protocol flow ----------
fig, ax = plt.subplots(figsize=(10.5, 8.6))
ax.axis("off")
ax.set_title("Dekker's algorithm — one process's entry path", fontsize=13, fontweight="bold", color=INK)
steps = [
    ("flag[self] = TRUE", "raise own flag"),
    ("while flag[other]:", "is the other interested?"),
    ("if turn == self:\n  spin on flag[other]", "turn favors us: keep waiting"),
    ("else: back off\n  flag[self] = FALSE\n  while turn != self: pass", "yield the turn, wait silently"),
    ("flag[self] = TRUE", "re-assert interest, repeat"),
    ("CRITICAL SECTION", "mutual exclusion holds\n(verified: 53 states, 0 violations)"),
    ("turn = other\nflag[self] = FALSE", "exit: hand the turn over first"),
]
y = 0.90
for i, (code, note) in enumerate(steps):
    fc = GRN if i == 5 else ("#eef4fb" if i < 5 else "#f6f0e4")
    ax.add_patch(mpatches.FancyBboxPatch((0.03, y - 0.055), 0.40, 0.088,
                                         boxstyle="round,pad=0.008", fc=fc, ec=INK, lw=1.4))
    ax.text(0.045, y - 0.011, code, fontsize=9.5, family="monospace", color=INK, va="center")
    ax.text(0.475, y - 0.011, note, fontsize=9.5, color=INK, va="center")
    if i < len(steps) - 1:
        ax.annotate("", xy=(0.23, y - 0.075), xytext=(0.23, y - 0.055),
                    arrowprops=dict(arrowstyle="-|>", color=INK))
    y -= 0.128
ax.set_xlim(0, 1.15); ax.set_ylim(0, 1)
save(fig, "fig_dekker_protocol.png")

# ---------- Fig 3: Peterson protocol flow ----------
fig, ax = plt.subplots(figsize=(10.5, 6.6))
ax.axis("off")
ax.set_title("Peterson's algorithm — three steps to exclusion", fontsize=13, fontweight="bold", color=INK)
steps = [
    ("flag[self] = TRUE", "I am interested"),
    ("turn = other", "but I defer: the turn is yours"),
    ("while flag[other] and turn == other:\n  pass", "wait only while the other wants it\nAND the turn is theirs"),
    ("CRITICAL SECTION", "verified: 34 states, 0 violations, 0 deadlocks"),
    ("flag[self] = FALSE", "release"),
]
y = 0.86
for i, (code, note) in enumerate(steps):
    fc = GRN if i == 3 else "#eef4fb"
    ax.add_patch(mpatches.FancyBboxPatch((0.03, y - 0.062), 0.46, 0.105,
                                         boxstyle="round,pad=0.008", fc=fc, ec=INK, lw=1.4))
    ax.text(0.045, y - 0.009, code, fontsize=9.5, family="monospace", color=INK, va="center")
    ax.text(0.53, y - 0.009, note, fontsize=9.5, color=INK, va="center")
    if i < len(steps) - 1:
        ax.annotate("", xy=(0.26, y - 0.082), xytext=(0.26, y - 0.062),
                    arrowprops=dict(arrowstyle="-|>", color=INK))
    y -= 0.165
ax.set_xlim(0, 1.15); ax.set_ylim(0, 1)
save(fig, "fig_peterson_protocol.png")

# ---------- Chart 4: state graph sizes ----------
fig, ax = plt.subplots(figsize=(9, 4.6))
names = ["dekker", "peterson", "turn_only", "flag_only"]
states = [mc[n]["graph"]["states"] for n in names]
trans = [mc[n]["graph"]["transitions"] for n in names]
x = np.arange(len(names))
ax.bar(x - 0.21, states, 0.4, label="reachable states", color=ACC)
ax.bar(x + 0.21, trans, 0.4, label="transitions", color=GOLD)
for xi, s, t in zip(x, states, trans):
    ax.text(xi - 0.21, s + 0.8, str(s), ha="center", fontsize=9, color=INK)
    ax.text(xi + 0.21, t + 0.8, str(t), ha="center", fontsize=9, color=INK)
ax.set_xticks(x); ax.set_xticklabels(["Dekker", "Peterson", "turn-only\n(broken)", "flag-only\n(broken)"])
ax.set_ylabel("count")
ax.set_title("Exhaustive state enumeration — model size per algorithm", fontweight="bold", color=INK)
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_model_graph.png")

# ---------- Chart 5: safety / deadlock verdicts ----------
fig, ax = plt.subplots(figsize=(9, 4.6))
viol = [mc[n]["safety"]["mutual_exclusion_violations"] for n in names]
dead = [mc[n]["deadlock"]["deadlock_states"] for n in names]
ax.bar(x - 0.21, viol, 0.4, label="mutual-exclusion violations", color=RED)
ax.bar(x + 0.21, dead, 0.4, label="deadlock states", color=GOLD)
ax.set_xticks(x); ax.set_xticklabels(["Dekker", "Peterson", "turn-only\n(broken)", "flag-only\n(broken)"])
ax.set_ylabel("count")
ax.set_ylim(0, 1.6)
ax.set_title("Model-check verdicts — correct algorithms show zero on both axes", fontweight="bold", color=INK)
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_safety_deadlock.png")

# ---------- Chart 6: lost updates ----------
fig, ax = plt.subplots(figsize=(9.5, 4.8))
two = [r for r in cb if r["threads"] == 2]
four = [r for r in cb if r["threads"] == 4]
mech2 = [r["mechanism"] for r in two]
order2 = ["none", "dekker", "peterson", "mutex", "semaphore", "ticket"]
lost2 = [next(r["lost_total"] for r in two if r["mechanism"] == m) for m in order2]
order4 = ["none", "mutex", "semaphore", "ticket"]
lost4 = [next(r["lost_total"] for r in four if r["mechanism"] == m) for m in order4]
ax.bar(np.arange(len(order2)) - 0.0, lost2, 0.55, label="2 threads (2 x 200 increments)", color=RED, alpha=0.85)
ax.set_xticks(np.arange(len(order2)))
ax.set_xticklabels([m if len(m) <= 9 else m for m in order2])
ax.set_ylabel("lost updates over 20 trials")
ax.set_title("Unsynchronized counter loses nearly every update; locks lose none", fontweight="bold", color=INK)
for xi, v in zip(np.arange(len(order2)), lost2):
    ax.text(xi, v + 60, str(v), ha="center", fontsize=9, color=INK)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_lost_updates.png")

# ---------- Chart 7: lock cost per operation ----------
fig, ax = plt.subplots(figsize=(9.5, 4.6))
mech_all = ["dekker", "peterson", "mutex", "semaphore", "ticket"]
dur2 = [next(r["avg_duration_s"] for r in two if r["mechanism"] == m) for m in mech_all]
ax.bar(np.arange(len(mech_all)), [1000 * d for d in dur2], 0.55, color=ACC)
ax.set_xticks(np.arange(len(mech_all)))
ax.set_xticklabels(mech_all)
ax.set_ylabel("avg wall time per trial (ms)")
ax.set_title("Cost of correctness — Dekker/Peterson spin vs library locks (2 threads)", fontweight="bold", color=INK)
for xi, d in zip(np.arange(len(mech_all)), dur2):
    ax.text(xi, 1000 * d + 0.02, f"{1000*d:.2f}", ha="center", fontsize=9, color=INK)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_lock_cost.png")

# ---------- Chart 8: fairness per thread ----------
fig, ax = plt.subplots(figsize=(9.5, 4.8))
t_ticket = fn["ticket"]["per_thread_avg_ms"]
t_mutex = fn["mutex"]["per_thread_avg_ms"]
idx = np.arange(4)
ax.bar(idx - 0.21, t_ticket, 0.4, label="ticket lock (FIFO)", color=GRN)
ax.bar(idx + 0.21, t_mutex, 0.4, label="threading.Lock (unfair)", color=RED, alpha=0.85)
ax.set_xticks(idx)
ax.set_xticklabels([f"thread {i}" for i in range(4)])
ax.set_ylabel("avg wait per acquisition (ms)")
ax.set_title("Ticket lock spreads wait time evenly across threads", fontweight="bold", color=INK)
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
save(fig, "chart_fairness.png")

# ---------- Fig 9: bounded buffer schematic ----------
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.axis("off")
ax.set_title("Bounded buffer — semaphore accounting (capacity = 3)", fontsize=13, fontweight="bold", color=INK)
ax.add_patch(mpatches.FancyBboxPatch((0.30, 0.45), 0.40, 0.28, boxstyle="round,pad=0.01",
                                     fc="#eef4fb", ec=INK, lw=1.6))
for i in range(3):
    ax.add_patch(mpatches.Rectangle((0.335 + i * 0.125, 0.52), 0.10, 0.14, fc="white", ec=INK, lw=1.3))
ax.text(0.50, 0.79, "buffer (3 slots)", ha="center", fontsize=10, color=INK, fontweight="bold")
ax.add_patch(mpatches.FancyArrowPatch((0.10, 0.59), (0.295, 0.59), arrowstyle="-|>", color=GRN, lw=2))
ax.text(0.10, 0.66, "producers\nsem_wait(empty)", fontsize=9.5, color=GRN)
ax.add_patch(mpatches.FancyArrowPatch((0.70, 0.59), (0.90, 0.59), arrowstyle="-|>", color=RED, lw=2))
ax.text(0.735, 0.66, "consumers\nsem_wait(full)", fontsize=9.5, color=RED)
ax.text(0.30, 0.30, "empty = 3 - occupied", fontsize=9.5, family="monospace", color=INK)
ax.text(0.30, 0.22, "full      = occupied", fontsize=9.5, family="monospace", color=INK)
ax.text(0.30, 0.14, "mutex   = 1 (mutual exclusion on the slots)", fontsize=9.5, family="monospace", color=INK)
ax.text(0.02, 0.02, "Invariant: occupancy never exceeds 3 — verified at runtime (max_occupancy = 3 for both semaphore and monitor versions).",
        fontsize=9, color=INK)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
save(fig, "fig_bounded_buffer.png")

# ---------- Fig 10: monitor schematic ----------
fig, ax = plt.subplots(figsize=(10, 5.4))
ax.axis("off")
ax.set_title("Monitor — encapsulation with condition variables", fontsize=13, fontweight="bold", color=INK)
ax.add_patch(mpatches.FancyBboxPatch((0.16, 0.30), 0.68, 0.52, boxstyle="round,pad=0.015",
                                     fc="#f6f0e4", ec=INK, lw=1.8))
ax.text(0.50, 0.775, "monitor  Buffer", ha="center", fontsize=12, fontweight="bold", color=INK)
ax.add_patch(mpatches.Rectangle((0.205, 0.47), 0.16, 0.21, fc="white", ec=INK, lw=1.2))
ax.text(0.285, 0.575, "procedure\nput()", ha="center", fontsize=10, family="monospace", color=INK)
ax.add_patch(mpatches.Rectangle((0.415, 0.47), 0.16, 0.21, fc="white", ec=INK, lw=1.2))
ax.text(0.495, 0.575, "procedure\nget()", ha="center", fontsize=10, family="monospace", color=INK)
ax.add_patch(mpatches.Rectangle((0.625, 0.47), 0.16, 0.21, fc="white", ec=INK, lw=1.2))
ax.text(0.705, 0.575, "condition\nnotFull / notEmpty", ha="center", fontsize=9, family="monospace", color=INK)
ax.text(0.50, 0.38, "entry queue: one thread at a time — exclusion is automatic", ha="center", fontsize=9.5, color=INK)
ax.text(0.50, 0.345, "signal() wakes a waiting thread inside the monitor", ha="center", fontsize=8.5, color=INK, alpha=0.8)
ax.set_xlim(0, 1); ax.set_ylim(0.2, 1)
save(fig, "fig_monitor.png")

# ---------- Fig 11: mechanism choice map ----------
fig, ax = plt.subplots(figsize=(10.5, 5.6))
ax.axis("off")
ax.set_title("Which mechanism for which job — decision map", fontsize=13, fontweight="bold", color=INK)
rows = [
    ("Need fair FIFO wakeup", "ticket / bakery lock", "starvation-free, O(1)"),
    ("Two threads, no kernel help", "Dekker / Peterson", "busy-wait, pedagogical"),
    ("N threads, short critical section", "spinlock / ticket lock", "lowest latency, burns CPU"),
    ("N threads, long critical section", "mutex / semaphore", "sleeps waiters, fair-ish"),
    ("Producer/consumer accounting", "counting semaphores", "full + empty counters"),
    ("Structured, composable exclusion", "monitor + condition", "exclusion by construction"),
]
y = 0.88
for need, mech, why in rows:
    ax.text(0.02, y, need, fontsize=10, color=INK, va="center")
    ax.text(0.44, y, mech, fontsize=10, family="monospace", color=ACC, va="center")
    ax.text(0.72, y, why, fontsize=9.5, color=INK, va="center", alpha=0.85)
    y -= 0.137
ax.set_xlim(0, 1.15); ax.set_ylim(0, 1)
save(fig, "fig_decision_map.png")

# ---------- Fig 12: proof obligations ----------
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.axis("off")
ax.set_title("What each tool proves — and what it cannot", fontsize=13, fontweight="bold", color=INK)
cols = ["finite-state enumeration", "threaded micro-benchmark", "code review"]
rows = [("mutual exclusion (safety)", True, True, None),
        ("deadlock freedom", True, None, None),
        ("starvation freedom", True, None, None),
        ("no lost updates in production", None, True, None),
        ("throughput / latency", None, True, None)]
for j, c in enumerate(cols):
    ax.text(0.34 + j * 0.24, 0.90, c, ha="center", fontsize=9.5, fontweight="bold", color=INK)
for i, (label, *marks) in enumerate(rows):
    y = 0.72 - i * 0.16
    ax.text(0.02, y, label, fontsize=10, color=INK, va="center")
    for j, m in enumerate(marks):
        mark = "yes" if m is True else "no"
        color = GRN if m is True else (RED if m is False else "#9aa5b1")
        ax.text(0.34 + j * 0.24, y, mark, ha="center", va="center", fontsize=9.5,
                fontweight="bold", color=color)
ax.set_xlim(0, 1.05); ax.set_ylim(0, 1)
save(fig, "fig_proof_map.png")
