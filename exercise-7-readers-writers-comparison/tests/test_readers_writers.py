import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from readers_writers import ReaderWriterLock, run_benchmark


def test_writer_exclusion_and_parallel_readers():
    lock = ReaderWriterLock("fair")
    state_guard = threading.Lock()
    active_readers = 0
    active_writers = 0
    peak_readers = 0
    errors = []

    def reader():
        nonlocal active_readers, peak_readers
        for _ in range(30):
            with lock.read_lock():
                with state_guard:
                    active_readers += 1
                    peak_readers = max(peak_readers, active_readers)
                    if active_writers:
                        errors.append("reader overlapped writer")
                time.sleep(0.0002)
                with state_guard:
                    active_readers -= 1

    def writer():
        nonlocal active_writers
        for _ in range(20):
            with lock.write_lock():
                with state_guard:
                    active_writers += 1
                    if active_writers > 1 or active_readers:
                        errors.append("writer overlap")
                time.sleep(0.0002)
                with state_guard:
                    active_writers -= 1

    threads = [threading.Thread(target=reader) for _ in range(4)]
    threads += [threading.Thread(target=writer) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    assert all(not t.is_alive() for t in threads)
    assert not errors
    assert peak_readers >= 2


def test_fair_policy_does_not_allow_later_reader_to_pass_queued_writer():
    lock = ReaderWriterLock("fair")
    first_reader_entered = threading.Event()
    release_first_reader = threading.Event()
    writer_entered = threading.Event()
    later_reader_entered = threading.Event()
    order = []

    def first_reader():
        with lock.read_lock():
            first_reader_entered.set()
            release_first_reader.wait(timeout=2)

    def writer():
        with lock.write_lock():
            order.append("writer")
            writer_entered.set()
            time.sleep(0.02)

    def later_reader():
        with lock.read_lock():
            order.append("reader")
            later_reader_entered.set()

    t1 = threading.Thread(target=first_reader)
    t1.start()
    assert first_reader_entered.wait(1)
    tw = threading.Thread(target=writer)
    tw.start()
    deadline = time.monotonic() + 1
    while lock.waiting_count < 1 and time.monotonic() < deadline:
        time.sleep(0.001)
    assert lock.waiting_count >= 1
    tr = threading.Thread(target=later_reader)
    tr.start()
    deadline = time.monotonic() + 1
    while lock.waiting_count < 2 and time.monotonic() < deadline:
        time.sleep(0.001)
    release_first_reader.set()
    assert writer_entered.wait(1)
    assert later_reader_entered.wait(1)
    for thread in (t1, tw, tr):
        thread.join(timeout=2)
    assert order == ["writer", "reader"]


def test_all_three_policies_complete_workload():
    results = [run_benchmark(policy, readers=2, writers=1, operations=12)
               for policy in ("reader", "writer", "fair")]
    assert all(result["final_version"] == 3 for result in results)
    assert all(result["write_entries"] == 3 for result in results)
    assert all(result["errors"] == [] for result in results)
