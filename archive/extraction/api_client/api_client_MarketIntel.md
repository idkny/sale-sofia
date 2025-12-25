---
id: 20251201_api_client_marketintel
type: extraction
subject: api_client
description: "API client with caching, retry, and deduplication from MarketIntel"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [api, cache, retry, http, marketintel, extraction]
source_repo: idkny/MarketIntel
---

# API Client Extraction: MarketIntel

**Source**: `idkny/MarketIntel`
**File**: `src/serp_api/serpapi_client.py`

---

## Conclusions

### What's Good (ALL HIGH PRIORITY)

| Pattern | Description | Use For |
|---------|-------------|---------|
| SHA256 cache key | Deterministic key from normalized params | Any API caching |
| TTL validation | Time-based cache expiry | Zoho API responses |
| In-flight dedup | Prevents duplicate concurrent requests | Rate limiting |
| Exponential backoff | Retry with 2^n + jitter | API resilience |
| Thread-safe ops | Lock around SQLite writes | Concurrent access |

### What to Adapt

- Change base URL to Zoho endpoints
- Add OAuth token refresh logic
- Change `engine` to Zoho module names

---

## Pattern 1: Parameter Normalization

```python
def _canon(value):
    """Recursively canonicalize value for consistent hashing."""
    if isinstance(value, dict):
        return {k: _canon(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [
            _canon(v)
            for v in sorted(value, key=lambda z: json.dumps(z, sort_keys=True))
        ]
    if isinstance(value, str):
        return " ".join(value.split())  # Normalize whitespace
    return value


_EXCLUDE = {"api_key", "async", "no_cache"}  # Don't include in cache key


def normalize_params(engine: str, params: dict) -> dict:
    """Normalize params for consistent cache key generation."""
    p = {k: v for k, v in (params or {}).items() if k not in _EXCLUDE}
    return _canon(p)
```

---

## Pattern 2: SHA256 Cache Key

```python
import hashlib
import json

def _key_for(engine: str, params: dict) -> str:
    """Generate SHA256 hash as cache key from engine + normalized params."""
    norm = normalize_params(engine, params)
    blob = json.dumps(
        {"engine": engine, "params": norm}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(blob.encode()).hexdigest()
```

**Why SHA256**: Deterministic, fixed length, collision-resistant.

---

## Pattern 3: TTL-Based Cache

```python
import threading
import time

_LOCK = threading.Lock()

def _db_get(conn, key: str) -> dict | None:
    """Get cached response if exists and not expired."""
    with _LOCK:
        row = conn.execute(
            "SELECT response_json, fetched_at, ttl_seconds FROM cache WHERE key=?",
            (key,),
        ).fetchone()
    if not row:
        return None
    resp_json, fetched_at, ttl = row
    if time.time() - fetched_at < ttl:  # Still valid
        return json.loads(resp_json)
    return None  # Expired


def _db_put(conn, key: str, engine: str, params: dict, resp: dict, ttl: int):
    """Store response in cache with TTL."""
    with _LOCK:
        conn.execute(
            """REPLACE INTO cache (key, engine, params_json, response_json, fetched_at, ttl_seconds)
               VALUES (?,?,?,?,?,?)""",
            (
                key,
                engine,
                json.dumps(params, sort_keys=True),
                json.dumps(resp),
                time.time(),
                ttl,
            ),
        )
        conn.commit()
```

---

## Pattern 4: Retry with Exponential Backoff

```python
import random
import requests

class ApiError(Exception):
    pass

_NO_RETRY_STATUS = {400, 401, 403, 404, 422}  # Client errors - don't retry


def _http_get(url: str, params: dict, timeout: int = 60) -> dict:
    """HTTP GET with exponential backoff retry."""
    for attempt in range(4):  # Max 4 attempts
        try:
            r = requests.get(url, params=params, timeout=timeout)

            if r.status_code in _NO_RETRY_STATUS:
                raise ApiError(f"HTTP {r.status_code}: {r.text[:200]}")

            r.raise_for_status()
            return r.json()

        except (requests.Timeout, requests.ConnectionError):
            sleep = (2**attempt) + random.random()  # Exponential + jitter
            time.sleep(sleep)

        except requests.HTTPError as e:
            if 500 <= r.status_code < 600:  # Server error - retry
                sleep = (2**attempt) + random.random()
                time.sleep(sleep)
            else:
                raise ApiError(str(e))

    raise ApiError("Exceeded retry budget")
```

**Backoff timing**: 1s, 2s, 4s, 8s (plus random 0-1s jitter)

---

## Pattern 5: In-flight Deduplication

```python
import asyncio

_inflight: dict[str, asyncio.Future] = {}

def get_or_fetch(conn, engine: str, params: dict, *, ttl_seconds: int = 3600) -> dict:
    """
    Get from cache or fetch from API.
    Prevents duplicate concurrent requests for same key.
    """
    key = _key_for(engine, params)

    # 1. Try cache first
    cached = _db_get(conn, key)
    if cached:
        return cached

    # 2. Check if already being fetched
    loop = asyncio.get_event_loop()
    if key in _inflight:
        return loop.run_until_complete(asyncio.wrap_future(_inflight[key]))

    # 3. Start new fetch
    fut = loop.create_future()
    _inflight[key] = fut

    try:
        data = _http_get(BASE_URL, params)
        fut.set_result(data)
        _db_put(conn, key, engine, normalize_params(engine, params), data, ttl_seconds)
        return data
    finally:
        _inflight.pop(key, None)
```

---

## Full Combined Client

```python
"""Complete API client with all patterns."""
import asyncio
import hashlib
import json
import random
import threading
import time
import requests

_LOCK = threading.Lock()
_inflight = {}
_EXCLUDE = {"api_key", "async", "no_cache"}
_NO_RETRY_STATUS = {400, 401, 403, 404, 422}


class ApiClient:
    def __init__(self, base_url: str, db_conn, default_ttl: int = 3600):
        self.base_url = base_url
        self.conn = db_conn
        self.default_ttl = default_ttl

    def _canon(self, value):
        if isinstance(value, dict):
            return {k: self._canon(value[k]) for k in sorted(value)}
        if isinstance(value, list):
            return [self._canon(v) for v in sorted(value, key=lambda z: json.dumps(z, sort_keys=True))]
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    def _key_for(self, endpoint: str, params: dict) -> str:
        norm = {k: self._canon(v) for k, v in params.items() if k not in _EXCLUDE}
        blob = json.dumps({"endpoint": endpoint, "params": norm}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def _cache_get(self, key: str):
        with _LOCK:
            row = self.conn.execute(
                "SELECT response_json, fetched_at, ttl_seconds FROM cache WHERE key=?", (key,)
            ).fetchone()
        if not row:
            return None
        if time.time() - row[1] < row[2]:
            return json.loads(row[0])
        return None

    def _cache_put(self, key: str, endpoint: str, params: dict, resp: dict, ttl: int):
        with _LOCK:
            self.conn.execute(
                "REPLACE INTO cache VALUES (?,?,?,?,?,?)",
                (key, endpoint, json.dumps(params), json.dumps(resp), time.time(), ttl)
            )
            self.conn.commit()

    def _http_get(self, url: str, params: dict, timeout: int = 60):
        for attempt in range(4):
            try:
                r = requests.get(url, params=params, timeout=timeout)
                if r.status_code in _NO_RETRY_STATUS:
                    raise Exception(f"HTTP {r.status_code}")
                r.raise_for_status()
                return r.json()
            except (requests.Timeout, requests.ConnectionError):
                time.sleep((2**attempt) + random.random())
        raise Exception("Exceeded retry budget")

    def get(self, endpoint: str, params: dict = None, ttl: int = None):
        params = params or {}
        ttl = ttl or self.default_ttl
        key = self._key_for(endpoint, params)

        cached = self._cache_get(key)
        if cached:
            return cached

        if key in _inflight:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(asyncio.wrap_future(_inflight[key]))

        fut = asyncio.get_event_loop().create_future()
        _inflight[key] = fut

        try:
            url = f"{self.base_url}/{endpoint}"
            data = self._http_get(url, params)
            fut.set_result(data)
            self._cache_put(key, endpoint, params, data, ttl)
            return data
        finally:
            _inflight.pop(key, None)
```

---

## AutoBiz Adaptation

```python
# Example Zoho API client using these patterns

class ZohoApiClient(ApiClient):
    def __init__(self, db_conn, access_token: str):
        super().__init__("https://www.zohoapis.com", db_conn, default_ttl=300)
        self.access_token = access_token

    def get_contacts(self, params: dict = None):
        params = params or {}
        params["Authorization"] = f"Zoho-oauthtoken {self.access_token}"
        return self.get("crm/v2/Contacts", params, ttl=300)

    def get_invoices(self, params: dict = None):
        return self.get("books/v3/invoices", params, ttl=600)
```
