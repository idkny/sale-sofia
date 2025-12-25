---
id: 20251201_config_autobiz
type: extraction
subject: config
source_repo: Auto-Biz
description: "Configuration patterns, paths management, project setup from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [config, paths, setup, pyproject, auto-biz]
---

# SUBJECT: config/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `config.py`, `paths.py`, `pyproject.toml`, `setup.sh`

---

## 1. EXTRACTED CODE

### 1.1 Centralized Path Management (EXCELLENT PATTERN)

```python
"""Defines and manages file paths for the Auto-Biz project."""

from pathlib import Path
import os

# Base project directory
PROJECT_ROOT = Path(os.environ.get("AUTO_BIZ_PROJECT_ROOT", Path(__file__).parent))

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
LOGS_DIR = DATA_DIR / "logs"
HTML_DIR = DATA_DIR / "html"
REPORT_DIR = DATA_DIR / "report"

# Proxy related paths
PROXIES_DIR = PROJECT_ROOT / "proxies"
PROXY_CHECKER_DIR = PROXIES_DIR / "external" / "proxy-scraper-checker"
MUBENG_EXECUTABLE_PATH = PROXIES_DIR / "external" / "mubeng"
PSC_EXECUTABLE_PATH = PROXY_CHECKER_DIR / "target" / "release" / "proxy-scraper-checker"

# Browser related paths
BROWSERS_DIR = PROJECT_ROOT / "browsers"
CAMOUFOX_PROFILE_DIR = BROWSERS_DIR / "profile" / "camoufox"
FINGERPRINT_CHROMIUM_PROFILE_DIR = BROWSERS_DIR / "profile" / "fingerprint-chromium"
CHROMIUM_DIR = Path.home() / ".local" / "share" / "fingerprint-chromium"
CHROMIUM_EXECUTABLE_PATH = CHROMIUM_DIR / "ungoogled-chromium" / "chrome"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
HTML_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
PROXIES_DIR.mkdir(exist_ok=True)
BROWSERS_DIR.mkdir(exist_ok=True)
CAMOUFOX_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
FINGERPRINT_CHROMIUM_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
```

### 1.2 Application Configuration

```python
"""Configuration settings for the Auto-Biz project."""

# Proxy settings
PROXY_VALID_THRESHOLD = 10  # Minimum number of live proxies required

# Search settings
SEARCH_QUERIES = [
    {"keywords": "real estate Bulgaria", "region": "BG", "language": "bg"},
    {"keywords": "apartments for sale Sofia", "region": "BG", "language": "bg"},
]

SEARCH_SETTINGS = {
    "ddg": {"max_results": 50},
    "serp": {"gl": "bg", "hl": "bg", "num": 20},
}

# RAG settings
RAG_CONFIG = {
    "tasks": {
        "url_classification": {
            "llm_provider": "ollama",
            "model_name": "llama3",
            "temperature": 0.3,
        }
    }
}
```

### 1.3 pyproject.toml (Modern Python Config)

```toml
[project]
name = "auto-biz"
version = "0.1.0"
description = "Auto-Biz Intelligence project"
requires-python = ">=3.9"
readme = "README.md"
license = { text = "MIT" }

[tool.black]
line-length = 120
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 120
multi_line_output = 3
include_trailing_comma = true

[tool.ruff]
line-length = 120
target-version = "py39"
exclude = [".git", "__pycache__", "build", "dist", "venv", "docs", "data", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "C", "N", "D", "UP", "B", "A", "ANN", "ASYNC", "S", "TID", "PERF", "RUF"]
```

### 1.4 Setup Script (Automation)

```bash
#!/bin/bash
set -e

echo "[INFO] Starting setup..."

# --- Helpers ---
is_installed() { dpkg -s "$1" &>/dev/null; }
is_command() { command -v "$1" &>/dev/null; }

# --- Ensure pip is up-to-date ---
python -m pip install --upgrade pip

# --- Python Dependencies ---
pip install -r requirements.txt

# --- pre-commit setup ---
if is_command pre-commit; then
  pre-commit install
else
  pip install pre-commit && pre-commit install
fi

# --- Camoufox ---
if python -m camoufox --help &>/dev/null; then
  python -m camoufox fetch
fi

# --- Directory Structure ---
mkdir -p proxies/external/proxy-scraper-checker

# --- Mubeng Binary ---
MUBENG_VERSION="0.22.0"
MUBENG_DIR="proxies/external"
MUBENG_PATH="$MUBENG_DIR/mubeng"

if [ ! -f "$MUBENG_PATH" ]; then
  wget -q "https://github.com/mubeng/mubeng/releases/download/v$MUBENG_VERSION/mubeng_${MUBENG_VERSION}_linux_amd64" -O "$MUBENG_PATH"
  chmod +x "$MUBENG_PATH"
fi

# --- Ungoogled Chromium ---
FPC_REPO="https://github.com/adryfish/fingerprint-chromium"
INSTALL_BASE="$HOME/.local/share/fingerprint-chromium"
INSTALL_DIR="$INSTALL_BASE/ungoogled-chromium"

LATEST_URL=$(wget -qO- https://api.github.com/repos/adryfish/fingerprint-chromium/releases/latest |
  grep "browser_download_url.*linux.tar.xz" |
  cut -d '"' -f 4 | head -n 1)

if [ -z "$LATEST_URL" ]; then
  echo "[ERROR] Could not find the latest fingerprint-chromium release."
  exit 1
fi

# Download and install if not present...
echo "[DONE] Setup completed successfully."
```

### 1.5 Celery Configuration

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

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **Centralized paths.py**: EXCELLENT pattern - all paths in one place
2. **Auto-create directories**: mkdir(exist_ok=True) on import
3. **Environment override**: PROJECT_ROOT from env or __file__
4. **Modern pyproject.toml**: Black, isort, ruff configured
5. **Setup automation**: Complete setup.sh with binary downloads
6. **Celery config**: Clean and simple

### What is Outdated

1. **Dict-based config**: No Pydantic validation (MarketIntel has this)

### What Must Be Rewritten

1. **Add Pydantic Settings**: For type-safe config

### Conflicts with Previous Repos

| Pattern | Auto-Biz | MarketIntel | Scraper | Best |
|---------|----------|-------------|---------|------|
| Paths | Centralized module | Basic | Centralized module | **Auto-Biz/Scraper** |
| Config validation | Dict | Pydantic | Dict | **MarketIntel** |
| Setup script | Complete | None | None | **Auto-Biz** |
| Celery | Yes | No | No | **Auto-Biz** |
| pyproject.toml | Yes | Yes | Partial | **Auto-Biz** |

### Best Version Recommendation

**Auto-Biz paths.py + MarketIntel Pydantic Settings**:
- Auto-Biz has best path management and setup automation
- MarketIntel has Pydantic validation for type safety
