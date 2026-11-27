# Exercise 6 — Research paper and seminar

## Academic source

The exercise reviews Waldspurger and Weihl's OSDI 1994 paper, *Lottery Scheduling: Flexible Proportional-Share Resource Management*. The report covers tickets, probability of service, transfer, currencies, compensation, and the distinction between proportional allocation and real-time guarantees.

## Reproduce the experiment

From the repository root:

    python exercise-6-research-paper-and-seminar/code/research_experiment.py
    pytest -q exercise-6-research-paper-and-seminar/tests
    python exercise-6-research-paper-and-seminar/seminar/make_slides.py

The JSON output is written to output/scheduler_comparison.json. The editable PowerPoint deck is written to docs/Lottery_Scheduling_Seminar.pptx. The GitHub Actions build exports a PDF version alongside the deck.

## Seminar materials

- REPORT_EN.md and REPORT_FA.md — the bilingual research review.
- seminar/SPEAKER_NOTES_EN.md and seminar/SPEAKER_NOTES_FA.md — presentation notes.
- seminar/make_slides.py — reproducible slide generator.

The comparison is a simplified single-resource model with equal quanta and continuously runnable clients. It is not a kernel benchmark and does not establish real-time deadline guarantees. The report records this scope explicitly.
