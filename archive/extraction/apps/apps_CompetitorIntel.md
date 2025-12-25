---
id: apps_competitor_intel
type: extraction
subject: apps
source_repo: Competitor-Intel
description: "Streamlit dashboard for competitor intelligence and crawl reports"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [apps, streamlit, dashboard, visualization, competitor-intel]
---

# Apps Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `apps/competitor_dashboard.py`

---

## Overview

Full-featured Streamlit dashboard:
- Competitor comparison (multi-domain)
- Deep dive per domain
- Crawl diagnostics
- Log parsing
- CSV exports

---

## Key Components

### 1. Domain Rollup Metrics

```python
def build_domain_rollups(db: dict) -> pd.DataFrame:
    """Aggregate metrics per domain."""
    page = db.get("pages", pd.DataFrame())

    grp = page.groupby("domain")
    metrics = {
        "total_urls": grp.size(),
        "fetched_urls": grp.apply(lambda g: g["status"].notna().sum()),
        "success_2xx": grp.apply(lambda g: (200 <= g["status"]) & (g["status"] < 300)).sum()),
        "client_err_4xx": grp.apply(lambda g: (400 <= g["status"]) & (g["status"] < 500)).sum()),
        "server_err_5xx": grp.apply(lambda g: (500 <= g["status"]) & (g["status"] < 600)).sum()),
    }

    out = pd.concat(metrics.values(), axis=1)
    out["success_rate"] = out["success_2xx"] / out["fetched_urls"]
    out["error_rate"] = (out["client_err_4xx"] + out["server_err_5xx"]) / out["fetched_urls"]

    return out.reset_index()
```

### 2. Log Parsing (Regex)

```python
import re

LOG_STATUS_RE = re.compile(r"\b(?:status[:= ]|HTTP(?:/\d\.\d)?\s+)(\d{3})\b")
LOG_URL_RE = re.compile(r"https?://[^\s\"']+")
LOG_ERR_RE = re.compile(r"\b([A-Za-z_]*Error|Exception|Timeout|Refused)\b", re.IGNORECASE)
LOG_TS_RE = re.compile(r"\b(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\b")

def parse_log(log_path: str):
    """Parse crawl log for status codes, URLs, errors."""
    rows = []
    with open(log_path, "r", errors="ignore") as f:
        for i, line in enumerate(f, start=1):
            url = LOG_URL_RE.search(line)
            status = LOG_STATUS_RE.search(line)
            err = LOG_ERR_RE.search(line)
            ts = LOG_TS_RE.search(line)

            rows.append({
                "line_no": i,
                "timestamp": ts.group("ts") if ts else None,
                "url": url.group(0) if url else None,
                "status": int(status.group(1)) if status else None,
                "error": err.group(1) if err else None,
                "raw": line.strip(),
            })

    return pd.DataFrame(rows)
```

### 3. Dashboard Layout

```python
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Competitor Intel", layout="wide")

# Sidebar
db_path = st.sidebar.text_input("SQLite DB path", default_db)
log_path = st.sidebar.text_input("Crawl log path", default_log)

# Load data
db = load_db(db_path)
rollups = build_domain_rollups(db)

# 1. Competitor Comparison
st.subheader("1) Competitor Comparison")
selected = st.multiselect("Choose domains", options=domains)
cmp = rollups[rollups["domain"].isin(selected)]

# KPI metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total URLs", cmp["total_urls"].sum())
col2.metric("Success Rate", f"{cmp['success_rate'].mean():.0%}")
col3.metric("Error Rate", f"{cmp['error_rate'].mean():.0%}")

# Charts
fig = px.bar(cmp, x="domain", y=["success_2xx", "client_err_4xx", "server_err_5xx"],
             barmode="stack", title="Fetch Outcomes")
st.plotly_chart(fig)

# 2. Deep Dive
st.subheader("2) Deep Dive per Competitor")
target = st.selectbox("Choose domain", options=selected)
# ... detailed page-level analysis

# 3. Crawl Diagnostics
st.subheader("3) Crawl Diagnostics")
events_df, errors_df, status_df = parse_log(log_path)
# ... error analysis, status distribution
```

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-domain comparison | Side-by-side competitor analysis |
| KPI metrics | Total URLs, success rate, error rate |
| Stacked bar charts | Fetch outcomes by domain |
| Deep dive | Page-level analysis per domain |
| Log parsing | Status codes, errors from crawl log |
| CSV export | Download buttons for all data |

---

## What's Good / Usable

1. **Comprehensive metrics** - All SEO-relevant data points
2. **Interactive filtering** - Domain selection, status filtering
3. **Plotly visualizations** - Professional charts
4. **Log analysis** - Crawl diagnostics from logs
5. **Export capability** - Download CSV for any view

---

## What Must Be Rewritten

1. Add **real-time updates** during crawl
2. Add **trend charts** from page_history
3. Add **authentication** for multi-user

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Others |
|---------|------------------|--------|
| Dashboard | Streamlit (full) | None |
| Visualizations | Plotly | None |
| Log parsing | Yes | None |

**Recommendation**: UNIQUE - Only repo with visualization. Adapt for AutoBiz monitoring.

---

## Dependencies

```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.18.0
python-dateutil>=2.8.0
```
