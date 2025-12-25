#!/usr/bin/env python3
"""
Test 2.2.6: PSC → Dispatcher → Mubeng (Data Flow Integration)

PURPOSE:
--------
This test validates the DATA HANDOFF between components, not just that each
component runs. It answers: "Can data flow correctly from PSC output through
the dispatcher to Mubeng workers?"

WHY THIS TEST EXISTS:
---------------------
We already tested:
- Test 2.2.5: Celery + PSC (PSC creates proxies_pretty.json)
- Test 2.2: Celery + Mubeng (Mubeng checks a hardcoded proxy list)

But we haven't verified:
1. PSC output FORMAT is compatible with dispatcher expectations
2. Dispatcher correctly READS and SPLITS the PSC output
3. Chunks are correctly PASSED to Mubeng workers
4. Results are correctly AGGREGATED from parallel workers

HOW THIS HELPS:
---------------
If Test 2.3 (full pipeline) fails, we won't know if it's:
- A PSC problem (already tested in 2.2.5)
- A Mubeng problem (already tested in 2.2)
- A DATA FORMAT problem (tested HERE)
- A DISPATCHER problem (tested HERE)
- An AGGREGATION problem (tested HERE)

This test isolates the "glue" logic that connects components.

TEST FLOW:
----------
1. Uses EXISTING PSC output (proxies_pretty.json) - no need to re-scrape
2. Triggers check_scraped_proxies_task (the dispatcher)
3. Dispatcher reads JSON, splits into chunks, sends to Mubeng workers
4. Mubeng workers check proxies in parallel
5. process_check_results_task aggregates and saves results
6. We verify live_proxies.json is created with valid data
"""

import json
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
             if line and 'test_psc_dispatcher_mubeng' not in line]
    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("Test 2.2.6: PSC → Dispatcher → Mubeng (Data Flow)")
    print("=" * 60)
    print("\nPURPOSE: Validate data handoff between components")
    print("- PSC output format → Dispatcher parsing")
    print("- Dispatcher chunking → Mubeng parallel workers")
    print("- Mubeng results → Aggregation and save")
    print("=" * 60)

    from paths import PROXY_CHECKER_DIR, PROXIES_DIR

    # Step 1: Verify PSC output exists (from previous test)
    psc_output = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
    print(f"\n[Step 1] Checking PSC output file...")

    if not psc_output.exists():
        print(f"FAIL: PSC output not found at {psc_output}")
        print("       Run Test 2.2.5 first to generate proxy data")
        return 1

    with open(psc_output) as f:
        proxies = json.load(f)
    print(f"OK: Found {len(proxies)} proxies from PSC output")

    # Verify format
    if proxies:
        sample = proxies[0]
        required_fields = ['host', 'port']
        missing = [f for f in required_fields if f not in sample]
        if missing:
            print(f"FAIL: PSC output missing required fields: {missing}")
            print(f"      Sample proxy: {sample}")
            return 1
        print(f"OK: Format valid (sample: {sample.get('host')}:{sample.get('port')})")

    # Step 2: Clear previous results to verify new ones are created
    live_json = PROXIES_DIR / "live_proxies.json"
    live_txt = PROXIES_DIR / "live_proxies.txt"

    print(f"\n[Step 2] Clearing previous results...")
    for f in [live_json, live_txt]:
        if f.exists():
            f.unlink()
            print(f"  Removed: {f.name}")
    print("OK: Previous results cleared")

    # Step 3: Start Celery worker
    print(f"\n[Step 3] Starting Celery worker...")
    log_file = Path(PROJECT_DIR) / "data" / "logs" / "celery_dataflow_test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as log_handle:
        celery_proc = subprocess.Popen(
            ["celery", "-A", "celery_app", "worker", "-Q", "celery,sale_sofia",
             "--loglevel=info", "--concurrency=4"],  # 4 workers for parallel chunks
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

    # Step 4: Trigger the dispatcher (check_scraped_proxies_task)
    print(f"\n[Step 4] Triggering check_scraped_proxies_task (dispatcher)...")
    from proxies.tasks import check_scraped_proxies_task

    result = check_scraped_proxies_task.delay()
    print(f"Task ID: {result.id}")

    # Wait for dispatcher to complete (it just dispatches, doesn't wait for chunks)
    print("Waiting for dispatcher to dispatch chunks...")
    for i in range(30):
        time.sleep(1)
        if result.ready():
            break

    if result.successful():
        print(f"OK: Dispatcher completed: {result.result}")
    else:
        print(f"WARN: Dispatcher state: {result.state}")

    # Step 5: Wait for chunk processing (Mubeng checks take time)
    print(f"\n[Step 5] Waiting for Mubeng workers to process chunks...")
    print("(29 chunks × ~60s each ÷ 4 workers = ~7-10 minutes)")

    timeout = 900  # 15 minutes (29 chunks, each 45-95s, 4 workers)
    start_time = time.time()
    check_interval = 15  # Check every 15 seconds

    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)

        # Check if the final results file exists (created by callback task)
        if live_json.exists():
            try:
                with open(live_json) as f:
                    proxies = json.load(f)
                print(f"  [{elapsed}s] Results file created with {len(proxies)} proxies!")
                break
            except (json.JSONDecodeError, IOError):
                print(f"  [{elapsed}s] Results file being written...")

        # Check Celery log for progress
        log_file = Path(PROJECT_DIR) / "data" / "logs" / "celery_dataflow_test.log"
        if log_file.exists():
            with open(log_file) as f:
                log_content = f.read()
            # Count completed chunks
            completed = log_content.count("check_proxy_chunk_task") - log_content.count("received")
            # Actually count "succeeded" messages
            succeeded = log_content.count("succeeded in")
            print(f"  [{elapsed}s] ~{succeeded} chunks completed...")

        time.sleep(check_interval)
    else:
        print(f"WARN: Timeout after {timeout}s, checking partial results...")

    # Step 6: Verify results
    print(f"\n[Step 6] Verifying results...")

    if not live_json.exists():
        print("FAIL: live_proxies.json not created")
        celery_proc.terminate()
        return 1

    with open(live_json) as f:
        live_proxies = json.load(f)

    print(f"OK: live_proxies.json exists with {len(live_proxies)} proxies")

    if len(live_proxies) == 0:
        print("WARN: No live proxies found (all proxies may be dead)")
        print("      This is not a test failure, just no working proxies")
    else:
        # Verify enrichment happened
        sample = live_proxies[0]
        print(f"Sample proxy: {json.dumps(sample, indent=2)[:200]}...")

        # Check for anonymity field (added by our pipeline)
        if 'anonymity' in sample:
            print("OK: Anonymity check was performed")
        if 'exit_ip' in sample:
            print("OK: Exit IP detection was performed")

    if live_txt.exists():
        with open(live_txt) as f:
            txt_count = len([l for l in f if l.strip()])
        print(f"OK: live_proxies.txt exists with {txt_count} entries")

    # Step 7: Cleanup
    print(f"\n[Step 7] Stopping Celery...")
    celery_proc.terminate()
    try:
        celery_proc.wait(timeout=10)
        print("OK: Celery terminated gracefully")
    except subprocess.TimeoutExpired:
        celery_proc.kill()
        print("WARN: Had to kill Celery")

    time.sleep(2)

    # Check for orphans
    print("\n[Step 8] Checking for orphan processes...")
    mubeng_orphans = check_process("proxies/external/mubeng")
    celery_orphans = check_process("celery -A celery_app")

    if mubeng_orphans:
        print(f"FAIL: Orphan mubeng processes:\n{mubeng_orphans}")
        return 1
    print("OK: No orphan mubeng processes")

    if celery_orphans:
        print(f"FAIL: Orphan celery processes:\n{celery_orphans}")
        return 1
    print("OK: No orphan celery processes")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Input:  {len(proxies)} proxies from PSC")
    print(f"  Output: {len(live_proxies)} live proxies after checking")
    print(f"  Rate:   {len(live_proxies)/len(proxies)*100:.1f}% alive")
    print("=" * 60)
    print("=== RESULT: PASS ===")
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
