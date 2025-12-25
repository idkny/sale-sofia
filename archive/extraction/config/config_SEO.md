---
id: config_seo
type: extraction
subject: config
source_repo: SEO
description: "Pydantic Settings + YAML config with per-source TTL"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [config, pydantic, yaml, seo]
---

# Config Extraction: SEO

**Source**: `idkny/SEO`
**Files**: `src/config.py`, `config.yaml`

---

## Overview

Clean Pydantic Settings with YAML config:
- Environment variables via `.env`
- YAML config for business logic
- Per-source TTL settings
- Structured models with validation

---

## Pydantic Settings

```python
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class SystemConfig(BaseModel):
    db_path: Path
    default_ttl: int

class LocationConfig(BaseModel):
    name: str
    type: str
    location_string: str
    hl: str
    gl: str
    active: bool

class EntityConfig(BaseModel):
    place_id: str
    name: str
    domain: Optional[str]
    is_ours: bool

class SourceConfig(BaseModel):
    ttl: int
    default_params: Optional[Dict[str, Any]] = None

class YamlConfig(BaseModel):
    system: SystemConfig
    locations: List[LocationConfig]
    service_categories: List[str]
    entities: List[EntityConfig]
    negatives: List[str]
    brand_terms: List[str]
    sources: Dict[str, SourceConfig]

def load_yaml_config() -> Dict[str, Any]:
    yaml_path = Path(__file__).parent.parent / "config.yaml"
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    serpapi_key: str = Field(..., alias="SERPAPI_KEY")
    yaml_config: YamlConfig = Field(default_factory=load_yaml_config)

settings = Settings()  # Singleton
```

---

## YAML Config Structure

```yaml
system:
  db_path: "data/seo.db"
  default_ttl: 3600

locations:
  - name: "Austin"
    type: "city"
    location_string: "Austin, Texas"
    hl: "en"
    gl: "us"
    active: true

service_categories:
  - "air_duct_cleaning"
  - "dryer_vent_cleaning"
  - "hvac_repair"

entities:
  - place_id: "YOUR_PLACE_ID"
    name: "our_business"
    is_ours: true
  - place_id: "COMPETITOR1_PLACE_ID"
    name: "competitor"
    domain: "competitor1.com"
    is_ours: false

negatives:
  - "free"
  - "diy"
  - "cheap"

brand_terms:
  - "our brand"

sources:
  google_search:
    ttl: 3600
    default_params:
      num: 100
  google_autocomplete:
    ttl: 86400
  google_trends:
    ttl: 86400
```

---

## Usage

```python
from config import settings

# API key from .env
api_key = settings.serpapi_key

# System config
db_path = settings.yaml_config.system.db_path
default_ttl = settings.yaml_config.system.default_ttl

# Per-source TTL
source = settings.yaml_config.sources.get("google_search")
ttl = source.ttl if source else default_ttl

# Locations
for loc in settings.yaml_config.locations:
    if loc.active:
        print(f"{loc.name}: {loc.location_string}")
```

---

## What's Good / Usable

1. **Pydantic Settings** - Type-safe env vars
2. **YAML for business** - Locations, entities, sources
3. **Per-source TTL** - Different cache times per API
4. **Nested models** - Clean structure with validation
5. **Singleton pattern** - Single instance

---

## Cross-Repo Comparison

| Feature | SEO | MarketIntel |
|---------|-----|-------------|
| Pydantic Settings | Yes | Yes |
| YAML config | Yes | Yes |
| Per-source TTL | Yes | No |
| Location config | Yes | No |
| Entity config | Yes | No |

**Recommendation**: SEO config is cleaner. Use as pattern for AutoBiz.
