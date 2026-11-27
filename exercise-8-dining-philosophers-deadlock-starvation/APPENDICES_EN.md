# Extended dining-philosophers appendix — Exercise 8

[[PAGEBREAK]]
## Appendix D.01 — System model and resource contract

There are N philosophers arranged in a ring and N exclusive fork resources. Philosopher i needs fork i and fork (i+1) modulo N before it may eat. A fork is either free or owned by exactly one philosopher. Eating is the critical section; thinking does not require a fork. The resource model makes the dependency graph explicit and allows safety and progress to be discussed separately.

The program uses Python locks to represent forks. The abstraction captures exclusive ownership but does not model physical utensil handling, CPU dispatch, or real dining time.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.02 — The four Coffman conditions

Deadlock requires mutual exclusion, hold-and-wait, no preemption, and circular wait in the classic resource-allocation model. The dining philosophers construction can satisfy all four: forks are exclusive, each philosopher keeps one while requesting another, locks are not forcibly taken, and requests can form a cycle around the table.

A prevention strategy should identify which condition it removes. Saying only that an algorithm 'avoids deadlock' without naming the broken condition hides the reasoning.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.03 — Mutual exclusion in the fork model

A fork cannot be used by two adjacent philosophers at the same time. This is the mutual-exclusion condition and is a safety requirement rather than the cause of every deadlock by itself. Removing mutual exclusion would not be a valid solution because two neighbours sharing one fork cannot both eat correctly.

The solution must preserve exclusive fork use while changing the acquisition protocol. Every alternative should be checked against adjacent-philosopher conflicts.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.04 — Hold-and-wait

In the classic construction, a philosopher first acquires one fork and retains it while waiting for the second. The philosopher cannot eat yet, but it continues holding a resource needed by another participant. This partial allocation is what allows the wait-for chain to form.

The fair monitor avoids separate partial acquisitions by granting the right to use both forks in one admission decision. The resource-hierarchy solution keeps separate locks but imposes a strict order.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.05 — No preemption

A fork is released by the philosopher that owns it; another thread cannot safely take it away in the middle of eating. This models non-preemption. A deadlock prevention approach should not casually violate this condition by forcibly releasing a resource while its critical section is active.

The monitor can coordinate access before a meal begins, but once admitted the philosopher must complete the finite meal and release its resources in a finally-safe path.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.06 — Circular wait graph

In the five-philosopher ring, philosopher P0 may hold fork 0 and wait for fork 1, while P1 holds fork 1 and waits for fork 2, continuing around the ring until P4 waits for fork 0. The wait-for graph then contains a directed cycle. No participant can obtain its second fork.

Writing the cycle explicitly is more precise than relying on a picture alone. Each edge should identify the requesting philosopher and the fork owner that blocks it.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.07 — Resource-allocation graph

A resource-allocation graph has process nodes and resource nodes. An assignment edge points from a resource to its owner; a request edge points from a process to the resource it needs. For single-instance resources, a cycle is a strong deadlock indicator. The dining model has one instance per fork.

Distinguish a request edge from an assignment edge. Confusing their directions can reverse the meaning of a graph and invalidate the deadlock argument.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.08 — Controlled deadlock witness

The demonstration makes every philosopher acquire its first fork and then synchronizes them at a barrier. Only after all first acquisitions complete do the threads request their second forks. This creates the circular-wait state deterministically rather than relying on a lucky race between thread starts.

The second barrier ensures every second-fork attempt has completed or timed out before any first fork is released. Without it, one timeout could release a fork early and let a neighbour proceed, making the witness flaky.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.09 — Purpose of timeout in the lab harness

The circular-wait example uses a finite timeout so the program can record the blocked state and clean up. A real deadlock would remain blocked indefinitely unless an external recovery mechanism intervened. The timeout is therefore a laboratory safety mechanism, not the algorithm that prevents deadlock.

The report must not claim that timeout solves deadlock. It detects a stalled acquisition in the demonstration and allows the test harness to terminate.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.10 — Barrier and deterministic setup

A barrier coordinates the point at which all philosophers have acquired their first fork. This removes timing variation from the critical part of the deadlock construction. A second barrier prevents early cleanup from changing the state before all second-fork attempts have been observed.

The test should assert that every philosopher holds its first fork and fails to acquire the second within the configured timeout. It should also assert that every thread terminates after cleanup.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.11 — Global resource hierarchy

Assign every fork a unique numeric rank. Each philosopher must acquire the lower-numbered fork before the higher-numbered fork, regardless of which fork is conceptually left or right. All threads therefore follow one strict global order for resource acquisition.

A single consistent order removes circular wait. The order must be global, not merely local to each philosopher, or a cycle can still form.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.12 — Proof that strict ordering removes cycles

Assume a wait-for cycle exists under the resource-hierarchy rule. Along every wait edge, a philosopher holds a lower-ranked resource and requests a higher-ranked resource. Following the cycle would require fork ranks to increase strictly at every step and eventually return to the starting fork. A strictly increasing sequence cannot return to its start, which is a contradiction.

This proof is stronger than a finite test. Tests demonstrate that the implementation follows the order; the ordering argument explains why a circular wait is impossible if the rule is always obeyed.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.13 — Why left-right ordering is insufficient

If each philosopher independently follows 'left first, right second', the global order may differ from one philosopher to the next. One philosopher's right fork is another philosopher's left fork, so all participants can still form a cycle. Naming resources by physical side does not establish a total order.

The implementation sorts the two numeric fork identifiers before acquisition. Review this exact operation because omitting it for one philosopher would break the proof.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.14 — Total order as a general technique

Resource hierarchy is not specific to dining philosophers. It is a general deadlock-prevention technique for programs that may need multiple locks. Assign each lock a rank and require every thread to acquire locks in ascending rank order. This also helps code reviews because lock order can be checked statically in many designs.

The cost is reduced flexibility: a caller may need to restructure operations to obey the order. The simplicity of the proof is often worth that discipline.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.15 — What hierarchy does not guarantee

A global acquisition order prevents circular wait in this model, but it does not make the operating system schedule every waiting thread promptly. Python Lock does not promise FIFO service. A philosopher can be repeatedly delayed even though the system as a whole continues to complete meals.

The report must state deadlock freedom and starvation freedom separately. The hierarchy solution claims the former but does not claim a hard starvation bound.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.16 — Monitor as a single admission decision

The fair monitor treats the two forks as one coordinated resource request. A philosopher queues once and is admitted only when neither required fork conflicts with an active eater and no earlier conflicting request is being bypassed. This avoids holding one fork while independently waiting for the other.

The monitor serializes admission state under one condition lock. Eating itself occurs outside the monitor lock, while the philosopher remains recorded in the active set.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.17 — Conflict relation on a ring

Two philosophers conflict if they are the same philosopher or neighbours in the ring, because they share at least one fork. Non-neighbouring philosophers may eat simultaneously. The monitor's conflict function captures this ring geometry and is used both for active-eater checks and queue-order fairness.

Unit tests should cover adjacent pairs, the first and last philosopher across the wraparound edge, and a non-neighbouring pair. The modulo arithmetic is a common source of boundary defects.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.18 — Safety proof for the monitor

A philosopher enters only when no active philosopher conflicts with it. Since adjacent philosophers conflict, no two neighbours can be in the active eating set simultaneously. The monitor checks this condition at admission and records violations defensively. The condition lock makes the active-set test and insertion atomic.

A proof should state that the conflict check is performed while holding the same monitor lock that protects the active set. Otherwise two neighbours could both observe an empty slot and enter.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.19 — Maximum simultaneous eaters

For a ring of five philosophers, at most two can eat simultaneously because the largest independent set of the cycle has size two. More generally, a cycle with N vertices has maximum independent set floor(N/2). This bound follows from the requirement that no two selected vertices be adjacent.

The experiment reports the theoretical maximum alongside the observed maximum. A smaller observed value may result from scheduling and queue order; it does not disprove safety.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.20 — Conflict-aware FIFO fairness

The monitor prevents a request from being passed by an earlier queued request that shares a fork with it. It does not block every later request behind every earlier request. A non-neighbour may be admitted concurrently because the two requests are compatible. This rule balances local FIFO order with resource utilization.

Fairness is defined among conflicting requests. The exact definition matters: saying 'FIFO' without explaining compatibility could lead a reader to expect global single-file admission.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.21 — Conditional progress argument

Suppose each meal finishes in finite time and the host operating system eventually schedules runnable threads. A request has only a finite set of earlier conflicting requests in front of it. Those predecessors eventually finish, after which the request can become eligible unless an active neighbour is still eating. Repeating the argument supports conditional progress.

This is not a fixed time bound. It depends on finite critical sections and host scheduling fairness, and it should be stated with those assumptions.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.22 — Why queue fairness is not real-time fairness

The monitor controls admission order but cannot force a thread to run at a precise time. A thread may be woken and then remain unscheduled. A critical section may also take longer than expected. Therefore the monitor does not provide a hard deadline or maximum wait in milliseconds.

Real-time guarantees require bounds on execution, scheduling, and resource-release behavior that are outside this teaching model.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.23 — Starvation under unfair locks

A lock implementation may wake waiters in an unspecified order. A philosopher can repeatedly lose the race to reacquire a fork even if no circular wait exists. This is starvation rather than deadlock because other philosophers may continue eating.

Use a per-philosopher completion count and maximum wait streak to study fairness. Aggregate meal count can hide one philosopher that has made no progress.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.24 — Resource hierarchy versus monitor

The hierarchy solution acquires two independent locks in a fixed order. The monitor grants permission to use both forks as a coordinated request. Hierarchy breaks circular wait by an ordering proof; the monitor avoids partial acquisition and adds a conflict-aware queue rule.

These solutions address deadlock through different mechanisms. They should not be merged into one vague statement that 'the monitor orders forks'.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.25 — Alternative: asymmetric acquisition

Another prevention approach lets one philosopher acquire forks in the opposite order while all others follow the same direction. This breaks the perfect ring symmetry and can prevent the all-left-first cycle. It is a useful teaching variant but less general than a total resource order.

A test should verify the selected asymmetry for arbitrary N and should still check exclusive fork use. The proof should identify the direction change that breaks the cycle.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.26 — Alternative: room semaphore

A common approach allows at most N-1 philosophers to compete for forks simultaneously. By preventing all N philosophers from holding one fork at the same time, the classic circular-wait state cannot form in the same way. A semaphore controls entry to the competition room.

This approach adds a shared admission resource and still needs careful release handling. Explain why the N-1 bound breaks the cycle rather than treating the semaphore as a magic fix.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.27 — Alternative: atomic two-resource reservation

A monitor can check and reserve both required forks as one atomic admission step. This is the approach used in the fair monitor. It prevents a philosopher from holding only one fork while waiting for another, so the classic partial-allocation cycle cannot form.

Atomic reservation requires a single synchronization authority for the fork state. If two separate locks guard the two forks without coordination, the atomicity argument no longer applies.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.28 — Deadlock prevention, avoidance, and detection

Prevention removes at least one necessary deadlock condition by construction. Avoidance checks whether a proposed allocation leaves the system in a safe state, often requiring knowledge of maximum future resource claims. Detection allows a deadlock to occur and then searches for cycles or blocked sets.

The dining exercise mainly demonstrates prevention. The timeout witness is a simple detection instrument for the lab; it is not a full system-wide deadlock detector.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.29 — Banker's algorithm comparison

Banker's algorithm is an avoidance technique for multiple resource types and known maximum claims. Before granting a request, it tests whether some safe sequence remains. Dining philosophers usually use local fork requirements and can be addressed more simply with resource ordering or a monitor.

The comparison is useful to clarify when a general resource-allocation algorithm is warranted. Do not claim that Banker's algorithm is necessary for this small ring problem.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.30 — Cancellation and interruption

A philosopher may be interrupted or cancelled while waiting for the monitor. A robust implementation must remove its queued request exactly once and notify other waiters whose fairness predicate may now be true. If interruption occurs while eating, the active reservation must be released safely.

The current exercise runs finite meals without cancellation. This appendix identifies the extra state transitions required before the primitive can be used as a general-purpose monitor.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.31 — Exception-safe resource release

The resource-hierarchy solution uses nested context managers so that both forks are released when the meal finishes or raises an exception. The monitor removes the philosopher from the active set in a finally block. These cleanup paths are part of liveness: a missed release can block all neighbours.

Inject a failure during eating and verify that every thread can still complete its remaining work or that the run terminates with a clear failure report.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.32 — Thread termination and cleanup

A demonstration should join every worker and report any thread that remains alive. Daemon threads alone are not proof of successful cleanup because they can be terminated when the main program exits. The deadlock witness must release its first forks after recording the state.

The test harness should use bounded joins and fail visibly if a thread does not terminate. Silent abandonment can hide a real deadlock in the test itself.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.33 — Scalability with philosopher count

The ring geometry generalizes to any N greater than or equal to three. A larger N increases the number of forks and possible wait patterns, but the resource-ordering proof remains the same because every fork rank belongs to one global order. The monitor's conflict check remains constant-size for a philosopher with two neighbours.

Stress tests should use several N values and verify completion counts, adjacency safety, and the maximum concurrency bound floor(N/2).

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.34 — Odd and even ring sizes

The maximum number of pairwise non-adjacent philosophers differs with ring size but is floor(N/2) for a cycle. Odd rings have one unavoidable gap in a maximum independent set; even rings can alternate eating and thinking positions. The fairness queue may produce different observed concurrency for the two cases.

Test both odd and even N. This catches assumptions that accidentally work only for the original five-philosopher diagram.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.35 — Boundary philosopher identifiers

The first and last philosophers are neighbours because the table is circular. A naive absolute-difference check can miss this wraparound conflict. The modulo-based conflict predicate must treat indices 0 and N-1 as adjacent.

A focused unit test should assert conflicts(0,N-1,N) and should also assert a non-neighbour pair does not conflict.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.36 — Trace and evidence design

A useful trace records request arrival order, philosopher index, required fork identifiers, admission time, release time, and whether the request waited behind a conflict. These fields allow a reviewer to reconstruct why an admission was legal and whether a later request bypassed an earlier one.

The current JSON records completion counts, active-set maximum, entry order, and summary metrics. A richer trace can support deeper latency and fairness analysis without changing the core protocol.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.37 — Safety and liveness are distinct

Safety states that something bad never happens, such as adjacent philosophers eating together. Liveness states that something good eventually happens, such as every philosopher completing a meal. Deadlock freedom supports liveness but does not alone prove starvation freedom.

A test suite should include separate assertions for safety and completion. One should not infer all progress properties from a single boolean called success.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.38 — Conditional starvation-freedom claim

The fair monitor ensures that a later conflicting request cannot pass an earlier one. If each active meal ends and waiting threads are eventually scheduled, the finite set of earlier conflicting requests drains. This supports a starvation-freedom argument under stated assumptions, not an unconditional theorem about wall-clock time.

The assumptions should appear beside the claim, not hidden in a footnote. A reader must understand that the operating system remains part of the progress argument.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.39 — Why the timeout witness is not a solution

A timeout can detect that a requested fork was not acquired within a chosen interval. It does not change the resource order or prevent the cycle from forming. Increasing the timeout changes how long the demonstration waits, not the deadlock condition.

The report should label timeout as test instrumentation. The actual prevention argument comes from hierarchy or atomic monitor admission.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.40 — Partial acquisition failure

If a philosopher acquires its first fork but fails to acquire the second, it must release the first fork during cleanup. The deadlock witness deliberately does this after all requests have been observed. In an uncontrolled implementation, releasing too early could alter the state and produce a misleading test result.

Use try/finally around the first acquisition and coordinate cleanup after recording the intended state. This prevents test harness logic from accidentally curing the deadlock before it is measured.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.41 — Proof obligations for hierarchy code

The mathematical ordering proof assumes every code path acquires forks in increasing rank. A single helper or exception path that acquires in reverse order can reintroduce a cycle even if the main philosopher loop is correct. The proof is only as strong as the implementation's adherence to the ordering discipline.

Centralize ordered acquisition in one helper and test it. Avoid duplicating lock-order logic across several call sites.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.42 — Proof obligations for the monitor

The monitor proof assumes the active set and request queue are protected by one condition lock. Admission must test active conflicts and earlier conflicting requests before inserting the philosopher into the active set. Release must remove the exact philosopher and notify waiters.

Review the monitor as a state machine. Check that no path inserts a philosopher twice, releases an inactive philosopher, or leaves a cancelled request in the queue.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.43 — Test matrix for the three scenarios

The deadlock witness checks that every philosopher holds one fork and times out on the other. Resource hierarchy checks that every configured meal completes. The fair monitor checks adjacency safety, completion, queue ordering, and simultaneous-eater bounds. Each scenario therefore validates a different property.

Keep expected properties separate in the result JSON. A deadlock witness is supposed to reproduce a bad state; it should not be reported as a failed prevention algorithm.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.44 — Stress testing and random delays

Small randomized delays before and after acquisition can explore more interleavings. Such stress tests are useful for finding implementation mistakes but are not a replacement for the resource-order proof or queue fairness test. A passing random run does not cover all schedules.

Fix and record the random seed for reproducibility, then run several seeds. Preserve a deterministic regression test for the key ordering property.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.45 — Performance interpretation

The monitor records mean waiting time and maximum simultaneous eaters. These are descriptive statistics of one runtime environment. They depend on Python thread scheduling and the duration of each meal. They do not prove that the monitor is faster than every hierarchy or semaphore-based solution.

Compare alternatives under the same philosopher count and meal duration. Include safety and fairness measures along with throughput or wait time.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.46 — Extension: configurable fork topology

The ring topology can be generalized to a graph in which philosophers are vertices and shared forks represent conflicts between adjacent vertices. A monitor can use a general conflict graph rather than the cycle-specific modulo rule. Resource hierarchy can assign a global order to all edges or resource nodes.

A graph-based extension should define conflicts explicitly and test whether the maximum simultaneous independent set matches the topology. Avoid reusing ring arithmetic in a non-ring graph.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.47 — Extension: weighted admission

A future design could assign ticket weights to philosophers competing for a monitor admission. This would combine proportional selection with fork-conflict constraints, but the selection must consider only requests compatible with current owners and earlier fairness constraints. A weighted draw cannot ignore safety.

Specify whether weights apply globally or only among currently compatible requests. The policy must not let a high-weight neighbour bypass an earlier conflicting request if local FIFO fairness is part of the contract.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.

[[PAGEBREAK]]
## Appendix D.48 — Final review checklist

A complete submission identifies the ring model, states the four deadlock conditions, provides a deterministic circular-wait witness, proves the hierarchy order, specifies monitor conflict semantics, and distinguishes deadlock freedom from starvation freedom. It reports completion counts and safety checks for all scenarios.

A reviewer should be able to run the program, inspect the JSON, and trace every conclusion to a proof, assertion, or measured result.

**Verification evidence:** Record philosopher identifiers, fork ownership, queue order, meal completion counts, and any detected violation. The report should distinguish a deliberately constructed deadlock witness from a successful prevention run.