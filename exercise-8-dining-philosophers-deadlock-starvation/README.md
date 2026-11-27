# Exercise 8 — Dining philosophers: deadlock and starvation

Three executions make the distinction between deadlock prevention and
starvation fairness concrete.

1. The deadlock witness has each philosopher take one fork, synchronize, and
   request the next fork. Every request times out while the cycle is held; the
   timeout exists to record the witness and clean up the demo.
2. Resource hierarchy requires every philosopher to acquire the lower-numbered
   fork before the higher-numbered fork. This removes circular wait and hence
   deadlock, but does not claim FIFO lock acquisition or starvation freedom.
3. FairDiningMonitor grants a request when no conflicting philosopher is
   eating and no earlier queued conflicting request exists. It permits
   non-neighbouring philosophers to eat together while preventing a later
   neighbour from overtaking an older request.

Run with: python code/dining.py
Run tests with: pytest -q tests

The output file is output/dining_philosophers_results.json.

## Correctness properties

- Safety: adjacent philosophers never eat simultaneously (they would share a fork).
- Deadlock freedom for resource hierarchy: strict global fork order makes a
  circular wait impossible.
- Local FIFO fairness for the monitor: a request cannot be bypassed by an
  earlier request that competes for either of the same forks.
- Conditional progress: the fairness argument assumes every meal finishes
  and the operating system eventually schedules waiting threads.

The resource-hierarchy method solves circular wait, not starvation. A general
Python Lock does not specify FIFO service. The fair monitor addresses a
different property by enforcing order among conflicting requests. Neither
algorithm provides a hard real-time response bound.
