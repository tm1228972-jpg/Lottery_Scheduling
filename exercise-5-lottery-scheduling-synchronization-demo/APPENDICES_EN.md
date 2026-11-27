# Extended technical appendix — Exercise 5

[[PAGEBREAK]]
## A.01 — Formal resource contract

The abstract resource is a single admission right to one critical-section execution. A request joins the eligible set when it calls acquire and remains eligible until it is selected, cancelled by shutdown, or otherwise removed by an explicit policy. The current owner is not eligible for another draw. This distinction prevents the model from silently counting a worker twice: once as owner and again as a waiter. The resource contract is intentionally narrower than CPU scheduling because no arbitrary running process is preempted.

A correct implementation must preserve the contract during every transition, including error and shutdown paths. Review the queue, owner field, and closed flag as one protected state tuple rather than as independent variables.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.02 — CPU lottery versus lock lottery

In a CPU lottery, the winner receives a processor quantum and may later be preempted by a timer. In this exercise, the winner receives lock ownership and remains the owner until release. The selection rule is related, but the unit of service and the enforcement mechanism are different. A thread that wins the lock can still be descheduled by the host operating system while holding it, so a lottery decision does not imply immediate execution or a fixed completion time.

Reports must use the phrase weighted lock arbitration rather than claiming that Python replaces the kernel scheduler. This distinction keeps the experimental conclusion aligned with what the program actually controls.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.03 — Eligibility at the instant of the draw

The eligible set consists only of requests already waiting at the moment the resource becomes free. A worker that has not called acquire contributes no tickets. A worker that owns the resource is excluded. If a new request arrives after a draw, it participates in a later draw, not retroactively in the completed decision. Consequently, observed grants depend on both ticket weights and request arrival patterns.

For a reproducible trace, record the waiting-set composition at each decision. Recording only the winner and its weight is not enough to reconstruct the exact conditional probability when the queue changes.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.04 — Ticket probability derivation

Let request i carry t_i positive tickets and let T be the sum over all eligible requests. A uniform integer draw from 1 through T assigns exactly t_i integers to request i. Therefore the probability of selecting i is t_i/T. This result is exact for one decision conditional on the eligible set; it does not require an asymptotic approximation.

A review calculation should sum the ticket intervals, show that they are disjoint, and verify that their union contains exactly T integers. This gives a simple correctness argument for the weighted selection loop.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.05 — Worked ticket intervals

With ticket counts 5, 3, and 2, the first request owns interval 1–5, the second 6–8, and the third 9–10. Draw 1 or 5 selects the first request; draw 6 or 8 selects the second; draw 9 or 10 selects the third. Boundary values are especially useful in tests because an off-by-one error often appears at the first or last ticket of an interval.

Test every interval boundary as well as one interior value. A deterministic helper that accepts an injected winning ticket can verify the mapping independently from the pseudo-random generator.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.06 — Conditional probability after queue changes

Suppose the second request leaves the waiting set. The total ticket count becomes 7, and the remaining probabilities become 5/7 and 2/7. It would be incorrect to keep using the original denominator 10. The draw routine must compute the total from the current waiters each time, not from a cached initial total.

A queue mutation test should remove one request, trigger another draw, and verify the new denominator and ticket intervals. This test checks both the data structure and the probability calculation.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.07 — Proof of the weighted selection loop

The selection loop maintains a cumulative ticket count. After processing request j, the cumulative value equals the number of tickets in requests 1 through j. The first request for which the winning ticket is no greater than that cumulative count owns the selected integer. Because the draw is in 1..T, some request must satisfy this condition. Positive ticket counts ensure no empty interval is created.

The assertion that a winner exists is a defensive invariant check. If it ever fails, the eligible-set sum and the traversal disagree, which is a state-integrity defect rather than an ordinary losing draw.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.08 — Request identity and owner identity

A process name is not a safe ownership token when a worker can issue multiple requests over its lifetime. The implementation creates a distinct request object and validates that exact object during release. This prevents a stale request from releasing a later grant that happens to belong to the same process name. The request identifier is useful for logs and debugging even when object identity is used for enforcement.

A negative test should attempt to release an old request after a later request from the same worker has become owner. The expected result is an exception and no change to the current owner.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.09 — Linearization points

The acquisition linearization point is the assignment of the winning request to the owner field while the condition lock is held. Before that assignment, no request owns the resource; after it, exactly one request does. The release linearization point is the clearing of the owner field under the same condition lock. These atomic state transitions give concurrent callers a coherent order even if their host threads are interleaved.

When reviewing race conditions, identify the exact line that changes ownership. Do not reason only from when a thread wakes or when it begins executing its critical section.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.10 — State-machine model

The lock can be represented by states OPEN_FREE, OPEN_OWNED, and CLOSED. OPEN_FREE may transition to OPEN_OWNED when a waiting request wins. OPEN_OWNED returns to OPEN_FREE on release unless the grant limit has been reached, in which case it transitions to CLOSED. CLOSED is terminal: new acquisitions fail, waiting requests are released from their wait loops, and no new winner is selected.

Enumerating transitions is a practical way to find missing notifications. Every transition that can make a wait predicate true must notify the condition so that blocked callers can re-check it.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.11 — Condition-variable predicate loop

A condition variable does not transfer ownership by itself. It merely allows a waiting thread to sleep until some state change may have occurred. The acquire method therefore waits in a while loop that checks whether the request is the owner or the lock is closed. A single if statement would be unsafe because wakeups can occur when the predicate is still false.

The predicate must be checked while holding the same condition lock that protects owner and closed. Otherwise a notification can occur between the check and the wait, producing a lost wakeup.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.12 — Spurious and unrelated wakeups

A thread may wake because another request was granted, because shutdown began, or because the condition implementation wakes more broadly than the caller expects. The awakened thread must not infer that it has won. It must re-evaluate identity against the owner field. The program intentionally broadcasts to all waiters after a transition; most waiters wake only to observe that they still do not own the resource.

A robust test can issue extra notifications without changing the owner and verify that no second thread enters the protected section. This tests the predicate loop rather than the random draw.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.13 — Broadcast versus single notification

A single notification can be sufficient if the implementation is redesigned around a directed per-request event. In this exercise, a condition variable coordinates multiple requests and the chosen owner may not be the particular thread that the runtime wakes first. Broadcasting ensures the selected owner is among the threads that re-check the predicate. The condition lock still serializes the state transition, so waking several threads does not grant several owners.

The trade-off is additional wakeup traffic. A production design could use per-request events or an explicit handoff queue, but such optimization should be introduced only after correctness invariants are independently tested.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.14 — Avoiding nested-lock ambiguity

The demonstration uses the condition lock to protect the lottery mutex state and does not rely on a second application mutex to make the critical-section invariant appear true. This matters because a second lock could serialize counter updates even if the lottery lock were broken. The active-section counter is therefore observed while ownership is held, not protected by an unrelated lock.

If additional metrics require synchronization, keep metric collection outside the correctness path or use an atomic snapshot that cannot mask duplicate ownership. Tests should exercise the target primitive directly.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.15 — Critical-section invariant

The safety invariant is that the number of active critical-section owners is at most one. The implementation maintains one owner field and grants a request only when that field is empty. The demo increments an active counter on entry and decrements it before release. The maximum observed value must therefore be one. This measurement is an executable assertion of the design, not a proof for every possible machine execution.

A test should deliberately insert a small delay inside the critical section. Without the delay, incorrect overlap may be too brief to appear in a low-resolution observation.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.16 — Lost-update demonstration

The shared counter is updated in multiple steps: read the old value, pause, then write the incremented value. Without mutual exclusion, two workers can read the same old value and one increment can be lost. With correct lock ownership, each successful grant produces exactly one increment, so the final counter must equal the grant count.

The pause is a testing instrument, not a model of all application critical sections. Its purpose is to widen the interleaving window so the test can expose an accidentally unprotected update.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.17 — Exception-safe release

Critical sections can fail because of input errors, application exceptions, or early returns. The worker wraps the protected operation in try/finally and releases its exact request in the finally clause. Without this structure, an exception could leave the lock permanently owned and block every waiter.

A fault-injection test should raise an exception inside a critical section and verify that the next waiter can still be selected. In production code, the policy for propagating the exception should be separate from the resource-release guarantee.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.18 — Finite shutdown protocol

The demo uses a finite grant limit to make the run terminate deterministically. The final release closes the lock, clears pending waiters, and broadcasts a notification. Each waiter wakes, observes CLOSED, and returns without claiming ownership. This shutdown protocol is part of the model and should not be confused with ordinary lock release.

A termination test should verify that all worker threads have joined, not merely that the main function returned. It should also check that no waiter remains blocked after shutdown.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.19 — Ticket validation and input safety

Ticket counts must be positive integers. A zero-ticket request can never win but may still occupy queue space; a negative count can corrupt the cumulative interval arithmetic. Rejecting invalid weights at the API boundary prevents these states from reaching the draw algorithm.

Validation should be tested for zero, negative, non-integer, and extremely large values. A production API may also need a maximum ticket count to avoid overflow in fixed-width implementations.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.20 — Request arrival races

Two workers can arrive close together and contend for the condition lock. The condition lock defines the order in which they are appended to the waiting set. That order is observable in the trace but does not change their probability if ticket totals are unchanged. A draw cannot occur concurrently with a queue mutation because both operations execute under the same lock.

This is the principal serialization point for request registration. Reviewers should verify that queue insertion and the decision to select a winner are not separated by an unlocked interval.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.21 — Arrival order is not FIFO service

The waiting collection may retain arrival order for deterministic trace output, but the lottery does not grant the oldest request automatically. Queue position determines the order of ticket intervals, not priority. A request later in the list can win if the random ticket falls in its interval.

Do not describe the queue as a fair FIFO lock. The data structure is a set of eligible claims with an iteration order; service is selected by weighted probability.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.22 — Cancellation semantics

The minimal demo cancels pending requests only when the lock closes. A general-purpose lock may need cancellation for a timed-out caller or a worker that no longer needs the resource. Cancellation must remove exactly one waiting request and recompute the eligible ticket total on the next draw. It must not remove the current owner or leave stale references in the queue.

A cancellation extension should specify whether cancellation is permitted before selection only, how it interacts with shutdown, and how the caller learns whether it was selected at the same time it attempted to cancel.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.23 — Fairness and starvation

A weighted lottery gives a positive probability of winning whenever a request has positive tickets and is eligible. Positive probability does not mean deterministic progress within a fixed number of draws. Repeated losses are possible, and a low-ticket request may experience a long wait. The mechanism offers proportional expected service, not FIFO fairness or a strict starvation-freedom theorem.

Use separate metrics for average share, longest losing streak, and request wait time. A good average share can coexist with a long tail for an individual request.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.24 — Why no hard waiting-time bound follows

A probability distribution can make long losing streaks unlikely without making them impossible. Furthermore, the host operating system can delay a thread after it is granted the lock. Therefore the program cannot derive a wall-clock upper bound from ticket count alone. A hard real-time guarantee would require bounded scheduling, execution-time, and resource-handoff assumptions beyond this exercise.

Any claim of bounded waiting should state the probability threshold, eligible-set assumptions, maximum critical-section time, and host scheduling assumptions. Without those, the claim is stronger than the evidence.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.25 — Random seed and reproducibility

A fixed seed makes the pseudo-random sequence repeatable for a fixed order of requests and a fixed implementation. It does not make arbitrary threaded interleavings deterministic. The reference simulator is deterministic because it defines the eligible set on each decision without concurrent arrival races; the real threaded run may vary when workers reach acquire.

Record seed, Python version, ticket map, decision count, and generated trace together. The seed alone is not a complete experiment description.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.26 — Trace schema and auditability

Each trace row records a decision index, winning process, winner ticket count, total waiting tickets, and winning ticket number. These fields allow a reader to verify that the selected ticket fell inside the winner's interval. For deeper audit, add the full eligible request list and its weights before every draw.

Machine-readable traces are preferable to screenshots for verification. A reviewer can recompute counts and conditional probabilities without rerunning the threaded schedule.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.27 — Observed share versus expected share

Expected share is the ticket ratio under a fixed eligible set. Observed share is the number of grants received by a worker divided by all grants in the measured run. The difference is sampling error. For short runs, the observed ratio may differ noticeably even when the implementation is correct.

Report both absolute and signed error. Signed error shows whether a process received more or less than its target; absolute error summarizes magnitude without direction.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.28 — Confidence intervals for grant share

If eligibility remains fixed and decisions are independent, the number of wins for one request over n draws follows a binomial model with probability p. The observed share is an estimator of p, and its standard error is approximately the square root of p(1-p)/n. A confidence interval communicates uncertainty more honestly than a single percentage.

The approximation is not directly valid when the eligible set changes after every release. In that case, analyze conditional probabilities per decision or design a separate fixed-population reference experiment.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.29 — Effect of the number of decisions

Increasing the number of decisions generally reduces the relative variability of a sample proportion under independent fixed-probability draws. It does not imply that every prefix of the trace becomes accurate or monotonic. A run can move closer to the target and later move farther away after another sequence of wins.

Plot the cumulative share after every decision. A final summary alone can hide transient deviations that matter to interactive systems.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.30 — Effect of the ticket ratio

Multiplying every ticket count by the same positive integer leaves all probabilities unchanged. Changing only one client's ticket count changes both its probability and the denominator for every other client. This provides a useful metamorphic property for testing the selection algorithm.

A scale-invariance test can compare ticket vectors [5,3,2] and [50,30,20] with an injected normalized draw sequence. The mapping should be identical after scaling the draw consistently.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.31 — Dynamic weight changes

Changing ticket weights while requests are waiting is a policy decision, not merely a data update. The implementation must decide whether a queued request keeps the weight from arrival or uses the latest configured weight at draw time. Either policy can be coherent, but the trace and documentation must identify which one is used.

The present request object captures its ticket count on arrival. A dynamic-weight extension should either update that field under the condition lock or issue a new request version so the trace remains auditable.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.32 — Ticket transfer across dependencies

Ticket transfer can be useful when a client is blocked on a server or lock holder whose action is required to satisfy the client. The client can temporarily delegate its resource rights so the dependency receives a greater chance of progress. The exercise's lock demo does not implement transfer, but its request-weight abstraction provides a starting point.

A transfer design needs rules for the transfer lifetime, partial transfers, nested dependencies, and restoration on completion. It must also prevent a cycle of transfers from creating an unintended ticket inflation.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.33 — Ticket currencies and hierarchy

A ticket currency lets a group divide its global entitlement among internal clients. The group may maintain a local budget and allocate local tickets without exposing every internal decision globally. Hierarchy is valuable when resource ownership follows users, containers, or application classes.

A hierarchical test should verify that the sum of local shares does not exceed the group's global allocation and that changing one local share does not silently change another group's entitlement.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.34 — Compensation after partial use

A client may receive a resource quantum but release it early because it has no more work or becomes blocked. Compensation mechanisms adjust future rights so that unused allocation is not treated as fully consumed. For a lock, the analogy is limited because lock duration depends on application behavior and the next allocation is a discrete grant.

Any compensation policy should identify what is measured, whether compensation is based on wall time or work completed, and how it avoids rewarding a client that deliberately manipulates its hold duration.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.35 — Priority inversion and dependency handling

A high-importance client can wait behind a low-ticket lock owner. Lottery selection among waiters does not automatically solve the time spent by the current owner. Priority inheritance or ticket donation addresses dependency execution, while the draw rule addresses which waiter receives the next grant after release.

A controlled experiment can hold the lock in a low-weight worker while a high-weight worker waits. Measure owner hold time separately from lottery selection delay; the two components require different remedies.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.36 — Comparison with semaphore handoff

A conventional semaphore may release one permit and let the runtime choose a waiter according to its implementation. A FIFO semaphore can promise arrival-order handoff; a lottery lock instead chooses by ticket weight. Both can enforce mutual exclusion, but their fairness contracts differ.

The comparison should hold the protected operation and arrival pattern constant. Measure throughput, tail wait, and grant proportions rather than treating mutual exclusion alone as the only outcome.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.37 — Comparison with ticket spinlocks

A hardware ticket spinlock typically gives each arriving thread a monotonically increasing ticket and serves ticket numbers in order. Despite the shared word ticket, this is not lottery scheduling: it is FIFO ordering. The name similarity can confuse readers, so the report should distinguish lottery tickets from lock queue tickets.

The key contrast is selection semantics. Lottery uses a random draw among weighted claims; a ticket spinlock advances a serving counter in arrival order.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.38 — Complexity of one grant

If n requests are waiting, the simple implementation sums n weights and scans up to n entries to find the winner. Its selection cost is O(n), and its queue storage is O(n). This is appropriate for a teaching model with three workers, but it would be costly for very large waiter populations.

A cumulative tree or indexed structure can reduce selection cost, but queue insertion, cancellation, and weight changes then become more complex. Optimize only after profiling a realistic workload.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.39 — Portability beyond CPython

The demonstration uses threading.Condition and Python scheduling. Lock handoff order, thread wakeup timing, and interpreter implementation can vary across environments. The safety invariant is protected by the condition lock, but observed shares and timing values are host-dependent.

A portability report should record operating system, interpreter version, CPU count, and workload. Results from one host should not be described as universal synchronization performance.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.40 — Security and untrusted ticket assignment

If an application lets clients choose their own weights, a client may request an excessive number of tickets to dominate the resource. The lottery algorithm faithfully enforces the configured weights; it does not decide whether those weights are fair or authorized.

A production system needs an entitlement policy, bounds on ticket values, auditing of updates, and possibly per-user quotas. Resource fairness begins with a trustworthy assignment of rights.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.41 — Fault injection matrix

Useful fault cases include an invalid ticket count, a release by a non-owner, an exception during the protected operation, a shutdown while several requests wait, and an extra condition notification. Each fault should have a defined expected state after recovery.

The test matrix should assert more than exception types. Check that the owner, waiter count, counter, and worker termination state remain consistent after every injected failure.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.42 — Performance measurement discipline

Measure acquisition delay separately from critical-section duration and thread scheduling delay. Use a monotonic clock, warm up the runtime, repeat the run, and report distributions rather than only one mean. The current program records aggregate share metrics; additional timing instrumentation can be added without changing the lock contract.

Do not compare a lottery run to a FIFO lock unless both receive the same arrival trace and critical-section work. Otherwise the result mixes policy effects with workload differences.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.43 — Interpretation checklist

A complete interpretation states the eligible set, ticket vector, number of decisions, seed, observed proportions, share error, critical-section safety result, and shutdown result. It also states what was not measured, especially deadline latency and kernel scheduling overhead.

A reviewer should be able to reproduce the JSON trace and independently verify every winner. If the experiment omits these details, its numerical conclusions are difficult to audit.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.44 — Extension: cancellation-safe requests

A future extension can associate each request with a completion event and a cancellation flag. Cancellation must be serialized with selection so that exactly one of two outcomes wins: the request is removed before selection, or selection succeeds and cancellation reports that ownership was granted. Ambiguous intermediate states can leak tickets or ownership.

Model cancellation and selection as competing state transitions under the same condition lock. Test cancellation immediately before and after the winning draw.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.45 — Extension: bounded queue admission

An application may cap the number of waiting requests to protect memory and latency. Rejection at capacity should be explicit and should not silently drop a request that the caller believes was queued. Ticket totals must include only requests that were actually admitted.

A queue-capacity test should fill the queue, submit one extra request, and verify the configured rejection behavior. It should also confirm that a rejected request cannot later receive ownership.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.

[[PAGEBREAK]]
## A.46 — Research interpretation and final review

The original proportional-share idea motivates this experiment, but a lock is not a CPU quantum. The correct research question is whether weighted random admission provides proportional grant counts while a separate ownership protocol preserves mutual exclusion. These are two different claims and require two different sets of evidence.

The final report should present the safety invariant as a protocol property and the share ratio as a statistical observation. Keeping them separate prevents a correct average from being mistaken for proof of safe synchronization.

**Verification focus:** Reproduce the stated state transition with a fixed input, record the request set before and after the decision, and check that the owner identity, grant count, and termination state are mutually consistent.