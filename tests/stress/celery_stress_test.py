#!/usr/bin/env python3
"""
Celery Stress Test Suite
Tests graceful/ungraceful shutdown, multiple workers, and beat schedule corruption
"""

import subprocess
import time
import os
import signal
import sys
from datetime import datetime
import shelve

LOG_FILE = "celery_stress_test_results.log"

def log(message):
    """Write to both console and log file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, 'a') as f:
        f.write(formatted + '\n')

def count_celery():
    """Count running celery processes"""
    try:
        result = subprocess.run(
            ['pgrep', '-c', '-f', 'celery'],
            capture_output=True,
            text=True
        )
        return int(result.stdout.strip()) if result.returncode == 0 else 0
    except:
        return 0

def list_celery():
    """List all celery processes"""
    try:
        result = subprocess.run(
            ['pgrep', '-af', 'celery'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.stdout else "No celery processes"
    except:
        return "Error listing processes"

def cleanup():
    """Kill all celery processes"""
    log("Cleaning up any remaining processes...")
    try:
        subprocess.run(['pkill', '-9', '-f', 'celery -A celery_app'],
                      stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass

def test_1_graceful_shutdown():
    """Test 1: Graceful Start/Stop Cycle (5 times)"""
    log("")
    log("=" * 60)
    log("TEST 1: Graceful Start/Stop Cycle (5 times)")
    log("=" * 60)

    results = []

    for i in range(1, 6):
        log("")
        log(f"=== Cycle {i}: Graceful Shutdown ===")

        # Start celery worker
        proc = subprocess.Popen(
            ['celery', '-A', 'celery_app', 'worker', '-Q', 'celery,sale_sofia',
             '--loglevel=info'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log(f"Started Celery worker with PID: {proc.pid}")

        time.sleep(5)

        # Check process count before shutdown
        before_count = count_celery()
        log(f"Celery processes before shutdown: {before_count}")
        log(list_celery())

        # Graceful shutdown
        log(f"Sending SIGTERM to PID {proc.pid}...")
        try:
            proc.terminate()
            exit_code = proc.wait(timeout=10)
            log(f"Exit code: {exit_code}")
        except subprocess.TimeoutExpired:
            log("Process didn't terminate gracefully, killing...")
            proc.kill()
            exit_code = proc.wait()
            log(f"Forced exit code: {exit_code}")

        time.sleep(2)

        # Check for orphans
        after_count = count_celery()
        log(f"Celery processes after shutdown: {after_count}")

        if after_count == 0:
            log("✓ No orphans detected")
            results.append("PASS")
        else:
            log("✗ ORPHANS DETECTED:")
            log(list_celery())
            results.append("FAIL")

        time.sleep(2)

    return results

def test_2_ungraceful_shutdown():
    """Test 2: Ungraceful Shutdown (SIGKILL) - 3 cycles"""
    log("")
    log("=" * 60)
    log("TEST 2: Ungraceful Shutdown (SIGKILL) - 3 cycles")
    log("=" * 60)

    results = []

    for i in range(1, 4):
        log("")
        log(f"=== Cycle {i}: Ungraceful Shutdown ===")

        # Start celery worker
        proc = subprocess.Popen(
            ['celery', '-A', 'celery_app', 'worker', '-Q', 'celery,sale_sofia',
             '--loglevel=info'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log(f"Started Celery worker with PID: {proc.pid}")

        time.sleep(5)

        # Check process count before kill
        before_count = count_celery()
        log(f"Celery processes before SIGKILL: {before_count}")
        log(list_celery())

        # Ungraceful shutdown
        log(f"Sending SIGKILL to PID {proc.pid}...")
        try:
            proc.kill()
            proc.wait()
        except:
            pass

        time.sleep(2)

        # Check for orphans
        after_count = count_celery()
        log(f"Celery processes after SIGKILL: {after_count}")
        log(f"Orphan count: {after_count}")

        if after_count > 0:
            log("✗ ORPHANS DETECTED:")
            log(list_celery())
            results.append(f"FAIL - {after_count} orphans")
        else:
            log("✓ No orphans detected")
            results.append("PASS")

        # Cleanup orphans for next cycle
        cleanup()

    return results

def test_3_multiple_workers():
    """Test 3: Multiple Celery Processes (5 workers)"""
    log("")
    log("=" * 60)
    log("TEST 3: Multiple Celery Processes (5 workers)")
    log("=" * 60)

    log("")
    log("=== Starting 5 Celery workers simultaneously ===")

    procs = []
    for i in range(1, 6):
        proc = subprocess.Popen(
            ['celery', '-A', 'celery_app', 'worker', '-Q', 'celery,sale_sofia',
             '--loglevel=info'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        procs.append(proc)
        log(f"Started worker {i} with PID: {proc.pid}")

    time.sleep(10)

    log("")
    log("Running workers:")
    log(list_celery())
    total_processes = count_celery()
    log(f"Total celery processes: {total_processes}")

    log("")
    log("Checking Redis queue state...")
    try:
        result = subprocess.run(['redis-cli', 'LLEN', 'celery'],
                              capture_output=True, text=True)
        celery_queue = result.stdout.strip()
        log(f"Celery queue length: {celery_queue}")

        result = subprocess.run(['redis-cli', 'LLEN', 'sale_sofia'],
                              capture_output=True, text=True)
        sofia_queue = result.stdout.strip()
        log(f"sale_sofia queue length: {sofia_queue}")
    except Exception as e:
        log(f"Error checking Redis: {e}")

    log("")
    log("Cleaning up all workers...")
    subprocess.run(['pkill', '-9', '-f', 'celery -A celery_app'],
                  stderr=subprocess.DEVNULL)
    time.sleep(2)

    after_cleanup = count_celery()
    if after_cleanup == 0:
        log("✓ All workers cleaned successfully")
        return "PASS"
    else:
        log(f"✗ Cleanup incomplete. Remaining processes: {after_cleanup}")
        log(list_celery())
        return f"FAIL - {after_cleanup} remaining"

def test_4_beat_corruption():
    """Test 4: Beat Schedule Corruption Check"""
    log("")
    log("=" * 60)
    log("TEST 4: Beat Schedule Corruption Check")
    log("=" * 60)

    log("")
    log("=== Starting Celery with Beat ===")

    # Remove old schedule files
    for pattern in ['celerybeat-schedule', 'celerybeat-schedule.db',
                   'celerybeat-schedule.dir', 'celerybeat-schedule.bak',
                   'celerybeat-schedule.dat']:
        try:
            if os.path.exists(pattern):
                os.remove(pattern)
        except:
            pass
    log("Removed old schedule files")

    # Start celery with beat
    proc = subprocess.Popen(
        ['celery', '-A', 'celery_app', 'worker', '--beat', '-Q',
         'celery,sale_sofia', '--loglevel=info'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    log(f"Started Celery with Beat, PID: {proc.pid}")

    time.sleep(10)

    log("")
    log("Schedule files created:")
    try:
        for pattern in ['celerybeat-schedule', 'celerybeat-schedule.db',
                       'celerybeat-schedule.dir', 'celerybeat-schedule.bak',
                       'celerybeat-schedule.dat']:
            if os.path.exists(pattern):
                stat = os.stat(pattern)
                log(f"  {pattern}: {stat.st_size} bytes")
    except Exception as e:
        log(f"Error listing files: {e}")

    log("")
    log("Killing ungracefully with SIGKILL...")
    subprocess.run(['pkill', '-9', '-f', 'celery'], stderr=subprocess.DEVNULL)
    time.sleep(2)

    log("")
    log("Schedule files after ungraceful kill:")
    try:
        for pattern in ['celerybeat-schedule', 'celerybeat-schedule.db',
                       'celerybeat-schedule.dir', 'celerybeat-schedule.bak',
                       'celerybeat-schedule.dat']:
            if os.path.exists(pattern):
                stat = os.stat(pattern)
                log(f"  {pattern}: {stat.st_size} bytes")
    except Exception as e:
        log(f"Error listing files: {e}")

    log("")
    log("Checking for file corruption...")
    corruption_detected = False
    try:
        if os.path.exists('celerybeat-schedule.db') or os.path.exists('celerybeat-schedule'):
            s = shelve.open('celerybeat-schedule')
            contents = dict(s)
            log(f"Schedule contents: {contents}")
            s.close()
            log("✓ Schedule file readable (not corrupted)")
            result = "PASS"
        else:
            log("No schedule file to check")
            result = "SKIP"
    except Exception as e:
        log(f"✗ Schedule file corrupted or unreadable: {e}")
        corruption_detected = True
        result = "FAIL"

    return result

def main():
    """Run all stress tests"""
    # Initialize log file
    with open(LOG_FILE, 'w') as f:
        f.write(f"=== Celery Stress Test Started at {datetime.now()} ===\n")

    log(f"Starting Celery stress tests from: {os.getcwd()}")

    # Initial cleanup
    cleanup()

    # Run tests
    test1_results = test_1_graceful_shutdown()
    test2_results = test_2_ungraceful_shutdown()
    test3_result = test_3_multiple_workers()
    test4_result = test_4_beat_corruption()

    # Final cleanup
    cleanup()

    # Summary
    log("")
    log("=" * 60)
    log(f"=== Celery Stress Test Completed at {datetime.now()} ===")
    log("=" * 60)
    log("")
    log("SUMMARY:")
    log(f"Test 1 (Graceful Shutdown): {test1_results}")
    log(f"Test 2 (Ungraceful Shutdown): {test2_results}")
    log(f"Test 3 (Multiple Workers): {test3_result}")
    log(f"Test 4 (Beat Corruption): {test4_result}")
    log("")
    log(f"Full results saved to: {LOG_FILE}")

    print("\n" + "=" * 60)
    print("Test complete! Check the log file for detailed results.")
    print("=" * 60)

if __name__ == '__main__':
    main()
