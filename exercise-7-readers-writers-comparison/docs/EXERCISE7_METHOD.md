# Exercise 7 — Experimental method

Each policy receives the same count of reader and writer operations. A reader
holds the read side briefly and samples the protected version. A writer
increments the version exclusively. Wait time is measured from immediately
before acquisition until entry into the protected region.

The p50 and p95 values are descriptive statistics of this one runtime run.
They are not a theorem about worst-case waiting time. Different Python
implementations, operating systems, CPU loads, and thread schedules can
change them. The tests establish safety invariants and the fair queue's
non-bypass ordering, while the policy descriptions explain the starvation
trade-off.

The fair queue batches only contiguous reader requests at the head. This
preserves reader concurrency without allowing readers that arrive after a
writer to overtake that writer. It is a pedagogical fair lock; production
read/write primitives have platform-specific semantics.
