"""
Unit tests for scraping/async_fetcher.py

Tests async HTTP fetching with circuit breaker, rate limiting, and soft block detection.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from scraping.async_fetcher import fetch_page, fetch_pages_concurrent
from resilience.exceptions import BlockedException, CircuitOpenException


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker that allows requests by default."""
    with patch('scraping.async_fetcher.get_circuit_breaker') as mock:
        breaker = MagicMock()
        breaker.can_request.return_value = True
        breaker.record_success = MagicMock()
        breaker.record_failure = MagicMock()
        mock.return_value = breaker
        yield breaker


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter that allows immediate requests."""
    with patch('scraping.async_fetcher.get_rate_limiter') as mock:
        limiter = MagicMock()
        limiter.acquire_async = AsyncMock()
        mock.return_value = limiter
        yield limiter


@pytest.fixture
def mock_soft_block_detector():
    """Mock soft block detector that returns no blocks by default."""
    with patch('scraping.async_fetcher.detect_soft_block') as mock:
        mock.return_value = (False, None)
        yield mock


@pytest.mark.asyncio
async def test_fetch_page_success(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test successful page fetch returns HTML content."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "<html><body>test content</body></html>"
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute
        result = await fetch_page("https://example.com/page")

        # Verify
        assert result == "<html><body>test content</body></html>"
        mock_circuit_breaker.can_request.assert_called_once_with("example.com")
        mock_rate_limiter.acquire_async.assert_called_once_with("example.com")
        mock_circuit_breaker.record_success.assert_called_once_with("example.com")
        mock_soft_block_detector.assert_called_once_with("<html><body>test content</body></html>")


@pytest.mark.asyncio
async def test_fetch_page_circuit_breaker_open(mock_circuit_breaker, mock_rate_limiter):
    """Test that CircuitOpenException is raised when circuit breaker is open."""
    # Configure circuit breaker to block requests
    mock_circuit_breaker.can_request.return_value = False

    # Execute and verify exception
    with pytest.raises(CircuitOpenException) as exc_info:
        await fetch_page("https://example.com/page")

    assert "Circuit breaker open for domain: example.com" in str(exc_info.value)
    mock_circuit_breaker.can_request.assert_called_once_with("example.com")
    # Rate limiter should not be called if circuit is open
    mock_rate_limiter.acquire_async.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_page_soft_block_detected(mock_circuit_breaker, mock_rate_limiter):
    """Test that BlockedException is raised when soft block is detected."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        with patch('scraping.async_fetcher.detect_soft_block') as mock_detector:
            # Setup mock response with blocked content
            mock_response = MagicMock()
            mock_response.text = "<html>Access Denied</html>"
            mock_response.raise_for_status = MagicMock()

            # Setup mock client
            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            # Configure soft block detector to detect block
            mock_detector.return_value = (True, "captcha_detected")

            # Execute and verify exception
            with pytest.raises(BlockedException) as exc_info:
                await fetch_page("https://example.com/page")

            assert "Soft block detected: captcha_detected" in str(exc_info.value)
            mock_circuit_breaker.record_failure.assert_called_once_with(
                "example.com", block_type="captcha_detected"
            )
            # Success should not be recorded
            mock_circuit_breaker.record_success.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_page_http_error(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that HTTP errors are handled and circuit breaker records failure."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock response with 403 error
        mock_response = MagicMock()
        mock_response.status_code = 403

        # Setup client to raise HTTPStatusError
        mock_client_instance = MagicMock()
        error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_client_instance.get = AsyncMock(side_effect=error)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute and verify exception
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_page("https://example.com/page")

        mock_circuit_breaker.record_failure.assert_called_once_with(
            "example.com", block_type="http_403"
        )
        mock_circuit_breaker.record_success.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_page_http_error_500(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that server errors (500) are handled correctly."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock response with 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500

        # Setup client to raise HTTPStatusError
        mock_client_instance = MagicMock()
        error = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )
        mock_client_instance.get = AsyncMock(side_effect=error)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute and verify exception
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_page("https://example.com/page")

        mock_circuit_breaker.record_failure.assert_called_once_with(
            "example.com", block_type="http_500"
        )


@pytest.mark.asyncio
async def test_fetch_pages_concurrent_success(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test concurrent fetching of multiple URLs successfully."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock responses for different URLs
        def create_mock_response(content):
            mock_response = MagicMock()
            mock_response.text = content
            mock_response.raise_for_status = MagicMock()
            return mock_response

        # Create different responses for each URL
        responses = [
            create_mock_response("<html>page1</html>"),
            create_mock_response("<html>page2</html>"),
            create_mock_response("<html>page3</html>"),
        ]

        # Setup mock client to return responses in order
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(side_effect=responses)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]
        results = await fetch_pages_concurrent(urls, max_concurrent=3)

        # Verify
        assert len(results) == 3
        assert results[0] == ("https://example.com/page1", "<html>page1</html>")
        assert results[1] == ("https://example.com/page2", "<html>page2</html>")
        assert results[2] == ("https://example.com/page3", "<html>page3</html>")

        # All should be successful
        successes = [r for r in results if isinstance(r[1], str)]
        assert len(successes) == 3


@pytest.mark.asyncio
async def test_fetch_pages_concurrent_partial_failure(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test concurrent fetching with some failures returns both successes and exceptions."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock responses - success, error, success
        mock_response_success_1 = MagicMock()
        mock_response_success_1.text = "<html>page1</html>"
        mock_response_success_1.raise_for_status = MagicMock()

        mock_response_error = MagicMock()
        mock_response_error.status_code = 403
        http_error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response_error
        )

        mock_response_success_2 = MagicMock()
        mock_response_success_2.text = "<html>page3</html>"
        mock_response_success_2.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(
            side_effect=[mock_response_success_1, http_error, mock_response_success_2]
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]
        results = await fetch_pages_concurrent(urls, max_concurrent=3)

        # Verify
        assert len(results) == 3

        # Check successes
        assert results[0][0] == "https://example.com/page1"
        assert results[0][1] == "<html>page1</html>"

        assert results[2][0] == "https://example.com/page3"
        assert results[2][1] == "<html>page3</html>"

        # Check failure
        assert results[1][0] == "https://example.com/page2"
        assert isinstance(results[1][1], httpx.HTTPStatusError)

        # Verify counts
        successes = [r for r in results if isinstance(r[1], str)]
        failures = [r for r in results if isinstance(r[1], Exception)]
        assert len(successes) == 2
        assert len(failures) == 1


@pytest.mark.asyncio
async def test_fetch_pages_concurrent_respects_semaphore(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that concurrent fetching respects max_concurrent limit."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Track concurrent requests
        active_requests = []
        max_concurrent_seen = 0

        async def mock_get(*args, **kwargs):
            # Simulate request in progress
            active_requests.append(1)
            nonlocal max_concurrent_seen
            max_concurrent_seen = max(max_concurrent_seen, len(active_requests))

            # Simulate some async work
            await asyncio.sleep(0.01)

            # Request complete
            active_requests.pop()

            # Return mock response
            mock_response = MagicMock()
            mock_response.text = "<html>test</html>"
            mock_response.raise_for_status = MagicMock()
            return mock_response

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get = mock_get
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute with max_concurrent=2
        import asyncio
        urls = [f"https://example.com/page{i}" for i in range(10)]
        results = await fetch_pages_concurrent(urls, max_concurrent=2)

        # Verify
        assert len(results) == 10
        # The semaphore should limit concurrent requests
        assert max_concurrent_seen <= 2
        # All should succeed
        successes = [r for r in results if isinstance(r[1], str)]
        assert len(successes) == 10


@pytest.mark.asyncio
async def test_fetch_page_network_error(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that network errors are handled and circuit breaker records failure."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup client to raise RequestError
        mock_client_instance = MagicMock()
        error = httpx.RequestError("Connection timeout")
        mock_client_instance.get = AsyncMock(side_effect=error)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute and verify exception
        with pytest.raises(httpx.RequestError):
            await fetch_page("https://example.com/page")

        mock_circuit_breaker.record_failure.assert_called_once_with(
            "example.com", block_type="network_error"
        )
        mock_circuit_breaker.record_success.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_page_custom_headers(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that custom headers are merged with default headers."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute with custom headers
        custom_headers = {"X-Custom-Header": "test-value"}
        await fetch_page("https://example.com/page", headers=custom_headers)

        # Verify headers were passed
        call_args = mock_client_instance.get.call_args
        headers_used = call_args.kwargs['headers']
        assert headers_used['X-Custom-Header'] == "test-value"
        # Default headers should still be present
        assert 'User-Agent' in headers_used


@pytest.mark.asyncio
async def test_fetch_page_custom_proxy(mock_circuit_breaker, mock_rate_limiter, mock_soft_block_detector):
    """Test that custom proxy is used when provided."""
    with patch('scraping.async_fetcher.httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()

        # Setup mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        # Execute with custom proxy
        custom_proxy = "http://custom-proxy:8080"
        await fetch_page("https://example.com/page", proxy=custom_proxy)

        # Verify proxy was used in client creation
        call_args = mock_client.call_args
        assert call_args.kwargs['proxy'] == custom_proxy
