#!/usr/bin/env python3
"""
Scraping Mode Performance Benchmark

Compares sequential vs parallel scraping performance using mocked fetchers.
No live network calls - simulates realistic timing via configurable delays.

Usage:
    python tests/stress/benchmark_scraping_modes.py
    python tests/stress/benchmark_scraping_modes.py --urls 200 --delay 300
"""

import argparse
import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scraping.metrics import MetricsCollector, RequestStatus

# Configuration defaults
DEFAULT_URL_COUNTS = [50, 100, 200]
DEFAULT_RESPONSE_TIME_MS = 500
DEFAULT_PARALLEL_WORKERS = 8
DEFAULT_SUCCESS_RATE = 0.95  # 95% success rate

LOG_FILE = Path(__file__).parent / "benchmark_results.log"


def log(message: str, also_print: bool = True) -> None:
    """Write to log file and optionally print to console."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted = f"[{timestamp}] {message}"
    if also_print:
        print(formatted)
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")


def generate_test_urls(count: int) -> list[str]:
    """Generate mock URLs for testing."""
    return [f"https://example.com/listing/{i}" for i in range(count)]


def simulate_fetch_delay(delay_ms: float, success_rate: float) -> tuple[bool, float]:
    """
    Simulate network fetch with delay.

    Returns:
        (success, actual_delay_ms)
    """
    import random

    # Add 10% jitter to delay
    jitter = delay_ms * 0.1 * (random.random() * 2 - 1)
    actual_delay = max(0, delay_ms + jitter)

    time.sleep(actual_delay / 1000.0)

    success = random.random() < success_rate
    return success, actual_delay


async def simulate_fetch_delay_async(
    delay_ms: float, success_rate: float
) -> tuple[bool, float]:
    """Async version of fetch delay simulation."""
    import random

    jitter = delay_ms * 0.1 * (random.random() * 2 - 1)
    actual_delay = max(0, delay_ms + jitter)

    await asyncio.sleep(actual_delay / 1000.0)

    success = random.random() < success_rate
    return success, actual_delay


def run_sequential_benchmark(
    urls: list[str],
    delay_ms: float,
    success_rate: float,
) -> dict:
    """
    Run sequential scraping benchmark.

    Processes URLs one-by-one, simulating network delay for each.
    """
    metrics = MetricsCollector(run_id="sequential_benchmark")
    metrics.start_run()

    start_time = time.perf_counter()
    total_response_time = 0.0

    for url in urls:
        domain = "example.com"
        metrics.record_request(url, domain)

        success, response_time = simulate_fetch_delay(delay_ms, success_rate)
        total_response_time += response_time

        if success:
            metrics.record_response(
                url=url,
                status=RequestStatus.SUCCESS,
                response_code=200,
                response_time_ms=response_time,
            )
        else:
            metrics.record_response(
                url=url,
                status=RequestStatus.FAILED,
                response_code=500,
                response_time_ms=response_time,
                error_type="SimulatedError",
            )

    elapsed = time.perf_counter() - start_time
    run_metrics = metrics.end_run()

    return {
        "mode": "Sequential",
        "urls_count": len(urls),
        "elapsed_seconds": elapsed,
        "urls_per_second": len(urls) / elapsed if elapsed > 0 else 0,
        "success_count": run_metrics.successful,
        "failed_count": run_metrics.failed,
        "success_rate": metrics.success_rate,
        "avg_response_ms": total_response_time / len(urls) if urls else 0,
    }


async def run_parallel_async_benchmark(
    urls: list[str],
    delay_ms: float,
    success_rate: float,
    max_concurrent: int,
) -> dict:
    """
    Run parallel async scraping benchmark.

    Uses asyncio.Semaphore to control concurrency.
    """
    metrics = MetricsCollector(run_id="parallel_async_benchmark")
    metrics.start_run()

    semaphore = asyncio.Semaphore(max_concurrent)
    response_times = []

    async def fetch_url(url: str) -> None:
        async with semaphore:
            domain = "example.com"
            metrics.record_request(url, domain)

            success, response_time = await simulate_fetch_delay_async(
                delay_ms, success_rate
            )
            response_times.append(response_time)

            if success:
                metrics.record_response(
                    url=url,
                    status=RequestStatus.SUCCESS,
                    response_code=200,
                    response_time_ms=response_time,
                )
            else:
                metrics.record_response(
                    url=url,
                    status=RequestStatus.FAILED,
                    response_code=500,
                    response_time_ms=response_time,
                    error_type="SimulatedError",
                )

    start_time = time.perf_counter()
    await asyncio.gather(*[fetch_url(url) for url in urls])
    elapsed = time.perf_counter() - start_time

    run_metrics = metrics.end_run()

    return {
        "mode": "Parallel (async)",
        "urls_count": len(urls),
        "elapsed_seconds": elapsed,
        "urls_per_second": len(urls) / elapsed if elapsed > 0 else 0,
        "success_count": run_metrics.successful,
        "failed_count": run_metrics.failed,
        "success_rate": metrics.success_rate,
        "avg_response_ms": sum(response_times) / len(response_times) if response_times else 0,
        "workers": max_concurrent,
    }


def run_parallel_threads_benchmark(
    urls: list[str],
    delay_ms: float,
    success_rate: float,
    max_workers: int,
) -> dict:
    """
    Run parallel thread-pool scraping benchmark.

    Uses ThreadPoolExecutor to simulate Celery-like worker pattern.
    """
    metrics = MetricsCollector(run_id="parallel_threads_benchmark")
    metrics.start_run()

    response_times = []
    lock = __import__("threading").Lock()

    def fetch_url(url: str) -> None:
        domain = "example.com"
        with lock:
            metrics.record_request(url, domain)

        success, response_time = simulate_fetch_delay(delay_ms, success_rate)

        with lock:
            response_times.append(response_time)
            if success:
                metrics.record_response(
                    url=url,
                    status=RequestStatus.SUCCESS,
                    response_code=200,
                    response_time_ms=response_time,
                )
            else:
                metrics.record_response(
                    url=url,
                    status=RequestStatus.FAILED,
                    response_code=500,
                    response_time_ms=response_time,
                    error_type="SimulatedError",
                )

    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_url, url) for url in urls]
        for future in as_completed(futures):
            future.result()  # Propagate any exceptions

    elapsed = time.perf_counter() - start_time
    run_metrics = metrics.end_run()

    return {
        "mode": "Parallel (threads)",
        "urls_count": len(urls),
        "elapsed_seconds": elapsed,
        "urls_per_second": len(urls) / elapsed if elapsed > 0 else 0,
        "success_count": run_metrics.successful,
        "failed_count": run_metrics.failed,
        "success_rate": metrics.success_rate,
        "avg_response_ms": sum(response_times) / len(response_times) if response_times else 0,
        "workers": max_workers,
    }


def check_celery_available() -> bool:
    """Check if Celery worker is available."""
    try:
        from celery_app import celery_app

        # Try to ping the worker with a very short timeout
        inspector = celery_app.control.inspect(timeout=1.0)
        active = inspector.active()
        return active is not None and len(active) > 0
    except Exception:
        return False


def run_celery_benchmark(
    urls: list[str],
    delay_ms: float,
    success_rate: float,
    chunk_size: int = 25,
) -> dict | None:
    """
    Run Celery-based parallel benchmark (if Celery is available).

    Returns None if Celery is not running.
    """
    if not check_celery_available():
        return None

    # This would be the actual Celery implementation
    # For now, we simulate it with thread pool
    log("Celery available - using actual Celery tasks")

    # TODO: Implement actual Celery task dispatch when needed
    # For benchmark purposes, thread simulation is sufficient
    return None


def format_results_table(results: list[dict], url_count: int) -> str:
    """Format benchmark results as ASCII table."""
    lines = []
    lines.append(f"\nResults for {url_count} URLs:")
    lines.append("-" * 60)
    lines.append(
        f"| {'Mode':<18} | {'Time (s)':<10} | {'URLs/sec':<10} | {'Speedup':<8} |"
    )
    lines.append("|" + "-" * 20 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 10 + "|")

    # Find sequential baseline for speedup calculation
    sequential = next((r for r in results if r["mode"] == "Sequential"), None)
    baseline_time = sequential["elapsed_seconds"] if sequential else 1.0

    for r in results:
        speedup = baseline_time / r["elapsed_seconds"] if r["elapsed_seconds"] > 0 else 0
        lines.append(
            f"| {r['mode']:<18} | {r['elapsed_seconds']:<10.2f} | "
            f"{r['urls_per_second']:<10.2f} | {speedup:<7.1f}x |"
        )

    lines.append("-" * 60)
    return "\n".join(lines)


def run_benchmark_suite(
    url_counts: list[int],
    delay_ms: float,
    parallel_workers: int,
    success_rate: float,
) -> None:
    """Run complete benchmark suite and output results."""

    # Clear log file
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        f.write(f"=== Scraping Performance Benchmark Started at {datetime.now()} ===\n\n")

    # Header
    log("")
    log("=" * 60)
    log("=== Scraping Performance Benchmark ===")
    log("=" * 60)
    log("")
    log("Configuration:")
    log(f"  - URL counts: {url_counts}")
    log(f"  - Simulated response time: {delay_ms}ms")
    log(f"  - Parallel workers: {parallel_workers}")
    log(f"  - Success rate: {success_rate * 100:.0f}%")
    log("")

    # Check Celery availability
    celery_available = check_celery_available()
    if celery_available:
        log("  - Celery: AVAILABLE (workers detected)")
    else:
        log("  - Celery: NOT AVAILABLE (using thread simulation)")
    log("")

    all_results = []

    for url_count in url_counts:
        log(f"\n--- Benchmarking with {url_count} URLs ---")
        urls = generate_test_urls(url_count)

        # Sequential benchmark
        log(f"Running sequential mode...")
        seq_result = run_sequential_benchmark(urls, delay_ms, success_rate)
        log(f"  Sequential: {seq_result['elapsed_seconds']:.2f}s ({seq_result['urls_per_second']:.2f} URLs/s)")

        # Parallel async benchmark
        log(f"Running parallel async mode ({parallel_workers} workers)...")
        async_result = asyncio.run(
            run_parallel_async_benchmark(urls, delay_ms, success_rate, parallel_workers)
        )
        log(f"  Parallel (async): {async_result['elapsed_seconds']:.2f}s ({async_result['urls_per_second']:.2f} URLs/s)")

        # Parallel threads benchmark
        log(f"Running parallel threads mode ({parallel_workers} workers)...")
        thread_result = run_parallel_threads_benchmark(
            urls, delay_ms, success_rate, parallel_workers
        )
        log(f"  Parallel (threads): {thread_result['elapsed_seconds']:.2f}s ({thread_result['urls_per_second']:.2f} URLs/s)")

        results = [seq_result, async_result, thread_result]

        # Celery benchmark (if available)
        if celery_available:
            celery_result = run_celery_benchmark(urls, delay_ms, success_rate)
            if celery_result:
                results.append(celery_result)
                log(f"  Celery: {celery_result['elapsed_seconds']:.2f}s ({celery_result['urls_per_second']:.2f} URLs/s)")

        all_results.append((url_count, results))

        # Print table for this URL count
        table = format_results_table(results, url_count)
        log(table)

    # Summary
    log("\n" + "=" * 60)
    log("=== SUMMARY ===")
    log("=" * 60)

    # Print final summary table
    log("\n" + "=" * 75)
    log(f"| {'URLs':<6} | {'Sequential':<14} | {'Async':<14} | {'Threads':<14} | {'Best Speedup':<12} |")
    log("|" + "-" * 8 + "|" + "-" * 16 + "|" + "-" * 16 + "|" + "-" * 16 + "|" + "-" * 14 + "|")

    for url_count, results in all_results:
        seq = next((r for r in results if r["mode"] == "Sequential"), None)
        async_r = next((r for r in results if r["mode"] == "Parallel (async)"), None)
        thread = next((r for r in results if r["mode"] == "Parallel (threads)"), None)

        seq_time = seq["elapsed_seconds"] if seq else 0
        async_time = async_r["elapsed_seconds"] if async_r else 0
        thread_time = thread["elapsed_seconds"] if thread else 0

        best_parallel = min(async_time, thread_time) if async_time and thread_time else 0
        speedup = seq_time / best_parallel if best_parallel > 0 else 0

        log(
            f"| {url_count:<6} | {seq_time:<13.2f}s | {async_time:<13.2f}s | "
            f"{thread_time:<13.2f}s | {speedup:<11.1f}x |"
        )

    log("=" * 75)
    log("")
    log(f"Full results saved to: {LOG_FILE}")
    log("")

    # Theoretical vs actual comparison
    log("Theoretical Analysis:")
    theoretical_seq = (url_counts[-1] * delay_ms) / 1000
    theoretical_parallel = (url_counts[-1] * delay_ms) / 1000 / parallel_workers
    log(f"  - Theoretical sequential time ({url_counts[-1]} URLs): {theoretical_seq:.2f}s")
    log(f"  - Theoretical parallel time ({parallel_workers} workers): {theoretical_parallel:.2f}s")
    log(f"  - Max theoretical speedup: {parallel_workers}x")
    log("")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark sequential vs parallel scraping modes"
    )
    parser.add_argument(
        "--urls",
        type=int,
        nargs="+",
        default=DEFAULT_URL_COUNTS,
        help=f"URL counts to test (default: {DEFAULT_URL_COUNTS})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_RESPONSE_TIME_MS,
        help=f"Simulated response time in ms (default: {DEFAULT_RESPONSE_TIME_MS})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_PARALLEL_WORKERS,
        help=f"Number of parallel workers (default: {DEFAULT_PARALLEL_WORKERS})",
    )
    parser.add_argument(
        "--success-rate",
        type=float,
        default=DEFAULT_SUCCESS_RATE,
        help=f"Simulated success rate 0-1 (default: {DEFAULT_SUCCESS_RATE})",
    )

    args = parser.parse_args()

    run_benchmark_suite(
        url_counts=args.urls,
        delay_ms=args.delay,
        parallel_workers=args.workers,
        success_rate=args.success_rate,
    )


if __name__ == "__main__":
    main()
