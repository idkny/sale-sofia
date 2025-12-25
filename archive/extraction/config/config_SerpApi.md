---
id: 20251201_config_serpapi
type: extraction
subject: configuration
source_repo: idkny/SerpApi
source_file: Note.md + .env + .gitignore
description: "Configuration patterns from SerpApi planning document"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, configuration, env, serpapi]
---

# CONFIGURATION - SerpApi

**Source**: `idkny/SerpApi/Note.md`, `.env`, `.gitignore`
**Type**: Specification + actual config files

---

## EXTRACTED CONFIGURATION CODE

### 1. Environment Variable Loading

```python
# src/config.py

import os
from typing import Optional

# Load from environment (expects .env file or system env vars)
SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")

if not SERPAPI_API_KEY:
    raise EnvironmentError(
        "SERPAPI_API_KEY not found. "
        "Set it in .env file or as environment variable."
    )

# Database configuration
DATABASE_FILE: str = os.getenv("DATABASE_FILE", "market_intelligence.db")

# API configuration
DEFAULT_DEVICE: str = os.getenv("DEFAULT_DEVICE", "desktop")
DEFAULT_NUM_RESULTS: int = int(os.getenv("DEFAULT_NUM_RESULTS", "20"))
```

---

### 2. .env File Structure

```bash
# .env template (actual key REDACTED)
SERPAPI_KEY=your_serpapi_key_here
```

**Note**: Key naming inconsistency - file uses `SERPAPI_KEY`, code expects `SERPAPI_API_KEY`.

---

### 3. .gitignore Patterns (Data & Cache)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.python-version
.venv/
venv/
env/
ENV/
build/
dist/
.eggs/
*.egg-info/
pip-wheel-metadata/
pip-log.txt
.tox/
.nox/
.mypy_cache/
.pytest_cache/
.pyre/
.ruff_cache/
.dmypy.json
.coverage
.coverage.*
htmlcov/

# Notebooks
.ipynb_checkpoints/

# Project data/artifacts
data/serp.db
data/*.db
data/*.sqlite*
*.sqlite
*.sqlite3
*.db-journal
*.db-shm
*.db-wal
data/cache/
cache/
logs/
*.log
output/
/reports/
tmp/
temp/
```

**Key patterns**:
- Database files: `*.db`, `*.sqlite*`, WAL files
- Cache directories: `data/cache/`, `cache/`
- Output directories: `output/`, `reports/`, `tmp/`

---

### 4. Module Architecture (Specified Structure)

```
your_project_directory/
├── .env                    # API keys (gitignored)
├── venv/                   # Virtual environment
└── src/
    ├── config.py           # Configuration constants
    ├── db_interface.py     # Database CRUD operations
    ├── api_client.py       # SerpAPI client functions
    ├── data_extractor.py   # JSON parsing functions
    ├── main.py             # Orchestration script
    ├── keyword_manager.py  # Keyword review CLI
    └── scripts/
        └── db.py           # SQL schema definitions
```

---

### 5. Configuration Parameters Specified

```python
# Target locations (would be in config or loaded from DB)
TARGET_CITIES = [
    {"city": "Dallas", "state": "Texas", "country": "United States"},
    {"city": "Houston", "state": "Texas", "country": "United States"},
    {"city": "Austin", "state": "Texas", "country": "United States"},
    {"city": "San Antonio", "state": "Texas", "country": "United States"},
    {"city": "Fort Worth", "state": "Texas", "country": "United States"},
]

# Core keywords (direct business queries)
CORE_KEYWORDS = [
    "air duct cleaning",
    "air duct cleaning near me",
    "hvac duct cleaning",
    "dryer vent cleaning",
    "air duct cleaning cost",
    "air duct cleaning service",
]

# Indirect keywords (related/discovery queries)
INDIRECT_KEYWORDS = [
    "improve indoor air quality",
    "reduce allergies at home",
    "hvac maintenance tips",
    "home air quality testing",
]
```

---

### 6. SerpAPI Engine Configuration

```python
# Engine-to-function mapping
SERPAPI_ENGINES = {
    'google': {
        'function': 'call_google_search_api',
        'required_params': ['q', 'location'],
        'optional_params': ['device', 'num', 'start', 'no_cache', 'json_restrictor'],
    },
    'google_local': {
        'function': 'call_google_local_api',
        'required_params': ['q', 'location'],
    },
    'google_maps_reviews': {
        'function': 'call_google_maps_reviews_api',
        'required_params': ['place_id'],
    },
    'google_trends': {
        'function': 'call_google_trends_api',
        'required_params': ['q', 'geo', 'date', 'data_type'],
        'optional_params': ['include_low_search_volume'],
    },
    'google_news': {
        'function': 'call_google_news_api',
        'required_params': ['q', 'location'],
    },
    'google_autocomplete': {
        'function': 'call_google_autocomplete_api',
        'required_params': ['q'],
    },
}

# Trends data types
TRENDS_DATA_TYPES = [
    'TIMESERIES',
    'RELATED_TOPICS',
    'RELATED_QUERIES',
    'GEO_MAP',
]

# Keyword status values
KEYWORD_STATUSES = [
    'pending_review',
    'approved',
    'rejected',
]
```

---

## CONCLUSIONS

### What is Good / Usable

1. **Environment variable pattern** - API keys in .env, not code
2. **Comprehensive .gitignore** - Covers Python, data, cache properly
3. **Module structure** - Clean separation of concerns
4. **Engine registry** - Configurable API endpoints
5. **Status enums** - Clear workflow states

### What is Outdated

1. **No Pydantic Settings** - Using raw os.getenv
2. **Key naming mismatch** - .env uses `SERPAPI_KEY`, code expects `SERPAPI_API_KEY`
3. **Hardcoded lists** - Keywords/locations in code, not config file
4. **No validation** - Missing type checking on config values

### What Must Be Rewritten

1. **Use Pydantic BaseSettings** - Type-safe env loading
2. **Fix key naming** - Consistent env var names
3. **Externalize data** - Keywords/locations in YAML or DB
4. **Add config validation** - Required fields, types, ranges

### How It Fits Into AutoBiz

- **Use .env pattern** for all API keys
- **Use .gitignore patterns** directly
- **Adapt module structure** to AutoBiz layout
- **Port engine registry** concept to tool configuration

### Conflicts with Previous Repos

| Feature | SerpApi (This) | MarketIntel | Best |
|---------|----------------|-------------|------|
| Env loading | os.getenv | Pydantic Settings | MarketIntel |
| Key naming | Inconsistent | Consistent | MarketIntel |
| .gitignore | Comprehensive | Similar | Same |
| Config validation | None | Pydantic | MarketIntel |

### Best Version

**MarketIntel's Pydantic approach** is better for config. **SerpApi's engine registry** pattern is useful addition.

---

## REUSABLE ARTIFACTS

### .gitignore Template (Full)

```gitignore
# ===== Python =====
__pycache__/
*.py[cod]
*$py.class
.python-version
.venv/
venv/
env/
ENV/
build/
dist/
.eggs/
*.egg-info/
pip-wheel-metadata/
pip-log.txt
.tox/
.nox/
.mypy_cache/
.pytest_cache/
.pyre/
.ruff_cache/
.dmypy.json
.coverage
.coverage.*
htmlcov/

# ===== Notebooks =====
.ipynb_checkpoints/

# ===== Data & Databases =====
data/*.db
data/*.sqlite*
*.sqlite
*.sqlite3
*.db-journal
*.db-shm
*.db-wal

# ===== Cache =====
data/cache/
cache/
.cache/

# ===== Logs =====
logs/
*.log

# ===== Output =====
output/
reports/
tmp/
temp/

# ===== Secrets =====
.env
.env.local
.env.*.local
*.pem
credentials.json
```

---

## REUSABLE PATTERNS SUMMARY

```python
# Pattern 1: Required env var with error
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise EnvironmentError("API_KEY not found")

# Pattern 2: Optional env var with default
DATABASE_FILE = os.getenv("DATABASE_FILE", "default.db")
NUM_RESULTS = int(os.getenv("NUM_RESULTS", "20"))

# Pattern 3: Engine/endpoint registry
ENGINES = {
    'engine_name': {
        'function': 'call_function',
        'required_params': ['param1'],
        'optional_params': ['param2'],
    },
}

# Pattern 4: Status enum (workflow states)
STATUSES = ['pending', 'approved', 'rejected']
```
