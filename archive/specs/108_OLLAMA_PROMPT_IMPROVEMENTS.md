# Spec 108: Ollama Prompt Accuracy Improvements

**Created**: 2025-12-26
**Status**: Superseded by Spec 110
**Priority**: P1 - Critical accuracy improvement (40% → 90%+)
**Depends On**: Spec 107 (Ollama Integration)

**OUTCOME**: While this spec proposed English prompts + JSON schema enforcement to improve accuracy, **Spec 110 (Dictionary-First Extraction)** achieved superior results (100% accuracy) by bypassing LLM for most fields. The dictionary approach extracts numeric, boolean, and enum fields directly via regex/keyword matching, using LLM only as fallback. This is more reliable and faster than prompt engineering alone.

**Key Learnings Applied**:
- English prompts with "RESPOND IN ENGLISH ONLY" (implemented in `llm/prompts.py`)
- JSON schema enforcement via `model_json_schema()` (implemented in `llm/llm_main.py`)
- Post-processing translation fallback (kept as defense-in-depth)

**Recommendation**: Read Spec 110 for the implemented solution. This spec remains as reference for prompt engineering best practices.

---

## 1. Problem Statement

### Current State
The Ollama integration (Spec 107) uses Bulgarian prompts with English enum hints:

```python
# Current prompt pattern (Bulgarian)
FIELD_MAPPING_PROMPT = """Ти си експерт по недвижими имоти.
...
- construction: тип строителство (brick/panel/epk)
- heating: отопление (district/gas/electric/air_conditioner)
"""
```

**Result**: 2/5 accuracy (40%) on enum fields due to Bulgarian value leakage.

### Target State
Switch to English prompts with explicit language constraints:

```python
# Target prompt pattern (English)
FIELD_MAPPING_PROMPT = """You are a Bulgarian real estate data extraction expert.

CRITICAL: RESPOND IN ENGLISH ONLY. Use ONLY English enum values.

Extract from this BULGARIAN TEXT:
{content}

Return JSON with these fields:
- construction: "brick" | "panel" | "epk" | null
- heating: "district" | "gas" | "electric" | "air_conditioner" | null
"""
```

**Goal**: 90%+ accuracy on enum fields with grammar-level enforcement.

---

## 2. Root Cause Analysis

### Research Findings
From [ollama_language_behavior.md](/home/wow/Projects/sale-sofia/docs/research/ollama_language_behavior.md):

| Prompt Variation | Accuracy | Notes |
|-----------------|----------|-------|
| **English + "RESPOND IN ENGLISH ONLY"** | **5/5 (100%)** | Best performer |
| English prompt + Bulgarian hints | 4/5 (80%) | furnishing wrong |
| Bulgarian prompt (current) | 2/5 (40%) | rooms, construction, furnishing wrong |
| Chat API + Bulgarian system | ~2/5 (40%) | Similar to current |
| Chat API + English system | ~3/5 (60%) | Better but not enough |

### Why Bulgarian Prompts Fail
1. **Model behavior**: qwen2.5 is multilingual - responds in prompt language by default
2. **Weak enforcement**: Parenthetical hints `(brick/panel/epk)` don't constrain token generation
3. **Format limitation**: `format: "json"` only ensures **syntax**, not **value language**

### Why English Prompts Work
1. **Explicit constraint**: "RESPOND IN ENGLISH ONLY" sets strong expectation
2. **Natural alignment**: English prompts naturally produce English values
3. **Grammar enforcement**: Can be combined with JSON schema for 100% reliability

---

## 3. Solution Architecture

### Three-Layer Defense Strategy

```
Layer 1: Prompt Language (English)
         ↓
Layer 2: JSON Schema with Enum Enforcement
         ↓
Layer 3: Post-Processing Fallback (_translate_values)
```

### Implementation Phases

| Phase | Change | Impact | Risk |
|-------|--------|--------|------|
| **Phase 1** | Switch prompts to English | Highest (40% → 80%+) | Low |
| **Phase 2** | Add `model_json_schema()` to format | High (80% → 95%+) | Low |
| **Phase 3** | Configure OLLAMA_KEEP_ALIVE for batch | Performance | Low |

**Recommendation**: Implement all 3 phases. No `/api/chat` needed - research shows `/api/generate` with English prompts achieves 100% accuracy.

---

## 4. Phase 1: English Prompts with Explicit Constraints

### 4.1 Changes to `llm/prompts.py`

#### Field Mapping Prompt

**Before**:
```python
FIELD_MAPPING_PROMPT = """Ти си експерт по недвижими имоти.

Анализирай следния текст от обява и извлечи данни за базата данни.

ТЕКСТ:
{content}

НАЛИЧНИ ПОЛЕТА В БАЗАТА ДАННИ:
- price_eur: цена в евро (число)
- construction: тип строителство (brick/panel/epk)
- heating: отопление (district/gas/electric/air_conditioner)
...

Отговори САМО с валиден JSON. Използвай null за липсваща информация.
"""
```

**After**:
```python
FIELD_MAPPING_PROMPT = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN TEXT below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Never translate enum values to Bulgarian
4. Return valid JSON matching the schema
5. Use null for missing information

BULGARIAN TEXT:
{content}

REQUIRED JSON FIELDS (use EXACT enum values):
- price_eur: number (price in euros) or null
- price_bgn: number (price in leva) or null
- area_sqm: number (area in square meters) or null
- floor: number (floor number) or null
- total_floors: number (total building floors) or null
- construction: "brick" | "panel" | "epk" | null
- heating: "district" | "gas" | "electric" | "air_conditioner" | null
- neighborhood: string (keep in Bulgarian) or null
- address: string (keep in Bulgarian) or null
- year_built: number or null
- confidence: number (0.0-1.0, your extraction confidence)

Return ONLY valid JSON with these exact field names and enum values.
"""
```

**Key changes**:
- Entire prompt in English
- "RESPOND IN ENGLISH ONLY" explicit constraint
- Enum values listed with pipe `|` syntax (clearer than slash)
- Clarified which fields stay Bulgarian (neighborhood, address)

#### Description Extraction Prompt

**Before**:
```python
EXTRACTION_PROMPT = """Ти си експерт по недвижими имоти в България.

Анализирай следното описание и извлечи структурирана информация.

ОПИСАНИЕ:
{description}

Отговори САМО с валиден JSON:
{
    "rooms": число или null,
    "furnishing": "furnished" | "partially" | "unfurnished" | null,
    ...
}
"""
```

**After**:
```python
EXTRACTION_PROMPT = """You are a Bulgarian real estate data extraction expert.

CRITICAL RULES:
1. Extract information from the BULGARIAN DESCRIPTION below
2. RESPOND IN ENGLISH ONLY - use ONLY English enum values
3. Never translate enum values to Bulgarian
4. Return valid JSON matching the schema
5. Use null for missing information

BULGARIAN DESCRIPTION:
{description}

REQUIRED JSON FIELDS (use EXACT enum values):
- rooms: number or null
- bedrooms: number or null
- bathrooms: number or null
- furnishing: "furnished" | "partially" | "unfurnished" | null
- condition: "new" | "renovated" | "needs_renovation" | null
- has_parking: boolean or null
- parking_type: "underground" | "outdoor" | "garage" | null
- has_elevator: boolean or null
- has_security: boolean or null
- has_balcony: boolean or null
- has_storage: boolean or null
- orientation: "north" | "south" | "east" | "west" | null
- has_view: boolean or null
- view_type: "city" | "mountain" | "park" | null
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
- payment_options: "cash" | "installments" | "mortgage" | null
- confidence: number (0.0-1.0)

Return ONLY valid JSON with these exact field names and enum values.
"""
```

### 4.2 Testing Phase 1

**Test script**: Create `/home/wow/Projects/sale-sofia/tests/debug/test_prompt_phase1.py`

```python
from llm import map_fields, extract_description

# Test input (Bulgarian real estate text)
BULGARIAN_TEXT = """
Цена: 125000 EUR
Квадратура: 85 кв.м
Етаж: 3 от 6
Строителство: тухла
Отопление: ТЕЦ
Район: Лозенец
"""

result = map_fields(BULGARIAN_TEXT)

# Assert English values
assert result.construction == "brick", f"Expected 'brick', got '{result.construction}'"
assert result.heating == "district", f"Expected 'district', got '{result.heating}'"
assert result.confidence > 0.7, f"Low confidence: {result.confidence}"
```

**Success criteria**: All enum fields return English values (5/5 accuracy).

---

## 5. Phase 2: JSON Schema Enforcement

### 5.1 Understanding JSON Schema + Grammar

From research:

> When using a full JSON schema with enums, Ollama generates a GBNF grammar that **constrains tokens to only valid enum values**. This is enforced at the grammar level, not just the prompt level.

**How it works**:
1. Pass `MappedFields.model_json_schema()` instead of `"json"` to `format` parameter
2. Ollama converts schema → GBNF grammar via llama.cpp
3. During token sampling, invalid tokens are masked (probability = 0)
4. Model **cannot** generate `"тухла"` because it's not in the enum

### 5.2 Changes to `llm/llm_main.py`

#### Current Implementation

```python
# llm/llm_main.py (current from Spec 107)
def map_fields(content: str, model: str = None) -> MappedFields:
    """Map raw page content to DB fields."""
    client = OllamaClient()

    if not model:
        config = client._load_task_config("field_mapping")
        model = config["primary_model"]

    prompt = FIELD_MAPPING_PROMPT.format(content=content)

    response = client.generate(
        model=model,
        prompt=prompt,
        format="json",  # WEAK: only ensures syntax
        temperature=0.0,
        max_tokens=500
    )

    data = json.loads(response["response"])
    return MappedFields(**data)
```

#### Phase 2 Implementation

```python
# llm/llm_main.py (Phase 2 - schema enforcement)
def map_fields(content: str, model: str = None) -> MappedFields:
    """Map raw page content to DB fields."""
    client = OllamaClient()

    if not model:
        config = client._load_task_config("field_mapping")
        model = config["primary_model"]

    prompt = FIELD_MAPPING_PROMPT.format(content=content)

    response = client.generate(
        model=model,
        prompt=prompt,
        format=MappedFields.model_json_schema(),  # STRONG: grammar-level enforcement
        temperature=0.0,
        max_tokens=500
    )

    data = json.loads(response["response"])
    return MappedFields(**data)
```

**Same pattern for `extract_description()`**:
```python
response = client.generate(
    model=model,
    prompt=prompt,
    format=ExtractedDescription.model_json_schema(),  # Schema enforcement
    temperature=0.1,
    max_tokens=500
)
```

### 5.3 Schema Validation

Verify Pydantic schemas have proper enum definitions:

```python
# llm/schemas.py (verify enums are defined correctly)
from pydantic import BaseModel
from typing import Optional, Literal

class MappedFields(BaseModel):
    # Enums MUST use Literal with exact string values
    construction: Optional[Literal["brick", "panel", "epk"]] = None
    heating: Optional[Literal["district", "gas", "electric", "air_conditioner"]] = None
    # ... etc
```

**Critical**: If enum is missing from schema, grammar enforcement won't work!

### 5.4 Testing Phase 2

**Test script**: Extend `/home/wow/Projects/sale-sofia/tests/debug/test_prompt_phase2.py`

```python
# Test that invalid values cannot be generated
BULGARIAN_TEXT_TRICKY = """
Строителство: тухла (brick equivalent)
Отопление: централно (district equivalent)
"""

result = map_fields(BULGARIAN_TEXT_TRICKY)

# Schema should FORCE English even if model wants Bulgarian
assert result.construction == "brick"
assert result.heating == "district"

# Test confidence with ambiguous input
assert result.confidence >= 0.6  # May be lower due to ambiguity
```

**Success criteria**:
- 100% English enum values (no Bulgarian leakage possible)
- Valid JSON structure (Pydantic validation passes)

---

## 6. Phase 3: OLLAMA_KEEP_ALIVE for Batch Processing

### 6.1 The Problem

When processing hundreds of listings:
1. Ollama loads model into VRAM
2. After 5 minutes idle, model is unloaded (default behavior)
3. Next request reloads model (~5-10 seconds overhead)
4. For batch processing, this causes unnecessary reloads

### 6.2 Solution: Configure OLLAMA_KEEP_ALIVE

`OLLAMA_KEEP_ALIVE` controls how long the model stays loaded after last request.

```bash
# Default: 5 minutes (may cause reloads during batch)
OLLAMA_KEEP_ALIVE=5m

# For batch processing: 1 hour
export OLLAMA_KEEP_ALIVE=1h

# Keep loaded forever (until manual unload)
export OLLAMA_KEEP_ALIVE=-1
```

### 6.3 Implementation

**Option A: Environment variable (recommended for development)**

Add to `~/.bashrc` or shell profile:
```bash
export OLLAMA_KEEP_ALIVE=1h
```

**Option B: Set in orchestrator (recommended for production)**

```python
# orchestrator.py - before starting batch extraction
import os

def start_llm_extraction_batch():
    """Configure Ollama for batch processing."""
    # Keep model loaded for duration of batch
    os.environ["OLLAMA_KEEP_ALIVE"] = "1h"

    # ... process listings ...
```

**Option C: Add to systemd service (if running Ollama as service)**

```ini
# /etc/systemd/system/ollama.service
[Service]
Environment="OLLAMA_KEEP_ALIVE=1h"
```

### 6.4 Why NOT /api/chat?

Research showed `/api/chat` provides no accuracy benefit over `/api/generate`:

| Approach | Accuracy | Notes |
|----------|----------|-------|
| `/api/generate` + English prompt | **5/5 (100%)** | Current recommendation |
| `/api/chat` + English system | 3/5 (60%) | No improvement |
| `/api/chat` + Bulgarian system | 2/5 (40%) | Same as current |

**Important clarification**: Both APIs are **stateless per request**:
- Each listing = 1 independent API call
- No context accumulates between listings
- No token overflow risk regardless of how many listings processed
- The "chat" in `/api/chat` just means different request format, NOT conversation memory

### 6.5 Hardware Considerations

For batch processing on limited hardware:

| Listings | Est. Time | Memory Strategy |
|----------|-----------|-----------------|
| <100 | <10 min | Default KEEP_ALIVE OK |
| 100-500 | 10-50 min | Set KEEP_ALIVE=1h |
| 500+ | 50+ min | Set KEEP_ALIVE=-1 (forever) |

**Tip**: Monitor with `nvidia-smi` or `ollama ps` to verify model stays loaded.

---

## 7. Keep Post-Processing as Safety Net

### 7.1 Rationale

Even with grammar enforcement, keep `_translate_values()` as defense-in-depth:

```python
# llm/llm_main.py (keep existing translation function)
def _translate_values(data: dict) -> dict:
    """
    Fallback translation layer (defense in depth).

    With Phase 1+2, this should rarely trigger. But if a model
    update changes behavior, this catches regressions.
    """
    CONSTRUCTION_MAP = {
        "тухла": "brick",
        "панел": "panel",
        # ... etc
    }

    if "construction" in data and data["construction"]:
        data["construction"] = CONSTRUCTION_MAP.get(
            data["construction"].lower(),
            data["construction"]
        )

    # ... similar for other enums
    return data
```

### 7.2 Monitoring Translation Triggers

Add logging to track when fallback is used:

```python
def map_fields(content: str, model: str = None) -> MappedFields:
    # ... generate response ...

    data = json.loads(response["response"])

    # Check if translation needed (indicates prompt failure)
    original_construction = data.get("construction")
    data = _translate_values(data)

    if original_construction != data.get("construction"):
        logger.warning(
            f"Translation fallback triggered: '{original_construction}' → '{data['construction']}'"
        )

    return MappedFields(**data)
```

**Alert**: If translation triggers frequently, indicates prompt/schema issue.

---

## 8. Model Upgrade Consideration

### 8.1 qwen2.5:1.5b vs 3b

From research:

| Aspect | qwen2.5:1.5b | qwen2.5:3b |
|--------|--------------|------------|
| VRAM | ~1.2 GB | ~2.4 GB |
| Instruction following | Adequate | **Significantly better** |
| JSON extraction | May deviate | **More reliable** |

**Recommendation**:
- Start with 1.5b + Phase 1+2
- If accuracy < 90%, upgrade to 3b model
- 3b has better instruction adherence → fewer prompt violations

### 8.2 Configuration Update

```yaml
# config/ollama.yaml
tasks:
  field_mapping:
    primary_model: qwen2.5:3b       # Upgrade if 1.5b insufficient
    fallback_model: qwen2.5:1.5b    # Cost fallback
    temperature: 0.0
```

---

## 9. Implementation Plan

### 9.1 Phases

| Phase | Tasks | Files Modified | Testing | Risk |
|-------|-------|----------------|---------|------|
| **Phase 1** | English prompts | `llm/prompts.py` | Manual test script | Low |
| **Phase 2** | Schema enforcement | `llm/llm_main.py` | Automated test suite | Low |
| **Phase 3** | OLLAMA_KEEP_ALIVE config | Environment/systemd | Batch test | Low |

### 9.2 Timeline

- **Phase 1**: 30 minutes (prompt rewrite + test)
- **Phase 2**: 1 hour (schema integration + validation)
- **Phase 3**: 10 minutes (environment configuration)

**Total**: ~1.5 hours for all phases.

---

## 10. Testing Strategy

### 10.1 Test Dataset

Create `/home/wow/Projects/sale-sofia/tests/fixtures/bulgarian_real_estate_samples.json`:

```json
[
  {
    "id": "sample_1",
    "text": "Тристаен апартамент, 85 кв.м, етаж 3 от 6, тухла, ТЕЦ, Лозенец",
    "expected": {
      "rooms": 3,
      "area_sqm": 85.0,
      "floor": 3,
      "total_floors": 6,
      "construction": "brick",
      "heating": "district",
      "neighborhood": "Лозенец"
    }
  },
  {
    "id": "sample_2",
    "text": "Двустаен, панел, газ, напълно обзаведен, асансьор",
    "expected": {
      "rooms": 2,
      "construction": "panel",
      "heating": "gas",
      "furnishing": "furnished",
      "has_elevator": true
    }
  }
  // ... 20+ samples covering edge cases
]
```

### 10.2 Automated Test Suite

```python
# tests/debug/test_ollama_accuracy.py
import json
import pytest
from llm import map_fields, extract_description

def load_test_cases():
    with open("tests/fixtures/bulgarian_real_estate_samples.json") as f:
        return json.load(f)

@pytest.mark.parametrize("case", load_test_cases())
def test_field_mapping_accuracy(case):
    result = map_fields(case["text"])
    expected = case["expected"]

    # Check enum fields (critical for Phase 1+2)
    if "construction" in expected:
        assert result.construction == expected["construction"], \
            f"Construction mismatch: expected '{expected['construction']}', got '{result.construction}'"

    if "heating" in expected:
        assert result.heating == expected["heating"], \
            f"Heating mismatch: expected '{expected['heating']}', got '{result.heating}'"

    # Check numeric fields
    if "rooms" in expected:
        assert result.rooms == expected["rooms"]

    # Check confidence
    assert result.confidence >= 0.6, f"Low confidence: {result.confidence}"

def test_accuracy_summary():
    """Overall accuracy test."""
    cases = load_test_cases()
    total = 0
    correct = 0

    for case in cases:
        result = map_fields(case["text"])
        expected = case["expected"]

        for field, expected_val in expected.items():
            total += 1
            actual_val = getattr(result, field, None)
            if actual_val == expected_val:
                correct += 1

    accuracy = correct / total
    print(f"Overall accuracy: {accuracy:.1%} ({correct}/{total})")

    # Phase 1+2 target
    assert accuracy >= 0.90, f"Accuracy {accuracy:.1%} below 90% target"
```

### 10.3 Success Criteria

| Metric | Phase 1 Target | Phase 2 Target | Final Target |
|--------|---------------|---------------|--------------|
| Enum accuracy | 80%+ | 95%+ | 95%+ |
| Overall accuracy | 70%+ | 85%+ | 90%+ |
| Confidence score | >0.7 avg | >0.75 avg | >0.75 avg |
| Bulgarian leakage | <10% | 0% | 0% |
| Model reload (batch) | N/A | N/A | 0 (Phase 3) |

---

## 11. Rollback Plan

### 11.1 If Phase 1 Fails (<70% accuracy)

**Rollback**: Revert to Bulgarian prompts (Spec 107 implementation)

```bash
git checkout llm/prompts.py
```

**Next step**: Investigate model behavior, consider model upgrade first.

### 11.2 If Phase 2 Breaks JSON Parsing

**Issue**: Schema too strict → model returns invalid JSON

**Fix**: Relax schema temporarily:
```python
# Temporarily allow strings for numbers
area_sqm: Optional[Union[float, str]] = None
```

**Next step**: Post-process string-to-number conversion.

### 11.3 If Phase 3 (KEEP_ALIVE) Causes Issues

**Issue**: Model staying loaded uses too much VRAM

**Fix**: Reduce KEEP_ALIVE or manually unload:
```bash
# Reduce to 15 minutes
export OLLAMA_KEEP_ALIVE=15m

# Or manually unload model after batch
curl -X DELETE http://localhost:11434/api/generate -d '{"model": "qwen2.5:1.5b", "keep_alive": 0}'
```

**Rollback**: Remove OLLAMA_KEEP_ALIVE override, use default 5m.

---

## 12. Files to Modify

| File | Changes | Lines Changed | Risk |
|------|---------|---------------|------|
| `llm/prompts.py` | Rewrite to English | ~50 lines | Low |
| `llm/llm_main.py` | Add schema to format param | ~10 lines | Low |
| `~/.bashrc` or systemd | Add OLLAMA_KEEP_ALIVE | 1 line | None |
| `tests/fixtures/bulgarian_real_estate_samples.json` | New test data | New file | None |
| `tests/debug/test_ollama_accuracy.py` | New test suite | New file | None |

**Total**: ~60 lines modified/added across 4 files + environment config.

---

## 13. Monitoring & Validation

### 13.1 Production Metrics

Add to `llm/llm_main.py`:

```python
# Track accuracy in production
METRICS = {
    "total_extractions": 0,
    "translation_fallbacks": 0,  # Should be 0 with Phase 2
    "low_confidence": 0,         # confidence < 0.6
    "parse_errors": 0            # JSON parsing failures
}

def log_metrics():
    """Log extraction metrics for monitoring."""
    total = METRICS["total_extractions"]
    if total > 0:
        fallback_rate = METRICS["translation_fallbacks"] / total
        low_conf_rate = METRICS["low_confidence"] / total

        logger.info(
            f"Ollama metrics: {total} extractions, "
            f"{fallback_rate:.1%} fallbacks, "
            f"{low_conf_rate:.1%} low confidence"
        )
```

### 13.2 Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Fallback rate | >5% | Investigate prompt regression |
| Low confidence rate | >20% | Review test cases, tune prompts |
| Parse errors | >1% | Check schema compatibility |

---

## 14. Documentation Updates

### 14.1 Update Spec 107

Add to `/home/wow/Projects/sale-sofia/docs/specs/107_OLLAMA_INTEGRATION.md`:

```markdown
## Prompt Language Strategy

**IMPORTANT**: Prompts are written in **English**, not Bulgarian.

**Rationale**: Research (Spec 108) shows English prompts achieve 5/5 accuracy
vs 2/5 for Bulgarian prompts when extracting English enum values from Bulgarian text.

See [Spec 108](/home/wow/Projects/sale-sofia/docs/specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md) for details.
```

### 14.2 Update README

Add to main README section on LLM integration:

```markdown
### LLM Data Extraction

Uses Ollama with qwen2.5 models for extracting structured data from Bulgarian real estate text.

**Accuracy**: 90%+ on field extraction with JSON schema enforcement.

**Key technique**: English prompts + JSON schema grammar enforcement ensures English enum values
even when extracting from Bulgarian text.

See [Spec 108](/home/wow/Projects/sale-sofia/docs/specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md) for implementation details.
```

---

## 15. Related Research

- [ollama_language_behavior.md](/home/wow/Projects/sale-sofia/docs/research/ollama_language_behavior.md) - Prompt testing results
- [Ollama Structured Outputs](https://ollama.com/blog/structured-outputs) - JSON schema enforcement
- [Qwen2.5 Model Comparison](https://qwenlm.github.io/blog/qwen2.5-llm/) - Model selection rationale

---

## 16. Success Metrics

### 16.1 Acceptance Criteria

- [ ] Phase 1 achieves 80%+ enum accuracy
- [ ] Phase 2 achieves 95%+ enum accuracy
- [ ] No Bulgarian enum values in production logs
- [ ] Test suite passes with 90%+ overall accuracy
- [ ] Translation fallback triggers <5% of extractions
- [ ] Average confidence score >0.75

### 16.2 Performance Targets

- Extraction time: <3s per listing (same as Spec 107)
- No degradation in throughput
- Memory usage unchanged (<1.5GB VRAM for qwen2.5:1.5b)

---

## 17. Next Steps

1. **Immediate**: Implement Phase 1 (English prompts)
2. **Test**: Run automated test suite, measure accuracy
3. **If >80%**: Implement Phase 2 (schema enforcement)
4. **Configure**: Set OLLAMA_KEEP_ALIVE for batch processing (Phase 3)
5. **If <90% after Phase 2**: Upgrade to qwen2.5:3b model

**Estimated completion**: ~1.5 hours for all 3 phases.

---

## 18. Dependencies

**Blocks**:
- Full Scrapling integration with LLM extraction (depends on this accuracy)
- Production deployment of field mapping pipeline

**Depends On**:
- [Spec 107](/home/wow/Projects/sale-sofia/docs/specs/107_OLLAMA_INTEGRATION.md) - Base Ollama integration must exist

**Related**:
- Crawler validation (Spec 106) - accuracy metrics tie into overall data quality
