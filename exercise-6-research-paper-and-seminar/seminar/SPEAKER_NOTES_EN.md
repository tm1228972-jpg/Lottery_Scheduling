# Seminar speaker notes — Lottery Scheduling

## 1. Opening
Frame the problem as resource allocation, not merely CPU priority. The key question is how a system can express relative shares among runnable clients.

## 2. Motivation
Fixed priorities do not directly express a proportional entitlement. Lottery scheduling gives each client tickets and makes each allocation decision a weighted random draw.

## 3. Rule
For client i, with t_i tickets and T total runnable tickets, the one-draw probability is t_i/T. Emphasize that this is an expectation, not a promise for a short finite interval.

## 4. Worked example
Use 5:3:2. If the winning ticket is 7, P2 wins because its interval is 6–8. A different draw may select a different client.

## 5. Extensions
Introduce ticket transfer, currencies, and compensation tickets. Explain that ticket transfer can carry resource rights across dependencies; currencies make hierarchical allocation composable.

## 6. Evidence
The experiment uses fixed seeds, a stated ticket vector, and equal quanta. The metric is maximum absolute share error. Do not generalize these results to kernel wall-clock behavior.

## 7. Lottery versus stride
Stride scheduling replaces random draws with deterministic virtual-time accounting. This typically reduces short-window variance but trades away some of lottery's responsiveness and simplicity.

## 8. Synchronization
Connect the original paper's lock/resource idea to the weighted lock in Exercise 5. A correct implementation still needs mutual exclusion and a safe waiting protocol. Probability is not a FIFO guarantee.

## 9. Conclusions
Lottery is useful when proportional sharing is the goal. It does not replace EDF/RM deadline analysis or guarantee bounded response time.

## 10. Questions
Invite discussion about finite-run fairness, ticket assignment, random seeds, lock contention, and evaluation methodology.
