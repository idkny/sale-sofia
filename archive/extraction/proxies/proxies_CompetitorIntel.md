---
id: proxies_competitor_intel
type: extraction
subject: proxies
source_repo: Competitor-Intel
description: "Comprehensive proxy management: scoring transport, async validation, Mubeng rotation, paid proxy integration"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [proxies, mubeng, httpx, async, validation, rotation, competitor-intel]
---

# Proxies Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `proxy_manager/manager.py`, `validator.py`, `paid_proxies.py`, `utils.py`, `config.py`
**Also**: `competitor_intel/crawl/transport.py` (RobustProxyTransport)

---

## Overview

Most comprehensive proxy management system in the codebase:

1. **ProxyManager** - Full lifecycle management with Mubeng integration
2. **ProxyValidator** - Async validation against multiple IP check services
3. **RobustProxyTransport** - httpx transport with scoring and auto-pruning
4. **PaidProxyService** - PacketStream.io integration
5. **Utilities** - Port management

---

## 1. RobustProxyTransport - Scored Proxy Pool

```python
import asyncio
import random
import time
import httpx
import logging
from typing import List, Dict, Optional

class AllProxiesFailedError(Exception):
    """Raised when a request fails with all available proxies."""
    pass

class RobustProxyTransport(httpx.AsyncBaseTransport):
    """
    An httpx Async Transport with proxy pool scoring.
    Auto-prunes failing proxies, weighted random selection.
    """

    def __init__(
        self,
        proxies: List[Dict],
        retries: int = 5,
        base_timeout: float = 10.0,
    ):
        if not proxies:
            raise ValueError("Proxy list cannot be empty.")

        self.logger = logging.getLogger(__name__)
        self.retries = retries
        self.base_timeout = base_timeout

        # Initialize proxy pool with scores
        self._proxies = [
            {
                "proxy": p["proxy"],
                "transport": httpx.AsyncHTTPTransport(proxy=p["proxy"]),
                "score": self._initial_score(p.get("response_time", float('inf'))),
                "last_used": 0,
                "failures": 0,
            }
            for p in proxies
        ]
        self._lock = asyncio.Lock()

    def _initial_score(self, response_time: float) -> float:
        """Score based on response time. Lower latency = higher score."""
        return 1.0 / max(response_time, 0.1)

    async def _select_proxy(self) -> Optional[Dict]:
        """Weighted random selection based on scores."""
        async with self._lock:
            if not self._proxies:
                return None

            total_score = sum(p["score"] for p in self._proxies)
            if total_score == 0:
                return random.choice(self._proxies)

            weights = [p["score"] / total_score for p in self._proxies]
            selected = random.choices(self._proxies, weights=weights, k=1)[0]
            selected["last_used"] = time.time()
            return selected

    async def _update_proxy_score(self, proxy: Dict, success: bool):
        """Adjust score based on outcome. Auto-prune bad proxies."""
        async with self._lock:
            for p in self._proxies:
                if p["proxy"] == proxy["proxy"]:
                    if success:
                        p["score"] *= 1.1      # Reward: +10%
                        p["failures"] = 0
                    else:
                        p["score"] *= 0.5      # Penalty: -50%
                        p["failures"] += 1

                    # Auto-prune: 3 failures OR score < 0.01
                    if p["failures"] >= 3 or p["score"] < 0.01:
                        self.logger.warning(
                            f"Removing failing proxy: {p['proxy']} "
                            f"after {p['failures']} failures."
                        )
                        self._proxies.remove(p)
                    break

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request with proxy rotation and retries."""
        last_exception = None

        for attempt in range(self.retries):
            selected_proxy = await self._select_proxy()

            if selected_proxy is None:
                raise AllProxiesFailedError("No proxies available in the pool.")

            self.logger.info(
                f"Attempt {attempt + 1}/{self.retries} "
                f"using proxy {selected_proxy['proxy']}"
            )

            try:
                response = await selected_proxy["transport"].handle_async_request(request)

                # Soft failures: non-2xx/3xx (except 404/403/401)
                if 400 <= response.status_code < 600 and response.status_code not in [404, 403, 401]:
                    raise httpx.HTTPStatusError(
                        f"Proxy returned status {response.status_code}",
                        request=request,
                        response=response
                    )

                await self._update_proxy_score(selected_proxy, success=True)
                return response

            except (httpx.ProxyError, httpx.TimeoutException, httpx.ConnectError,
                    httpx.ReadError, httpx.HTTPStatusError) as e:
                self.logger.warning(f"Request with proxy {selected_proxy['proxy']} failed: {e}")
                await self._update_proxy_score(selected_proxy, success=False)
                last_exception = e
                # Exponential backoff
                await asyncio.sleep(0.5 * (attempt + 1))

        raise AllProxiesFailedError(
            f"Request failed after {self.retries} retries."
        ) from last_exception

    async def aclose(self) -> None:
        """Close all underlying proxy transports."""
        for p in self._proxies:
            await p["transport"].aclose()
```

---

## 2. ProxyValidator - Async Validation

```python
import asyncio
import random
import httpx
import logging
from typing import List, Dict, Optional

IP_CHECK_URLS = [
    "https://ipinfo.io/json",
    "https://api.ipify.org?format=json",
    "https://ifconfig.co/json",
]
DEFAULT_TIMEOUT = 10

class ProxyValidator:
    """
    Validates proxies by checking liveness, anonymity, and response time.
    """

    def __init__(self, proxies: List[Dict], timeout: int = DEFAULT_TIMEOUT):
        self.proxies = proxies
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    async def validate_proxies(self) -> List[Dict]:
        """Async validate all proxies in parallel."""
        tasks = [self.check_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)

        # Filter None (invalid), deduplicate
        valid_proxies_map = {p["proxy"]: p for p in results if p is not None}
        valid_proxies = list(valid_proxies_map.values())

        # Sort by response time (fastest first)
        valid_proxies.sort(key=lambda p: p['response_time'])

        self.logger.info(f"Validated {len(valid_proxies)} out of {len(self.proxies)} proxies.")
        return valid_proxies

    async def check_proxy(self, proxy: Dict) -> Optional[Dict]:
        """Check single proxy against random test site."""
        proxy_url = f"{proxy.get('protocol', 'http')}://{proxy['host']}:{proxy['port']}"
        test_url = random.choice(IP_CHECK_URLS)

        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=self.timeout) as client:
                start_time = asyncio.get_event_loop().time()
                response = await client.get(test_url)
                end_time = asyncio.get_event_loop().time()

                if response.status_code == 200:
                    response_time = end_time - start_time
                    data = response.json()

                    # Normalize response from different services
                    ip = data.get("ip") or data.get("ip_addr")
                    country = data.get("country") or data.get("country_name", "Unknown")
                    city = data.get("city", "Unknown")

                    return {
                        "proxy": proxy_url,
                        "ip": ip,
                        "response_time": response_time,
                        "country": country,
                        "city": city,
                    }
                else:
                    return None
        except Exception:
            return None
```

---

## 3. PaidProxyService - PacketStream.io

```python
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class PaidProxyService:
    """Interface to PacketStream.io paid proxy service."""

    def __init__(self):
        self.username = os.getenv("PACKETSTREAM_USERNAME")
        self.password = os.getenv("PACKETSTREAM_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("Missing PacketStream credentials in .env file")

        self.base_host = "proxy.packetstream.io"
        self.port_map = {"http": 31112, "https": 31112, "socks5": 31113}

    def get_proxy(
        self,
        protocol: str = "http",
        country: Optional[str] = None,
        as_dict: bool = False
    ) -> str | Dict[str, str]:
        """Generate authenticated proxy string or dict."""
        port = self.port_map[protocol]
        user = f"{self.username}:{self.password}"
        if country:
            user = f"{self.username}_country-{country}:{self.password}"

        prefix = "socks5h" if protocol == "socks5" else protocol
        proxy_str = f"{prefix}://{user}@{self.base_host}:{port}"

        if as_dict:
            return {"http": proxy_str, "https": proxy_str}
        return proxy_str
```

---

## What's Good / Usable

1. **Scoring system** - Weighted random selection with performance tracking
2. **Auto-pruning** - Removes bad proxies (3 failures OR score < 0.01)
3. **Async validation** - Parallel checking with response time sorting
4. **Mubeng integration** - Production-ready proxy rotation
5. **Paid proxy support** - PacketStream.io with country targeting

---

## What Must Be Rewritten

1. Add **persistent scoring** with Redis/SQLite
2. Add **configurable thresholds** for max_failures, min_score

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Auto-Biz | Scraper |
|---------|------------------|----------|---------|
| Scoring transport | RobustProxyTransport | None | ProxyChecker |
| Auto-pruning | Yes (3 failures) | No | No |
| Mubeng integration | Full | No | No |
| Paid proxies | PacketStream.io | No | No |

**Recommendation**: Use Competitor-Intel as primary proxy system for AutoBiz.
