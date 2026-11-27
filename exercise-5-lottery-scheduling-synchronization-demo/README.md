# Exercise 5 — Lottery Scheduling synchronization demo and clip

This exercise moves lottery scheduling from CPU time slices to a contended
synchronization resource. Three worker threads compete for a shared critical
section through a weighted LotteryMutex. The current owner is the only thread
allowed to update the protected counter; on release, the next owner is drawn
from the waiting requests in proportion to their ticket counts.

Reproduce with: python code/lottery_sync.py --decisions 3000 --seed 20261127
Then run: python code/make_clip.py
Run tests with: pytest -q tests

The experiment writes output/lottery_sync_results.json and
output/lottery_sync_trace.json. The animation is saved as MP4 and GIF in media/.

## Correct interpretation

This is a teaching implementation of lottery-based lock/resource arbitration,
inspired by the resource-generalization in Waldspurger and Weihl (OSDI 1994).
It is not a kernel scheduler, does not preempt arbitrary machine instructions,
and does not provide a hard real-time wait bound. Ticket counts control the
probability of the next grant among requests that are waiting at the draw.
threading.Condition protects the wait queue and the owner invariant.
max_simultaneous_critical_sections is the experimental mutual-exclusion check.
protected_counter == decisions checks that no protected update was lost.
absolute_share_error compares observed grants with the long-run ticket share.
seed makes the random draw sequence reproducible for the reference simulator.
threading interleavings can still vary across platforms.

## Invariants

1. At most one request owns the critical section.
2. Only the owner can release the lock.
3. Every grant corresponds to exactly one protected counter update.
4. A closed demonstration wakes all remaining waiters and terminates cleanly.

A weighted lottery offers probabilistic proportional access, not FIFO ordering.
A low-ticket client can experience a long unlucky wait in a finite run.
threading.Condition wake-up order is not treated as a fairness guarantee.
tests/test_lottery_sync.py covers deterministic draws, invalid tickets,
mutual exclusion, and lost-update prevention.
media/lottery_sync_demo.mp4 is the seminar clip; the GIF is a preview.
