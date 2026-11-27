#!/usr/bin/env python3
"""Exercise 4 — exact, finite-state models of shared-memory mutual exclusion.

Two-process models, enumerated as transition systems. Used both for the
proof-style checks (exhaustive state enumeration — Python can be the model
checker when the system is this small) and for explaining the algorithms
step by step in the report.

Process programs (classical forms):

  dekker:
    0: want[i] = True                       # flag raise
    1: while want[j]:                       # other wants it too?
    2:   while turn != i:                   # then defer by turn
    3:     want[i] = False                  #   back off completely
    4:     while turn != i: pass            #   wait silently
    5:     want[i] = True                   #   re-assert
    6: CS                                   # (line 6/7 merged)
    7: want[i] = False                      # exit: release
    (turn = j set inside the back-off branch per Dekker's description)

  peterson:
    0: want[i] = True
    1: turn = j                              # offer priority to the other
    2: while want[j] and turn == j: pass     # wait while other wants AND has priority
    3: CS
    4: want[i] = False

  turn_only (broken):
    0: while turn != i: pass
    1: CS
    2: turn = j

  flag_only (broken):
    0: want[i] = True
    1: while want[j]: pass                  # no turn arbitration -> deadlock
    2: CS
    3: want[i] = False
"""
from __future__ import annotations

from collections import deque
from itertools import product

CS = "CS"


def _other(i):
    return 1 - i


def dekker_successors(state):
    pc, want, turn = state
    i = None
    nxt = []
    for self_i in (0, 1):
        s = pc[self_i]
        o = _other(self_i)
        if s == 0:
            p2 = list(pc); p2[self_i] = 1
            w2 = list(want); w2[self_i] = True
            nxt.append((tuple(p2), tuple(w2), turn))
        elif s == 1:
            # while want[other]: -> enter turn contest if other also wants
            if want[o]:
                p2 = list(pc); p2[self_i] = 2
                nxt.append((tuple(p2), want, turn))
            else:
                p2 = list(pc); p2[self_i] = CS
                nxt.append((tuple(p2), want, turn))
        elif s == 2:
            # if (turn != i): back off; otherwise keep spinning on want[j]
            if turn == self_i:
                p2 = list(pc); p2[self_i] = 1   # turn favors us but other still wants -> wait
                nxt.append((tuple(p2), want, turn))
            else:
                p2 = list(pc); p2[self_i] = 3
                nxt.append((tuple(p2), want, turn))
        elif s == 3:
            # flag[i] = False  (back off completely)
            p2 = list(pc); p2[self_i] = 4
            w2 = list(want); w2[self_i] = False
            nxt.append((tuple(p2), tuple(w2), turn))
        elif s == 4:
            # while turn != i: pass  (silent wait)
            if turn == self_i:
                p2 = list(pc); p2[self_i] = 5
                nxt.append((tuple(p2), want, turn))
        elif s == 5:
            # flag[i] = True  (re-assert) — loop back to the while header
            p2 = list(pc); p2[self_i] = 1
            w2 = list(want); w2[self_i] = True
            nxt.append((tuple(p2), tuple(w2), turn))
        elif s == CS:
            # CS body (atomic in this model) -> turn = j  (Dekker exit assignment)
            p2 = list(pc); p2[self_i] = 6
            nxt.append((tuple(p2), want, turn))
        elif s == 6:
            # turn = j
            p2 = list(pc); p2[self_i] = 7
            nxt.append((tuple(p2), want, _other(self_i)))
        elif s == 7:
            # flag[i] = False
            p2 = list(pc); p2[self_i] = 8  # halted
            w2 = list(want); w2[self_i] = False
            nxt.append((tuple(p2), tuple(w2), turn))
    return nxt


def peterson_successors(state):
    pc, want, turn = state
    nxt = []
    for self_i in (0, 1):
        s = pc[self_i]
        o = _other(self_i)
        if s == 0:
            p2 = list(pc); p2[self_i] = 1
            w2 = list(want); w2[self_i] = True
            nxt.append((tuple(p2), tuple(w2), turn))
        elif s == 1:
            p2 = list(pc); p2[self_i] = 2
            nxt.append((tuple(p2), want, o))
        elif s == 2:
            if want[o] and turn == o:
                pass  # blocked: no transition (this is the wait)
            else:
                p2 = list(pc); p2[self_i] = CS
                nxt.append((tuple(p2), want, turn))
        elif s == CS:
            p2 = list(pc); p2[self_i] = 4
            nxt.append((tuple(p2), want, turn))
        elif s == 4:
            p2 = list(pc); p2[self_i] = 8  # halted
            w2 = list(want); w2[self_i] = False
            nxt.append((tuple(p2), tuple(w2), turn))
    return nxt


def turn_only_successors(state):
    pc, want, turn = state
    nxt = []
    for self_i in (0, 1):
        s = pc[self_i]
        if s == 0:
            if turn == self_i:
                p2 = list(pc); p2[self_i] = CS
                nxt.append((tuple(p2), want, turn))
        elif s == CS:
            p2 = list(pc); p2[self_i] = 2
            nxt.append((tuple(p2), want, _other(self_i)))
        elif s == 2:
            p2 = list(pc); p2[self_i] = 8
            nxt.append((tuple(p2), want, _other(self_i)))
    return nxt


def flag_only_successors(state):
    pc, want, turn = state
    nxt = []
    for self_i in (0, 1):
        s = pc[self_i]
        o = _other(self_i)
        if s == 0:
            p2 = list(pc); p2[self_i] = 1
            w2 = list(want); w2[self_i] = True
            nxt.append((tuple(p2), tuple(w2), turn))
        elif s == 1:
            if want[o]:
                pass  # blocked forever if both want
            else:
                p2 = list(pc); p2[self_i] = CS
                nxt.append((tuple(p2), want, turn))
        elif s == CS:
            p2 = list(pc); p2[self_i] = 3
            nxt.append((tuple(p2), want, turn))
        elif s == 3:
            p2 = list(pc); p2[self_i] = 8
            w2 = list(want); w2[self_i] = False
            nxt.append((tuple(p2), tuple(w2), turn))
    return nxt


MODELS = {
    "dekker": dekker_successors,
    "peterson": peterson_successors,
    "turn_only": turn_only_successors,
    "flag_only": flag_only_successors,
}

HALT = 8
INIT = ((0, 0), (False, False), 0)


def enumerate_states(model: str):
    succ = MODELS[model]
    start = INIT
    seen = {start}
    q = deque([start])
    transitions = 0
    while q:
        state = q.popleft()
        for ns in succ(state):
            transitions += 1
            if ns not in seen:
                seen.add(ns)
                q.append(ns)
    return seen, transitions


def check_safety(model: str):
    """Mutual exclusion: no reachable state with both in CS."""
    states, transitions = enumerate_states(model)
    violations = [s for s in states if s[0][0] == CS and s[0][1] == CS]
    return {"model": model, "states": len(states), "transitions": transitions,
            "mutual_exclusion_violations": len(violations),
            "violation_states": violations[:5]}


def check_deadlock(model: str):
    """Deadlock: reachable non-final state with no enabled transitions, not both halted."""
    succ = MODELS[model]
    states, _ = enumerate_states(model)
    deadlocks = []
    for s in states:
        if all(p == HALT for p in s[0]):
            continue
        if not succ(s):
            deadlocks.append(s)
    return {"model": model, "deadlock_states": len(deadlocks), "examples": deadlocks[:5]}


ENTRY_PCS = {
    "dekker": {0, 1, 2, 3, 4, 5},
    "peterson": {0, 1, 2},
    "turn_only": {0},
    "flag_only": {0, 1},
}

def check_liveness(model: str):
    """Every reachable state with process i inside the entry protocol can reach CS.

    States where i has already passed through the protocol (exit states) or halted
    are legitimate and excluded. This is starvation-freedom for one pass of the
    entry protocol, which is the strongest useful liveness for a 2-process model.
    """
    succ = MODELS[model]
    states, _ = enumerate_states(model)
    rev = {s: [] for s in states}
    for s in states:
        for ns in succ(s):
            rev.setdefault(ns, []).append(s)
    entry = ENTRY_PCS[model]
    for i in (0, 1):
        target = set()
        dq = deque(s for s in states if s[0][i] == CS)
        while dq:
            cur = dq.popleft()
            if cur in target:
                continue
            target.add(cur)
            dq.extend(rev.get(cur, ()))
        unreachable = [s for s in states
                       if s not in target and s[0][i] in entry]
        if unreachable:
            return {"model": model, "process": i, "live": False,
                    "states_from_which_cs_unreachable": len(unreachable)}
    return {"model": model, "live": True}


def state_graph_summary(model: str):
    seen, transitions = enumerate_states(model)
    both_halt = sum(1 for s in seen if all(p == HALT for p in s[0]))
    in_cs = sum(1 for s in seen if s[0][0] == CS or s[0][1] == CS)
    return {"model": model, "states": len(seen), "transitions": transitions,
            "terminal_states": both_halt, "cs_states": in_cs}
