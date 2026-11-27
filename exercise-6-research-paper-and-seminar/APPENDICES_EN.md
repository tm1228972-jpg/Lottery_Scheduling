# Extended research and seminar appendix — Exercise 6

[[PAGEBREAK]]
## Appendix B.01 — Research question and scope

The paper asks how a system can distribute a scarce resource according to explicit relative entitlements rather than relying only on a fixed priority order. The exercise studies that question at the level of allocation decisions. Its implementation is a simplified single-resource model with equal quanta and continuously runnable clients, so its conclusions concern grant proportions rather than kernel-level latency or general workload throughput.

A strong research report separates the original paper's broader design claims from the narrower result reproduced by this repository. Each claim should identify whether it is derived from the paper, proved from the model, or observed in the experiment.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.02 — Paper identification and provenance

The anchor publication is Carl A. Waldspurger and William E. Weihl's OSDI 1994 paper, Lottery Scheduling: Flexible Proportional-Share Resource Management. A research review should record title, authors, venue, year, and the version actually consulted. This bibliographic discipline matters because later technical reports expand the treatment and may use different examples or terminology.

When a secondary survey is used, distinguish it from the primary paper. Keep page numbers or section identifiers in the seminar notes so another student can check the interpretation without relying on an untraceable paraphrase.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.03 — Problem with fixed priorities

A fixed-priority scheduler selects among runnable entities according to an ordering. That ordering does not automatically state how much processor service each client should receive over a long interval. Two applications may need a relative resource share rather than a strict precedence relation. Lottery scheduling changes the representation of entitlement from an ordering to a count of tickets.

The contrast is not that priorities are always wrong. Fixed priorities are useful for precedence and real-time analysis; tickets are useful when proportional sharing is the objective. The report should identify the objective before declaring one policy superior.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.04 — Ticket as an entitlement abstraction

A ticket is a claim on a resource allocation decision. If client i has t_i tickets and the eligible population owns T tickets in total, its probability of winning one draw is t_i/T. This representation is compact and easy to redistribute. A client's share can be changed by modifying its ticket entitlement rather than recalibrating a global priority scale.

A ticket count is meaningful only relative to the current eligible set. The same ticket vector can produce different service proportions when some clients block or are excluded from the draw.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.05 — Probability of a single draw

The probability rule follows by counting equally likely ticket numbers. Exactly t_i outcomes select client i out of T possible outcomes, so P(i wins)=t_i/T. This conditional probability is exact for a fixed eligible set. It is not the same as saying the client will receive exactly that fraction in every short window.

A useful seminar demonstration writes out the intervals for 5:3:2 and asks the audience to classify boundary ticket numbers. This turns the probability expression into an operational selection rule rather than an abstract formula.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.06 — Expected share over repeated draws

If eligibility and ticket counts stay fixed and draws are independent, the expected number of wins for i over n decisions is n(t_i/T). Dividing by n gives an expected share of t_i/T. The observed result is random around this expectation. The expectation describes the centre of the distribution, not a deterministic schedule trace.

This distinction is central to honest reporting. A result that differs from the target in one finite run does not by itself prove a defect, just as a run that matches the target does not prove correctness.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.07 — Finite-sample variance

For a fixed probability p, the number of wins in n independent draws has binomial variance np(1-p). The variance of the observed proportion is p(1-p)/n. As n grows, the proportion becomes more concentrated around p under the model assumptions. Short traces naturally display more visible fluctuation.

The experiment should state n alongside every reported share. Percentages without sample counts conceal whether the result comes from ten decisions or ten thousand.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.08 — Ticket transfer

Ticket transfer allows a client to lend some or all of its resource entitlement to another entity that is temporarily responsible for completing its request. This can help a server or lock holder whose progress is a prerequisite for the client. The mechanism expresses a dependency through resource rights rather than through a fixed priority boost.

A transfer design must define when the rights return, whether transfers can be nested, and how cycles are prevented. A paper review should discuss the intended dependency case instead of presenting transfer as an unrestricted increase in global entitlement.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.09 — Ticket currencies

Ticket currencies support hierarchical allocation. A group receives a global share and distributes an internal budget among its own clients. Local ticket decisions can be made in a group's currency while the global allocator sees the group's external entitlement. This separation helps compose resource sharing across users, applications, or modules.

A hierarchy needs conservation rules. Local distribution should not create more global entitlement than the parent group owns, and unused rights should have a documented treatment.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.10 — Compensation tickets

Compensation mechanisms address early blocking or partial quantum use. A client that relinquishes a quantum before consuming all of it should not automatically be treated as though it used the whole allocation. Compensation adjusts future selection rights to reflect the amount of service actually consumed.

The seminar should explain both the motivation and the risk: a poorly designed compensation rule can be manipulated by clients that deliberately yield or block to obtain extra future service.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.11 — Resource generality

The paper's conceptual contribution is broader than one CPU scheduling loop. A ticket can represent a share of any resource whose use can be divided into meaningful allocation units and whose eligible claimants can be identified. Examples include CPU service, locks, and other contended resources, subject to resource-specific rules.

Generality does not mean every resource behaves identically. A CPU quantum can be preempted; a mutex critical section usually cannot be safely interrupted at an arbitrary instruction. Each application needs a correct ownership protocol.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.12 — Lottery versus stride

Stride scheduling is a deterministic proportional-share method often studied alongside lottery scheduling. It assigns each client a stride inversely related to its ticket count and advances a virtual pass value when the client receives service. Selecting the smallest pass approximates the target shares without random draws.

The comparison is useful because it separates proportional entitlement from randomization. Both methods can target a share ratio, but their short-term allocation sequences and implementation trade-offs differ.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.13 — Virtual pass interpretation

A pass value represents virtual service accumulated by a client. A client with more tickets has a smaller stride and therefore advances its pass by a smaller amount after receiving a quantum. Over repeated decisions, this helps keep its service proportionate to its entitlement.

The virtual-time explanation should be accompanied by a worked trace. A reader should be able to calculate each stride, identify the minimum pass, and update the selected client's pass without relying on source code.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.14 — Stride arithmetic and rounding

A real implementation must choose a stride constant and a representation for pass values. Integer arithmetic avoids floating-point drift but introduces rounding and possible wraparound concerns. A large stride constant can preserve resolution for common ticket counts, while a bounded pass representation requires periodic renormalization.

The experiment uses a simple floating-point model for clarity. Its output should not be presented as a bit-for-bit reproduction of every production stride scheduler.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.15 — Tie-breaking in deterministic scheduling

Two clients can have equal pass values. A deterministic tie-break rule is necessary to make the trace reproducible. The chosen tie-break may slightly influence finite-window counts, especially for small numbers of decisions, even when long-run proportions remain close to their targets.

Document the tie-break explicitly and include at least one tie in a worked trace. Omitting this detail makes the experiment under-specified and can prevent independent reproduction.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.16 — Equal-quantum assumption

The comparison assumes each allocation decision grants one equal-sized quantum. Under this model, counting wins is equivalent to counting resource quanta. If the resource units differ in duration or cost, grant count alone is no longer a reliable measure of consumed service.

A more realistic CPU evaluation might record execution time, not just dispatch count. The report deliberately does not make that extension, so the limitation must remain visible in the conclusion.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.17 — Continuously runnable workload

The experiment assumes all clients remain runnable for every decision. This keeps the eligible set constant and makes the probability rule easy to interpret. Real processes block, yield, terminate, or become ready at different times, changing the denominator and the composition of the lottery.

This assumption is a controlled experimental choice, not a statement about real workloads. A follow-up experiment should vary arrival and blocking behavior and report conditional eligible sets.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.18 — Why changing eligibility matters

When a client blocks, its tickets are removed from the eligible pool. The other clients' conditional probabilities increase because the total eligible ticket count falls. When it becomes runnable again, it returns to the pool. This is why the same configured tickets do not always translate into identical shares under every workload.

A dynamic workload trace should record ready and blocked transitions alongside each allocation. Otherwise the observed share can be misread as a failure of proportional allocation.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.19 — Workload vector and rationale

The 5:3:2 ticket vector creates visibly different target shares while remaining small enough for manual verification. It produces target proportions of 50%, 30%, and 20%, and its intervals are easy to draw on a whiteboard. This is a pedagogical workload, not a claim that these weights fit a specific production application.

A second workload with more clients or less balanced weights can test whether the implementation handles a larger interval and whether interpretation remains clear when the share is small.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.20 — Number of seeds and repeated runs

Repeated seeds measure the variability of lottery outcomes across pseudo-random streams. One seed is useful for a reproducible demonstration but insufficient for a summary of typical variability. The experiment records multiple runs and computes the distribution of the maximum absolute share error.

The seed set should be fixed and disclosed. Selecting only the seed with the smallest error would introduce selection bias and overstate the quality of the method.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.21 — Choice of error metric

Absolute share error for client i is |observed_i-target_i|. The maximum across clients describes the worst deviation in a run. This metric is symmetric: it does not distinguish over-service from under-service. Signed error should therefore also be inspected when explaining the direction of deviations.

Other metrics answer different questions. Sum of absolute errors emphasizes total mismatch; squared error penalizes large deviations; per-client tail metrics show whether one small client repeatedly loses.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.22 — Mean and worst run-level error

The mean maximum error summarizes typical performance across seeds, while the worst maximum error describes the largest deviation observed in the tested set. Neither value is a mathematical worst-case bound. The worst sample is simply the worst among the selected seeds and decision counts.

Label the statistic precisely. Avoid describing the worst sampled seed as a guaranteed worst case for the algorithm.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.23 — Confidence intervals and interpretation

A confidence interval expresses uncertainty in an estimated share under a stated statistical model. For independent fixed-probability draws, a binomial interval is appropriate. For dynamically changing eligible sets, simple binomial assumptions may not hold; conditional probabilities or a more explicit stochastic model are required.

A report that adds confidence intervals should state the model and interval method. Statistical decoration without matching assumptions can make a result less, not more, trustworthy.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.24 — Convergence is not monotonic

As the number of decisions increases, the cumulative share often becomes more stable under fixed eligibility, but it need not move monotonically toward the target. A sequence can approach the target and then move away after several wins by one client. The long-run convergence statement is not a promise about every prefix.

Plot a cumulative share curve and identify both an improving and a worsening segment. This prevents a misleading narrative based only on the final point.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.25 — Reproducibility record

A complete experiment record includes source revision, Python version, ticket vector, number of decisions, seed list, tie-break rule, and the generated JSON file. Recording these inputs makes it possible to distinguish a code change from normal sample variability.

A reproducibility checklist should be stored beside the raw output rather than reconstructed from memory after results have been discussed.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.26 — Internal validity

Internal validity asks whether the observed difference can be attributed to the scheduling policy rather than to an uncontrolled change in workload. Using identical ticket weights, quantum counts, and tie-break definitions helps isolate the policy. Running each policy under a consistent environment further reduces avoidable variation.

State the controlled variables and the factors that were not controlled. A small educational experiment should be honest about its limitations rather than imitate the certainty of a large benchmark.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.27 — External validity

External validity asks whether the result generalizes to workloads, operating systems, processor counts, and resource types not included in the experiment. This repository's model has one resource, equal quanta, and always-runnable clients, so external validity is intentionally narrow.

Conclusions should use scoped language such as 'in this simplified model'. Avoid extrapolating grant-count results to multicore scheduling or production latency.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.28 — Construct validity

Construct validity asks whether the chosen metric really measures the concept named in the research question. Grant-share error measures proportionality of allocation counts, but it does not measure responsiveness, user-perceived fairness, energy, or deadline satisfaction.

The report should map every metric to one claim. If a claim is about latency, share error alone is not a valid measure.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.29 — Lottery and hard real-time scheduling

Lottery scheduling is probabilistic proportional sharing. EDF and RM are real-time scheduling policies whose analyses concern deadlines and schedulability under specific task models. These goals are different. A lottery can provide a useful expected share without proving that any particular job completes before its deadline.

The seminar should not state that lottery replaces EDF or RM. It should explain which objective each policy addresses and why deadline guarantees require additional worst-case analysis.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.30 — EDF and RM comparison boundaries

EDF prioritizes the job with the earliest absolute deadline. RM assigns fixed priorities according to task periods under its classic assumptions. A proportional-share lottery chooses probabilistically among eligible clients. A meaningful comparison must either evaluate all policies against a shared objective or clearly separate their intended purposes.

A simple share experiment cannot establish that EDF or RM is inferior. It only demonstrates that lottery and stride target proportional resource allocation under the selected model.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.31 — Seminar narrative design

A clear seminar begins with the resource-allocation problem, introduces tickets, demonstrates a small draw, explains extensions, and then presents the experiment and limitations. This sequence moves from motivation to mechanism to evidence. It avoids placing implementation details before the audience understands the allocation contract.

Every slide should answer one question. Use the speaker notes to expand technical detail, not to compensate for slides that have no coherent message.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.32 — Explaining the 5:3:2 example

The 5:3:2 example makes probability visible. Draw a line of ten positions and allocate five to the first client, three to the second, and two to the third. Ask the audience to predict the winner for a boundary value such as 8 or 9. Then connect the example to the formula t_i/T.

The worked example should also show a losing streak. This is a natural way to explain why a positive probability is not a deterministic waiting-time bound.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.33 — Visual design of the result slide

A good result slide shows target shares, observed shares, and the error metric in the same visual frame. It should identify the number of decisions and the number of seeds. A chart without workload metadata is difficult to interpret because the same percentages can have very different uncertainty at different sample sizes.

Keep the raw values in the JSON and the chart focused on comparison. Do not place more significant digits on the slide than the experiment supports.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.34 — Speaker notes and oral delivery

Speaker notes should contain transitions, definitions, and explanations of assumptions. They should not simply repeat the visible bullets. A presenter needs to explain why a short-run deviation is expected and why a share ratio is not a deadline guarantee.

Practice the paper summary in a short form and a long form. The short form should preserve the research problem, mechanism, contribution, and limitation even if time is reduced.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.35 — Critical reading checklist

A critical paper review identifies the problem, assumptions, mechanism, evidence, limitations, and contribution. It distinguishes the authors' claims from the student's reproduction. It checks that cited extensions are actually supported by the source and that terminology is used consistently.

For each major claim, note the source section or experiment that supports it. If the claim is an interpretation, label it as such rather than attributing it directly to the authors.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.36 — Threats to experimental validity

Threats include pseudo-random number quality, seed selection, client eligibility assumptions, deterministic tie-breaking, runtime scheduling noise, and the use of grant count as a proxy for service. These do not make the experiment useless; they define the range of conclusions it can support.

A useful limitations section explains how each threat could bias or obscure a result and what additional experiment would address it.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.37 — Ablation of lottery assumptions

An ablation experiment changes one assumption at a time: use unequal quantum sizes, allow one client to block, change ticket weights during the run, or add a late-arriving client. Comparing each variant with the baseline shows which conclusions depend strongly on the original assumptions.

Keep the baseline unchanged and store each variant under a separate workload identifier. This prevents results from different models being mixed in one summary.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.38 — Statistical versus deterministic policies

Lottery introduces controlled random variation in each allocation decision. Stride uses deterministic virtual-time accounting and therefore tends to reduce variation in short windows for the same simplified workload. Determinism helps reproducibility, but it does not automatically make a policy fair under every dynamic or adversarial workload.

Discuss the trade-off in terms of the design goal: statistical proportionality and dynamic flexibility versus deterministic allocation sequence and virtual-time bookkeeping.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.39 — Hierarchical allocation example

Imagine a global scheduler that grants a group 40% of a resource. The group can divide its currency between two applications in a 3:1 ratio. The applications then receive 30% and 10% of the global resource under a stable group entitlement. This illustrates how local policy can compose with a global share.

A numeric hierarchy example should conserve the global entitlement at every level. Use the same units and state whether local tickets are normalized inside the parent currency.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.40 — Lock and synchronization connection

The original work motivates using proportional-share rights for resources beyond a processor. Exercise 5 applies the selection concept to a lock, but safety still comes from an ownership protocol and a condition variable. A weighted winner is not enough by itself to make the critical section safe.

Use the synchronization demo to show the boundary between allocation policy and mutual-exclusion mechanism. The two are complementary, not interchangeable.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.41 — Limitations of the repository experiment

The reference experiment is a pedagogical allocation-count model. It does not emulate kernel dispatch, interrupts, context-switch cost, CPU affinity, multicore load balancing, or application I/O. The results should not be advertised as a benchmark of real operating-system schedulers.

A transparent limitations section improves credibility. It tells the reader what the evidence can establish and prevents unsupported claims about performance outside the model.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.42 — Future research directions

Useful extensions include dynamically changing eligibility, hierarchical ticket currencies, compensation for early blocking, ticket transfer across dependencies, multicore resource pools, and latency-aware metrics. Each extension introduces new assumptions and invariants that must be specified before implementation.

Prioritize one extension at a time. A small controlled study with a precise hypothesis is more informative than a large collection of interacting features with no clear evaluation.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.43 — Research review conclusion

The central contribution is a flexible representation of proportional entitlement using tickets, together with mechanisms that make the abstraction useful across clients and resources. The experiment in this repository illustrates the probability rule and contrasts a randomized policy with deterministic stride accounting.

The appropriate conclusion is scoped: lottery is useful when expected proportional sharing is desired; it is not a replacement for worst-case deadline analysis and does not supply a hard response-time guarantee by itself.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.44 — Questions for oral defense

A reviewer may ask why a fixed seed is not enough to make thread scheduling deterministic, why stride uses virtual pass, why a low-ticket client can wait a long time, or why the experiment cannot prove deadline satisfaction. Prepare answers that refer to the assumptions and evidence in the report.

A strong oral answer identifies the relevant model variable, explains the mechanism, and states the limit of the claim. Avoid responding with a general statement that one scheduler is always better.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.

[[PAGEBREAK]]
## Appendix B.45 — Final submission audit

Before submission, verify that the primary source is cited, the research question is explicit, all experiment inputs are recorded, the JSON result exists, the slide deck opens, and both language versions communicate the same conclusions. Page count should be checked after final rendering because Word and PDF can paginate differently.

The audit should also confirm that every numerical result in the slides comes from the committed output file and that no unexecuted prediction is presented as a measurement.

**Review evidence:** Keep the workload definition, source revision, and generated result file together. A reviewer should be able to reproduce the example and identify which assumptions limit the conclusion.