---
id: cli_competitor_intel
type: extraction
subject: cli
source_repo: Competitor-Intel
description: "argparse CLI with 7-step pipeline orchestration"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [cli, argparse, pipeline, orchestration, competitor-intel]
---

# CLI Extraction: Competitor-Intel

**Source**: `idkny/Competitor-Intel`
**Files**: `competitor_intel/cli/main.py`

---

## Overview

argparse-based CLI with:
- Subcommand structure (9 commands)
- 7-step pipeline in `run-all`
- Proxy integration
- Logging to file + console

---

## CLI Structure

```python
import argparse
from pathlib import Path

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Competitor Intel Pipeline")
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("--db", default="./db/competitor.sqlite")
        sp.add_argument("--data", default="./data")
        sp.add_argument("--exports", default="./data/exports")
        sp.add_argument("--domains", nargs="+", default=["https://example.com/"])

    def add_proxy_args(sp):
        sp.add_argument("--use-proxies", action="store_true")
        sp.add_argument("--proxy-file", default="./proxies.json")
        sp.add_argument("--proxy-protocols", nargs="+", choices=["http", "https", "socks4", "socks5"])

    # Subcommands
    sp = sub.add_parser("init-db"); common(sp)
    sp = sub.add_parser("enumerate"); common(sp)
    sp = sub.add_parser("fetch-parse"); common(sp); add_proxy_args(sp)
    sp = sub.add_parser("extract-text"); common(sp)
    sp = sub.add_parser("extract-structured"); common(sp)
    sp = sub.add_parser("phrase-mine"); common(sp)
    sp = sub.add_parser("usage-map"); common(sp)
    sp = sub.add_parser("export"); common(sp)
    sp = sub.add_parser("run-all"); common(sp); add_proxy_args(sp)

    return p.parse_args(argv or ["run-all"])
```

---

## 7-Step Pipeline

```
Step 1: enumerate      - Discover URLs from sitemaps
Step 2: fetch-parse    - Crawl pages, extract SEO elements
Step 3: extract-text   - Extract body content (Trafilatura)
Step 4: extract-structured - Extract JSON-LD, microdata
Step 5: phrase-mine    - NLP keyword extraction
Step 6: usage-map      - Map keywords to page elements
Step 7: export         - Generate CSV reports
```

---

## What's Good / Usable

1. **Modular subcommands** - Run individual steps or full pipeline
2. **Default fallback** - `run-all` if no args
3. **Common args pattern** - DRY definition
4. **Proxy integration** - Built-in validation

---

## Cross-Repo Comparison

| Feature | Competitor-Intel | Auto-Biz |
|---------|------------------|----------|
| Subcommands | 9 | Multiple |
| Pipeline steps | 7 | Celery tasks |
| Proxy integration | Yes | No |

**Recommendation**: Use this pipeline structure for AutoBiz CLI.
