"""
Async HTTP fetcher using httpx.AsyncClient.

Provides true async I/O for concurrent URL fetching with:
- Per-domain rate limiting via asyncio.Semaphore
- Integration with resilience/rate_limiter.py (acquire_async)
- Circuit breaker and soft block detection
"""

import asyncio

import httpx
from loguru import logger

from config.settings import (
    ASYNC_FETCHER_MAX_CONCURRENT,
    PROXY_TIMEOUT_SECONDS,
)
from resilience.circuit_breaker import extract_domain, get_circuit_breaker
from resilience.exceptions import BlockedException, CircuitOpenException
from resilience.rate_limiter import get_rate_limiter
from resilience.response_validator import detect_soft_block

# Default headers to mimic a browser
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


async def fetch_page(
    url: str,
    proxy: str,
    timeout: float = PROXY_TIMEOUT_SECONDS,
    headers: dict | None = None,
) -> str:
    """
    Fetch a single page asynchronously using httpx.

    Args:
        url: URL to fetch
        proxy: Proxy URL (required, get from ScoredProxyPool)
        timeout: Request timeout in seconds
        headers: Optional custom headers (merged with defaults)

    Returns:
        HTML content as string

    Raises:
        ValueError: If proxy is None
        CircuitOpenException: If circuit breaker is open for domain
        BlockedException: If soft block detected in response
        httpx.HTTPError: On network/HTTP errors
    """
    if not proxy:
        raise ValueError("proxy is required - get from ScoredProxyPool")
    domain = extract_domain(url)
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()

    # Check circuit breaker
    if not circuit_breaker.can_request(domain):
        logger.warning(f"Circuit open for {domain}, skipping {url}")
        raise CircuitOpenException(f"Circuit breaker open for domain: {domain}")

    # Acquire rate limit token
    await rate_limiter.acquire_async(domain)

    # Prepare headers
    request_headers = DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    proxy_url = proxy

    try:
        async with httpx.AsyncClient(
            proxy=proxy_url,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        ) as client:
            logger.debug(f"Fetching {url} via proxy {proxy_url}")
            response = await client.get(url, headers=request_headers)
            response.raise_for_status()
            html = response.text

        # Check for soft blocks
        is_blocked, reason = detect_soft_block(html)
        if is_blocked:
            circuit_breaker.record_failure(domain, block_type=reason)
            logger.warning(f"Soft block detected for {url}: {reason}")
            raise BlockedException(f"Soft block detected: {reason}")

        # Record success
        circuit_breaker.record_success(domain)
        logger.debug(f"Successfully fetched {url} ({len(html)} bytes)")
        return html

    except (CircuitOpenException, BlockedException):
        raise
    except httpx.HTTPStatusError as e:
        circuit_breaker.record_failure(domain, block_type=f"http_{e.response.status_code}")
        logger.error(f"HTTP error {e.response.status_code} for {url}")
        raise
    except httpx.RequestError as e:
        circuit_breaker.record_failure(domain, block_type="network_error")
        logger.error(f"Request error for {url}: {e}")
        raise


async def fetch_pages_concurrent(
    urls: list[str],
    proxy: str,
    max_concurrent: int = ASYNC_FETCHER_MAX_CONCURRENT,
) -> list[tuple[str, str | Exception]]:
    """
    Fetch multiple URLs concurrently with controlled parallelism.

    Args:
        urls: List of URLs to fetch
        proxy: Proxy URL (required, get from ScoredProxyPool)
        max_concurrent: Maximum concurrent requests (default 5)

    Returns:
        List of (url, result) tuples where result is either:
        - HTML content string on success
        - Exception instance on failure
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(url: str) -> tuple[str, str | Exception]:
        async with semaphore:
            try:
                html = await fetch_page(url, proxy=proxy)
                return (url, html)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                return (url, e)

    logger.info(f"Fetching {len(urls)} URLs with max_concurrent={max_concurrent}")
    tasks = [fetch_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)

    # Log summary
    successes = sum(1 for _, r in results if isinstance(r, str))
    failures = len(results) - successes
    logger.info(f"Fetch complete: {successes} succeeded, {failures} failed")

    return results
