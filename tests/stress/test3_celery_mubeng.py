#!/usr/bin/env python3
"""
Test 3: Celery + Mubeng integration
Tests if mubeng processes are cleaned up when Celery worker stops gracefully
"""

import os
import signal
import subprocess
import time
import sys

PROJECT_DIR = "/home/wow/Projects/sale-sofia"
os.chdir(PROJECT_DIR)

def check_process(name):
    """Check if process is running (excludes this test script)"""
    result = subprocess.run(
        ["pgrep", "-af", name],
        capture_output=True,
        text=True
    )
    # Filter out lines matching this test script itself
    lines = [line for line in result.stdout.strip().split('\n')
             if line and 'test3_celery_mubeng' not in line]
    return '\n'.join(lines)

def main():
    print("=== Test 3: Celery + Mubeng Integration ===")

    # Start Celery worker
    print("Starting Celery worker...")
    celery_proc = subprocess.Popen(
        ["celery", "-A", "celery_app", "worker", "-Q", "celery,sale_sofia",
         "--loglevel=info", "--concurrency=2"],
        cwd=PROJECT_DIR
    )
    print(f"Celery PID: {celery_proc.pid}")

    time.sleep(5)

    # Trigger a task
    print("\nTriggering proxy check task...")
    result = subprocess.run([
        "python", "-c",
        """
from proxies.tasks import check_proxy_chunk_task
import time

chunk = [{'host': '1.1.1.1', 'port': 80, 'protocol': 'http'}]
result = check_proxy_chunk_task.delay(chunk)
print(f'Task ID: {result.id}')

for i in range(30):
    time.sleep(1)
    print(f'State: {result.state}')
    if result.ready():
        print(f'Result: {result.result}')
        break
        """
    ], cwd=PROJECT_DIR)

    print("\n--- Processes before Celery shutdown ---")
    mubeng_before = check_process("mubeng")
    if mubeng_before:
        print(f"Mubeng processes:\n{mubeng_before}")
    else:
        print("No mubeng processes")

    # Stop Celery gracefully
    print("\nStopping Celery with SIGTERM...")
    celery_proc.terminate()
    try:
        celery_proc.wait(timeout=10)
        print("Celery terminated")
    except subprocess.TimeoutExpired:
        print("Celery didn't stop gracefully, killing...")
        celery_proc.kill()

    time.sleep(3)

    # Check for orphans
    print("\n--- Checking for orphans ---")
    mubeng_after = check_process("mubeng")
    celery_after = check_process("celery")

    if mubeng_after:
        print(f"FAIL: Orphan mubeng processes:\n{mubeng_after}")
        return 1
    else:
        print("OK: No orphan mubeng processes")

    if celery_after:
        print(f"FAIL: Orphan celery processes:\n{celery_after}")
        return 1
    else:
        print("OK: No orphan celery processes")

    print("\n=== RESULT: PASS ===")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
