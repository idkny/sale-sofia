#!/usr/bin/env python3
"""Test if proxy rotator stays running after startup."""

import asyncio
import subprocess
from loguru import logger
from orchestrator import Orchestrator

async def test_proxy_rotator():
    """Test proxy rotator lifecycle."""
    orch = Orchestrator()

    try:
        # Start Redis
        logger.info("Starting Redis...")
        await orch.start_redis()

        # Start Celery
        logger.info("Starting Celery...")
        await orch.start_celery()

        # Wait for proxies
        logger.info("Waiting for proxies...")
        if not await orch.wait_for_proxies(timeout=60):
            logger.error("No proxies available")
            return False

        # Start proxy rotator
        logger.info("Starting proxy rotator...")
        proxy_url = await orch.start_proxy_rotator()
        if not proxy_url:
            logger.error("Failed to start proxy rotator")
            return False

        logger.success(f"Proxy rotator started at: {proxy_url}")

        # Wait a bit
        logger.info("Waiting 5 seconds...")
        await asyncio.sleep(5)

        # Check if still running
        logger.info("Testing proxy connection...")
        result = subprocess.run(
            ["curl", "-s", proxy_url, "--connect-timeout", "2"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.success("Proxy rotator is responding!")
            return True
        else:
            logger.error(f"Proxy rotator not responding (exit code: {result.returncode})")
            logger.error(f"Output: {result.stderr}")
            return False

    finally:
        logger.info("Stopping all processes...")
        await orch.stop_all()

if __name__ == "__main__":
    result = asyncio.run(test_proxy_rotator())
    exit(0 if result else 1)
