#!/usr/bin/env python3
"""
Test 5: Celery dies mid-task
CRITICAL TEST: Tests if mubeng processes become orphans when Celery is killed during task execution
"""

import os
import signal
import subprocess
import time
import sys

PROJECT_DIR = "/home/wow/Projects/sale-sofia"
os.chdir(PROJECT_DIR)

def check_process(name):
    """Check if process is running"""
    result = subprocess.run(
        ["pgrep", "-af", name],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def main():
    print("=== Test 5: Celery Dies Mid-Task ===")
    print("This is the CRITICAL test for subprocess cleanup\n")

    # Start Celery worker
    print("Starting Celery worker...")
    celery_proc = subprocess.Popen(
        ["celery", "-A", "celery_app", "worker", "-Q", "celery,sale_sofia",
         "--loglevel=info"],
        cwd=PROJECT_DIR
    )
    print(f"Celery PID: {celery_proc.pid}")

    time.sleep(5)

    # Start a long-running task
    print("\nStarting task with 50 proxies (will take time)...")
    task_proc = subprocess.Popen([
        "python", "-c",
        """
from proxies.tasks import check_proxy_chunk_task

chunk = [{'host': f'1.1.1.{i}', 'port': 80, 'protocol': 'http'} for i in range(50)]
result = check_proxy_chunk_task.delay(chunk)
print(f'Task ID: {result.id}')

import time
for i in range(60):
    time.sleep(1)
    print(f'State: {result.state}')
    if result.ready():
        print(f'Result: {result.result}')
        break
        """
    ], cwd=PROJECT_DIR)

    # Give task time to start and spawn mubeng
    time.sleep(3)

    print("\n--- Processes BEFORE killing Celery ---")
    celery_before = check_process("celery")
    mubeng_before = check_process("mubeng")

    print(f"Celery processes: {len(celery_before.splitlines())} found")
    if mubeng_before:
        print(f"Mubeng processes: {len(mubeng_before.splitlines())} found")
        print(mubeng_before)
    else:
        print("WARNING: No mubeng processes found yet")

    # Kill Celery ungracefully
    print(f"\nKilling Celery (PID {celery_proc.pid}) with SIGKILL...")
    celery_proc.kill()
    time.sleep(3)

    # Kill the task script too
    task_proc.kill()

    # Check for orphan mubeng
    print("\n--- Processes AFTER killing Celery ---")
    mubeng_after = check_process("mubeng")
    celery_after = check_process("celery")

    if celery_after:
        print(f"WARNING: Celery processes still running:\n{celery_after}")

    if mubeng_after:
        print(f"\nCRITICAL FAIL: Orphan mubeng processes found!")
        print(f"Count: {len(mubeng_after.splitlines())}")
        print(mubeng_after)
        print("\nThis indicates mubeng processes are NOT being cleaned up when Celery dies.")
        print("Root cause: Subprocess management issue in check_proxy_chunk_task")

        # Cleanup orphans
        print("\nCleaning up orphan mubeng processes...")
        subprocess.run(["pkill", "-9", "-f", "mubeng"])

        return 1
    else:
        print("OK: No orphan mubeng processes")
        print("\n=== RESULT: PASS ===")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        subprocess.run(["pkill", "-9", "-f", "celery"])
        subprocess.run(["pkill", "-9", "-f", "mubeng"])
        sys.exit(1)
