---
id: data_extractors_competitor_intel
type: extraction
subject: data_extractors
source_repo: Competitor-Intel
description: "Text extraction (Trafilatura) and structured data extraction (extruct)"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extractors, trafilatura, extruct, json-ld, microdata, competitor-intel]
---

# Data Extractors: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/extract/text.py`, `competitor_intel/extract/structured.py`

---

## 1. Text Extraction (Trafilatura)

```python
import gzip
import re
import sqlite3
from pathlib import Path

def extract_text(conn: sqlite3.Connection, data_dir: Path) -> int:
    """Extract main body text from HTML using Trafilatura."""
    try:
        import trafilatura
    except Exception:
        print("[WARN] trafilatura not installed - skipping.")
        return 0

    cur = conn.execute(
        "SELECT url, html_path FROM pages "
        "WHERE html_path IS NOT NULL AND url NOT IN (SELECT page_url FROM texts)"
    )
    rows = cur.fetchall()
    if not rows:
        return 0

    done = 0
    for url, html_path in rows:
        try:
            with gzip.open(html_path, "rb") as f:
                raw = f.read()

            # Extract main content (no comments, no tables)
            extracted = trafilatura.extract(
                raw,
                include_comments=False,
                include_tables=False
            )
            if not extracted:
                extracted = ""

            # Count tokens and words
            tokens = len(re.findall(r"\b\w+\b", extracted.lower()))
            wc = len(extracted.split())

            conn.execute(
                "INSERT OR REPLACE INTO texts(page_url, text, tokens, word_count) VALUES(?,?,?,?)",
                (url, extracted, tokens, wc)
            )
            done += 1
        except Exception:
            continue

    conn.commit()
    return done
```

**Key Features**:
- Uses **Trafilatura** for boilerplate removal
- Excludes comments and tables
- Stores token and word counts

---

## 2. Structured Data Extraction (extruct)

```python
import gzip
import json
import sqlite3

def extract_structured(conn: sqlite3.Connection) -> int:
    """Extract JSON-LD, microdata, RDFa, OpenGraph, microformat."""
    try:
        import extruct
        from w3lib.html import get_base_url
    except Exception:
        print("[WARN] extruct/w3lib not installed - skipping.")
        return 0

    cur = conn.execute("SELECT url, html_path FROM pages WHERE html_path IS NOT NULL")
    rows = cur.fetchall()

    total = 0
    for url, html_path in rows:
        try:
            with gzip.open(html_path, "rb") as f:
                raw = f.read()

            base_url = get_base_url(raw, url)
            data = extruct.extract(
                raw,
                base_url=base_url,
                syntaxes=["json-ld", "microdata", "rdfa", "opengraph", "microformat"]
            )

            for syntax, items in data.items():
                if not items:
                    continue
                for item in items:
                    t = None
                    if isinstance(item, dict):
                        t = item.get("@type") or item.get("type")
                        if isinstance(t, list):
                            t = ",".join(map(str, t))

                    conn.execute(
                        "INSERT INTO structured(page_url, syntax, type, json) VALUES(?,?,?,?)",
                        (url, syntax, t, json.dumps(item, ensure_ascii=False))
                    )
                    total += 1
        except Exception:
            continue

    conn.commit()
    return total
```

**Supported Syntaxes**:
- `json-ld` - JSON Linked Data (schema.org)
- `microdata` - HTML5 microdata
- `rdfa` - RDFa attributes
- `opengraph` - Facebook Open Graph
- `microformat` - Microformats

---

## What's Good / Usable

1. **Trafilatura** - Best-in-class boilerplate removal
2. **Multi-format extraction** - 5 structured data formats
3. **Type extraction** - Stores @type for filtering
4. **Graceful degradation** - Skips if libraries missing

---

## What Must Be Rewritten

1. Add **parallel processing** for large sites
2. Add **extraction validation** for malformed data
3. Add **caching** to avoid re-extraction

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Market_AI | Others |
|---------|------------------|-----------|--------|
| Text extraction | Trafilatura | None | None |
| Structured data | extruct (5 formats) | None | None |
| Token counting | Yes | None | None |

**Recommendation**: UNIQUE - Only repo with text/structured extraction. Use for AutoBiz.

---

## Dependencies

```
trafilatura>=1.6.0
extruct>=0.14.0
w3lib>=2.1.0
```
