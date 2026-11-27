# Lottery Scheduling — Operating Systems Project

This repository contains eight exercises covering proportional-share CPU scheduling, real-time scheduling, synchronization primitives, and classical concurrency problems. Each completed exercise is organized around source code, tests, reproducible output, and bilingual reports.

## Exercise map

| Exercise | Topic | Main deliverables |
|---|---|---|
| 1 | Lottery Scheduling introduction | Seeded simulator, experiments, charts, bilingual report |
| 2 | Lottery vs. EDF/RM | Head-to-head simulator, periodic workloads, metrics and traces |
| 3 | Manual EDF/RM scheduling | Worked tick-by-tick schedules, acceptance analysis, verified traces |
| 4 | Dekker, Peterson, semaphores, monitors | Finite-state checks, threaded demonstrations, bounded-buffer experiments |
| 5 | Lottery synchronization demo | Weighted lottery mutex, mutual-exclusion tests, MP4/GIF clip |
| 6 | Research paper and seminar | Paper review, lottery-vs-stride experiment, editable PowerPoint and speaker notes |
| 7 | Readers-writers comparison | Reader preference, writer preference, fair queue, wait-time measurements |
| 8 | Dining philosophers | Circular-wait witness, resource hierarchy, fair monitor, safety/fairness tests |

## Repository layout

Each exercise has a dedicated folder named exercise-N-.... The common structure is:

- code/ — runnable implementations and experiment drivers
- tests/ — automated regression tests
- output/ — machine-readable results and execution traces
- diagrams/, media/, seminar/ — visual or presentation material where applicable
- docs/ — generated Word and PDF reports
- REPORT_EN.md and REPORT_FA.md — report source in English and Persian

The shared builder is tools/report_build.py. It builds a PDF and a Word document from each Markdown report. Persian reports use Vazirmatn and right-to-left paragraph formatting. English identifiers, code, dates and paths are kept left-to-right inside Persian text. Tables use Word's RTL visual table direction without reversing the source columns twice.

All eight exercises now have bilingual visual reports: embedded diagrams, charts, and at least one exercise-specific Gantt/timeline in both Word and PDF. Exercises 5–8 generate their additional figures from the recorded JSON experiment outputs; Exercise 4 includes a protected-section interleaving timeline. The shared validation step checks that the figure assets are actually embedded in both DOCX and PDF files, not merely referenced in Markdown.

Each exercise also has an editable five-slide visual seminar deck (PPTX) and a matching PDF export under its docs/ directory. Every slide contains a related figure, chart, or Gantt/timeline, and the slides are consecutive without blank separators.

## Requirements

Python 3.11 or newer is recommended. Install packages with:

    python -m pip install -r requirements.txt

For the animation and presentation build, the build workflow also installs FFmpeg, LibreOffice, and Poppler utilities.

## Run all tests

    pytest -q exercise-1-lottery-algorithm-introduction/tests exercise-2-lottery-vs-edf-rm-comparison/tests exercise-3-manual-edf-rm-scheduling/tests exercise-4-dekker-peterson-semaphores-monitors/tests exercise-5-lottery-scheduling-synchronization-demo/tests exercise-6-research-paper-and-seminar/tests exercise-7-readers-writers-comparison/tests exercise-8-dining-philosophers-deadlock-starvation/tests

## Run the new exercises

Exercise 5 — generate a weighted-lock synchronization trace and clip:

    python exercise-5-lottery-scheduling-synchronization-demo/code/lottery_sync.py --decisions 3000 --seed 20261127
    python exercise-5-lottery-scheduling-synchronization-demo/code/make_clip.py

Exercise 6 — compare lottery and stride, then build the seminar deck:

    python exercise-6-research-paper-and-seminar/code/research_experiment.py
    python exercise-6-research-paper-and-seminar/seminar/make_slides.py

Exercise 7 — benchmark the three readers-writers policies:

    python exercise-7-readers-writers-comparison/code/readers_writers.py

Exercise 8 — run deadlock, hierarchy, and fair-monitor scenarios:

    python exercise-8-dining-philosophers-deadlock-starvation/code/dining.py

Each command writes a JSON result under that exercise's output/ directory.

## Build reports

Example:

    python tools/report_build.py fa exercise-5-lottery-scheduling-synchronization-demo/REPORT_FA.md exercise-5-lottery-scheduling-synchronization-demo/docs/Exercise5_Lottery_Sync_FA
    python tools/report_build.py en exercise-5-lottery-scheduling-synchronization-demo/REPORT_EN.md exercise-5-lottery-scheduling-synchronization-demo/docs/Exercise5_Lottery_Sync_EN

The reports for Exercises 5–8 include extended, exercise-specific technical appendices. Every English and Persian Word/PDF report for Exercises 5–8 must contain more than 40 pages (minimum 41). The build workflow checks the PDF page count and independently converts each DOCX with LibreOffice to confirm the Word pagination also exceeds 40 pages.

The shared builder defaults to a minimum of 41 PDF pages:

    python tools/report_build.py fa exercise-5-lottery-scheduling-synchronization-demo/REPORT_FA.md exercise-5-lottery-scheduling-synchronization-demo/docs/Exercise5_Lottery_Sync_FA

The appendix entry in each report's front matter loads its corresponding APPENDICES_EN.md or APPENDICES_FA.md file. The [[PAGEBREAK]] markers create matching section breaks in both PDF and Word output.

## Reproducibility and scope

Randomized experiments accept fixed seeds. The generated JSON records workload parameters and metrics so results can be reproduced and audited. A statistical share is an expectation, not a per-window guarantee. Lottery Scheduling is not a hard real-time scheduler and does not inherently guarantee deadlines or bounded waiting.

For the synchronization exercises, safety, deadlock freedom, starvation freedom, and hard response-time guarantees are treated as separate properties. Each report states which properties are implemented or checked and the assumptions behind progress claims.

## Automated branch build

The GitHub Actions workflow on branch arena/ce95d03c-lottery-scheduling runs the tests, regenerates all bilingual Word/PDF reports, produces the exercise outputs and seminar artifacts, performs document conversion checks, and commits generated deliverables to the same branch.
