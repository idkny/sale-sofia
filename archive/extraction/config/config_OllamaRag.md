---
id: extraction_ollamarag_config
type: extraction
subject: config
source_repo: Ollama-Rag
description: "Configuration patterns from Ollama-Rag - YAML-based config"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, config, yaml, ollamarag]
---

# Configuration Patterns - Ollama-Rag

**Source**: `config/config.yaml`, `utils.py`
**Approach**: Pure YAML configuration with Python loader
**Status**: SIMPLER than MarketIntel (YAML only, no Pydantic)

---

## 1. YAML Configuration File

```yaml
# Source: config/config.yaml (complete file)
llm:
  model_name: mistral
  temperature: 0.2

embeddings:
  model_name: BAAI/bge-small-en
  device: auto
  normalize_embeddings: true

batch_settings:
  max_batch_size: 16

memory_per_document: 50000000
```

---

## 2. Config Loader

```python
# Source: utils.py:21-33
import yaml
import os

def load_config(config_file: str = "config/config.yaml") -> dict:
    """Load YAML configuration."""
    if not os.path.isabs(config_file):
        config_file = os.path.abspath(config_file)

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file, "r") as file:
        return yaml.safe_load(file)

# Load the configuration once (module-level singleton)
config = load_config()
```

---

## 3. Config Access Pattern

```python
# How config is accessed throughout the codebase

# LLM config
llm_config = config.get("llm", {})
model_name = llm_config.get("model_name")
temperature = llm_config.get("temperature", 0)

# Embeddings config
embedding_config = config.get("embeddings", {})
model_name = embedding_config.get("model_name")
device = embedding_config.get("device", "auto")
normalize_embeddings = embedding_config.get("normalize_embeddings", True)

# Batch settings
user_max_batch_size = config.get("batch_settings", {}).get("max_batch_size", 20)
memory_per_document = config.get("memory_per_document", 50 * 1024 * 1024)
```

---

## Comparison: Ollama-Rag vs MarketIntel Config

### Ollama-Rag (YAML Only)

```python
# Pros:
# - Simple
# - Human-readable YAML
# - No dependencies beyond PyYAML

# Cons:
# - No type validation
# - No schema enforcement
# - No environment variable support
# - No nested config classes
# - Manual .get() with defaults everywhere

config = load_config("config/config.yaml")
model = config.get("llm", {}).get("model_name")  # Could be None, no error
```

### MarketIntel (Pydantic Settings)

```python
# Pros:
# - Type validation at load time
# - Environment variable support (OLLAMA_MODEL=...)
# - Nested models with defaults
# - IDE autocomplete
# - JSON Schema generation

# Cons:
# - More complex
# - Requires Pydantic dependency

from pydantic_settings import BaseSettings

class OllamaSettings(BaseSettings):
    model: str = "mistral"
    temperature: float = 0.0
    base_url: str = "http://localhost:11434"

    class Config:
        env_prefix = "OLLAMA_"

settings = OllamaSettings()
model = settings.model  # Type-checked, validated
```

---

## Conclusions

### ✅ Good / Usable

1. **Simple YAML structure** - Easy to edit manually
2. **Module-level singleton** - Config loaded once
3. **Absolute path handling** - Converts relative to absolute
4. **Safe YAML loading** - Uses `yaml.safe_load()`

### ⚠️ Outdated / Limited

1. **No type validation** - Config values not validated
2. **No env var support** - Can't override via environment
3. **No defaults in schema** - Defaults scattered in code
4. **No IDE support** - No autocomplete or type hints

### 🔧 Must Rewrite for AutoBiz

1. **Use Pydantic Settings** - MarketIntel pattern is better
2. **Add environment variable support** - For deployment flexibility
3. **Centralize defaults** - In config class, not in code

### 📊 Comparison Matrix

| Feature | MarketIntel | SerpApi | Ollama-Rag |
|---------|-------------|---------|------------|
| Format | Pydantic + YAML | Env vars | Pure YAML |
| Type Validation | Yes | No | No |
| Env Var Support | Yes | Yes | No |
| IDE Autocomplete | Yes | No | No |
| Nested Config | Yes | No | Yes (dicts) |
| Default Values | In class | In code | In code |

### 🎯 Fit for AutoBiz

- **Do NOT use this pattern** - MarketIntel's Pydantic Settings is superior
- **Reuse YAML structure** - The nested YAML format is clean
- **Merge**: Pydantic Settings + YAML file hybrid from MarketIntel

---

## Files

- `/tmp/Ollama-Rag/config/config.yaml` - YAML config
- `/tmp/Ollama-Rag/utils.py:21-33` - Config loader
