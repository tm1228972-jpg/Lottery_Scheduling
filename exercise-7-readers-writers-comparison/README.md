# Exercise 7 — Readers-writers comparison

The implementation compares three admission policies for a shared data object:
reader preference, writer preference, and a fair arrival queue. Readers may
overlap one another; a writer must have exclusive access.

Run with: python code/readers_writers.py
Run tests with: pytest -q tests

The results file is output/readers_writers_results.json. It reports sample
counts, mean, median-like p50, p95, maximum wait time, peak concurrent readers,
and completed writes.

## Policy semantics

- Reader preference lets a new reader pass waiting writers while no writer is
  active. A continuing stream of readers can starve a writer.
- Writer preference blocks newly arriving readers while any writer waits.
  A continuing stream of writers can starve readers.
- Fair mode queues requests by arrival. Consecutive readers at the head may
  enter as a batch, but a later reader cannot pass an earlier writer.

## Correctness and measurement

Every test checks exclusive writer access and parallel reader access. A
deterministic queue-order test places a writer between two readers and checks
that the later reader cannot bypass it in fair mode. The benchmark uses real
CPython threads and therefore reports host-dependent timing, not a universal
latency guarantee. The no-starvation statement for fair mode assumes each
critical section terminates and runnable threads eventually receive CPU time.
