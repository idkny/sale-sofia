---
id: 20251201_config_market_ai
type: extraction
subject: config
source_repo: Market_AI
description: "dotenv config, targeting configuration (cities, keywords), common parameters"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [config, dotenv, targeting, keywords, locations, api]
---

# SUBJECT: config/

**Source Repository**: Market_AI (https://github.com/idkny/Market_AI)
**Extracted From**: `app_config.py`, `SerpApi/src/config.py`

---

## 1. EXTRACTED CODE

### 1.1 Root App Config (dotenv-based)

```python
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- API Keys ---
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# --- Compliance & Legal ---
TEXAS_ACR_LICENSE = os.getenv("TEXAS_ACR_LICENSE", "TACLB00000000X")
COMPANY_LEGAL_NAME = os.getenv("COMPANY_LEGAL_NAME", "AirCentral LLC")
PRIMARY_PHONE = os.getenv("PRIMARY_PHONE", "512-555-1234")
SERVICE_AREAS = os.getenv("SERVICE_AREAS", "Austin, Round Rock, Cedar Park")
ZIP_LIST = os.getenv("ZIP_LIST", "78701,78702,78703")

# --- Model Configuration ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# A simple check to ensure critical secrets are loaded
if not SERPAPI_KEY:
    print("Warning: SERPAPI_KEY is not set in the environment.")
```

### 1.2 .env.example Template

```bash
# API Keys
SERPAPI_KEY=your_serpapi_key_here

# Compliance
TEXAS_ACR_LICENSE=TACLB12345678X
COMPANY_LEGAL_NAME=Your Company LLC
PRIMARY_PHONE=512-555-1234
SERVICE_AREAS=Austin, Round Rock, Cedar Park
ZIP_LIST=78701,78702,78703

# Model Configuration
OLLAMA_HOST=http://localhost:11434
```

### 1.3 SerpAPI Common Parameters

```python
# --- SerpApi Common Parameters ---
SERPAPI_COMMON_PARAMS = {
    "google_domain": "google.com",
    "gl": "us",  # Geolocation: United States
    "hl": "en",  # Host Language: English
}
```

### 1.4 Targeting Configuration (Cities)

```python
TARGET_CITIES = [
    {
        "canonical_name": "Austin,Texas,United States",
        "city": "Austin",
        "state": "TX",
        "country": "USA"
    },
    {
        "canonical_name": "Houston,Texas,United States",
        "city": "Houston",
        "state": "TX",
        "country": "USA"
    },
    {
        "canonical_name": "Dallas-Fort Worth,Texas,United States",
        "city": "Dallas",
        "state": "TX",
        "country": "USA"
    },
    {
        "canonical_name": "San Antonio,Texas,United States",
        "city": "San Antonio",
        "state": "TX",
        "country": "USA"
    },
]
```

### 1.5 Keyword Configuration

```python
# Core business keywords
CORE_KEYWORDS = [
    "air duct cleaning",
    "hvac services",
    "dryer vent cleaning",
    "ac repair",
    "furnace maintenance",
]

# Indirect/content marketing keywords
INDIRECT_KEYWORDS = [
    "home maintenance tips",
    "allergy relief home",
    "improve indoor air quality",
    "energy saving tips for home",
    "hvac system lifespan",
]
```

---

## 2. WHAT'S GOOD / USABLE

| Component | Value | Notes |
|-----------|-------|-------|
| **dotenv loading** | HIGH | Standard .env pattern |
| **Default values** | HIGH | Fallbacks for non-critical config |
| **Warning on missing** | MEDIUM | Alerts when SERPAPI_KEY missing |
| **Targeting config** | HIGH | Structured city data |
| **Keyword categories** | HIGH | Core vs indirect separation |
| **Common params** | MEDIUM | Reusable API parameters |
| **Compliance fields** | HIGH | License, legal name, phone |

---

## 3. WHAT'S OUTDATED

| Component | Issue | Fix |
|-----------|-------|-----|
| No Pydantic validation | Raw os.getenv | Use Pydantic Settings |
| No type hints | Missing | Add proper types |
| Print warning | Not logging | Use logging.warning |
| Hardcoded cities | Not configurable | Move to YAML/JSON |

---

## 4. HOW IT FITS INTO AUTOBIZ

**Direct Port Candidates:**
1. Targeting configuration pattern (cities + canonical names)
2. Keyword categorization (core vs indirect)
3. Common API parameters pattern
4. Compliance field storage

**Integration Points:**
- `autobiz/core/config.py` - Main configuration
- `autobiz/tools/search/targets.py` - Targeting data
- `autobiz/pipelines/keywords.py` - Keyword lists

---

## 5. CONFLICTS WITH EXISTING EXTRACTIONS

| Pattern | Market_AI | Existing | Resolution |
|---------|-----------|----------|------------|
| Config loading | dotenv only | MarketIntel (Pydantic Settings) | **USE MarketIntel** - type-safe |
| Targeting | Python lists | None | **USE Market_AI** - unique |
| Keywords | Core + indirect | Auto-Biz (status workflow) | **MERGE** - categories + status |
| Path management | Basic | Auto-Biz (paths.py) | **USE Auto-Biz** - centralized |

---

## 6. BEST VERSION RECOMMENDATION

**MERGE approach:**
1. **Pydantic Settings** from MarketIntel (type validation)
2. **Targeting config** from Market_AI (cities structure)
3. **Keywords** from Market_AI (categorization)
4. **paths.py** from Auto-Biz (centralized paths)

**Recommended final config:**

```python
from pydantic_settings import BaseSettings
from typing import List

class AppConfig(BaseSettings):
    # API Keys
    serpapi_key: str = ""
    ollama_host: str = "http://localhost:11434"

    # Compliance
    license_number: str = ""
    company_name: str = ""
    primary_phone: str = ""

    # Targeting
    target_cities: List[dict] = []
    core_keywords: List[str] = []
    indirect_keywords: List[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = AppConfig()
```

---

## 7. TARGETING DATA STRUCTURE

```python
# Structure for geo-targeting in SerpAPI
{
    "canonical_name": "Austin,Texas,United States",  # For SerpAPI location param
    "city": "Austin",                                 # For database storage
    "state": "TX",                                    # Short form
    "country": "USA",                                 # Country code
    "uule_code": "...",                              # Optional UULE encoding
    "population": 1000000,                           # Optional
    "service_area": True,                            # Business flag
}
```
