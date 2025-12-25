#!/usr/bin/env python3
"""
Test: Orchestrator Event-Based Completion

PURPOSE:
--------
Verify that orchestrator.wait_for_refresh_completion() correctly uses
the new event-based completion (AsyncResult.get()) instead of polling.

This tests the ACTUAL production code path used by main.py.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = "/home/wow/Projects/sale-sofia"
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)


def main():
    print("=" * 60)
    print("Test: Orchestrator Event-Based Completion")
    print("=" * 60)
    print("\nPURPOSE: Verify wait_for_refresh_completion uses chord_id")
    print("=" * 60)

    from paths import PROXY_CHECKER_DIR, PROXIES_DIR

    # Step 1: Clear previous results
    print(f"\n[Step 1] Clearing previous results...")
    psc_output = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
    live_json = PROXIES_DIR / "live_proxies.json"
    live_txt = PROXIES_DIR / "live_proxies.txt"

    for f in [psc_output, live_json, live_txt]:
        if f.exists():
            f.unlink()
            print(f"  Removed: {f}")
    print("OK: Previous results cleared")

    # Step 2: Start Celery worker
    print(f"\n[Step 2] Starting Celery worker...")
    log_file = Path(PROJECT_DIR) / "data" / "logs" / "celery_orchestrator_test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as log_handle:
        celery_proc = subprocess.Popen(
            ["celery", "-A", "celery_app", "worker", "-Q", "celery,sale_sofia",
             "--loglevel=info", "--concurrency=4"],
            cwd=PROJECT_DIR,
            stdout=log_handle,
            stderr=subprocess.STDOUT
        )
    print(f"Celery PID: {celery_proc.pid}")
    time.sleep(5)

    if celery_proc.poll() is not None:
        print("FAIL: Celery worker died on startup")
        return 1
    print("OK: Celery worker started")

    # Step 3: Create orchestrator and trigger refresh
    print(f"\n[Step 3] Creating orchestrator and triggering refresh...")
    from orchestrator import Orchestrator

    orch = Orchestrator()
    mtime_before, task_id = orch.trigger_proxy_refresh()
    print(f"Chain Task ID: {task_id}")

    if not task_id:
        print("FAIL: No task_id returned from trigger_proxy_refresh")
        celery_proc.terminate()
        return 1
    print("OK: Refresh triggered")

    # Step 4: Call wait_for_refresh_completion (THE CODE WE'RE TESTING)
    print(f"\n[Step 4] Calling wait_for_refresh_completion...")
    print("(This should use AsyncResult.get() with chord_id)")
    print("(Watch for 'chord_id' in output - proves new code path)")
    print("-" * 60)

    start_time = time.time()
    success = orch.wait_for_refresh_completion(
        mtime_before=mtime_before,
        min_count=1,  # Low threshold for testing
        timeout=0,    # No timeout - wait until done (event-based!)
        task_id=task_id
    )
    elapsed = int(time.time() - start_time)

    print("-" * 60)
    print(f"wait_for_refresh_completion returned: {success}")
    print(f"Time taken: {elapsed}s")

    # Step 5: Verify results
    print(f"\n[Step 5] Verifying results...")

    if not success:
        print("FAIL: wait_for_refresh_completion returned False")
        # Check log for errors
        if log_file.exists():
            with open(log_file) as f:
                log_content = f.read()
            if "chord_id" in log_content:
                print("OK: chord_id WAS used (check log for details)")
            else:
                print("WARN: chord_id NOT found in log")
        celery_proc.terminate()
        return 1

    if not live_json.exists():
        print("FAIL: live_proxies.json not created")
        celery_proc.terminate()
        return 1

    import json
    with open(live_json) as f:
        live_proxies = json.load(f)
    print(f"OK: {len(live_proxies)} live proxies saved")

    # Step 6: Check log for chord_id usage
    print(f"\n[Step 6] Checking log for chord_id usage...")
    if log_file.exists():
        with open(log_file) as f:
            log_content = f.read()
        if "chord_id" in log_content:
            print("OK: chord_id found in log - event-based code used!")
        else:
            print("WARN: chord_id NOT found in log - may have used fallback")

    # Step 7: Cleanup
    print(f"\n[Step 7] Stopping Celery...")
    celery_proc.terminate()
    try:
        celery_proc.wait(timeout=10)
        print("OK: Celery terminated gracefully")
    except subprocess.TimeoutExpired:
        celery_proc.kill()
        print("WARN: Had to kill Celery")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  wait_for_refresh_completion: {'PASSED' if success else 'FAILED'}")
    print(f"  Live proxies: {len(live_proxies)}")
    print(f"  Time: {elapsed}s")
    print("=" * 60)
    print("=== RESULT: PASS ===" if success else "=== RESULT: FAIL ===")
    return 0 if success else 1


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
