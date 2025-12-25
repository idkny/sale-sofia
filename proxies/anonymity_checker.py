"""
Anonymity Checker - Determines proxy anonymity level by analyzing HTTP headers.

Three-tier anonymity detection:
- Transparent: Your real IP appears in the response (proxy exposes you)
- Anonymous: IP hidden but privacy headers present (server knows you use proxy)
- Elite: IP hidden AND no privacy headers (undetectable)

Based on implementation from old repositories (Scraper/Auto-Biz).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Privacy-revealing headers that indicate proxy usage
PRIVACY_HEADERS = [
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "FORWARDED-FOR",
    "FORWARDED-FOR-IP",
    "FORWARDED",
    "X-REAL-IP",
    "CLIENT-IP",
    "X-CLIENT-IP",
    "PROXY-CONNECTION",
    "X-PROXY-ID",
    "X-BLUECOAT-VIA",
    "X-ORIGINATING-IP",
]

# Judge URLs that return request headers (for anonymity detection)
# Multiple judges with fallback for reliability
JUDGE_URLS = [
    "https://httpbin.org/headers",
    "http://httpbin.org/headers",
    "https://httpbin.io/headers",
    "http://httpbin.io/headers",
    "https://ifconfig.me/all.json",
]

# URLs for getting your real IP (without proxy)
REAL_IP_URLS = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
]

DEFAULT_TIMEOUT = 15

# Cache for real IP (doesn't change during session)
_real_ip_cache: Optional[str] = None


def get_real_ip(timeout: int = DEFAULT_TIMEOUT, force_refresh: bool = False) -> Optional[str]:
    """
    Get your real IP address (without using proxy).

    Caches result since real IP doesn't change during session.

    Args:
        timeout: Request timeout in seconds
        force_refresh: If True, bypass cache and fetch fresh IP

    Returns:
        Real IP address as string, or None if detection failed
    """
    global _real_ip_cache

    if _real_ip_cache and not force_refresh:
        return _real_ip_cache

    for url in REAL_IP_URLS:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                ip = response.text.strip()
                # Basic validation - should look like an IP
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                    _real_ip_cache = ip
                    logger.debug(f"Real IP detected: {ip}")
                    return ip
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to get real IP from {url}: {e}")
            continue

    logger.warning("Could not determine real IP address")
    return None


def parse_anonymity(response_text: str, real_ip: str) -> str:
    """
    Parse anonymity level from HTTP response.

    Args:
        response_text: The full HTTP response (headers as text/JSON)
        real_ip: Your real IP address

    Returns:
        "Transparent", "Anonymous", or "Elite"
    """
    response_upper = response_text.upper()

    # Check if real IP appears in response → Transparent
    if real_ip and real_ip in response_text:
        return "Transparent"

    # Check for privacy-revealing headers → Anonymous
    for header in PRIVACY_HEADERS:
        if header.upper() in response_upper:
            return "Anonymous"

    # No IP leak, no privacy headers → Elite
    return "Elite"


def check_proxy_anonymity(
    proxy_url: str,
    real_ip: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """
    Check the anonymity level of a proxy.

    Makes a request through the proxy to a judge URL and analyzes
    the returned headers to determine anonymity level.

    Args:
        proxy_url: Full proxy URL (e.g., "http://1.2.3.4:8080" or "socks5://1.2.3.4:1080")
        real_ip: Your real IP (will be fetched if not provided)
        timeout: Request timeout in seconds

    Returns:
        "Transparent", "Anonymous", "Elite", or None if check failed
    """
    # Get real IP if not provided
    if not real_ip:
        real_ip = get_real_ip(timeout=timeout)
        if not real_ip:
            logger.warning("Cannot check anonymity without knowing real IP")
            # Assume Anonymous if we can't determine (safer than Elite)
            return "Anonymous"

    # Try each judge URL with individual timeout handling
    for judge_url in JUDGE_URLS:
        try:
            response = requests.get(
                judge_url,
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (anonymity-check)"},
            )

            if response.status_code == 200:
                anonymity = parse_anonymity(response.text, real_ip)
                logger.debug(f"Proxy {proxy_url} anonymity: {anonymity} (via {judge_url})")
                return anonymity

        except requests.exceptions.Timeout:
            logger.debug(f"Judge {judge_url} timed out for {proxy_url}")
            continue
        except requests.exceptions.ProxyError as e:
            logger.debug(f"Proxy error with {judge_url} for {proxy_url}: {e}")
            continue
        except requests.exceptions.ConnectionError as e:
            logger.debug(f"Connection error with {judge_url} for {proxy_url}: {e}")
            continue
        except requests.exceptions.RequestException as e:
            logger.debug(f"Judge {judge_url} failed for {proxy_url}: {e}")
            continue

    # All judges failed - proxy might be dead or blocking these URLs
    logger.debug(f"All judge URLs failed for {proxy_url}")
    return None


def check_proxy_anonymity_batch(
    proxies: list[dict],
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """
    Check anonymity for a batch of proxies.

    Adds 'anonymity' field to each proxy dict.

    Args:
        proxies: List of proxy dicts with 'protocol', 'host', 'port' keys
        timeout: Request timeout per proxy

    Returns:
        Same list with 'anonymity' field added to each proxy
    """
    # Get real IP once for all checks
    real_ip = get_real_ip(timeout=timeout)

    for proxy in proxies:
        protocol = proxy.get("protocol", "http")
        host = proxy.get("host")
        port = proxy.get("port")

        if not host or not port:
            proxy["anonymity"] = None
            continue

        proxy_url = f"{protocol}://{host}:{port}"

        # Check anonymity
        anonymity = check_proxy_anonymity(proxy_url, real_ip=real_ip, timeout=timeout)

        if anonymity:
            proxy["anonymity"] = anonymity
        else:
            # Fallback: use exit_ip comparison if judge check failed
            exit_ip = proxy.get("exit_ip")
            if exit_ip and exit_ip != host:
                proxy["anonymity"] = "Anonymous"  # Conservative assumption
            else:
                proxy["anonymity"] = "Transparent"

    return proxies


def enrich_proxy_with_anonymity(proxy: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Add anonymity level to a single proxy dict.

    Args:
        proxy: Proxy dict with 'protocol', 'host', 'port' keys
        timeout: Request timeout

    Returns:
        Same proxy dict with 'anonymity' and 'anonymity_verified_at' fields added
    """
    protocol = proxy.get("protocol", "http")
    host = proxy.get("host")
    port = proxy.get("port")

    if not host or not port:
        proxy["anonymity"] = None
        proxy["anonymity_verified_at"] = None
        return proxy

    proxy_url = f"{protocol}://{host}:{port}"

    # Try full anonymity check first
    anonymity = check_proxy_anonymity(proxy_url, timeout=timeout)

    if anonymity:
        proxy["anonymity"] = anonymity
        proxy["anonymity_verified_at"] = datetime.now(timezone.utc).isoformat()
    else:
        # Fallback: use exit_ip comparison
        exit_ip = proxy.get("exit_ip")
        if exit_ip and exit_ip != host:
            proxy["anonymity"] = "Anonymous"
        else:
            proxy["anonymity"] = "Transparent"
        proxy["anonymity_verified_at"] = datetime.now(timezone.utc).isoformat()

    return proxy
