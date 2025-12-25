---
id: 20251201_config_marketintel
type: extraction
subject: config
description: "Pydantic Settings + YAML config pattern from MarketIntel"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [config, pydantic, yaml, settings, marketintel, extraction]
source_repo: idkny/MarketIntel
---

# Config Extraction: MarketIntel

**Source**: `idkny/MarketIntel`
**Files**: `src/config.py`, `config.yaml`

---

## Conclusions

### What's Good (HIGH PRIORITY)

| Pattern | Description | Use For |
|---------|-------------|---------|
| Pydantic Settings | Type-safe .env loading | API keys, secrets |
| Typed YAML models | Nested config validation | Business rules |
| Singleton pattern | Single settings instance | Global access |
| TTL per source | Different cache times | API optimization |

### What to Skip

- Location/geo config (not needed)
- Service categories (HVAC-specific)

---

## Pattern 1: Pydantic + YAML Hybrid

```python
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# YAML Config Models (Typed)
# =============================================================================

class SystemConfig(BaseModel):
    """System-level configuration."""
    db_path: Path
    default_ttl: int


class SourceConfig(BaseModel):
    """Per-source API configuration."""
    ttl: int
    default_params: Optional[Dict[str, Any]] = None


class YamlConfig(BaseModel):
    """Complete YAML config structure."""
    system: SystemConfig
    sources: Dict[str, SourceConfig]
    # Add more sections as needed


# =============================================================================
# YAML Loader
# =============================================================================

def load_yaml_config() -> Dict[str, Any]:
    """Load and parse YAML configuration file."""
    yaml_path = Path(__file__).parent.parent / "config.yaml"
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


# =============================================================================
# Main Settings Class
# =============================================================================

class Settings(BaseSettings):
    """
    Combined settings from .env and YAML.

    .env provides secrets (API keys)
    YAML provides business configuration
    """
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unknown env vars
    )

    # From .env file
    api_key: str = Field(..., alias="API_KEY")

    # From YAML file
    yaml_config: YamlConfig = Field(default_factory=load_yaml_config)


# =============================================================================
# Singleton Instance
# =============================================================================

settings = Settings()

# Usage:
# from config import settings
# print(settings.api_key)
# print(settings.yaml_config.system.db_path)
```

---

## Pattern 2: config.yaml Structure

```yaml
# config.yaml

system:
  db_path: "data/app.db"
  default_ttl: 3600

sources:
  zoho_crm:
    ttl: 300  # 5 min cache for CRM
    default_params:
      per_page: 200

  zoho_books:
    ttl: 600  # 10 min cache for Books
    default_params:
      per_page: 100

  zoho_inventory:
    ttl: 300
    default_params:
      per_page: 100

# Business rules
thresholds:
  confidence_auto_approve: 0.85
  confidence_auto_reject: 0.90

# Feature flags
features:
  enable_ai_classification: true
  enable_caching: true
```

---

## Pattern 3: AI Provider Config

```python
# AI provider configuration pattern

ACTIVE_AI_PROVIDER = "ollama"  # or "openai", "mock"

AI_PROVIDERS = {
    "mock": {
        "model": "mock"
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "gemma:2b",
        "timeout": 60
    },
    "openai": {
        "api_key": "YOUR_KEY_HERE",  # Better: load from .env
        "model": "gpt-4"
    }
}

CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.85
```

---

## Pattern 4: Nested Typed Models

```python
from pydantic import BaseModel
from typing import List, Optional

class LocationConfig(BaseModel):
    """Location configuration."""
    name: str
    type: str  # "city", "region", "country"
    active: bool = True


class EntityConfig(BaseModel):
    """Entity (business) configuration."""
    id: str
    name: str
    domain: Optional[str] = None
    is_ours: bool = False


class YamlConfig(BaseModel):
    """Complete config with nested models."""
    system: SystemConfig
    locations: List[LocationConfig]
    entities: List[EntityConfig]
    negatives: List[str]  # Exclude keywords
    brand_terms: List[str]  # Include keywords
    sources: Dict[str, SourceConfig]
```

---

## AutoBiz Adaptation

```python
# autobiz/core/config.py

from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ZohoConfig(BaseModel):
    """Zoho API configuration."""
    client_id: str
    client_secret: str
    refresh_token: str
    organization_id: str


class CacheConfig(BaseModel):
    """Cache TTL per Zoho module."""
    crm_contacts: int = 300
    crm_deals: int = 300
    books_invoices: int = 600
    books_payments: int = 600
    inventory_items: int = 300


class PipelineConfig(BaseModel):
    """Pipeline behavior settings."""
    batch_size: int = 100
    retry_attempts: int = 3
    confidence_threshold: float = 0.85


class AutoBizYamlConfig(BaseModel):
    """Complete AutoBiz YAML config."""
    cache: CacheConfig
    pipeline: PipelineConfig


class AutoBizSettings(BaseSettings):
    """AutoBiz settings from .env + YAML."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Secrets from .env
    zoho_client_id: str = Field(..., alias="ZOHO_CLIENT_ID")
    zoho_client_secret: str = Field(..., alias="ZOHO_CLIENT_SECRET")
    zoho_refresh_token: str = Field(..., alias="ZOHO_REFRESH_TOKEN")

    # From YAML
    yaml_config: AutoBizYamlConfig = Field(default_factory=lambda: {})


# Singleton
settings = AutoBizSettings()
```

```yaml
# autobiz/config.yaml

cache:
  crm_contacts: 300
  crm_deals: 300
  books_invoices: 600
  books_payments: 600
  inventory_items: 300

pipeline:
  batch_size: 100
  retry_attempts: 3
  confidence_threshold: 0.85
```
