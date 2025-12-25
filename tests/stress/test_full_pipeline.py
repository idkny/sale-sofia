#!/usr/bin/env python3
"""
Test 2.3: Full Pipeline End-to-End

PURPOSE:
--------
This test validates the COMPLETE proxy refresh pipeline from start to finish.
It triggers `scrape_and_check_chain_task` which orchestrates:
1. PSC scrape (3-5 min)
2. Dispatcher splits proxies into chunks
3. Mubeng workers check chunks in parallel
4. Callback aggregates results and saves to live_proxies.json

WHY THIS TEST EXISTS:
---------------------
Previous tests verified individual handoffs:
- Test 2.2.5: Celery + PSC (scraping works)
- Test 2.2.6: PSC → Dispatcher → Mubeng (data flow works)

This test verifies:
1. The chain task correctly sequences scrape → check
2. The entire pipeline completes successfully
3. Dynamic timeout calculation works for varying proxy counts
4. No orphan processes after completion

TIMING CONSIDERATIONS (per spec 105):
-------------------------------------
- PSC scrape: 3-5 minutes
- Chunk processing: (proxies / 100 / workers) * 90s * 1.5
- Total: PSC time + chunk time + buffer
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
             if line and 'test_full_pipeline' not in line]
    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("Test 2.3: Full Pipeline End-to-End")
    print("=" * 60)
    print("\nPURPOSE: Validate complete proxy refresh pipeline")
    print("- PSC scrape → Dispatcher → Mubeng chunks → Result save")
    print("- Tests the chain task that Celery Beat triggers every 6h")
    print("=" * 60)

    from paths import PROXY_CHECKER_DIR, PROXIES_DIR

    # Step 1: Clear ALL previous results (force fresh run)
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
    log_file = Path(PROJECT_DIR) / "data" / "logs" / "celery_full_pipeline_test.log"
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

    # Step 3: Trigger the full chain task
    print(f"\n[Step 3] Triggering scrape_and_check_chain_task...")
    from proxies.tasks import scrape_and_check_chain_task

    chain_result = scrape_and_check_chain_task.delay()
    print(f"Chain Task ID: {chain_result.id}")

    # Step 4: Wait for PSC scrape phase
    print(f"\n[Step 4] Waiting for PSC scrape phase...")
    print("(PSC typically takes 3-5 minutes)")
    psc_timeout = 360  # 6 minutes max for PSC
    start_time = time.time()

    while time.time() - start_time < psc_timeout:
        elapsed = int(time.time() - start_time)

        # Check if PSC output exists
        if psc_output.exists():
            try:
                with open(psc_output) as f:
                    proxies = json.load(f)
                if len(proxies) > 0:
                    print(f"  [{elapsed}s] PSC complete: {len(proxies)} proxies scraped")
                    break
            except (json.JSONDecodeError, IOError):
                pass

        # Check log for progress
        if log_file.exists():
            with open(log_file) as f:
                log_content = f.read()
            if "Scraped" in log_content and "potential proxies" in log_content:
                # Extract count from log
                import re
                match = re.search(r"Scraped (\d+) potential proxies", log_content)
                if match:
                    print(f"  [{elapsed}s] PSC complete (from log): {match.group(1)} proxies")
                    break

        print(f"  [{elapsed}s] PSC running...")
        time.sleep(15)
    else:
        print(f"FAIL: PSC phase timed out after {psc_timeout}s")
        celery_proc.terminate()
        return 1

    # Verify PSC output
    if not psc_output.exists():
        print("FAIL: PSC output file not created")
        celery_proc.terminate()
        return 1

    with open(psc_output) as f:
        all_proxies = json.load(f)
    print(f"OK: PSC scraped {len(all_proxies)} proxies")

    # Step 5: Wait for chunk processing (dynamic timeout per spec 105)
    chunk_size = 100
    workers = 4
    time_per_chunk = 90  # seconds
    num_chunks = (len(all_proxies) + chunk_size - 1) // chunk_size
    num_rounds = (num_chunks + workers - 1) // workers
    calculated_timeout = num_rounds * time_per_chunk * 1.5
    chunk_timeout = max(calculated_timeout, 300)  # minimum 5 minutes

    print(f"\n[Step 5] Waiting for chunk processing...")
    print(f"(Dynamic timeout: {len(all_proxies)} proxies → {num_chunks} chunks → {num_rounds} rounds → {int(chunk_timeout)}s)")
    start_time = time.time()

    while time.time() - start_time < chunk_timeout:
        elapsed = int(time.time() - start_time)

        # Check if final results exist
        if live_json.exists():
            try:
                with open(live_json) as f:
                    live_proxies = json.load(f)
                print(f"  [{elapsed}s] Results ready: {len(live_proxies)} live proxies!")
                break
            except (json.JSONDecodeError, IOError):
                print(f"  [{elapsed}s] Results file being written...")

        # Monitor progress via log
        if log_file.exists():
            with open(log_file) as f:
                log_content = f.read()
            succeeded = log_content.count("succeeded in")
            dispatched = log_content.count("Dispatched")
            print(f"  [{elapsed}s] ~{succeeded}/{num_chunks} chunks completed...")

        time.sleep(15)
    else:
        print(f"WARN: Chunk processing timed out after {int(chunk_timeout)}s, checking partial results...")

    # Step 6: Verify final results
    print(f"\n[Step 6] Verifying results...")

    if not live_json.exists():
        print("FAIL: live_proxies.json not created")
        # Check log for errors
        if log_file.exists():
            with open(log_file) as f:
                log_content = f.read()
            if "Error" in log_content or "error" in log_content:
                print("\nErrors found in log:")
                for line in log_content.split('\n'):
                    if 'error' in line.lower():
                        print(f"  {line[:200]}")
        celery_proc.terminate()
        return 1

    with open(live_json) as f:
        live_proxies = json.load(f)

    print(f"OK: live_proxies.json exists with {len(live_proxies)} proxies")

    if len(live_proxies) == 0:
        print("WARN: No live proxies found (all proxies may be dead)")
        print("      This is not a test failure, just no working proxies")
    else:
        # Verify enrichment
        sample = live_proxies[0]
        print(f"Sample proxy: {json.dumps(sample, indent=2)[:300]}...")

        checks_performed = []
        if 'anonymity' in sample:
            checks_performed.append("anonymity")
        if 'exit_ip' in sample:
            checks_performed.append("exit_ip")
        if 'ip_check_passed' in sample:
            checks_performed.append("quality")
        print(f"OK: Enrichment checks performed: {', '.join(checks_performed) or 'none'}")

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

    # Step 8: Check for orphans
    print("\n[Step 8] Checking for orphan processes...")
    orphan_checks = [
        ("proxy-scraper-checker", "PSC"),
        ("proxies/external/mubeng", "mubeng"),
        ("celery -A celery_app", "celery"),
    ]

    orphans_found = False
    for pattern, name in orphan_checks:
        orphans = check_process(pattern)
        if orphans:
            print(f"FAIL: Orphan {name} processes:\n{orphans}")
            orphans_found = True
        else:
            print(f"OK: No orphan {name} processes")

    if orphans_found:
        return 1

    # Summary
    total_time = int(time.time() - start_time)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Input:  {len(all_proxies)} proxies scraped by PSC")
    print(f"  Output: {len(live_proxies)} live proxies after checking")
    if len(all_proxies) > 0:
        print(f"  Rate:   {len(live_proxies)/len(all_proxies)*100:.1f}% alive")
    print(f"  Time:   {total_time}s total (excluding PSC phase)")
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
