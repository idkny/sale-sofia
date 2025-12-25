---
id: api_client_seo
type: extraction
subject: api_client
source_repo: SEO
description: "Production SerpAPI client with cache, in-flight dedup, retry, 18 endpoints"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [api-client, serpapi, cache, retry, seo]
---

# API Client Extraction: SEO

**Source**: `idkny/SEO`
**Files**: `src/serp_api/serpapi_client.py`, `endpoints.py`, `optimization_strategies.py`

---

## Overview

Production SerpAPI client implementing:
- SQLite response cache with TTL
- In-flight request deduplication
- Retry with exponential backoff + jitter
- 18 SerpAPI endpoints
- Thread-safe operations

This is the IMPLEMENTATION of the SerpApi spec from the earlier spec repo.

---

## Core Client

```python
import asyncio
import hashlib
import json
import random
import sqlite3
import threading
import time
from typing import Any, Dict, Optional
import requests

_LOCK = threading.Lock()
_inflight: Dict[str, asyncio.Future] = {}

_EXCLUDE = {"api_key", "async", "no_cache"}

def _canon(value):
    """Canonicalize values for consistent hashing."""
    if isinstance(value, dict):
        return {k: _canon(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_canon(v) for v in sorted(value, key=lambda z: json.dumps(z, sort_keys=True))]
    if isinstance(value, str):
        return " ".join(value.split())
    return value

def normalize_params(engine: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize params excluding volatile keys."""
    p = {k: v for k, v in (params or {}).items() if k not in _EXCLUDE}
    return _canon(p)

def _key_for(engine: str, params: Dict[str, Any]) -> str:
    """Generate SHA256 cache key from engine + normalized params."""
    norm = normalize_params(engine, params)
    blob = json.dumps({"engine": engine, "params": norm}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()
```

---

## Cache Layer

```python
def _db_get(conn: sqlite3.Connection, key: str) -> Optional[Dict[str, Any]]:
    """Get cached response if not expired."""
    with _LOCK:
        row = conn.execute(
            "SELECT response_json, fetched_at, ttl_seconds FROM cache WHERE key=?",
            (key,)
        ).fetchone()
    if not row:
        return None
    resp_json, fetched_at, ttl = row
    if time.time() - fetched_at < ttl:
        return json.loads(resp_json)
    return None

def _db_put(conn, key, engine, params, resp, ttl):
    """Store response in cache."""
    with _LOCK:
        conn.execute(
            "REPLACE INTO cache (key, engine, params_json, response_json, fetched_at, ttl_seconds) VALUES (?,?,?,?,?,?)",
            (key, engine, json.dumps(params, sort_keys=True), json.dumps(resp), time.time(), ttl)
        )
        conn.commit()
```

---

## HTTP with Retry

```python
_NO_RETRY_STATUS = {400, 401, 403, 404, 422}

def _http_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """HTTP GET with retry for transient errors."""
    url = "https://serpapi.com/search.json"
    params.setdefault("no_cache", False)

    for attempt in range(4):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code in _NO_RETRY_STATUS:
                raise SerpApiError(f"HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError):
            sleep = (2**attempt) + random.random()  # Exp backoff + jitter
            time.sleep(sleep)
        except requests.HTTPError as e:
            if 500 <= r.status_code < 600:
                sleep = (2**attempt) + random.random()
                time.sleep(sleep)
            else:
                raise SerpApiError(str(e))
    raise SerpApiError("Exceeded retry budget")
```

---

## In-Flight Deduplication

```python
def get_or_fetch(conn, engine, params, *, ttl_seconds=None, api_key=None):
    """Get from cache or fetch, with in-flight dedup."""
    params = dict(params or {})
    params["engine"] = engine
    params["api_key"] = api_key or settings.serpapi_key

    key = _key_for(engine, params)

    # Check cache first
    cached = _db_get(conn, key)
    if cached:
        return cached

    # In-flight deduplication - wait if already fetching
    loop = asyncio.get_event_loop()
    if key in _inflight:
        return loop.run_until_complete(asyncio.wrap_future(_inflight[key]))

    # Start fetch, register in-flight
    fut = loop.create_future()
    _inflight[key] = fut

    try:
        data = _http_get(params)
        fut.set_result(data)
        _db_put(conn, key, engine, normalize_params(engine, params), data, ttl_seconds)
        return data
    finally:
        _inflight.pop(key, None)
```

---

## Endpoints (18 Total)

```python
REGISTRY = {
    # Competition/SERP presence
    "google_search": lambda conn, q, **kw: get_or_fetch(conn, "google", {"q": q, **kw}),
    "google_local": lambda conn, q, **kw: get_or_fetch(conn, "google_local", {"q": q, **kw}),
    "google_maps": lambda conn, q=None, **kw: get_or_fetch(conn, "google_maps", {"q": q, **kw}),
    "google_local_services": lambda conn, q, **kw: get_or_fetch(conn, "google_local_services", {"q": q, **kw}),
    "google_about_this_result": lambda conn, q, **kw: get_or_fetch(conn, "google_about_this_result", {"q": q, **kw}),
    "google_ai_overview_results": lambda conn, q, **kw: get_or_fetch(conn, "google_ai_overview", {"q": q, **kw}),
    "google_maps_reviews": lambda conn, place_id, **kw: get_or_fetch(conn, "google_maps_reviews", {"place_id": place_id, **kw}),
    "competitor_overview": competitor_overview,  # Composite endpoint

    # Keyword discovery
    "google_autocomplete": google_autocomplete,  # With save_discovered_keyword
    "google_trends": lambda conn, **kw: get_or_fetch(conn, "google_trends", {**kw}),
    "google_related_questions": google_related_questions,  # With save_discovered_keyword
    "get_keyword_serp": get_keyword_serp,  # Enriched with PAA expansion

    # Marketing/content
    "google_images": lambda conn, q, **kw: get_or_fetch(conn, "google_images", {"q": q, **kw}),
    "google_videos": lambda conn, q, **kw: get_or_fetch(conn, "google_videos", {"q": q, **kw}),
    "youtube_search": lambda conn, q=None, **kw: get_or_fetch(conn, "youtube", {"search_query": q, **kw}),
    "google_news": lambda conn, q, **kw: get_or_fetch(conn, "google_news", {"q": q, **kw}),
    "google_events": lambda conn, q, **kw: get_or_fetch(conn, "google_events", {"q": q, **kw}),
    "trends_snapshot": trends_snapshot,  # Multi-term batching
}
```

---

## Optimization Strategies

```python
def google_search_enriched(conn, q, **opts):
    """Single call, multiple extractions."""
    data = get_or_fetch(conn, "google", {"q": q, **opts}, ttl_seconds=3600)
    return {
        "organic": data.get("organic_results", []),
        "paa_base": data.get("related_questions", []),
        "kg": data.get("knowledge_graph"),
        "top_stories": data.get("top_stories", []),
        "answer_box": data.get("answer_box"),
        "raw": data,
    }

def fetch_interest_over_time(conn, terms, horizon="3m", **base):
    """Batch Google Trends - 5 terms per request."""
    DATE_MAP = {"7d": "now 7-d", "1m": "today 1-m", "3m": "today 3-m", "12m": "today 12-m"}
    results = []
    for group in _chunk5(terms):  # Groups of 5
        params = {**base, "q": ", ".join(group), "date": DATE_MAP.get(horizon)}
        data = get_or_fetch(conn, "google_trends", params, ttl_seconds=3600)
        results.append(data)
    return results
```

---

## What's Good / Usable

1. **Production-ready caching** - SQLite + TTL + SHA256 keys
2. **In-flight deduplication** - Prevents duplicate API calls
3. **Retry with backoff** - Handles transient errors
4. **18 endpoints** - Comprehensive SerpAPI coverage
5. **Optimization strategies** - Single call, multiple extractions
6. **Trends batching** - 5 terms per request

---

## Cross-Repo Comparison

| Feature | SEO | MarketIntel | SerpApi Spec |
|---------|-----|-------------|--------------|
| Cache | SQLite + TTL | SQLite + TTL | Spec only |
| In-flight dedup | Yes | Yes | Spec |
| Retry | Exp backoff + jitter | Exp backoff + jitter | Spec |
| Endpoints | 18 | ~5 | 12 spec |
| Thread-safe | Yes | Yes | N/A |

**Recommendation**: SEO has the most complete SerpAPI client. Use as primary for AutoBiz.
