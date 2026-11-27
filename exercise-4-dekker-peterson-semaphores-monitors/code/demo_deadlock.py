#!/usr/bin/env python3
"""Bounded live-demonstration of the flag-only deadlock (deterministic).

Both threads raise their flags and only THEN enter the spin. Forcing the
interleaving this way reproduces the exact deadlocked state the enumeration
finds: ((1, 1), (True, True), 0) — both at the spin PC, both flags up.
The spin is bounded so this demo terminates; the real algorithm never exits.
"""
import threading

SPIN_LIMIT = 50

flags = [False, False]
counts = [0, 0]
both_up = threading.Barrier(2)

def worker(i):
    j = 1 - i
    flags[i] = True                    # flag[i] := true
    both_up.wait()                     # both flags are up before either spins
    while flags[j]:                    # while flag[j]: pass — never satisfied
        counts[i] += 1
        if counts[i] >= SPIN_LIMIT:
            return                     # would spin forever; we stop counting

def main():
    t0 = threading.Thread(target=worker, args=(0,))
    t1 = threading.Thread(target=worker, args=(1,))
    t0.start(); t1.start()
    t0.join(); t1.join()
    print(f"flag-only: thread0 spun {counts[0]} times, thread1 spun {counts[1]} times")
    print("verdict: both threads still inside the entry loop; CS never reached (deadlock demonstrated, bounded)")

if __name__ == "__main__":
    main()
