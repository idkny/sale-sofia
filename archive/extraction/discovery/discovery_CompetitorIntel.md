---
id: discovery_competitor_intel
type: extraction
subject: discovery
source_repo: Competitor-Intel
description: "URL discovery via sitemap parsing (advertools) with homepage fallback"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [discovery, sitemap, advertools, crawl, competitor-intel]
---

# Discovery Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/discovery/sitemaps.py`

---

## URL Enumeration

```python
import datetime as dt
import re
import sqlite3
from typing import Iterable, List
import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def enumerate_urls(domain: str, conn: sqlite3.Connection, max_urls: int = 5000) -> int:
    """Enumerate URLs from sitemaps with fallback to homepage anchors."""
    domain = domain.rstrip("/")
    discovered = set()

    def insert(urls: Iterable[str]):
        ts = dt.datetime.now(dt.UTC).isoformat()
        for u in urls:
            u = normalize_url(u)
            if not u.startswith(domain):
                continue
            if u in discovered:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO pages(url, domain, discovered_at) VALUES(?,?,?)",
                (u, domain, ts)
            )
            discovered.add(u)
        conn.commit()

    # Try advertools sitemap parsing
    try:
        import advertools as adv

        candidates = [
            f"{domain}/sitemap.xml",
            f"{domain}/sitemap_index.xml",
            f"{domain}/sitemap_index.xml.gz",
        ]

        seen = set()
        for sm in candidates:
            if sm in seen:
                continue
            seen.add(sm)
            try:
                df = adv.sitemaps.sitemap_to_df(sm, allow_redirects=True)
            except Exception:
                continue
            if df is None or df.empty:
                continue
            urls = df["loc"].dropna().astype(str).tolist()
            insert(urls)
            if len(discovered) >= max_urls:
                break
    except Exception:
        pass

    # Fallback: crawl homepage anchors (one hop)
    if not discovered:
        try:
            urls = limited_anchor_discovery(domain)
            insert(urls)
        except Exception:
            pass

    return len(discovered)


def limited_anchor_discovery(domain: str) -> List[str]:
    """Extract internal links from homepage."""
    resp = requests.get(domain, headers={"User-Agent": UA}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    urls = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        u = absolutize(href, domain)
        if u.startswith(domain):
            urls.add(u)
    return sorted(urls)


def normalize_url(u: str) -> str:
    u = u.strip()
    u = re.sub(r"#[^#]*$", "", u)
    if u.endswith("/") and not re.search(r"/[^/]+\.[a-zA-Z0-9]{1,6}$", u):
        return u[:-1]
    return u


def absolutize(href: str, base: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, href)
```

---

## Sitemap Locations Tried

1. `/sitemap.xml`
2. `/sitemap_index.xml`
3. `/sitemap_index.xml.gz`

---

## What's Good / Usable

1. **advertools integration** - Robust sitemap parsing
2. **Fallback strategy** - Homepage anchors if no sitemap
3. **Deduplication** - Set-based URL tracking
4. **Max URL limit** - Prevents unbounded crawls
5. **Domain filtering** - Only includes internal URLs

---

## What Must Be Rewritten

1. Add **robots.txt parsing** for sitemap discovery
2. Add **sitemap index** recursive parsing
3. Add **lastmod filtering** for fresh URLs only

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Others |
|---------|------------------|--------|
| Sitemap parsing | advertools | None |
| Fallback discovery | Homepage anchors | None |
| Max URL limit | Yes (5000 default) | None |

**Recommendation**: Use Competitor-Intel discovery for URL enumeration in AutoBiz.

---

## Dependencies

```
advertools>=0.13.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```
