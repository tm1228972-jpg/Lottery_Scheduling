import subprocess
import time
import random
import psutil

processes = []

number = int(input("Number of programs: "))
quantum = float(input("Time quantum (seconds): "))

for i in range(number):
    print(f"\nProgram {i + 1}")

    path = input("Program path: ")
    tickets = int(input("Number of tickets: "))

    if tickets <= 0:
        raise ValueError("Tickets must be greater than zero")

    processes.append({
        "name": f"P{i + 1}",
        "path": path,
        "tickets": tickets,
        "process": None,
        "monitor": None,
        "cpu_time": 0.0,
        "start": 0.0,
        "runtime": 0.0,
        "finished": False
    })

try:
    for p in processes:
        p["start"] = time.perf_counter()
        p["process"] = subprocess.Popen([p["path"]])
        p["monitor"] = psutil.Process(p["process"].pid)
        p["monitor"].suspend()

    while any(not p["finished"] for p in processes):
        active = [p for p in processes if not p["finished"]]

        winner = random.choices(
            active,
            weights=[p["tickets"] for p in active],
            k=1
        )[0]

        process = winner["process"]
        monitor = winner["monitor"]

        try:
            before = monitor.cpu_times()
            monitor.resume()

            try:
                process.wait(timeout=quantum)
                winner["finished"] = True
            except subprocess.TimeoutExpired:
                monitor.suspend()

            after = monitor.cpu_times()

            winner["cpu_time"] += (
                after.user + after.system
                - before.user - before.system
            )

            if winner["finished"]:
                winner["runtime"] = time.perf_counter() - winner["start"]
                print(f'{winner["name"]} finished')

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            if process.poll() is not None:
                winner["finished"] = True
                winner["runtime"] = time.perf_counter() - winner["start"]
            else:
                print(f'Unable to control {winner["name"]}')
                winner["finished"] = True

finally:
    for p in processes:
        process = p["process"]
        monitor = p["monitor"]

        if process is not None and process.poll() is None:
            try:
                if monitor is not None and monitor.is_running():
                    monitor.resume()
                process.terminate()
                process.wait(timeout=2)
            except (psutil.NoSuchProcess, psutil.AccessDenied, subprocess.TimeoutExpired):
                process.kill()

print("\nResults")
print("Program\tTickets\tCPU Time\tRuntime\tReturn Code")

for p in processes:
    if p["process"] is not None:
        print(
            f'{p["name"]}\t{p["tickets"]}\t'
            f'{p["cpu_time"]:.3f}\t\t'
            f'{p["runtime"]:.3f}\t'
            f'{p["process"].returncode}'
        )
