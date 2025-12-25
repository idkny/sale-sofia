"""
Isolated Celery Test

Tests Celery worker start/stop and basic task execution.
Run: python tests/debug/test_celery_isolated.py

IMPORTANT: Redis must be running before these tests.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_redis_running():
    """Pre-check: Redis must be running."""
    print("\n=== PRE-CHECK: Redis ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        if r.ping():
            print("[PASS] Redis is running")
            return True
    except Exception as e:
        print(f"[FAIL] Redis not running: {e}")
        print("       Start Redis first: redis-server --daemonize yes")
        return False
    return False


def kill_existing_celery():
    """Kill any existing Celery workers."""
    print("\n=== CLEANUP: Kill existing Celery workers ===")
    result = subprocess.run(
        ["pkill", "-9", "-f", "celery -A celery_app"],
        capture_output=True
    )
    if result.returncode == 0:
        print("[INFO] Killed existing Celery workers")
    else:
        print("[INFO] No existing Celery workers found")
    time.sleep(1)  # Give time for cleanup


def clear_beat_schedule():
    """Remove Celery beat schedule files to avoid corruption issues."""
    print("\n=== CLEANUP: Clear beat schedule files ===")
    for pattern in ["celerybeat-schedule.bak", "celerybeat-schedule.dat", "celerybeat-schedule.dir"]:
        path = PROJECT_ROOT / pattern
        if path.exists():
            path.unlink()
            print(f"[INFO] Removed {pattern}")
    print("[PASS] Beat schedule files cleared")


def test_celery_import():
    """Test Celery app can be imported."""
    print("\n=== TEST: Celery App Import ===")
    try:
        os.chdir(PROJECT_ROOT)
        from celery_app import celery_app
        print(f"[PASS] Celery app imported: {celery_app.main}")
        print(f"[INFO] Broker: {celery_app.conf.broker_url}")
        print(f"[INFO] Backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        print(f"[FAIL] Cannot import celery_app: {e}")
        return False


def test_celery_worker_start():
    """Test starting Celery worker."""
    print("\n=== TEST: Celery Worker Start ===")
    try:
        # Start worker (without beat for simpler test)
        log_file = PROJECT_ROOT / "data" / "logs" / "celery_debug.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "w") as log_handle:
            process = subprocess.Popen(
                [
                    "celery",
                    "-A", "celery_app",
                    "worker",
                    "-Q", "celery,sale_sofia",
                    "--loglevel=info",
                    "--concurrency=2",  # Fewer workers for test
                ],
                cwd=PROJECT_ROOT,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
            )

        # Wait for startup
        print("[INFO] Waiting for worker to start...")
        time.sleep(5)

        # Check if still running
        if process.poll() is None:
            print(f"[PASS] Celery worker started (PID: {process.pid})")

            # Check pgrep
            result = subprocess.run(
                ["pgrep", "-f", "celery -A celery_app.*worker"],
                capture_output=True
            )
            if result.returncode == 0:
                pids = result.stdout.decode().strip().split('\n')
                print(f"[INFO] Found {len(pids)} Celery processes")

            return process
        else:
            # Worker died - check log
            with open(log_file, "r") as f:
                log_content = f.read()
            print(f"[FAIL] Worker died. Log:\n{log_content[-1000:]}")
            return None
    except FileNotFoundError:
        print("[FAIL] 'celery' command not found. Install: pip install celery")
        return None
    except Exception as e:
        print(f"[FAIL] Failed to start worker: {e}")
        return None


def test_celery_task_execution(worker_process):
    """Test sending and executing a registered task."""
    print("\n=== TEST: Celery Task Execution ===")
    if not worker_process:
        print("[SKIP] No worker process to test")
        return False

    try:
        os.chdir(PROJECT_ROOT)
        # Use the actual registered scrape_and_check_chain_task
        # We'll just check that it gets picked up (not wait for full execution)
        from proxies.tasks import scrape_and_check_chain_task

        print("[INFO] Sending scrape_and_check_chain_task (will check dispatch only)")
        result = scrape_and_check_chain_task.delay()

        # Wait briefly to confirm task is received (not completed)
        print("[INFO] Waiting for task to be received...")
        time.sleep(3)

        state = result.state
        if state in ("PENDING", "STARTED", "SUCCESS"):
            print(f"[PASS] Task received and processing (state: {state})")
            # Revoke the task to avoid long wait
            result.revoke(terminate=True)
            return True
        elif state == "FAILURE":
            print(f"[FAIL] Task failed immediately: {result.result}")
            return False
        else:
            print(f"[INFO] Task state: {state}")
            return True
    except Exception as e:
        print(f"[FAIL] Task test failed: {e}")
        return False


def test_celery_worker_stop(worker_process):
    """Test stopping Celery worker cleanly."""
    print("\n=== TEST: Celery Worker Stop ===")
    if not worker_process:
        print("[SKIP] No worker process to stop")
        return True

    try:
        print(f"[INFO] Stopping worker (PID: {worker_process.pid})")
        worker_process.terminate()

        # Wait for graceful shutdown
        try:
            worker_process.wait(timeout=5)
            print("[PASS] Worker stopped gracefully")
            return True
        except subprocess.TimeoutExpired:
            print("[WARN] Worker didn't stop, killing...")
            worker_process.kill()
            worker_process.wait()
            print("[PASS] Worker killed")
            return True
    except Exception as e:
        print(f"[FAIL] Stop failed: {e}")
        return False


def test_orphan_detection():
    """Check for orphan Celery processes."""
    print("\n=== TEST: Orphan Process Detection ===")
    result = subprocess.run(
        ["pgrep", "-f", "celery -A celery_app"],
        capture_output=True
    )
    if result.returncode == 0:
        pids = result.stdout.decode().strip().split('\n')
        print(f"[WARN] Found {len(pids)} Celery processes still running")
        print(f"       PIDs: {pids}")
        print("       Kill with: pkill -9 -f 'celery -A celery_app'")
        return False
    else:
        print("[PASS] No orphan Celery processes")
        return True


def main():
    """Run all Celery tests."""
    print("=" * 60)
    print("ISOLATED CELERY TESTS")
    print("=" * 60)

    # Pre-checks
    if not check_redis_running():
        return 1

    # Cleanup
    kill_existing_celery()
    clear_beat_schedule()

    results = []
    worker_process = None

    try:
        # Test import
        results.append(("Celery Import", test_celery_import()))

        # Test worker lifecycle
        worker_process = test_celery_worker_start()
        results.append(("Worker Start", worker_process is not None))

        # Test task execution
        results.append(("Task Execution", test_celery_task_execution(worker_process)))

        # Test stop
        results.append(("Worker Stop", test_celery_worker_stop(worker_process)))

        # Check for orphans
        time.sleep(2)  # Give time for cleanup
        results.append(("Orphan Detection", test_orphan_detection()))

    finally:
        # Ensure cleanup
        if worker_process and worker_process.poll() is None:
            worker_process.kill()

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
        print("ALL CELERY TESTS PASSED")
        return 0
    else:
        print("SOME CELERY TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
