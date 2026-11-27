# Extended readers-writers appendix — Exercise 7

[[PAGEBREAK]]
## Appendix C.01 — Shared-object contract

The shared object is readable by multiple threads at the same time, but a write requires exclusive access. A read operation must observe a coherent version and must not overlap a write that changes the same state. A write operation may update several fields, so exclusive admission is required for the whole logical transaction, not only for one machine instruction.

The benchmark uses a version counter as a compact shared object. It is small enough to verify and still exposes the difference between read concurrency and exclusive write access.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.02 — Safety invariants

The first invariant is that no writer overlaps another writer. The second is that no writer overlaps any reader. The third is that multiple readers may overlap when no writer is active. These are safety properties: a single violating execution is enough to disprove correctness, regardless of average performance.

Tests should instrument active reader and writer counts while the lock is held. Checking final values alone can miss a brief illegal overlap.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.03 — Compatibility matrix

Two reader requests are compatible with one another. A reader and writer are incompatible, as are two writer requests. The policy decides admission order only among requests that are waiting; it must never relax this compatibility relation. Separating compatibility from priority helps prevent an optimization from accidentally breaking safety.

An implementation review can write the matrix explicitly and verify that each admission predicate checks the active set against it.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.04 — Reader-preference semantics

Reader preference admits a new reader whenever no writer is currently active. A waiting writer does not block later readers. This can maximize read concurrency in a read-heavy system, but a continuing arrival stream can keep a writer waiting while readers repeatedly enter.

The report should specify that preference is an admission rule, not a statement that readers are more important in every application. The right policy depends on workload and service objectives.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.05 — Writer starvation scenario

Imagine one writer queued while a new reader arrives just before the last active reader releases. Under reader preference, the new reader may enter immediately and keep the reader count nonzero. Repeating that arrival pattern can postpone the writer for an arbitrarily long time.

A deterministic test can arrange the arrival order with events and barriers. It should demonstrate the bypass rule without relying on one lucky timing run.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.06 — Writer-preference semantics

Writer preference prevents a new reader from entering while at least one writer is waiting. Existing readers finish, then a writer can be admitted. This stops an unending stream of new readers from overtaking a writer that is already queued.

The implementation must increment the waiting-writer count before the writer sleeps and decrement it only when the writer has been admitted or cancelled. Otherwise a reader can observe an incorrect policy state.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.07 — Reader starvation scenario

Under writer preference, a continuing stream of writers can repeatedly take the resource before waiting readers. The readers are safe, but their progress may be postponed indefinitely under an unconstrained arrival pattern. This is the symmetric cost of protecting writers.

A good experiment should vary writer arrival rate and report reader tail waits. A low average writer wait does not reveal whether readers are accumulating in a long queue.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.08 — Fair arrival queue

Fair mode records requests in arrival order and admits a request only if it is compatible with current holders and no earlier conflicting request is being bypassed. Consecutive readers at the head can enter together because they are mutually compatible. A later reader cannot pass a writer that arrived first.

This policy is conflict-aware FIFO rather than a single-file queue. It preserves reader concurrency while applying order only where the access modes conflict.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.09 — FIFO versus phase fairness

Strict FIFO can serialize readers unnecessarily if one writer separates two compatible groups. Phase-fair algorithms instead alternate or batch reader and writer phases under specific rules. This exercise uses a simpler conflict-aware FIFO policy whose semantics are easier to verify.

Do not label the implementation phase-fair unless it actually implements phase transitions. Precise naming prevents the reader from assuming stronger guarantees than the code provides.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.10 — Reader batching

When several readers arrive consecutively before any writer, fair mode can admit the whole reader prefix. They share access safely and do not need to wait for one another. A writer at the head prevents later readers from joining the active phase, preserving the order of conflicting requests.

The test suite should confirm both sides of the behavior: multiple readers overlap when no writer is ahead, and a later reader does not bypass an earlier writer.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.11 — Queue conflict rule

The fair policy scans earlier queued requests and blocks a new request only when an earlier request conflicts with it. This is the key distinction from an unconditional global FIFO mutex. An earlier reader does not prevent a later reader from joining a compatible batch, but an earlier writer blocks a later reader.

The conflict predicate should be small, explicit, and unit-tested. A complex predicate hidden inside the wait loop is difficult to review and easy to invert.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.12 — Condition-variable discipline

Each acquire path waits in a predicate loop under one condition lock. The predicate includes active readers, active writer, waiting writers, and queue position as required by the policy. Notification is a prompt to re-evaluate state, not a transferable admission token.

Every variable used by the predicate must be updated under the same condition lock. Otherwise the condition check and the state transition can race.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.13 — Reader acquisition transition

A reader increments the active-reader count only after the admission predicate succeeds. In fair mode, it also removes its own request from the queue. This transition must happen atomically with respect to competing acquisitions so that a writer cannot enter between the predicate check and the increment.

The linearization point is the increment of the active-reader count while holding the condition lock. Use that point when reasoning about race conditions.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.14 — Writer acquisition transition

A writer records itself as waiting before sleeping. When admitted, it leaves the fair queue, decreases the waiting-writer count, and sets the active-writer flag. The predicate guarantees that the active-reader count is zero and no other writer is active.

The transition should be one protected state change. Splitting the waiting count and active flag across unlocked operations can temporarily expose a false policy state to new readers.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.15 — Release and wakeup

A reader release decreases the reader count; a writer release clears the active-writer flag. Both operations notify waiters because they may make a previously blocked predicate true. Waiters must still re-check the predicate after waking.

Tests should include extra notifications and verify that a wakeup does not allow an incompatible request to enter.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.16 — Context-manager safety

The context-manager wrappers release the read or write side in a finally clause. This prevents an exception in application code from leaving the lock held forever. The synchronization primitive cannot assume that the protected operation always returns normally.

Inject an exception inside both read and write contexts and verify that subsequent requests complete. Also verify that a mismatched release raises a clear error.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.17 — Reentrancy and upgrades

The teaching lock does not claim to support reentrant acquisition or read-to-write upgrades. A thread that holds a read lock and then waits for a write lock can deadlock itself if the policy waits for all readers to leave. Supporting upgrades requires a separate protocol and well-defined ownership tracking.

Documenting unsupported operations is part of a correct API. Users should not infer reentrancy or upgrade semantics from the existence of context managers.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.18 — Deadlock versus starvation

Deadlock means a set of requests cannot progress because each waits for a resource held by another request in the set. Starvation means a particular request is postponed while the system continues to process others. Reader and writer preference primarily create starvation risks, not necessarily deadlock.

The report should use separate terms and tests. A system can satisfy all safety invariants and still starve one class of request.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.19 — Mutual exclusion proof for writers

The writer flag can be set only when there are no active readers and no active writer. Because the condition lock serializes this check and update, two writers cannot both set the flag. Once set, reader predicates reject entry until the flag is cleared.

A proof should identify both the protected predicate and the atomic state transition. Simply asserting that the code uses a Condition is not a proof of mutual exclusion.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.20 — Reader overlap proof

Readers are admitted when the writer flag is false and policy-specific fairness conditions are satisfied. Multiple readers can increment the reader count under the condition lock before a writer becomes active. A writer cannot pass its predicate until the count returns to zero.

A concurrency test should create several readers and hold their read sections open long enough to observe overlap. A global mutex would pass exclusivity tests but fail this concurrency requirement.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.21 — Benchmark workload design

The benchmark starts a fixed number of reader and writer threads. Readers acquire the shared read lock and observe the version; writers acquire the write lock and increment it. Each operation holds the lock for a short configured interval so contention is measurable.

The same operation counts and critical-section duration should be used for all policies. Otherwise the results combine admission-policy effects with workload differences.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.22 — Reader-to-writer ratio

The ratio of reader to writer requests strongly influences results. A reader-heavy workload may make reader preference look attractive, while a writer-heavy workload may expose its writer starvation risk. A fair comparison should test multiple ratios rather than one convenient configuration.

Report the actual number of successful read and write entries. The configured thread count alone does not prove that every operation completed.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.23 — Critical-section duration

Longer critical sections increase queueing and make policy differences easier to observe, but they also amplify thread-scheduling noise. Very short sections may finish before meaningful contention develops. The chosen duration should be justified and held constant across policy comparisons.

Repeat the benchmark with at least two durations. If a conclusion changes, explain whether it is driven by contention intensity or by the admission rule.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.24 — Waiting-time definition

Wait time is measured from immediately before acquisition until the thread enters the protected section. It excludes time spent inside the critical section and work performed after release. Reader and writer samples are recorded separately because the policies deliberately treat the two classes differently.

Use a monotonic clock. Wall-clock adjustments can make elapsed intervals invalid.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.25 — Mean, p50, and p95

The mean describes average waiting, p50 describes the median sample, and p95 describes a high percentile of the observed distribution. They answer different questions. A low mean can coexist with a high p95 if most requests are served quickly while a few wait much longer.

State the percentile calculation method and sample count. With a small number of samples, p95 is unstable and should be interpreted cautiously.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.26 — Maximum wait and tail risk

The maximum observed wait highlights one extreme sample but is sensitive to thread scheduling and system load. It is not a worst-case guarantee. A long maximum may indicate a starvation tendency, a slow host thread, or an unusually long competing critical section.

Report the maximum alongside p95 and the number of requests. Do not translate one measured maximum into a claim that the policy has a bounded wait.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.27 — Throughput and concurrency

Throughput is the number of completed operations per unit time. Peak simultaneous readers shows whether a policy uses read concurrency. A policy that minimizes one class's wait may reduce overall throughput if it serializes compatible readers unnecessarily.

A balanced evaluation should report both latency and throughput. No single metric captures safety, fairness, and utilization together.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.28 — Fairness index

A Jain-style fairness index can summarize how evenly a set of clients receives service, but a single index can hide which class is disadvantaged. Reader and writer requests also have different operation costs, so raw entry counts may not be comparable as resource consumption.

If using a fairness index, define its inputs and compute it separately for classes or normalized service units. Explain what the scalar hides.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.29 — Policy-level starvation conditions

Reader preference can starve writers under continuous reader arrivals. Writer preference can starve readers under continuous writer arrivals. Fair queue mode prevents a later conflicting request from overtaking an earlier queued request, but progress still assumes finite critical sections and host scheduling.

The no-bypass property is a queue-order guarantee, not a hard real-time deadline. State this assumption wherever fairness is discussed.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.30 — Test: writer exclusivity

The safety test runs several readers and writers at once and tracks active counts. A writer entering while any reader or another writer is active records a violation. A correct run finishes with no violations and the expected number of writes.

Repeat the test with longer protected intervals to widen race windows. A test that happens to pass once under extremely short sections may be too weak.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.31 — Test: parallel readers

At least two readers should be able to hold the read side simultaneously when no writer is active. This confirms the implementation is a read-write lock rather than a plain mutex. The maximum active reader count is an observable metric.

A test should not assert a host-specific exact maximum. It should assert that overlap greater than one is possible under a controlled barrier.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.32 — Test: writer not bypassed

The fair-mode ordering test holds an initial reader, queues a writer, and then queues a later reader. When the first reader exits, the writer should enter before the later reader. This checks the conflict-aware queue rule directly.

Use events to confirm queue insertion before releasing the initial reader. Otherwise the test may accidentally run without the intended queue order.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.33 — Test: compatible reader batching

A complementary test queues two readers before a writer and verifies that the readers can share the active phase. The fairness rule must not become an unconditional one-request-at-a-time gate.

This test protects the performance property that motivates read-write locks: compatible readers should not serialize unnecessarily.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.34 — Arrival races

Two acquire calls can arrive almost simultaneously. The condition lock determines the order in which they update the queue or waiting counters. That ordering is the policy's recorded arrival order. No acquisition predicate should read partially updated queue state.

Concurrent stress tests should randomize small delays around arrival, acquisition, and release while checking the safety invariants.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.35 — Cancellation and timeout design

The current primitive does not expose a timeout or cancellation API. A production version must define how a timed-out waiter is removed from the queue or waiting counter and how notifications are issued to requests that may now proceed.

Cancellation must be serialized with admission. A request cannot be both cancelled and active, and queue removal must not leave a stale writer count.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.36 — Exception and worker failure

A thread can raise an exception inside a protected operation. Context managers ensure release, but the application must still decide whether to retry, report failure, or stop the workload. One failed writer should not leave the shared object permanently inaccessible.

A fault-injection test should fail one reader and one writer, then verify that remaining operations still complete and the final version matches the successful write count.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.37 — Condition notification policy

The implementation notifies waiters after state changes. Broad notification is simple but may wake many incompatible requests that immediately return to sleep. Targeted notification can reduce wakeups but requires a more sophisticated waiter structure.

Optimization should follow measurement. Keep the simple broadcast protocol until correctness is established, then compare wakeup counts and contention.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.38 — Memory visibility and consistency

The condition lock protects the synchronization state and the shared version update. In a real system, memory-ordering guarantees are part of the lock contract: a reader entering after a writer releases must observe the completed write according to the language and runtime memory model.

Do not generalize Python behavior to all languages. A low-level C or C++ implementation must use the appropriate atomic and mutex memory-ordering rules.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.39 — Read-write lock versus immutable snapshots

If the shared data can be represented as immutable snapshots, readers may access a stable version without holding a read lock for the full operation. Writers publish a new snapshot atomically. This can reduce contention but changes the memory and update model.

A report may mention snapshots as an alternative, but the benchmark should not compare them without including allocation and publication costs.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.40 — Read-copy-update comparison

Read-copy-update allows readers to access data with very low synchronization overhead while updates publish a new version and defer reclamation until old readers finish. It is useful for read-mostly workloads but requires a different lifecycle and memory-reclamation protocol.

The comparison helps explain why reader-writer locks are not the only answer to read-heavy access. State the additional complexity rather than presenting RCU as a drop-in replacement.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.41 — Phase-based alternatives

Phase-fair and queue-based read-write locks coordinate groups of readers and writers in phases. They can provide stronger fairness or predictable handoff than a simple preference flag. The current fair mode is deliberately a teaching policy with a transparent conflict rule.

When comparing to a production primitive, consult its documented semantics. Different libraries use 'fair' to mean different queue and phase guarantees.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.42 — Limitations of host-thread timing

The measured waits depend on Python implementation, operating-system scheduling, CPU load, and lock wakeup behavior. A thread can be ready but not scheduled, or a wakeup can be delayed by unrelated work. These factors add noise to policy-specific queueing delay.

Report environment information and repeated runs. Avoid interpreting tiny differences between means as a meaningful policy advantage.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.43 — Statistical repeatability

A timing benchmark should be repeated and should summarize distributions across samples or runs. One run is useful for demonstrating the code, but it is weak evidence for a general performance claim. A fixed operation count and seed-like workload configuration make the experiment easier to compare.

Keep raw wait samples if possible. Summary statistics alone make it difficult to inspect outliers or recompute a different percentile.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.44 — Comparing policies fairly

Use the same thread counts, operation counts, critical-section duration, and measurement method for each policy. Randomize or rotate execution order across repeated benchmark batches if host thermal or background load may bias one policy.

A fair benchmark controls the environment as much as practical and labels uncontrolled factors. It should not hide results that contradict the expected qualitative trade-off.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.45 — API guarantees and unsupported modes

The teaching lock does not promise reentrancy, recursive reads, writer-to-reader downgrade, or reader-to-writer upgrade. These operations require explicit owner tracking and policy rules. A caller that assumes unsupported behavior can deadlock itself even when the core lock is correct.

Document unsupported modes near the API. Correctness includes stating what the implementation does not promise.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.46 — When reader preference is appropriate

Reader preference can be reasonable when reads dominate, writers are infrequent, and occasional long writer waits are acceptable. It can provide high read concurrency with a simple admission predicate. The application must still assess whether writers have service deadlines.

A policy decision should use the workload's service objectives, not only its average read-to-write ratio.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.47 — When writer preference is appropriate

Writer preference can be reasonable when stale data is costly and writers must make progress promptly after arrival. Blocking new readers helps drain the current reader phase. The application must check that a steady stream of writers will not make reader latency unacceptable.

Report the expected update frequency and freshness requirement. Writer preference is a trade-off, not a universal correctness upgrade.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.48 — When fair mode is appropriate

A fair arrival queue is attractive when neither readers nor writers should be systematically bypassed. It preserves compatible reader batches while respecting earlier conflicting requests. Its extra queue bookkeeping can cost more than a simple preference flag.

Use fair mode when predictability between classes matters more than the absolute minimum overhead. Verify that the host scheduler and critical-section behavior satisfy the progress assumptions.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.

[[PAGEBREAK]]
## Appendix C.49 — Final policy selection checklist

Before selecting a policy, record read/write ratio, maximum acceptable writer delay, maximum acceptable reader delay, critical-section length, whether operations may block, and whether FIFO order is required. Then test the chosen implementation against both safety and progress scenarios.

A policy selection table makes trade-offs explicit and prevents a report from declaring a winner without reference to the application's requirements.

**Validation evidence:** Record the queue order, active reader/writer counts, completed operations, and wait-time samples. The report should connect each measured value to the policy rule it is intended to evaluate.