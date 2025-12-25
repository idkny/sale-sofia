---
id: parser_competitor_intel
type: extraction
subject: parser
source_repo: Competitor-Intel
description: "lxml-based HTML parser for SEO elements, links, and media extraction"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [parser, lxml, html, seo, links, media, competitor-intel]
---

# Parser Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/crawl/parser.py`

---

## Overview

lxml-based HTML parser extracting:
- SEO elements (title, meta, h1-h3, canonical, robots, lang)
- Hyperlinks with nofollow detection
- Media (images) with alt text
- URL utilities (normalize, hash, sanitize)

---

## URL Utilities

```python
import hashlib
import re
from urllib.parse import urljoin

def normalize_url(u: str) -> str:
    """Strip fragments, normalize trailing slash."""
    u = u.strip()
    u = re.sub(r"#[^#]*$", "", u)  # Remove fragments
    if u.endswith("/") and not re.search(r"/[^/]+\.[a-zA-Z0-9]{1,6}$", u):
        return u[:-1]
    return u

def absolutize(href: str, base: str) -> str:
    """Convert relative URL to absolute."""
    return urljoin(base, href)

def url_hash(u: str) -> str:
    """SHA256 hash of URL (24 chars)."""
    return hashlib.sha256(u.encode("utf-8")).hexdigest()[:24]

def content_hash(data: bytes) -> str:
    """SHA256 hash of content."""
    return hashlib.sha256(data).hexdigest()

def sanitize_url_for_filename(url: str) -> str:
    """Convert URL to safe filename."""
    url = re.sub(r"https?://", "", url)
    url = re.sub(r'[\\/*?:"<>|]', "_", url)
    if len(url) > 200:
        url = url[:200]
    return url
```

---

## SEO Element Extraction

```python
from lxml import html as lxml_html

def parse_html_basic(raw_html: bytes, base_url: str):
    """Extract SEO-critical elements from HTML."""
    try:
        doc = lxml_html.fromstring(raw_html)
        doc.make_links_absolute(base_url)
    except Exception:
        return (None,) * 9

    def text_or_none(x):
        return x.strip() if x else None

    # Title
    title = text_or_none("".join(doc.xpath("string(//title)") or []))

    # Meta description (case-insensitive)
    meta_desc = None
    meta = doc.xpath(
        '//meta[translate(@name, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")="description"]/@content'
    )
    if meta:
        meta_desc = text_or_none(meta[0])

    # Canonical URL
    canonical = None
    c = doc.xpath(
        '//link[translate(@rel, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")="canonical"]/@href'
    )
    if c:
        canonical = text_or_none(c[0])

    # Headings (joined with |)
    h1 = " | ".join([t.strip() for t in doc.xpath("//h1//text()") if t.strip()]) or None
    h2 = " | ".join([t.strip() for t in doc.xpath("//h2//text()") if t.strip()]) or None
    h3 = " | ".join([t.strip() for t in doc.xpath("//h3//text()") if t.strip()]) or None

    # Robots meta
    robots = None
    rbt = doc.xpath(
        '//meta[translate(@name, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")="robots"]/@content'
    )
    if rbt:
        robots = text_or_none(rbt[0])

    rel_canonical = canonical

    # Language
    lang = None
    lang_attr = doc.xpath("//@lang")
    if lang_attr:
        for l in lang_attr:
            if l and len(l) <= 10:
                lang = l
                break

    return title, meta_desc, canonical, h1, h2, h3, robots, rel_canonical, lang
```

---

## Link & Media Extraction

```python
def parse_links_media(raw_html: bytes, base_url: str, domain: str):
    """Extract all links and images with metadata."""
    try:
        doc = lxml_html.fromstring(raw_html)
        doc.make_links_absolute(base_url)
    except Exception:
        return [], []

    links = []
    for a in doc.xpath("//a[@href]"):
        href = a.get("href")
        anchor = (a.text_content() or "").strip()
        rel = a.get("rel") or None
        rel_str = ",".join(rel) if isinstance(rel, (list, tuple)) else (rel or None)
        nofollow = 1 if (rel_str and "nofollow" in rel_str.lower()) else 0
        dst = normalize_url(href)
        is_internal = 1 if dst.startswith(domain.rstrip("/")) else 0
        links.append((base_url, dst, anchor, rel_str, nofollow, is_internal))

    media = []
    for img in doc.xpath("//img[@src]"):
        src = img.get("src")
        src = absolutize(src, base_url)
        alt = img.get("alt") or None
        media.append((src, base_url, alt, "img"))

    return links, media
```

---

## What's Good / Usable

1. **Case-insensitive XPath** - Handles inconsistent HTML
2. **Multiple heading support** - Joins all h1/h2/h3 with ` | `
3. **Nofollow detection** - Tracks rel="nofollow" links
4. **Internal/external classification** - Domain-based link categorization
5. **URL normalization** - Strips fragments, normalizes slashes

---

## What Must Be Rewritten

1. Add **schema.org extraction** for structured data
2. Add **Open Graph / Twitter Cards** extraction
3. Add **more media types** (video, audio, iframes)

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Others |
|---------|------------------|--------|
| SEO elements | Full (title, meta, h1-3, canonical, robots) | Partial |
| Link classification | Internal/external | None |
| Nofollow detection | Yes | No |
| Case-insensitive | Yes | No |

**Recommendation**: Use Competitor-Intel parser for all HTML parsing in AutoBiz.
