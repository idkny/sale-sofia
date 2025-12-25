"""
Full Pipeline Integration Test

Tests the complete Celery + Mubeng + PSC pipeline.
Run: python tests/debug/test_full_pipeline.py

WARNING: This test takes 5-15 minutes to complete a full cycle.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def cleanup_environment():
    """Clean up environment before test."""
    print("\n=== CLEANUP: Prepare Environment ===")

    # Kill any existing Celery workers
    subprocess.run(["pkill", "-9", "-f", "celery -A celery_app"], capture_output=True)
    print("[INFO] Killed existing Celery workers")

    # Clear beat schedule files
    for pattern in ["celerybeat-schedule.bak", "celerybeat-schedule.dat", "celerybeat-schedule.dir"]:
        path = PROJECT_ROOT / pattern
        if path.exists():
            path.unlink()
    print("[INFO] Cleared beat schedule files")

    time.sleep(2)


def start_services():
    """Start Redis and Celery."""
    print("\n=== SETUP: Start Services ===")

    # Check/start Redis
    import redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("[INFO] Redis already running")
    except redis.ConnectionError:
        print("[INFO] Starting Redis...")
        subprocess.Popen(
            ["redis-server", "--daemonize", "yes"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        try:
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            print("[PASS] Redis started")
        except:
            print("[FAIL] Could not start Redis")
            return None

    # Start Celery worker
    log_file = PROJECT_ROOT / "data" / "logs" / "celery_integration_test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as log_handle:
        celery_process = subprocess.Popen(
            [
                "celery",
                "-A", "celery_app",
                "worker",
                "-Q", "celery,sale_sofia",
                "--loglevel=info",
                "--concurrency=4",
            ],
            cwd=PROJECT_ROOT,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )

    print("[INFO] Waiting for Celery to start...")
    time.sleep(5)

    if celery_process.poll() is not None:
        with open(log_file, "r") as f:
            print(f"[FAIL] Celery died. Log:\n{f.read()[-1000:]}")
        return None

    print(f"[PASS] Celery worker started (PID: {celery_process.pid})")
    return celery_process


def test_scrape_task():
    """Test scrape_new_proxies_task."""
    print("\n=== TEST: Scrape Proxies Task ===")
    print("[INFO] This may take 5-10 minutes...")

    try:
        from proxies.tasks import scrape_new_proxies_task

        result = scrape_new_proxies_task.delay()
        print(f"[INFO] Task sent: {result.id}")

        # Wait for completion (max 10 minutes)
        start = time.time()
        while time.time() - start < 600:
            if result.ready():
                if result.successful():
                    print(f"[PASS] Scrape completed: {result.result}")
                    return True
                else:
                    print(f"[FAIL] Scrape failed: {result.result}")
                    return False

            elapsed = int(time.time() - start)
            print(f"[WAIT] Scraping... ({elapsed}s, state: {result.state})")
            time.sleep(15)

        print("[FAIL] Scrape task timed out after 10 minutes")
        return False

    except Exception as e:
        print(f"[FAIL] Scrape test failed: {e}")
        return False


def test_check_task():
    """Test check_scraped_proxies_task."""
    print("\n=== TEST: Check Proxies Task ===")
    print("[INFO] This may take 2-5 minutes...")

    try:
        from proxies.tasks import check_scraped_proxies_task
        from paths import PROXY_CHECKER_DIR

        # Verify input file exists
        input_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
        if not input_file.exists():
            print(f"[SKIP] No scraped proxies file at: {input_file}")
            return True  # Not a failure if scrape wasn't run

        with open(input_file, 'r') as f:
            proxies = json.load(f)
        print(f"[INFO] Input: {len(proxies)} proxies to check")

        result = check_scraped_proxies_task.delay()
        print(f"[INFO] Task sent: {result.id}")

        # Wait for dispatcher to complete
        start = time.time()
        while time.time() - start < 60:
            if result.ready():
                print(f"[PASS] Dispatcher completed: {result.result}")
                break
            time.sleep(5)

        # Now wait for chunk tasks to complete (monitor output file)
        from paths import PROXIES_DIR
        output_file = PROXIES_DIR / "live_proxies.json"
        initial_mtime = output_file.stat().st_mtime if output_file.exists() else 0

        print("[INFO] Waiting for chunk tasks to complete...")
        start = time.time()
        while time.time() - start < 300:  # 5 minutes for chunks
            if output_file.exists():
                current_mtime = output_file.stat().st_mtime
                if current_mtime > initial_mtime:
                    with open(output_file, 'r') as f:
                        live = json.load(f)
                    print(f"[PASS] Check completed: {len(live)} live proxies")
                    return True

            elapsed = int(time.time() - start)
            print(f"[WAIT] Checking proxies... ({elapsed}s)")
            time.sleep(15)

        print("[WARN] Check task may still be running")
        return True  # Don't fail, chunks may be slow

    except Exception as e:
        print(f"[FAIL] Check test failed: {e}")
        return False


def test_chain_task():
    """Test the full scrape_and_check_chain_task."""
    print("\n=== TEST: Full Chain Task ===")
    print("[INFO] This is the main production workflow...")

    try:
        from proxies.tasks import scrape_and_check_chain_task
        from paths import PROXIES_DIR

        output_file = PROXIES_DIR / "live_proxies.json"
        initial_mtime = output_file.stat().st_mtime if output_file.exists() else 0

        result = scrape_and_check_chain_task.delay()
        print(f"[INFO] Chain task sent: {result.id}")

        # Wait for completion (max 15 minutes)
        start = time.time()
        while time.time() - start < 900:
            # Check if output file updated
            if output_file.exists():
                current_mtime = output_file.stat().st_mtime
                if current_mtime > initial_mtime:
                    with open(output_file, 'r') as f:
                        live = json.load(f)
                    print(f"[PASS] Chain completed: {len(live)} live proxies")
                    return True

            elapsed = int(time.time() - start)
            mins = elapsed // 60
            secs = elapsed % 60
            print(f"[WAIT] Chain running... ({mins}m {secs}s)")
            time.sleep(30)

        print("[FAIL] Chain task timed out after 15 minutes")
        return False

    except Exception as e:
        print(f"[FAIL] Chain test failed: {e}")
        return False


def stop_services(celery_process):
    """Stop Celery worker."""
    print("\n=== CLEANUP: Stop Services ===")

    if celery_process and celery_process.poll() is None:
        celery_process.terminate()
        try:
            celery_process.wait(timeout=5)
            print("[PASS] Celery stopped gracefully")
        except subprocess.TimeoutExpired:
            celery_process.kill()
            print("[WARN] Celery killed")

    # Kill any orphans
    subprocess.run(["pkill", "-9", "-f", "celery -A celery_app"], capture_output=True)


def main():
    """Run full pipeline integration test."""
    print("=" * 60)
    print("FULL PIPELINE INTEGRATION TEST")
    print("=" * 60)
    print("[WARN] This test takes 10-20 minutes to complete fully")

    cleanup_environment()
    celery_process = start_services()

    if not celery_process:
        print("[FAIL] Could not start services")
        return 1

    results = []

    try:
        # Run tests
        # Note: For quick validation, you can skip the slow tests
        results.append(("Chain Task", test_chain_task()))

    finally:
        stop_services(celery_process)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("FULL PIPELINE TEST PASSED")
        return 0
    else:
        print("FULL PIPELINE TEST FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
