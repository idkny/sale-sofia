---
id: analysis_competitor_intel
type: extraction
subject: analysis
source_repo: Competitor-Intel
description: "SEO analysis: keyword usage mapping and CSV report generation"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [analysis, seo, keywords, reports, csv, competitor-intel]
---

# Analysis Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/analysis/usage_map.py`, `competitor_intel/analysis/reports.py`

---

## 1. Keyword Usage Mapping

Maps where keywords appear on each page (title, h1, h2, anchors, alt text, body).

```python
import sqlite3
from typing import Dict

def usage_map(conn: sqlite3.Connection) -> int:
    """Map phrase presence across page elements."""
    # Get all (page_url, phrase) pairs
    cur = conn.execute("SELECT DISTINCT page_url, phrase FROM phrases")
    pairs = cur.fetchall()
    if not pairs:
        return 0

    # Preload page SEO fields
    pages = {}
    cur2 = conn.execute("SELECT url, title, h1, h2, h3 FROM pages")
    for row in cur2.fetchall():
        pages[row[0]] = {
            "title": (row[1] or "").lower(),
            "h1": (row[2] or "").lower(),
            "h2": (row[3] or "").lower(),
            "h3": (row[4] or "").lower(),
        }

    # Preload anchor text (aggregated per source page)
    anchors: Dict[str, str] = {}
    cur3 = conn.execute(
        "SELECT src_url, GROUP_CONCAT(LOWER(anchor), ' || ') FROM links GROUP BY src_url"
    )
    for src, agg in cur3.fetchall():
        anchors[src] = (agg or "").lower()

    # Preload alt text (aggregated per page)
    alts: Dict[str, str] = {}
    cur4 = conn.execute(
        "SELECT page_url, GROUP_CONCAT(LOWER(alt_text), ' || ') FROM media GROUP BY page_url"
    )
    for src, agg in cur4.fetchall():
        alts[src] = (agg or "").lower()

    # Preload body text
    bodies: Dict[str, str] = {}
    cur5 = conn.execute("SELECT page_url, LOWER(text) FROM texts")
    for u, t in cur5.fetchall():
        bodies[u] = (t or "").lower()

    # Map presence for each (page, phrase) pair
    total = 0
    for page_url, phrase in pairs:
        p = phrase.lower().strip()
        pf = pages.get(page_url, {"title": "", "h1": "", "h2": "", "h3": ""})

        in_title = 1 if p and p in pf["title"] else 0
        in_h1 = 1 if p and p in pf["h1"] else 0
        in_h2 = 1 if p and p in pf["h2"] else 0
        in_h3 = 1 if p and p in pf["h3"] else 0
        in_anchor = 1 if p and p in anchors.get(page_url, "") else 0
        in_alt = 1 if p and p in alts.get(page_url, "") else 0
        in_body = 1 if p and p in bodies.get(page_url, "") else 0

        conn.execute(
            """INSERT INTO phrase_usage
               (page_url, phrase, in_title, in_h1, in_h2, in_anchor, in_alt, in_body)
               VALUES(?,?,?,?,?,?,?,?)""",
            (page_url, phrase, in_title, in_h1, in_h2, in_anchor, in_alt, in_body)
        )
        total += 1

    conn.commit()
    return total
```

---

## 2. Report Generation

```python
import csv
import sqlite3
from pathlib import Path
from typing import List
import pandas as pd

def exports(conn: sqlite3.Connection, exports_dir: Path) -> List[Path]:
    """Generate CSV reports for SEO analysis."""
    out_paths: List[Path] = []

    # 1. Sitewide keyword aggregation
    q1 = """
    SELECT
      phrase,
      COUNT(DISTINCT page_url) AS pages_coverage,
      SUM(COALESCE(in_title,0)) AS in_title_pages,
      SUM(COALESCE(in_h1,0)) AS in_h1_pages,
      SUM(COALESCE(in_anchor,0)) AS in_anchor_pages,
      SUM(COALESCE(in_alt,0)) AS in_alt_pages,
      SUM(COALESCE(in_body,0)) AS in_body_pages
    FROM phrase_usage
    GROUP BY phrase
    HAVING pages_coverage >= 2
    ORDER BY pages_coverage DESC, in_title_pages DESC, in_h1_pages DESC
    LIMIT 2000
    """
    df1 = pd.read_sql_query(q1, conn)
    p1 = exports_dir / "keywords_sitewide.csv"
    df1.to_csv(p1, index=False, quoting=csv.QUOTE_NONNUMERIC)
    out_paths.append(p1)

    # 2. Representative URLs per phrase (weighted strength)
    q2 = """
    SELECT pu.phrase, pu.page_url,
           (pu.in_title + pu.in_h1*0.9 + pu.in_body*0.5 + pu.in_anchor*0.4 + pu.in_alt*0.2) AS strength
    FROM phrase_usage pu
    WHERE pu.phrase IN (
        SELECT phrase FROM (
            SELECT phrase, COUNT(DISTINCT page_url) c FROM phrase_usage GROUP BY phrase HAVING c >= 2
        )
    )
    ORDER BY phrase, strength DESC
    """
    df2 = pd.read_sql_query(q2, conn)
    df2 = df2.groupby("phrase").head(5).reset_index(drop=True)  # Top 5 per phrase
    p2 = exports_dir / "keywords_representative_urls.csv"
    df2.to_csv(p2, index=False, quoting=csv.QUOTE_NONNUMERIC)
    out_paths.append(p2)

    # 3. Structured data types summary
    q3 = """
    SELECT type, syntax, COUNT(*) as cnt
    FROM structured
    GROUP BY type, syntax
    ORDER BY cnt DESC
    """
    df3 = pd.read_sql_query(q3, conn)
    p3 = exports_dir / "schema_types.csv"
    df3.to_csv(p3, index=False, quoting=csv.QUOTE_NONNUMERIC)
    out_paths.append(p3)

    return out_paths
```

---

## Strength Formula

```
strength = in_title*1.0 + in_h1*0.9 + in_body*0.5 + in_anchor*0.4 + in_alt*0.2
```

| Element | Weight | Rationale |
|---------|--------|-----------|
| Title | 1.0 | Most important for SEO |
| H1 | 0.9 | Primary heading |
| Body | 0.5 | Content relevance |
| Anchor | 0.4 | Internal linking signal |
| Alt | 0.2 | Accessibility/image SEO |

---

## What's Good / Usable

1. **Comprehensive mapping** - 7 page elements tracked
2. **Weighted strength** - Prioritizes title/h1 over body
3. **Aggregated reports** - Sitewide keyword coverage
4. **Representative URLs** - Best pages per keyword

---

## What Must Be Rewritten

1. Add **JSON export** in addition to CSV
2. Add **domain-level aggregation** for multi-competitor analysis
3. Add **trend analysis** using page_history

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Others |
|---------|------------------|--------|
| Usage mapping | 7 elements | None |
| Strength formula | Yes (weighted) | None |
| CSV reports | 3 reports | None |
| Sitewide aggregation | Yes | None |

**Recommendation**: UNIQUE - Only repo with SEO analysis. Use for AutoBiz content features.
