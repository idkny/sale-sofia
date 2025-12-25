#!/usr/bin/env python3
"""
Test 2.2.5: Celery + PSC (Proxy-Scraper-Checker) integration
Tests if Celery can successfully run the PSC binary to scrape proxies
"""

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = "/home/wow/Projects/sale-sofia"
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)


def check_process(name):
    """Check if process is running (excludes this test script)"""
    result = subprocess.run(
        ["pgrep", "-af", name],
        capture_output=True,
        text=True
    )
    lines = [line for line in result.stdout.strip().split('\n')
             if line and 'test_celery_psc' not in line]
    return '\n'.join(lines)


def main():
    print("=== Test 2.2.5: Celery + PSC Integration ===")

    # Check PSC binary exists
    from paths import PSC_EXECUTABLE_PATH, PROXY_CHECKER_DIR
    if not PSC_EXECUTABLE_PATH.exists():
        print(f"FAIL: PSC binary not found at {PSC_EXECUTABLE_PATH}")
        return 1
    print(f"OK: PSC binary found at {PSC_EXECUTABLE_PATH}")

    # Start Celery worker
    print("\nStarting Celery worker...")
    log_file = Path(PROJECT_DIR) / "data" / "logs" / "celery_psc_test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as log_handle:
        celery_proc = subprocess.Popen(
            ["celery", "-A", "celery_app", "worker", "-Q", "celery,sale_sofia",
             "--loglevel=info", "--concurrency=2"],
            cwd=PROJECT_DIR,
            stdout=log_handle,
            stderr=subprocess.STDOUT
        )
    print(f"Celery PID: {celery_proc.pid}")

    time.sleep(5)

    if celery_proc.poll() is not None:
        print("FAIL: Celery worker died on startup")
        with open(log_file) as f:
            print(f.read()[-500:])
        return 1
    print("OK: Celery worker started")

    # Trigger scrape_new_proxies_task
    print("\nTriggering scrape_new_proxies_task...")
    from proxies.tasks import scrape_new_proxies_task

    result = scrape_new_proxies_task.delay()
    print(f"Task ID: {result.id}")

    # Wait for task to complete (PSC takes ~1-3 minutes)
    print("Waiting for PSC to complete (timeout: 5 min)...")
    start_time = time.time()
    timeout = 300  # 5 minutes

    while not result.ready():
        elapsed = int(time.time() - start_time)
        print(f"  State: {result.state} ({elapsed}s elapsed)")
        if elapsed > timeout:
            print("FAIL: Task timed out")
            result.revoke(terminate=True)
            celery_proc.terminate()
            return 1
        time.sleep(10)

    # Check result
    if result.successful():
        print(f"\nOK: Task succeeded: {result.result}")
    else:
        print(f"\nFAIL: Task failed: {result.result}")
        celery_proc.terminate()
        return 1

    # Verify output file exists and has content
    psc_output = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
    if psc_output.exists():
        import json
        with open(psc_output) as f:
            proxies = json.load(f)
        print(f"OK: Output file exists with {len(proxies)} proxies")
    else:
        print(f"FAIL: Output file not found at {psc_output}")
        celery_proc.terminate()
        return 1

    # Stop Celery gracefully
    print("\nStopping Celery with SIGTERM...")
    celery_proc.terminate()
    try:
        celery_proc.wait(timeout=10)
        print("OK: Celery terminated gracefully")
    except subprocess.TimeoutExpired:
        print("WARN: Celery didn't stop gracefully, killing...")
        celery_proc.kill()

    time.sleep(2)

    # Check for orphans
    print("\n--- Checking for orphans ---")
    psc_after = check_process("proxy-scraper-checker")
    celery_after = check_process("celery -A celery_app")

    if psc_after:
        print(f"FAIL: Orphan PSC processes:\n{psc_after}")
        return 1
    else:
        print("OK: No orphan PSC processes")

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
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
