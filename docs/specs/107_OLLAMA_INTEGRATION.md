# Spec 107: Ollama Integration

**Status**: Planning
**Created**: 2025-12-26
**Instance**: 2

---

## Overview

Integrate Ollama for two primary use cases:
1. **Page Content Mapping** - Read scraped page content, identify fields, map to correct DB columns
2. **Description Extraction** - Parse unstructured Bulgarian text, extract structured data

**Reference**: ZohoCentral's proven Ollama integration at `/home/wow/Documents/ZohoCentral/autobiz/tools/ai/`

---

## Architecture

**Pattern**: Same as `proxies/proxies_main.py` - facade with internal modules.

```
llm/
├── __init__.py          # Exports: map_fields, extract_description, ensure_ollama_ready
├── llm_main.py          # THE FACADE - OllamaClient + all public functions
├── prompts.py           # Prompt templates (internal, easy to tune)
└── schemas.py           # Pydantic models: MappedFields, ExtractedDescription

config/
└── ollama.yaml          # Models, tasks, timeouts
```

**Why this structure?**
- **4 files** - simple, no deep nesting
- **Debug**: prompt wrong → `prompts.py`, API issue → `llm_main.py`, schema wrong → `schemas.py`
- **Scale**: add new task = add function to `llm_main.py` + prompt to `prompts.py`
- **Consistent** with `proxies/` pattern in this project

---

## Model Selection (4GB GPU)

From ZohoCentral benchmarks on GTX 960M 4GB VRAM:

| Model | VRAM | Speed | Best For |
|-------|------|-------|----------|
| `qwen2.5:1.5b` | 1.2GB | 16 tok/s | **Primary** - extraction, field mapping |
| `qwen2.5:0.5b` | 0.5GB | 32 tok/s | Batch processing, speed-critical |
| `phi3:3.8b` | 2.6GB | 11 tok/s | Complex reasoning (if needed) |

**Why Qwen?**
- Excellent multilingual (Bulgarian/Cyrillic)
- Good instruction following
- Native JSON output mode
- Fits in 4GB VRAM

---

## Configuration

```yaml
# config/ollama.yaml
ollama:
  host: localhost
  port: 11434
  health_check_timeout: 2      # seconds
  startup_wait: 3              # seconds after starting
  max_restart_attempts: 2

models:
  qwen2.5:1.5b:
    vram_mb: 1200
    tier: 2
    use_cases: [field_mapping, extraction]
  qwen2.5:0.5b:
    vram_mb: 500
    tier: 1
    use_cases: [batch_extraction]

tasks:
  field_mapping:
    primary_model: qwen2.5:1.5b
    fallback_model: qwen2.5:0.5b
    temperature: 0.0            # Deterministic
    max_tokens: 500
    format: json
    timeout_seconds: 30

  description_extraction:
    primary_model: qwen2.5:1.5b
    fallback_model: qwen2.5:0.5b
    temperature: 0.1            # Slight variation OK
    max_tokens: 500
    format: json
    timeout_seconds: 30
```

---

## Health Check Pattern (from ZohoCentral)

```python
class OllamaClient:
    def check_health(self, timeout=2) -> bool:
        """HTTP GET to http://localhost:11434/"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def kill_port_holder(self, port=11434) -> bool:
        """lsof -t -i:11434 | xargs kill -9"""
        result = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            subprocess.run(["kill", "-9", pid])
            # Wait for port to be free
            for _ in range(10):
                if self.is_port_free(port):
                    return True
                time.sleep(0.5)
        return self.is_port_free(port)

    def start_server(self) -> bool:
        """Start ollama serve as detached process"""
        if self.check_health():
            return True
        if not self.is_port_free(self.port):
            self.kill_port_holder()
        subprocess.Popen(["ollama", "serve"], start_new_session=True, ...)
        return self.wait_for_healthy()

    def ensure_ready(self) -> bool:
        """Self-healing: check → restart if needed"""
        if self.check_health():
            return True
        for attempt in range(self.max_restart_attempts):
            if self.start_server():
                return True
            time.sleep(2)
        return False
```

---

## Use Case 1: Page Content → DB Field Mapping

**Problem**: Scraped page has raw content, need to map to correct DB columns.

**Example Input**:
```
Цена: 125000 EUR
Квадратура: 85 кв.м
Етаж: 3 от 6
Строителство: тухла
Район: Лозенец
```

**Example Output**:
```json
{
    "price_eur": 125000,
    "area_sqm": 85,
    "floor": 3,
    "total_floors": 6,
    "construction": "brick",
    "neighborhood": "Лозенец",
    "confidence": 0.95
}
```

**Prompt Template**:
```python
FIELD_MAPPING_PROMPT = """Ти си експерт по недвижими имоти.

Анализирай следния текст от обява и извлечи данни за базата данни.

ТЕКСТ:
{content}

НАЛИЧНИ ПОЛЕТА В БАЗАТА ДАННИ:
- price_eur: цена в евро (число)
- price_bgn: цена в лева (число)
- area_sqm: квадратура (число)
- floor: етаж (число)
- total_floors: общо етажи (число)
- construction: тип строителство (brick/panel/epk)
- neighborhood: квартал (текст)
- address: адрес (текст)
- year_built: година на строителство (число)
- heating: отопление (district/gas/electric/air_conditioner)

Отговори САМО с валиден JSON:
{{
    "field_name": value,
    ...
    "confidence": 0.0-1.0
}}

Използвай null за липсваща информация.
"""
```

---

## Use Case 2: Description → Structured Data

**Problem**: Free-text descriptions contain valuable info not in structured fields.

**Example Input**:
```
Тристаен апартамент в идеален център. Напълно обзаведен с нови мебели.
Има паркомясто в подземен гараж. Асансьор, денонощна охрана.
Южно изложение с панорамна гледка към Витоша. ТЕЦ отопление.
Възможност за разсрочено плащане.
```

**Example Output**:
```json
{
    "rooms": 3,
    "furnishing": "furnished",
    "has_parking": true,
    "parking_type": "underground",
    "has_elevator": true,
    "has_security": true,
    "orientation": "south",
    "has_view": true,
    "view_type": "mountain",
    "heating_type": "district",
    "payment_options": "installments",
    "confidence": 0.92
}
```

**Prompt Template**:
```python
EXTRACTION_PROMPT = """Ти си експерт по недвижими имоти в България.

Анализирай следното описание и извлечи структурирана информация.

ОПИСАНИЕ:
{description}

Отговори САМО с валиден JSON:
{{
    "rooms": число или null,
    "bedrooms": число или null,
    "bathrooms": число или null,
    "furnishing": "furnished" | "partially" | "unfurnished" | null,
    "condition": "new" | "renovated" | "needs_renovation" | null,
    "has_parking": true/false/null,
    "parking_type": "underground" | "outdoor" | "garage" | null,
    "has_elevator": true/false/null,
    "has_security": true/false/null,
    "has_balcony": true/false/null,
    "has_storage": true/false/null,
    "orientation": "north" | "south" | "east" | "west" | null,
    "has_view": true/false/null,
    "view_type": "city" | "mountain" | "park" | null,
    "heating_type": "district" | "gas" | "electric" | "air_conditioner" | null,
    "payment_options": "cash" | "installments" | "mortgage" | null,
    "confidence": 0.0-1.0
}}

Ако информацията липсва, използвай null.
"""
```

---

## Integration with Scrapling

```python
# websites/scrapling_base.py
from llm import map_fields, extract_description

class ScraplingMixin:
    use_llm: bool = True  # Can disable for testing

    def extract_listing(self, page) -> dict:
        """Extract all data from listing page."""

        # 1. Get raw page text
        raw_text = self.get_page_text(page)

        # 2. LLM maps content to DB fields
        if self.use_llm:
            mapped = map_fields(raw_text)
            if mapped.confidence < 0.7:
                # Fallback to CSS selectors
                mapped = self._extract_with_selectors(page)
        else:
            mapped = self._extract_with_selectors(page)

        # 3. Get description text
        description = self.css_first(page, ".description")

        # 4. LLM extracts structured data from description
        if description and self.use_llm:
            extracted = extract_description(description)
            if extracted.confidence > 0.7:
                mapped.update(extracted.to_dict())

        return mapped

    def _extract_with_selectors(self, page) -> dict:
        """Fallback: CSS selector extraction."""
        return {
            "price_eur": self._parse_price(self.css_first(page, ".price")),
            "area_sqm": self._parse_area(self.css_first(page, ".area")),
            # ... etc
        }
```

---

## Pydantic Output Schemas

```python
from pydantic import BaseModel
from typing import Optional, Literal

class MappedFields(BaseModel):
    """DB field mapping result."""
    price_eur: Optional[int] = None
    price_bgn: Optional[int] = None
    area_sqm: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    construction: Optional[Literal["brick", "panel", "epk"]] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    year_built: Optional[int] = None
    heating: Optional[Literal["district", "gas", "electric", "air_conditioner"]] = None
    confidence: float = 0.0

class ExtractedDescription(BaseModel):
    """Extracted from free-text description."""
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    furnishing: Optional[Literal["furnished", "partially", "unfurnished"]] = None
    condition: Optional[Literal["new", "renovated", "needs_renovation"]] = None
    has_parking: Optional[bool] = None
    parking_type: Optional[Literal["underground", "outdoor", "garage"]] = None
    has_elevator: Optional[bool] = None
    has_security: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_storage: Optional[bool] = None
    orientation: Optional[Literal["north", "south", "east", "west"]] = None
    has_view: Optional[bool] = None
    view_type: Optional[Literal["city", "mountain", "park"]] = None
    heating_type: Optional[Literal["district", "gas", "electric", "air_conditioner"]] = None
    payment_options: Optional[Literal["cash", "installments", "mortgage"]] = None
    confidence: float = 0.0
```

---

## Phases

**Tasks tracked in**: [TASKS.md](../tasks/TASKS.md#ollama-integration-p1)

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| 1 | Foundation + Health Check | `llm/` directory, `ollama.yaml`, OllamaClient with health check |
| 2 | API + Field Mapping | REST API, JSON parsing, `map_fields()` function |
| 3 | Description Extraction | `extract_description()` function, Bulgarian prompts |
| 4 | Scrapling Integration | LLM in scraper pipeline, CSS fallback |
| 5 | Production Hardening | Cache, metrics, performance testing |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Health check | Auto-starts, port conflicts resolved |
| Field mapping accuracy | >80% correct on test set |
| Description extraction accuracy | >70% correct on test set |
| Performance | <3s per extraction |
| Integration | Works with existing scraper pipeline |

---

## Files to Create

| File | Purpose |
|------|---------|
| `config/ollama.yaml` | Model and task configuration |
| `llm/__init__.py` | Exports: `map_fields`, `extract_description`, `ensure_ollama_ready` |
| `llm/llm_main.py` | OllamaClient class + all public functions (THE FACADE) |
| `llm/prompts.py` | Prompt templates (FIELD_MAPPING_PROMPT, EXTRACTION_PROMPT) |
| `llm/schemas.py` | Pydantic models (MappedFields, ExtractedDescription) |

**Total: 5 files** (4 in `llm/` + 1 config)

---

## Dependencies

```
# requirements.txt additions (if not already present)
pydantic>=2.0
requests
pyyaml
```

---

## Reference

- ZohoCentral Ollama: `/home/wow/Documents/ZohoCentral/autobiz/tools/ai/_llm.py`
- ZohoCentral Config: `/home/wow/Documents/ZohoCentral/autobiz/config/ai_config.yaml`
