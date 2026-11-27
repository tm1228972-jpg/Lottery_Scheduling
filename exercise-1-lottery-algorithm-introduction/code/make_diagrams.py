"""Generate the conceptual diagrams for Exercise 1 (structure, flowchart, metrics)."""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "diagrams")
os.makedirs(FIG, exist_ok=True)

NAVY = "#1F3864"
STEEL = "#2F5496"
LIGHT = "#DCE6F1"
ACCENT = "#C00000"
GREEN = "#1E6B3C"


def fig_structure():
    fig, ax = plt.subplots(figsize=(11, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 66)
    ax.axis("off")

    # processes on the left
    procs = [("P1\n5 tickets", 54, LIGHT), ("P2\n3 tickets", 38, LIGHT), ("P3\n2 tickets", 22, LIGHT)]
    for label, y, color in procs:
        ax.add_patch(FancyBboxPatch((2, y - 6), 13, 10, boxstyle="round,pad=0.6",
                                    fc=color, ec=STEEL, lw=1.6))
        ax.text(8.5, y, label, ha="center", va="center", fontsize=10, color=NAVY, fontweight="bold")

    # ticket pool
    ax.add_patch(FancyBboxPatch((30, 14), 22, 42, boxstyle="round,pad=0.8",
                                fc="#F5F8FE", ec=STEEL, lw=1.8))
    ax.text(41, 51, "Ticket pool", ha="center", va="center", fontsize=11,
            fontweight="bold", color=NAVY)
    for i in range(10):
        xx = 33 + (i % 5) * 4.6
        yy = 40 - (i // 5) * 4.4
        color = STEEL if i < 5 else (ACCENT if i < 8 else GREEN)
        ax.add_patch(mpatches.Circle((xx, yy), 1.55, fc=color, ec="white", lw=1.2))
    ax.text(41, 26, "1–5: P1\n6–8: P2\n9–10: P3", ha="center", va="center",
            fontsize=9, color=NAVY)

    # lottery draw
    ax.add_patch(FancyBboxPatch((63, 31), 15, 14, boxstyle="round,pad=0.7",
                                fc="#FFF2CC", ec="#B8860B", lw=1.8))
    ax.text(70.5, 40.5, "Lottery draw", ha="center", fontsize=10, fontweight="bold", color="#7A5200")
    ax.text(70.5, 34.5, "w ~ Uniform{1..10}", ha="center", fontsize=8.5, color="#7A5200")

    # CPU
    ax.add_patch(FancyBboxPatch((86, 31), 11, 14, boxstyle="round,pad=0.7",
                                fc="#E7F5EC", ec=GREEN, lw=1.8))
    ax.text(91.5, 40.5, "CPU", ha="center", fontsize=13, fontweight="bold", color=GREEN)
    ax.text(91.5, 34.5, "one quantum", ha="center", fontsize=8, color=GREEN)

    # arrows
    ax.add_patch(FancyArrowPatch((16, 54), (29.4, 47), arrowstyle="-|>", lw=1.6, color=STEEL))
    ax.add_patch(FancyArrowPatch((16, 38), (29.4, 36), arrowstyle="-|>", lw=1.6, color=STEEL))
    ax.add_patch(FancyArrowPatch((16, 22), (29.4, 25), arrowstyle="-|>", lw=1.6, color=STEEL))
    ax.add_patch(FancyArrowPatch((53, 38), (62, 38.4), arrowstyle="-|>", lw=2.2, color=NAVY))
    ax.add_patch(FancyArrowPatch((79, 38), (85.4, 38), arrowstyle="-|>", lw=2.2, color=NAVY))

    # extensions box
    ax.add_patch(FancyBboxPatch((30, 1.5), 57, 9, boxstyle="round,pad=0.6",
                                fc="#FBF3F9", ec="#7B2FBE", lw=1.4))
    ax.text(58.5, 7.6, "Documented extensions", ha="center", fontsize=9,
            fontweight="bold", color="#7B2FBE")
    ax.text(58.5, 3.4,
            "compensation tickets (I/O-bound)  ·  timed ticket transfer  ·  hierarchical ticket currencies",
            ha="center", fontsize=8, color="#4A235A")

    ax.set_title("Lottery Scheduling — tickets, pool and one scheduling decision",
                 fontsize=12, fontweight="bold", color=NAVY, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_structure.png"), dpi=170)
    plt.close(fig)


def fig_flowchart():
    fig, ax = plt.subplots(figsize=(8.6, 11.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 130)
    ax.axis("off")

    def box(x, y, w, h, text, fc=LIGHT, ec=STEEL, fs=9, bold=True):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5",
                                    fc=fc, ec=ec, lw=1.5))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", wrap=True)

    def diamond(cx, cy, w, h, text, fs=8.5):
        pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
        ax.add_patch(plt.Polygon(pts, closed=True, fc="#FFF2CC", ec="#B8860B", lw=1.5))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color="#7A5200", fontweight="bold")

    def arrow(x1, y1, x2, y2, text=None):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     lw=1.6, color=STEEL))
        if text:
            ax.text((x1 + x2) / 2 + 1.5, (y1 + y2) / 2, text, fontsize=8, color=STEEL)

    box(28, 118, 44, 8, "scheduler tick begins", fc="#E7F5EC", ec=GREEN)
    arrow(50, 117, 50, 108)
    box(28, 100, 44, 7, "admit arrivals; wake unblocked")
    arrow(50, 99, 50, 90)
    diamond(50, 83, 46, 13, "runnable pool\nnon-empty?")
    arrow(27, 83, 12, 83, )
    ax.text(19.5, 80, "no", fontsize=9, color=ACCENT, fontweight="bold")
    box(2, 62, 21, 9, "advance clock to\nnext event\n(idle)", fs=8)
    arrow(12.5, 61.5, 12.5, 52)
    arrow(12.5, 52, 44, 52)
    arrow(50, 76, 50, 68)
    ax.text(52, 72, "yes", fontsize=9, color=GREEN, fontweight="bold")
    box(28, 60, 44, 7, "effective tickets = base × comp\n+ donated − lent")
    arrow(50, 59, 50, 50)
    box(28, 42, 44, 7, "convert currencies (if configured)\nT = Σ effective tickets")
    arrow(50, 41, 50, 33)
    box(28, 25, 44, 7, "draw w ∈ [0, T); winner = ticket owner")
    arrow(50, 24, 50, 15)
    box(28, 7, 44, 7, "run winner for one quantum\nor until it finishes / blocks")
    arrow(50, 6, 50, 1)
    box(28, -0.5, 44, 0.1, "", fc="white", ec="white")  # spacer anchor

    ax.set_ylim(-2, 128)
    ax.set_title("Lottery Scheduling — one scheduling decision",
                 fontsize=12, fontweight="bold", color=NAVY, pad=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_flowchart.png"), dpi=170)
    plt.close(fig)


def fig_metrics_timeline():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.axis("off")
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 40)

    ax.annotate("", xy=(106, 8), xytext=(4, 8),
                arrowprops=dict(arrowstyle="-|>", lw=1.6, color=NAVY))
    ax.text(106, 4.5, "time (ticks)", fontsize=9, color=NAVY, ha="right")

    events = [(10, "arrival\n(A)"), (34, "first dispatch\n(S)"), (88, "finish\n(F)")]
    for x, label in events:
        ax.plot([x], [8], marker="|", markersize=18, color=ACCENT, markeredgewidth=2.4)
        ax.text(x, 13, label, ha="center", fontsize=9, color=ACCENT, fontweight="bold")

    ax.plot([34, 88], [8, 8], lw=0)  # invisible
    ax.add_patch(mpatches.Rectangle((34, 6.4), 54, 3.2, fc=STEEL, ec=NAVY, alpha=0.85))
    ax.text(61, 8, "CPU burst (C)", color="white", ha="center", va="center", fontsize=10, fontweight="bold")

    for x0, x1, y, label, color in [
        (10, 34, 26, "response time = S − A", GREEN),
        (10, 88, 33, "turnaround time = F − A", STEEL),
        (10, 34, 19, "waiting = turnaround − burst", ACCENT),
    ]:
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="<|-|>", lw=1.6, color=color))
        ax.text((x0 + x1) / 2, y + 1.2, label, ha="center", fontsize=9, color=color, fontweight="bold")

    ax.set_title("Definitions used throughout this report (A = arrival, S = first start, F = finish)",
                 fontsize=10.5, fontweight="bold", color=NAVY)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_metrics_timeline.png"), dpi=170)
    plt.close(fig)


def fig_ticket_pool():
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    segments = [("P1", 5, STEEL), ("P2", 3, ACCENT), ("P3", 2, GREEN)]
    x = 5
    scale = 9.2
    for name, tickets, color in segments:
        w = tickets * scale
        ax.add_patch(mpatches.Rectangle((x, 10), w, 9, fc=color, ec="white", lw=2))
        ax.text(x + w / 2, 14.5, f"{name}\n{tickets} tickets", ha="center",
                va="center", fontsize=11, color="white", fontweight="bold")
        x += w
    for i in range(11):
        ax.plot([5 + i * scale], [6], marker="|", markersize=10, color=NAVY)
        ax.text(5 + i * scale, 2.5, str(i), ha="center", fontsize=8, color=NAVY)
    ax.set_title("The ticket interval view: every integer in [0, 10) belongs to exactly one process",
                 fontsize=10, fontweight="bold", color=NAVY)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_ticket_intervals.png"), dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    fig_structure()
    fig_flowchart()
    fig_metrics_timeline()
    fig_ticket_pool()
    print("diagrams written to", FIG)
