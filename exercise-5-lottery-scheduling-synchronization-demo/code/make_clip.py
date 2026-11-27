#!/usr/bin/env python3
"""Build an MP4/GIF clip visualizing weighted lottery lock grants."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "output" / "lottery_sync_trace.json"
MEDIA = ROOT / "media"


def main() -> None:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    if not trace:
        raise RuntimeError("trace is empty; run lottery_sync.py first")
    MEDIA.mkdir(parents=True, exist_ok=True)
    names = ["P1", "P2", "P3"]
    tickets = {"P1": 5, "P2": 3, "P3": 2}
    shares = [tickets[n] / sum(tickets.values()) for n in names]
    fig, (ax_share, ax_timeline) = plt.subplots(
        2, 1, figsize=(10, 6), gridspec_kw={"height_ratios": [1, 1.4]}
    )
    fig.suptitle("Lottery Scheduling as a Synchronization / Lock-Arbitration Demo", fontsize=13)
    bars = ax_share.bar(names, [0, 0, 0])
    ax_share.set_ylim(0, 0.7)
    ax_share.set_ylabel("Observed grant share")
    ax_share.set_title("Observed share approaches ticket share over repeated grants")
    ax_share.grid(axis="y", alpha=0.25)
    ax_timeline.set_xlim(0, 40)
    ax_timeline.set_ylim(-0.7, 2.7)
    ax_timeline.set_yticks(range(3), names)
    ax_timeline.set_xlabel("Most recent lottery decisions (one grant per slot)")
    ax_timeline.set_title("Grant history")
    ax_timeline.grid(axis="x", alpha=0.2)
    cells = [ax_timeline.barh(0, 0.8, left=i, height=0.48)[0] for i in range(40)]
    labels = [ax_share.text(i, 0.02, "", ha="center", va="bottom") for i in range(3)]
    footer = fig.text(0.5, 0.015, "", ha="center", fontsize=9)

    # Keep the teaching clip short while sampling the full trace uniformly.
    # The final decision is always included, even when the step does not divide
    # the number of decisions exactly.
    step = max(1, (len(trace) + 99) // 100)
    frame_indices = list(range(0, len(trace), step))
    if frame_indices[-1] != len(trace) - 1:
        frame_indices.append(len(trace) - 1)

    def update(frame: int):
        decision_index = frame_indices[frame]
        start = max(0, decision_index - 39)
        window = trace[start:decision_index + 1]
        recent = {n: 0 for n in names}
        for row in window:
            recent[row["process"]] += 1
        denom = max(1, len(window))
        for i, name in enumerate(names):
            value = recent[name] / denom
            bars[i].set_height(value)
            labels[i].set_position((i, value + 0.02))
            labels[i].set_text(f"{value:.0%} / target {shares[i]:.0%}")
        for i, rect in enumerate(cells):
            if i < len(window):
                winner = window[i]["process"]
                rect.set_x(i + 0.1)
                rect.set_width(0.8)
                rect.set_y(names.index(winner) - 0.24)
                rect.set_height(0.48)
                rect.set_visible(True)
            else:
                rect.set_visible(False)
        current = trace[decision_index]
        footer.set_text(
            f"Decision {decision_index + 1}/{len(trace)} | winner: {current['process']} "
            f"| winning ticket: {current['winning_ticket']}/{current['total_waiting_tickets']}"
        )
        return list(bars) + labels + cells + [footer]

    animation = FuncAnimation(fig, update, frames=len(frame_indices), interval=120, blit=False)
    animation.save(MEDIA / "lottery_sync_demo.gif", writer=PillowWriter(fps=8))
    animation.save(MEDIA / "lottery_sync_demo.mp4", writer=FFMpegWriter(fps=12, bitrate=1600))
    plt.close(fig)
    print(f"Wrote {MEDIA / 'lottery_sync_demo.mp4'} and GIF")


if __name__ == "__main__":
    main()
