---
id: 20251201_automation_autobiz
type: extraction
subject: automation
source_repo: Auto-Biz
description: "Celery task patterns, setup automation from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [automation, celery, tasks, setup, auto-biz]
---

# SUBJECT: automation/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `auto_biz/celery_app.py`, `auto_biz/tasks/proxies.py`, `setup.sh`, `start_worker.sh`

---

## 1. EXTRACTED CODE

### 1.1 Celery Application Setup

```python
from celery import Celery

app = Celery(
    "auto_biz",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["auto_biz.tasks.proxies"],
)

app.conf.task_default_queue = "auto_biz"
```

### 1.2 Celery Task Patterns (chord/group/chain)

```python
"""Celery tasks demonstrating advanced patterns."""

from celery import group, chord, chain
from auto_biz.celery_app import app as celery_app


# Pattern 1: Task chaining (sequential)
@celery_app.task
def scrape_new_proxies_task():
    """Scrape proxies, then auto-trigger checking."""
    # ... scraping logic ...
    check_scraped_proxies_task.delay()  # Chain to next task
    return "Scraped proxies"


# Pattern 2: Group + Chain (parallel then sequential)
@celery_app.task
def check_scraped_proxies_task():
    """Dispatcher: Orchestrates multi-stage validation."""
    # Split work into chunks
    chunk_size = 100
    proxy_chunks = [all_proxies[i:i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]

    # Parallel execution (group) followed by sequential processing (chain)
    header = group(mubeng_check_chunk_task.s(chunk) for chunk in proxy_chunks)
    callback_chain = chain(
        combine_mubeng_results_task.s(),
        dispatch_quality_checks_task.s()
    )
    chord(header)(callback_chain)

    return f"Dispatched {len(proxy_chunks)} chunks"


# Pattern 3: Chord (fan-out, fan-in)
@celery_app.task
def dispatch_quality_checks_task(proxies: list):
    """Fan-out to parallel quality checks, then collect results."""
    callback = process_final_results_task.s()
    header = group(sequential_quality_check_task.s(proxy) for proxy in proxies)
    (header | callback).delay()


# Pattern 4: Worker task with timeout
@celery_app.task
def mubeng_check_chunk_task(proxy_chunk: list):
    """Worker task with timeout handling."""
    try:
        subprocess.run(cmd, check=True, timeout=120)  # 2 minute timeout
    except subprocess.TimeoutExpired:
        logger.error("Task timed out")
    return results


# Pattern 5: Task signature composition
@celery_app.task
def scrape_if_missing():
    """Chain scrape -> check if file missing."""
    if not file_exists:
        (scrape_new_proxies_task.s() | check_scraped_proxies_task.s()).delay()
```

### 1.3 Worker Startup Script

```bash
#!/bin/bash
# start_worker.sh
cd /path/to/project
source venv/bin/activate
export AUTO_BIZ_PROJECT_ROOT=$(pwd)
export PYTHONPATH=$AUTO_BIZ_PROJECT_ROOT:$PYTHONPATH

celery -A auto_biz.celery_app worker \
    --loglevel=INFO \
    --concurrency=4 \
    -Q auto_biz
```

### 1.4 Setup Automation Script

```bash
#!/bin/bash
set -e

echo "[INFO] Starting setup..."

# Helpers
is_installed() { dpkg -s "$1" &>/dev/null; }
is_command() { command -v "$1" &>/dev/null; }

# Python Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# pre-commit setup
if is_command pre-commit; then
    pre-commit install
else
    pip install pre-commit && pre-commit install
fi

# Camoufox browser engine
if python -m camoufox --help &>/dev/null; then
    python -m camoufox fetch
fi

# Create directories
mkdir -p proxies/external/proxy-scraper-checker

# Download Mubeng binary
MUBENG_VERSION="0.22.0"
MUBENG_PATH="proxies/external/mubeng"
if [ ! -f "$MUBENG_PATH" ]; then
    wget -q "https://github.com/mubeng/mubeng/releases/download/v$MUBENG_VERSION/mubeng_${MUBENG_VERSION}_linux_amd64" -O "$MUBENG_PATH"
    chmod +x "$MUBENG_PATH"
fi

# Download Ungoogled Chromium
INSTALL_DIR="$HOME/.local/share/fingerprint-chromium/ungoogled-chromium"
LATEST_URL=$(wget -qO- https://api.github.com/repos/adryfish/fingerprint-chromium/releases/latest |
    grep "browser_download_url.*linux.tar.xz" | cut -d '"' -f 4 | head -n 1)

if [ -n "$LATEST_URL" ]; then
    TEMP_DIR=$(mktemp -d)
    wget -q "$LATEST_URL" -O "$TEMP_DIR/chromium.tar.xz"
    tar -xf "$TEMP_DIR/chromium.tar.xz" -C "$TEMP_DIR"
    mv "$TEMP_DIR"/* "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/chrome"
    rm -rf "$TEMP_DIR"
fi

echo "[DONE] Setup completed successfully."
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **Celery chord/group/chain**: Production-ready parallel processing
2. **Task chaining**: Auto-trigger next task on completion
3. **Chunking pattern**: Split large workloads
4. **Timeout handling**: subprocess with timeout
5. **Setup script**: Complete automation for dependencies + binaries

### What is Outdated

Nothing - patterns are current

### What Must Be Rewritten

1. **Hardcoded values**: Chunk size, timeouts should be configurable
2. **Error recovery**: Could add retry decorators

### Conflicts with Previous Repos

| Pattern | Auto-Biz | Ollama-Rag | Best |
|---------|----------|------------|------|
| Task queue | Celery | None | **Auto-Biz** |
| Server management | None | Yes (health checks) | **Ollama-Rag** |
| Setup automation | Full | Partial | **Auto-Biz** |
| Binary download | Yes | No | **Auto-Biz** |

### Best Version Recommendation

**Auto-Biz is BEST for automation**:
- Only repo with Celery integration
- Complete setup.sh for reproducible environments
- Advanced task patterns (chord, group, chain)
