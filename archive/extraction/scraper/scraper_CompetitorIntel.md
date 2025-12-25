---
id: scraper_competitor_intel
type: extraction
subject: scraper
source_repo: Competitor-Intel
description: "Async web crawler with rate limiting, anti-bot detection, content change tracking"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [scraper, crawler, httpx, async, rate-limiting, anti-bot, competitor-intel]
---

# Scraper Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/crawl/pipeline.py`, `parser.py`, `transport.py`

---

## Overview

Async web crawler with:
- **RateLimiter** - Domain-aware with anti-bot adaptation
- **Content change detection** - SHA256 hash comparison
- **Page history archiving** - Version control for competitors
- **Anti-bot detection** - Flags domains returning 404 after success

---

## RateLimiter

```python
import asyncio
import random
import time
import sqlite3
from pathlib import Path

class RateLimiter:
    _last_request_time = 0
    _lock = asyncio.Lock()

    def __init__(self, db_path: Path, global_min_delay: float = 5.0):
        self.db_path = db_path
        self.global_min_delay = global_min_delay
        self._domain_delays = {}

    async def get_delay(self, domain: str) -> float:
        """Get randomized delay for domain from database."""
        if domain not in self._domain_delays:
            conn = db_connect(self.db_path)
            try:
                cur = conn.execute(
                    "SELECT delay_seconds, anti_bot FROM domain_metadata WHERE domain = ?",
                    (domain,)
                )
                row = cur.fetchone()
                if row:
                    min_delay = row["delay_seconds"]
                    # Anti-bot domains get longer delays (min+25 vs min+7)
                    max_delay = min_delay + 25.0 if row["anti_bot"] else min_delay + 7.0
                    self._domain_delays[domain] = (min_delay, max_delay)
                else:
                    self._domain_delays[domain] = (3.0, 10.0)  # Default
            except sqlite3.OperationalError:
                self._domain_delays[domain] = (3.0, 10.0)
            finally:
                conn.close()

        min_delay, max_delay = self._domain_delays[domain]
        return random.uniform(min_delay, max_delay)

    async def wait(self, domain: str):
        """Enforce global + domain-specific delays."""
        async with self._lock:
            # 1. Global minimum delay
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.global_min_delay:
                await asyncio.sleep(self.global_min_delay - elapsed)

            # 2. Domain-specific random delay
            domain_delay = await self.get_delay(domain)
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < domain_delay:
                await asyncio.sleep(domain_delay - elapsed)

            # 3. Update global timestamp
            self._last_request_time = time.time()
```

---

## Main Crawl Pipeline

```python
import asyncio
import datetime as dt
import gzip
from pathlib import Path
from typing import Dict, List, Optional
import httpx

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

async def fetch_and_parse_async(
    db_path: Path,
    data_dir: Path,
    domains: List[str],
    validated_proxies: Optional[List[Dict]] = None,
    timeout: int = 25,
) -> int:
    """Fetch unfetched pages, parse SEO tags, save gzipped HTML."""
    rate_limiter = RateLimiter(db_path)
    conn = db_connect(db_path)

    transport = None
    if validated_proxies:
        transport = RobustProxyTransport(proxies=validated_proxies)

    async with httpx.AsyncClient(
        timeout=timeout,
        headers={"User-Agent": UA},
        transport=transport
    ) as client:
        placeholders = ",".join("?" for _ in domains)
        sql = f"""
            SELECT url, domain, html_path, content_hash
            FROM pages
            WHERE
                (fetched_at IS NULL OR (status < 200 OR status >= 400))
                AND retry_count < 3
                AND needs_investigation = 0
                AND domain IN ({placeholders})
            ORDER BY
                CASE WHEN status IS NOT NULL AND (status < 200 OR status >= 400) THEN 0 ELSE 1 END,
                discovered_at
            LIMIT 10000
        """
        cur = conn.execute(sql, domains)
        rows = cur.fetchall()
        if not rows:
            return 0

        tasks = [
            _fetch_and_parse_one(db_path, data_dir, client, url, domain, rate_limiter, html_path, content_hash)
            for url, domain, html_path, content_hash in rows
        ]

        results = await asyncio.gather(*tasks)
        return sum(results)
```

---

## Single Page Fetch with Change Detection

```python
async def _fetch_and_parse_one(
    db_path: Path,
    data_dir: Path,
    client: httpx.AsyncClient,
    url: str,
    domain: str,
    rate_limiter: RateLimiter,
    html_path: str | None = None,
    existing_content_hash: str | None = None,
) -> int:
    conn = db_connect(db_path)
    try:
        # Reprocess from disk if HTML exists
        if html_path and Path(html_path).exists():
            with gzip.open(Path(html_path), "rb") as f:
                raw = f.read()
            status = 200
        else:
            # Fetch from network
            await rate_limiter.wait(domain)
            r = await client.get(url)
            status = r.status_code
            raw = r.content

            # Anti-bot detection: 404 after recent success
            if status == 404:
                cur = conn.execute(
                    "SELECT last_success_at FROM domain_metadata WHERE domain = ?",
                    (domain,)
                )
                row = cur.fetchone()
                if row and row["last_success_at"]:
                    last_success = dt.datetime.fromisoformat(row["last_success_at"])
                    if (dt.datetime.now(dt.UTC) - last_success).total_seconds() < 3600:
                        conn.execute(
                            "UPDATE domain_metadata SET anti_bot = 1 WHERE domain = ?",
                            (domain,)
                        )

            # On success, reset anti-bot flag
            if 200 <= status < 300:
                conn.execute(
                    """
                    INSERT INTO domain_metadata (domain, last_success_at, anti_bot)
                    VALUES (?, ?, 0)
                    ON CONFLICT(domain) DO UPDATE SET
                        last_success_at=excluded.last_success_at,
                        anti_bot=0;
                    """,
                    (domain, dt.datetime.now(dt.UTC).isoformat())
                )

        # Content hash comparison
        new_hash = content_hash(raw)
        if new_hash == existing_content_hash:
            # Unchanged - just update timestamp
            conn.execute(
                "UPDATE pages SET last_scrape_time = ? WHERE url = ?",
                (dt.datetime.now(dt.UTC).isoformat(), url)
            )
            return 0

        # Save gzipped HTML
        filename = f"{sanitize_url_for_filename(url)}.html.gz"
        gz_path = data_dir / "raw_html" / filename
        gz_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(gz_path, "wb") as f:
            f.write(raw)

        # Archive old version
        if existing_content_hash:
            conn.execute(
                "INSERT OR IGNORE INTO page_history (url, scraped_at, html_path, content_hash) VALUES (?, ?, ?, ?)",
                (url, dt.datetime.now(dt.UTC).isoformat(), html_path, existing_content_hash)
            )

        # Parse SEO elements
        title, meta_desc, canonical, h1, h2, h3, robots, rel_canonical, lang = parse_html_basic(raw, url)
        links, media = parse_links_media(raw, url, domain)

        # Update page record
        ts = dt.datetime.now(dt.UTC).isoformat()
        conn.execute(
            """
            UPDATE pages
            SET fetched_at=?, last_scrape_time=?, status=?, html_path=?, content_hash=?,
                canonical=?, title=?, meta_desc=?, h1=?, h2=?, h3=?, robots=?, rel_canonical=?, lang=?,
                retry_count=0
            WHERE url=?
            """,
            (ts, ts, status, str(gz_path), new_hash, canonical, title, meta_desc, h1, h2, h3, robots, rel_canonical, lang, url)
        )

        # Store links & media
        if links:
            conn.executemany(
                "INSERT OR REPLACE INTO links(src_url, dst_url, anchor, rel, nofollow, is_internal) VALUES(?,?,?,?,?,?)",
                links
            )
        if media:
            conn.executemany(
                "INSERT OR REPLACE INTO media(url, page_url, alt_text, type) VALUES(?,?,?,?)",
                media
            )
        conn.commit()
        return 1

    except Exception as e:
        _handle_fetch_failure(conn, url)
        return 0
    finally:
        conn.close()


def _handle_fetch_failure(conn, url, status=-2):
    """Track failures with investigation flag."""
    cur = conn.execute("SELECT retry_count FROM pages WHERE url = ?", (url,))
    row = cur.fetchone()
    retry_count = row[0] if row else 0

    new_retry_count = retry_count + 1
    needs_investigation = 1 if new_retry_count >= 3 else 0

    conn.execute(
        "UPDATE pages SET status=?, retry_count=?, needs_investigation=? WHERE url=?",
        (status, new_retry_count, needs_investigation, url)
    )
    conn.commit()
```

---

## What's Good / Usable

1. **Domain-aware rate limiting** - Per-domain delays from database
2. **Anti-bot adaptation** - Longer delays when anti-bot detected
3. **Content change detection** - SHA256 hash comparison
4. **Page history archiving** - Version control for tracking changes
5. **Retry tracking** - `needs_investigation` flag after 3 failures
6. **Gzip storage** - Compressed HTML storage

---

## What Must Be Rewritten

1. Add **configurable retry limits**
2. Add **backoff strategy** for failed domains
3. Add **robots.txt compliance** checking

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Auto-Biz | Scraper |
|---------|------------------|----------|---------|
| Rate limiter | Domain-aware | None | Basic |
| Anti-bot detection | Yes (404 heuristic) | No | No |
| Content change | SHA256 hash | No | No |
| Page history | Yes | No | No |
| Retry tracking | Yes (3 max) | No | Yes |

**Recommendation**: Competitor-Intel has the most complete scraping logic. Use for AutoBiz.
