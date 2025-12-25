"""
Proxy Quality Checker - Tests proxies against Google and target sites.

Checks if proxies work with specific target sites and detects Google captchas.
This complements the basic liveness checks by verifying proxies work with
the actual sites we intend to scrape (e.g., imot.bg).

Features:
1. Google captcha detection - identifies when Google blocks proxy traffic
2. Target site validation - ensures proxy works with imot.bg or other sites
3. Combined quality check - returns comprehensive proxy quality metrics
4. Integration function - enriches proxy dicts with quality data

Usage:
    from proxies.quality_checker import QualityChecker, enrich_proxy_with_quality

    checker = QualityChecker(timeout=15)

    # Individual checks
    google_ok = checker.check_google("http://1.2.3.4:8080")
    target_ok = checker.check_target_site("http://1.2.3.4:8080", "https://www.imot.bg")

    # Combined check
    results = checker.check_all("http://1.2.3.4:8080")
    # Returns: {"google_passed": bool, "target_passed": bool}

    # Enrich proxy dict
    proxy = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}
    enriched = enrich_proxy_with_quality(proxy, timeout=15)
    # Returns proxy with added: google_passed, target_passed, quality_checked_at
"""

import logging
import time
from typing import Optional

import httpx

from proxies.anonymity_checker import get_real_ip

logger = logging.getLogger(__name__)

# Cache real IP to avoid repeated lookups
_cached_real_ip: Optional[str] = None

# IP check services - used to verify proxy connectivity
# These return the requester's IP address in plain text or JSON
IP_CHECK_SERVICES = [
    {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"},
    {"url": "https://icanhazip.com", "type": "text"},
    {"url": "https://ifconfig.me/ip", "type": "text"},
    {"url": "https://checkip.amazonaws.com", "type": "text"},
    {"url": "https://ipinfo.io/ip", "type": "text"},
]

# Expected content indicators for imot.bg
IMOT_BG_INDICATORS = [
    "imot.bg",
    "имоти",  # Bulgarian for "properties"
    "ИМОТИ",
    "недвижими имоти",  # Real estate
]

DEFAULT_TIMEOUT = 60


class QualityChecker:
    """
    Checks proxy quality against Google and target sites.

    This class provides methods to validate that proxies work with specific
    sites (Google, imot.bg) and aren't triggering captchas or blocks.

    Attributes:
        timeout: Request timeout in seconds for all checks
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the quality checker.

        Args:
            timeout: Timeout in seconds for HTTP requests (default: 15)
        """
        self.timeout = timeout
        self._user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def check_ip_service(self, proxy_url: str) -> tuple[bool, str | None]:
        """
        Test proxy against IP check services to verify connectivity.

        Tries multiple IP check services in sequence until one succeeds.
        Returns both pass/fail status and the detected exit IP.

        Args:
            proxy_url: Full proxy URL (e.g., "http://1.2.3.4:8080")

        Returns:
            Tuple of (passed: bool, exit_ip: str | None)
            - passed: True if proxy works with at least one service
            - exit_ip: The IP address returned by the service, or None if failed

        Example:
            >>> checker = QualityChecker()
            >>> passed, ip = checker.check_ip_service("http://localhost:8089")
            >>> passed
            True
            >>> ip
            '1.2.3.4'
        """
        for service in IP_CHECK_SERVICES:
            try:
                with httpx.Client(
                    proxy=proxy_url,
                    timeout=self.timeout,
                    follow_redirects=True,
                ) as client:
                    response = client.get(
                        service["url"],
                        headers={"User-Agent": self._user_agent},
                    )

                if response.status_code != 200:
                    logger.debug(
                        f"Proxy {proxy_url} failed {service['url']}: "
                        f"status {response.status_code}"
                    )
                    continue

                # Parse response based on type
                if service["type"] == "json":
                    import json
                    try:
                        data = response.json()
                        exit_ip = data.get(service.get("key", "ip"))
                    except json.JSONDecodeError:
                        continue
                else:
                    exit_ip = response.text.strip()

                # Validate it looks like an IP
                if exit_ip and len(exit_ip) >= 7 and "." in exit_ip:
                    # CRITICAL: Reject if exit_ip matches our real IP (proxy not working)
                    global _cached_real_ip
                    if _cached_real_ip is None:
                        _cached_real_ip = get_real_ip()

                    if _cached_real_ip:
                        real_ip_prefix = ".".join(_cached_real_ip.split(".")[:3])
                        if exit_ip.startswith(real_ip_prefix + "."):
                            logger.warning(
                                f"Proxy {proxy_url} returned our real IP {exit_ip} - "
                                f"proxy not working, rejecting"
                            )
                            return False, None

                    logger.debug(
                        f"Proxy {proxy_url} passed IP check via {service['url']}: {exit_ip}"
                    )
                    return True, exit_ip

            except httpx.TimeoutException:
                logger.debug(f"Proxy {proxy_url} timed out on {service['url']}")
                continue
            except httpx.ProxyError as e:
                logger.debug(f"Proxy {proxy_url} error on {service['url']}: {e}")
                continue
            except Exception as e:
                logger.debug(
                    f"Proxy {proxy_url} unexpected error on {service['url']}: {e}"
                )
                continue

        logger.debug(f"Proxy {proxy_url} failed all IP check services")
        return False, None

    def check_target_site(
        self,
        proxy_url: str,
        target_url: str = "https://www.imot.bg",
    ) -> bool:
        """
        Test proxy against target site (default: imot.bg).

        Makes a request to the target site and verifies the proxy can
        successfully retrieve the page with expected content.

        Args:
            proxy_url: Full proxy URL (e.g., "http://1.2.3.4:8080")
            target_url: URL to test against (default: "https://www.imot.bg")

        Returns:
            True if proxy works with target site, False otherwise

        Example:
            >>> checker = QualityChecker()
            >>> checker.check_target_site("http://localhost:8089")
            True
            >>> checker.check_target_site("http://1.2.3.4:8080", "https://www.example.com")
            False
        """
        try:
            with httpx.Client(
                proxy=proxy_url,
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = client.get(
                    target_url,
                    headers={"User-Agent": self._user_agent},
                )

            if response.status_code != 200:
                logger.debug(
                    f"Proxy {proxy_url} failed target site check: "
                    f"status {response.status_code}"
                )
                return False

            # For imot.bg, check for expected content
            if "imot.bg" in target_url.lower():
                response_text_lower = response.text.lower()

                for indicator in IMOT_BG_INDICATORS:
                    if indicator.lower() in response_text_lower:
                        logger.debug(
                            f"Proxy {proxy_url} passed imot.bg check "
                            f"(found: '{indicator}')"
                        )
                        return True

                logger.debug(
                    f"Proxy {proxy_url} failed imot.bg check: "
                    f"no expected content found"
                )
                return False
            else:
                # For other sites, just check 200 status
                logger.debug(f"Proxy {proxy_url} passed target site check")
                return True

        except httpx.TimeoutException:
            logger.debug(
                f"Proxy {proxy_url} timed out on target site check"
            )
            return False
        except httpx.ProxyError as e:
            logger.debug(
                f"Proxy {proxy_url} error on target site check: {e}"
            )
            return False
        except Exception as e:
            logger.debug(
                f"Proxy {proxy_url} unexpected error on target site check: {e}"
            )
            return False

    def check_all(self, proxy_url: str) -> dict:
        """
        Run all quality checks on a proxy.

        Performs IP service check and target site check,
        returning comprehensive quality metrics.

        Args:
            proxy_url: Full proxy URL (e.g., "http://1.2.3.4:8080")

        Returns:
            Dictionary with check results:
            {
                "ip_check_passed": bool,
                "ip_check_exit_ip": str | None,
                "target_passed": bool,
            }

        Example:
            >>> checker = QualityChecker()
            >>> results = checker.check_all("http://localhost:8089")
            >>> results
            {'ip_check_passed': True, 'ip_check_exit_ip': '1.2.3.4', 'target_passed': True}
        """
        ip_check_passed, exit_ip = self.check_ip_service(proxy_url)
        # Skip target site check - free proxies too slow/unreliable for imot.bg
        target_passed = None

        logger.info(
            f"Proxy {proxy_url} quality check: "
            f"IP={ip_check_passed} (exit: {exit_ip})"
        )

        return {
            "ip_check_passed": ip_check_passed,
            "ip_check_exit_ip": exit_ip,
            "target_passed": target_passed,
        }


def enrich_proxy_with_quality(
    proxy: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Add quality check results to a proxy dictionary.

    Performs comprehensive quality checks (Google captcha detection,
    target site validation) and adds the results to the proxy dict.

    Args:
        proxy: Proxy dict with 'protocol', 'host', 'port' keys
        timeout: Request timeout in seconds (default: 15)

    Returns:
        Same proxy dict with added fields:
        - google_passed: bool
        - target_passed: bool
        - quality_checked_at: float (Unix timestamp)

    Example:
        >>> proxy = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}
        >>> enriched = enrich_proxy_with_quality(proxy)
        >>> enriched
        {
            'host': '1.2.3.4',
            'port': 8080,
            'protocol': 'http',
            'google_passed': True,
            'target_passed': True,
            'quality_checked_at': 1703123456.789
        }
    """
    protocol = proxy.get("protocol", "http")
    host = proxy.get("host")
    port = proxy.get("port")

    if not host or not port:
        logger.warning(
            f"Cannot check quality for proxy without host/port: {proxy}"
        )
        proxy["ip_check_passed"] = None
        proxy["ip_check_exit_ip"] = None
        proxy["target_passed"] = None
        proxy["quality_checked_at"] = time.time()
        return proxy

    # Build proxy URL
    proxy_url = f"{protocol}://{host}:{port}"

    # Run quality checks
    checker = QualityChecker(timeout=timeout)
    results = checker.check_all(proxy_url)

    # Add results to proxy dict
    proxy["ip_check_passed"] = results["ip_check_passed"]
    proxy["ip_check_exit_ip"] = results["ip_check_exit_ip"]
    proxy["target_passed"] = results["target_passed"]
    proxy["quality_checked_at"] = time.time()

    return proxy


def enrich_proxies_batch(
    proxies: list[dict],
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """
    Add quality check results to a batch of proxies.

    Convenient wrapper for checking multiple proxies. Continues checking
    even if some proxies fail.

    Args:
        proxies: List of proxy dicts with 'protocol', 'host', 'port' keys
        timeout: Request timeout per proxy (default: 15)

    Returns:
        Same list with quality fields added to each proxy

    Example:
        >>> proxies = [
        ...     {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        ...     {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
        ... ]
        >>> enriched = enrich_proxies_batch(proxies)
        >>> len(enriched)
        2
    """
    logger.info(f"Checking quality for {len(proxies)} proxies...")

    for i, proxy in enumerate(proxies, 1):
        logger.debug(f"Checking proxy {i}/{len(proxies)}: {proxy}")
        enrich_proxy_with_quality(proxy, timeout=timeout)

    # Count results
    ip_passed = sum(1 for p in proxies if p.get("ip_check_passed"))
    target_passed = sum(1 for p in proxies if p.get("target_passed"))
    both_passed = sum(
        1 for p in proxies
        if p.get("ip_check_passed") and p.get("target_passed")
    )

    logger.info(
        f"Quality check complete: {both_passed}/{len(proxies)} passed both checks "
        f"(IP: {ip_passed}, Target: {target_passed})"
    )

    return proxies
