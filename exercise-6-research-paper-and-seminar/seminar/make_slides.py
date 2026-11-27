#!/usr/bin/env python3
"""Build a visual, editable, gap-free seminar deck for Lottery Scheduling."""
from __future__ import annotations

import json
import random
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "output" / "scheduler_comparison.json"
OUT = ROOT / "docs" / "Lottery_Scheduling_Seminar.pptx"

NAVY = "172B4D"
BLUE = "2864B4"
CYAN = "28A6B8"
TEAL = "168A83"
ORANGE = "E58A32"
GREEN = "3D9B68"
RED = "C65B5B"
INK = "26364A"
MUTED = "66758A"
PAPER = "F3F6FA"
WHITE = "FFFFFF"
PALE_BLUE = "E8F0FB"
PALE_CYAN = "E6F6F7"
PALE_ORANGE = "FFF2E3"
PALE_GREEN = "E9F5EE"
PALE_RED = "FCEEEE"
TRACK = "E5EAF1"
FONT = "Aptos"


def color(hex_value: str) -> RGBColor:
    return RGBColor.from_string(hex_value)


def set_name(shape, name: str):
    shape.name = name
    return shape


def add_rect(slide, x, y, w, h, fill=WHITE, line=None, rounded=True, name=""):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(fill)
    shape.line.color.rgb = color(line or fill)
    shape.line.width = Pt(0.8)
    if name:
        set_name(shape, name)
    return shape


def add_circle(slide, x, y, d, fill, line=None, name=""):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(fill)
    shape.line.color.rgb = color(line or fill)
    if name:
        set_name(shape, name)
    return shape


def add_text(slide, text, x, y, w, h, size=14, fill=INK, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, name=""):
    shape = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    if name:
        set_name(shape, name)
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.035)
    tf.margin_right = Inches(0.035)
    tf.margin_top = Inches(0.015)
    tf.margin_bottom = Inches(0.015)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.text = str(text)
    p.alignment = align
    p.font.name = FONT
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color(fill)
    return shape


def add_line(slide, x1, y1, x2, y2, fill=TRACK, width=2):
    shape = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    shape.line.color.rgb = color(fill)
    shape.line.width = Pt(width)
    return shape


def add_panel(slide, title, subtitle=""):
    panel = add_rect(
        slide, 6.55, 1.68, 6.18, 5.05, WHITE, "E5EAF1",
        name="VISUAL | PANEL"
    )
    add_text(slide, title, 6.86, 1.91, 5.55, 0.36,
             size=16, fill=NAVY, bold=True)
    if subtitle:
        add_text(slide, subtitle, 6.88, 2.28, 5.48, 0.28,
                 size=9, fill=MUTED)
    return panel


def add_header(slide, title, subtitle, number, total):
    add_rect(slide, 0, 0, 13.333, 0.11, BLUE, rounded=False)
    add_text(slide, title, 0.62, 0.35, 11.7, 0.62,
             size=27, fill=NAVY, bold=True)
    add_text(slide, subtitle, 0.66, 1.05, 11.7, 0.34,
             size=11, fill=MUTED)
    add_circle(slide, 12.24, 0.43, 0.42, PALE_BLUE)
    add_text(slide, f"{number:02d}", 12.24, 0.43, 0.42, 0.42,
             size=10, fill=BLUE, bold=True, align=PP_ALIGN.CENTER)


def add_bullets(slide, items):
    top = 1.95
    available = 4.55
    step = available / max(1, len(items))
    font_size = 15 if len(items) <= 4 else 13
    for idx, item in enumerate(items):
        y = top + idx * step
        add_circle(slide, 0.72, y + 0.18, 0.13,
                   [BLUE, CYAN, ORANGE, GREEN][idx % 4])
        add_text(slide, item, 1.01, y, 5.12, min(0.92, step - 0.03),
                 size=font_size, fill=INK, valign=MSO_ANCHOR.MIDDLE)


def add_footer(slide, number, total):
    add_line(slide, 0.62, 6.98, 12.70, 6.98, "E1E7EF", 0.8)
    add_text(slide, "OPERATING SYSTEMS  •  LOTTERY SCHEDULING",
             0.66, 7.06, 7.9, 0.2, size=8, fill=MUTED)
    add_text(slide, f"{number:02d} / {total:02d}",
             11.72, 7.04, 0.93, 0.22, size=8, fill=MUTED,
             align=PP_ALIGN.RIGHT)
    # A single fast fade keeps the deck flowing without blank separator slides.
    transition = OxmlElement("p:transition")
    transition.set("spd", "fast")
    transition.append(OxmlElement("p:fade"))
    slide._element.insert(1, transition)


def add_node(slide, x, y, w, h, title, detail, fill=PALE_BLUE, accent=BLUE):
    add_rect(slide, x, y, w, h, fill, "E2E9F2", name="VISUAL | NODE")
    add_rect(slide, x, y, 0.075, h, accent, rounded=False)
    add_text(slide, title, x + 0.18, y + 0.09, w - 0.3, 0.32,
             size=12, fill=NAVY, bold=True)
    add_text(slide, detail, x + 0.18, y + 0.43, w - 0.3, h - 0.5,
             size=9, fill=MUTED)


def add_bar_chart(slide, rows, max_value=1.0, unit="%", x=6.9, y=2.8,
                  width=5.35, row_h=0.82):
    label_w, value_w = 1.18, 0.82
    bar_x = x + label_w
    bar_w = width - label_w - value_w
    for i, (label, value, shade) in enumerate(rows):
        yy = y + i * row_h
        add_text(slide, label, x, yy, label_w - 0.08, 0.35,
                 size=10, fill=INK, bold=True)
        add_rect(slide, bar_x, yy + 0.05, bar_w, 0.24, TRACK,
                 rounded=True, name="VISUAL | CHART TRACK")
        fill_w = max(0.03, bar_w * max(0.0, min(1.0, value / max_value)))
        add_rect(slide, bar_x, yy + 0.05, fill_w, 0.24, shade,
                 rounded=True, name="VISUAL | BAR")
        text_value = f"{value * 100:.2f}{unit}"
        add_text(slide, text_value, bar_x + bar_w + 0.04, yy,
                 value_w - 0.04, 0.35, size=9, fill=MUTED,
                 align=PP_ALIGN.RIGHT)


def add_ticket_strip(slide):
    start_x, y, cell_w, gap = 6.91, 3.18, 0.49, 0.045
    shades = [BLUE] * 5 + [CYAN] * 3 + [ORANGE] * 2
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    for idx, (shade, label) in enumerate(zip(shades, labels)):
        x = start_x + idx * (cell_w + gap)
        fill = ORANGE if idx == 6 else shade
        add_rect(slide, x, y, cell_w, 0.62, fill, rounded=True,
                 name="VISUAL | TICKET")
        add_text(slide, label, x, y + 0.04, cell_w, 0.48,
                 size=12, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "P1  •  tickets 1–5", 6.96, 4.05, 2.2, 0.36,
             size=10, fill=BLUE, bold=True)
    add_text(slide, "P2  •  tickets 6–8", 9.06, 4.05, 1.85, 0.36,
             size=10, fill=CYAN, bold=True)
    add_text(slide, "P3  •  9–10", 10.93, 4.05, 1.45, 0.36,
             size=10, fill=ORANGE, bold=True)
    add_line(slide, 10.1, 3.86, 10.1, 3.72, ORANGE, 2)
    add_text(slide, "Draw = 7  →  P2 wins", 7.05, 4.72, 5.1, 0.48,
             size=17, fill=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "The winning ticket lies inside P2's interval.",
             7.02, 5.28, 5.2, 0.32, size=10, fill=MUTED,
             align=PP_ALIGN.CENTER)


def add_extension_map(slide):
    cards = [
        (6.9, 2.86, "TRANSFER", "Lend tickets to a dependency", PALE_BLUE, BLUE),
        (9.75, 2.86, "CURRENCIES", "Local shares inside modules", PALE_CYAN, CYAN),
        (6.9, 4.52, "COMPENSATION", "Account for early blocking", PALE_ORANGE, ORANGE),
        (9.75, 4.52, "MORE RESOURCES", "Locks, I/O, and other claims", PALE_GREEN, GREEN),
    ]
    for x, y, title, detail, fill, accent in cards:
        add_node(slide, x, y, 2.55, 1.25, title, detail, fill, accent)
    add_circle(slide, 9.25, 3.93, 0.48, NAVY)
    add_text(slide, "T", 9.25, 3.93, 0.48, 0.48,
             size=15, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)


def add_gantt(slide):
    labels = ["Configure workload", "Run lottery seeds", "Run stride baseline", "Aggregate metrics"]
    stages = [(0, 1), (1, 3), (1, 3), (4, 1)]
    x0, y0, total_w = 8.7, 2.86, 3.35
    for i, (label, (start, length)) in enumerate(zip(labels, stages)):
        yy = y0 + i * 0.72
        add_text(slide, label, 6.9, yy, 1.72, 0.36,
                 size=9, fill=INK, bold=True)
        add_rect(slide, x0, yy + 0.05, total_w, 0.25, TRACK,
                 rounded=True, name="VISUAL | GANTT TRACK")
        bx = x0 + total_w * (start / 5)
        bw = total_w * (length / 5)
        shade = [BLUE, CYAN, ORANGE, GREEN][i]
        add_rect(slide, bx, yy + 0.05, bw, 0.25, shade,
                 rounded=True, name="VISUAL | GANTT BAR")
    for tick in range(6):
        xx = x0 + total_w * tick / 5
        add_line(slide, xx, 2.75, xx, 5.88, "EEF1F5", 0.6)
        add_text(slide, str(tick + 1), xx - 0.08, 5.98, 0.18, 0.24,
                 size=8, fill=MUTED, align=PP_ALIGN.CENTER)
    add_text(slide, "Ordered experiment phases (not wall-clock durations)",
             7.02, 6.34, 5.15, 0.22, size=8, fill=MUTED,
             align=PP_ALIGN.CENTER)


def lottery_sequence(tickets, decisions=10, seed=7):
    rng = random.Random(seed)
    names = list(tickets)
    total = sum(tickets.values())
    sequence = []
    for _ in range(decisions):
        draw = rng.randint(1, total)
        cumulative = 0
        for name in names:
            cumulative += tickets[name]
            if draw <= cumulative:
                sequence.append(name)
                break
    return sequence


def stride_sequence(tickets, decisions=10, stride_constant=1_000_000):
    names = list(tickets)
    strides = {name: stride_constant / tickets[name] for name in names}
    passes = {name: 0.0 for name in names}
    sequence = []
    for _ in range(decisions):
        winner = min(names, key=lambda name: (passes[name], names.index(name)))
        sequence.append(winner)
        passes[winner] += strides[winner]
    return sequence


def add_sequence_row(slide, label, sequence, y, subtitle):
    palette = {"P1": BLUE, "P2": CYAN, "P3": ORANGE}
    add_text(slide, label, 6.92, y - 0.35, 5.25, 0.28,
             size=11, fill=NAVY, bold=True)
    start_x, cell_w, gap = 6.95, 0.47, 0.055
    for i, name in enumerate(sequence):
        x = start_x + i * (cell_w + gap)
        add_rect(slide, x, y, cell_w, 0.56, palette[name],
                 rounded=True, name="VISUAL | SCHEDULE SLOT")
        add_text(slide, name, x, y + 0.03, cell_w, 0.48,
                 size=10, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, subtitle, 6.98, y + 0.64, 5.05, 0.23,
             size=8, fill=MUTED)


def add_lock_cycle(slide):
    nodes = [
        (6.92, 3.15, "1", "REQUEST", "Client asks for lock", PALE_BLUE, BLUE),
        (9.72, 3.15, "2", "SELECT", "Eligible owner is chosen", PALE_CYAN, CYAN),
        (9.72, 4.86, "3", "CRITICAL", "Only owner enters", PALE_ORANGE, ORANGE),
        (6.92, 4.86, "4", "RELEASE", "Unlock and wake waiters", PALE_GREEN, GREEN),
    ]
    for x, y, number, title, detail, fill, accent in nodes:
        add_circle(slide, x + 0.08, y + 0.18, 0.42, accent)
        add_text(slide, number, x + 0.08, y + 0.18, 0.42, 0.42,
                 size=11, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_node(slide, x + 0.58, y, 2.1, 0.95, title, detail, fill, accent)
    add_line(slide, 9.55, 3.62, 9.72, 3.62, MUTED, 2)
    add_line(slide, 10.77, 4.12, 10.77, 4.82, MUTED, 2)
    add_line(slide, 9.72, 5.33, 9.55, 5.33, MUTED, 2)
    add_line(slide, 8.13, 4.86, 8.13, 4.18, MUTED, 2)
    add_text(slide, "Ownership and wake-up protocol remain correctness-critical.",
             7.0, 6.18, 5.15, 0.28, size=9, fill=MUTED,
             align=PP_ALIGN.CENTER)


def add_limit_matrix(slide):
    x0, y0 = 6.91, 2.85
    cols = [2.05, 1.28, 1.55]
    headers = ["QUESTION", "STATUS", "EVIDENCE"]
    xx = x0
    for title, width in zip(headers, cols):
        add_rect(slide, xx, y0, width, 0.48, NAVY, rounded=True)
        add_text(slide, title, xx + 0.06, y0 + 0.04, width - 0.12, 0.38,
                 size=9, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)
        xx += width + 0.06
    rows = [
        ("Proportional share", "Shown", "Share error"),
        ("Hard deadlines", "Not shown", "No deadline model"),
        ("Wall-clock latency", "Not measured", "No latency data"),
        ("Multicore effects", "Not measured", "Single CPU"),
    ]
    status_colors = [PALE_GREEN, PALE_RED, PALE_ORANGE, PALE_ORANGE]
    for i, row in enumerate(rows):
        yy = y0 + 0.62 + i * 0.73
        xx = x0
        for j, (text, width) in enumerate(zip(row, cols)):
            fill = status_colors[i] if j == 1 else ("F7F9FC" if i % 2 == 0 else WHITE)
            add_rect(slide, xx, yy, width, 0.53, fill, "E8EDF3",
                     rounded=True, name="VISUAL | LIMIT MATRIX")
            add_text(slide, text, xx + 0.06, yy + 0.04, width - 0.12, 0.43,
                     size=8 if j == 2 else 9, fill=INK,
                     bold=(j == 1), align=PP_ALIGN.CENTER)
            xx += width + 0.06
    add_text(slide, "Interpret the experiment within its stated model.",
             7.0, 6.24, 5.2, 0.25, size=9, fill=MUTED,
             align=PP_ALIGN.CENTER)


def add_decision_tree(slide):
    add_node(slide, 8.05, 2.77, 3.25, 0.9,
             "WHAT MUST THE SYSTEM GUARANTEE?",
             "Start from the service objective", PALE_BLUE, BLUE)
    add_line(slide, 9.67, 3.68, 9.67, 4.05, MUTED, 2)
    add_line(slide, 8.2, 4.05, 11.15, 4.05, MUTED, 2)
    add_line(slide, 8.2, 4.05, 8.2, 4.34, MUTED, 2)
    add_line(slide, 11.15, 4.05, 11.15, 4.34, MUTED, 2)
    add_node(slide, 6.9, 4.36, 2.55, 1.2,
             "PROPORTIONAL SHARE",
             "Consider lottery scheduling", PALE_CYAN, CYAN)
    add_node(slide, 9.85, 4.36, 2.55, 1.2,
             "DEADLINE GUARANTEES",
             "Analyze EDF / RM", PALE_ORANGE, ORANGE)
    add_text(slide, "Choose by guarantee, not by a single benchmark score.",
             7.0, 6.12, 5.15, 0.3, size=9, fill=MUTED,
             align=PP_ALIGN.CENTER)


def add_reference_timeline(slide):
    points = [
        (7.18, "1994", "OSDI paper", "Lottery Scheduling", BLUE),
        (8.92, "1995", "MIT report", "Lottery + Stride", CYAN),
        (10.67, "1995", "MIT memo", "Stride Scheduling", ORANGE),
        (12.18, "2026", "This lab", "Reproducible model", GREEN),
    ]
    add_line(slide, 7.25, 4.0, 12.15, 4.0, "C7D2E0", 3)
    for x, year, title, detail, shade in points:
        add_circle(slide, x - 0.12, 3.88, 0.28, shade)
        add_text(slide, year, x - 0.35, 3.2, 0.75, 0.32,
                 size=11, fill=shade, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, x - 0.62, 4.35, 1.22, 0.35,
                 size=9, fill=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, detail, x - 0.68, 4.74, 1.35, 0.54,
                 size=8, fill=MUTED, align=PP_ALIGN.CENTER)
    add_rect(slide, 7.02, 5.65, 5.3, 0.62, PALE_BLUE, "E2E9F2")
    add_text(slide, "Core idea: make resource entitlement explicit and measurable.",
             7.2, 5.73, 4.95, 0.45, size=10, fill=NAVY,
             bold=True, align=PP_ALIGN.CENTER)


def add_visual(slide, kind, results):
    if kind == "cover":
        add_panel(slide, "From tickets to a resource decision",
                  "The same entitlement model can describe many shared resources")
        add_node(slide, 6.95, 3.0, 1.45, 1.4, "TICKETS",
                 "5 : 3 : 2", PALE_BLUE, BLUE)
        add_node(slide, 8.88, 3.0, 1.45, 1.4, "DRAW",
                 "Choose 1..T", PALE_CYAN, CYAN)
        add_node(slide, 10.82, 3.0, 1.52, 1.4, "QUANTUM",
                 "Allocate next", PALE_ORANGE, ORANGE)
        add_line(slide, 8.41, 3.68, 8.84, 3.68, MUTED, 2)
        add_line(slide, 10.34, 3.68, 10.78, 3.68, MUTED, 2)
        for i, shade in enumerate([BLUE] * 5 + [CYAN] * 3 + [ORANGE] * 2):
            add_rect(slide, 7.1 + i * 0.48, 5.12, 0.38, 0.3, shade,
                     rounded=True, name="VISUAL | TICKET LEGEND")
        add_text(slide, "5 tickets", 7.02, 5.56, 1.28, 0.26,
                 size=9, fill=BLUE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "3 tickets", 8.97, 5.56, 1.28, 0.26,
                 size=9, fill=CYAN, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, "2 tickets", 10.88, 5.56, 1.28, 0.26,
                 size=9, fill=ORANGE, bold=True, align=PP_ALIGN.CENTER)
    elif kind == "share":
        add_panel(slide, "Target resource share",
                  "Ticket proportions are expectations over repeated allocations")
        targets = results["target_shares"]
        add_bar_chart(slide, [
            ("P1 · 5", targets["P1"], BLUE),
            ("P2 · 3", targets["P2"], CYAN),
            ("P3 · 2", targets["P3"], ORANGE),
        ], max_value=0.55, y=3.05)
        add_text(slide, "Total tickets = 10", 7.0, 5.9, 5.2, 0.4,
                 size=15, fill=NAVY, bold=True, align=PP_ALIGN.CENTER)
    elif kind == "rule":
        add_panel(slide, "Lottery draw: one decision at a time",
                  "The eligible set determines the denominator T")
        steps = [
            (6.9, "1", "COUNT", "T = Σ tickets", PALE_BLUE, BLUE),
            (8.28, "2", "DRAW", "Uniform integer 1..T", PALE_CYAN, CYAN),
            (9.66, "3", "MAP", "Find the winning interval", PALE_ORANGE, ORANGE),
            (11.04, "4", "ALLOCATE", "Grant next quantum", PALE_GREEN, GREEN),
        ]
        for x, num, title, detail, fill, shade in steps:
            add_circle(slide, x + 0.39, 3.14, 0.46, shade)
            add_text(slide, num, x + 0.39, 3.14, 0.46, 0.46,
                     size=12, fill=WHITE, bold=True, align=PP_ALIGN.CENTER)
            add_node(slide, x, 3.83, 1.23, 1.18, title, detail, fill, shade)
        for x in [8.16, 9.54, 10.92]:
            add_line(slide, x, 4.41, x + 0.1, 4.41, MUTED, 2)
        add_text(slide, "P(client i wins) = tᵢ / T",
                 7.04, 5.63, 5.12, 0.55, size=19, fill=NAVY,
                 bold=True, align=PP_ALIGN.CENTER)
    elif kind == "example":
        add_panel(slide, "Ticket intervals for the 5 : 3 : 2 example",
                  "Each ticket number belongs to exactly one client")
        add_ticket_strip(slide)
    elif kind == "extensions":
        add_panel(slide, "Extensions in the original design",
                  "Ticket ownership can express more than one CPU share")
        add_extension_map(slide)
    elif kind == "gantt":
        add_panel(slide, "Reproducible experiment plan",
                  "Each run uses the same workload and a different seed")
        add_gantt(slide)
    elif kind == "results":
        add_panel(slide, "Maximum absolute share error",
                  "Lower error means closer observed shares in this workload")
        lottery = results["lottery"]
        stride = results["stride"]
        add_bar_chart(slide, [
            ("Lottery mean", lottery["mean_max_absolute_share_error"], BLUE),
            ("Lottery worst", lottery["worst_max_absolute_share_error"], ORANGE),
            ("Stride", stride["max_absolute_share_error"], GREEN),
        ], max_value=max(lottery["worst_max_absolute_share_error"] * 1.15, 0.001),
           unit="%", y=3.02)
        add_text(slide, f"{results['workload']['seeds']} seeds  •  "
                 f"{results['workload']['decisions_per_run']:,} decisions/run",
                 7.0, 5.88, 5.2, 0.34, size=10, fill=MUTED,
                 align=PP_ALIGN.CENTER)
        add_text(slide, "Stride error is zero in this divisible, equal-quantum model.",
                 7.0, 6.22, 5.2, 0.28, size=8, fill=GREEN,
                 align=PP_ALIGN.CENTER)
    elif kind == "schedule":
        add_panel(slide, "Random choice versus virtual-time order",
                  "Illustrative first 10 decisions; not a measured kernel trace")
        tickets = results["workload"]["tickets"]
        add_sequence_row(slide, "LOTTERY · fixed example seed 7",
                         lottery_sequence(tickets), 3.25,
                         "Random order can vary from one seed to another.")
        add_sequence_row(slide, "STRIDE · deterministic tie-break",
                         stride_sequence(tickets), 5.05,
                         "Virtual pass orders service deterministically.")
    elif kind == "lock":
        add_panel(slide, "From scheduler rights to a lock protocol",
                  "The lottery selects a waiter; the lock still enforces ownership")
        add_lock_cycle(slide)
    elif kind == "limits":
        add_panel(slide, "What this experiment can and cannot claim",
                  "Evidence is meaningful only inside the declared model")
        add_limit_matrix(slide)
    elif kind == "choice":
        add_panel(slide, "Choose the policy that matches the service goal",
                  "Proportional allocation and deadline guarantees are different goals")
        add_decision_tree(slide)
    elif kind == "references":
        add_panel(slide, "Research lineage and reproducible lab work",
                  "Primary paper, follow-up technical reports, and this experiment")
        add_reference_timeline(slide)


def build_slide(prs, number, total, title, subtitle, bullets, kind, results):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(PAPER)
    add_header(slide, title, subtitle, number, total)
    add_bullets(slide, bullets)
    add_visual(slide, kind, results)
    add_footer(slide, number, total)
    return slide


def main():
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slides = [
        ("Lottery Scheduling",
         "A visual seminar on proportional-share resource management",
         ["How tickets express a client's entitlement to a shared resource.",
          "How a random draw converts entitlement into one allocation decision.",
          "What the research paper contributes—and what the lab model can verify."],
         "cover"),
        ("Why proportional share?",
         "An explicit share contract is different from a fixed priority number",
         ["Tickets represent relative entitlement among currently eligible clients.",
          "More tickets increase the probability of receiving the next quantum.",
          "Expected share is proportional; a short sample can still vary.",
          "The scheduler must define which clients are eligible at each draw."],
         "share"),
        ("The allocation rule",
         "A small, auditable procedure with a clear probability model",
         ["Sum the tickets belonging to runnable clients.",
          "Draw one uniformly distributed integer from 1 through the total.",
          "Map the winning integer to the client that owns that ticket interval.",
          "Grant one allocation quantum, then repeat with the updated eligible set."],
         "rule"),
        ("A worked 5 : 3 : 2 example",
         "A concrete ticket interval makes the random choice easy to inspect",
         ["P1 owns tickets 1–5; P2 owns 6–8; P3 owns 9–10.",
          "The total is 10, so the expected shares are 50%, 30%, and 20%.",
          "A draw of 7 falls inside P2's interval and selects P2.",
          "This is one decision, not a promise that every ten draws match exactly."],
         "example"),
        ("Resource-management extensions",
         "The paper generalizes tickets to dependencies and other resource types",
         ["Ticket transfer can temporarily direct entitlement to a dependency.",
          "Ticket currencies let a subsystem distribute its own internal shares.",
          "Compensation tickets can account for a client that blocks early.",
          "The same idea can be applied to locks and resources beyond CPU time."],
         "extensions"),
        ("Experimental method",
         "The comparison is reproducible, controlled, and deliberately narrow",
         ["Workload: P1:P2:P3 = 5:3:2, with equal allocation quanta.",
          f"Lottery: {results['workload']['seeds']} independent seeds, "
          f"{results['workload']['decisions_per_run']:,} decisions per seed.",
          "Stride uses deterministic virtual-pass accounting and a fixed tie-break.",
          "Metric: maximum absolute deviation from the target share."],
         "gantt"),
        ("Measured comparison",
         "The observed values come from the repository's reproducible experiment",
         [f"Lottery mean maximum error: "
          f"{results['lottery']['mean_max_absolute_share_error'] * 100:.3f}%.",
          f"Lottery worst-seed maximum error: "
          f"{results['lottery']['worst_max_absolute_share_error'] * 100:.3f}%.",
          f"Stride maximum error: "
          f"{results['stride']['max_absolute_share_error'] * 100:.3f}%.",
          "The zero stride error is specific to this divisible, equal-quantum setup."],
         "results"),
        ("Lottery and stride are not identical",
         "The allocation order matters even when the long-run target is the same",
         ["Lottery makes each eligible client's next-win probability explicit.",
          "Stride tracks virtual service and selects the smallest virtual pass.",
          "Lottery can vary over short windows; stride is deterministic here.",
          "This comparison does not measure latency, overhead, cache, or multicore effects."],
         "schedule"),
        ("Synchronization connection",
         "A weighted lock still needs correct mutual exclusion and wake-up rules",
         ["The lock must identify the current owner and serialize ownership changes.",
          "Waiters must sleep and re-check the guarded predicate after waking.",
          "Release must make the next eligible owner visible without a lost wake-up.",
          "Ticket weights alone do not imply FIFO service or a hard starvation bound."],
         "lock"),
        ("Limitations and interpretation",
         "A correct conclusion states both the evidence and the missing evidence",
         ["The model has one CPU, equal quanta, and continuously runnable clients.",
          "It does not establish hard real-time deadlines or wall-clock latency bounds.",
          "It does not measure context-switch cost, caches, multicore behavior, or a kernel.",
          "Treat measured share error as one metric—not as a complete system verdict."],
         "limits"),
        ("Which policy should be used?",
         "Select a scheduler from the service guarantee the system actually needs",
         ["Use lottery when probabilistic proportional allocation is the objective.",
          "Use EDF/RM analysis when deadline feasibility is the requirement.",
          "Use workload-specific measurements before making performance claims.",
          "State assumptions and the fairness definition alongside every result."],
         "choice"),
        ("References and research path",
         "Primary research, technical follow-ups, and the experiment in this repository",
         ["Waldspurger & Weihl, Lottery Scheduling, OSDI 1994.",
          "Waldspurger, Lottery and Stride Scheduling, MIT-LCS-TR-667, 1995.",
          "Waldspurger & Weihl, Stride Scheduling, MIT-LCS-TM-528, 1995.",
          "Repository experiment: 50 seeds and 10,000 decisions per run."],
         "references"),
    ]

    total = len(slides)
    for number, (title, subtitle, bullets, kind) in enumerate(slides, start=1):
        build_slide(prs, number, total, title, subtitle, bullets, kind, results)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"Wrote {OUT} with {len(prs.slides)} consecutive visual slides.")


if __name__ == "__main__":
    main()
