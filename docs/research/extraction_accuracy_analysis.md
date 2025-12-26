# Extraction Accuracy Analysis

**Date**: 2025-12-26
**Goal**: Understand why extract_description() achieves only 78% accuracy
**Target**: 95%+ accuracy

## Background

Session 7 fixed enum value accuracy (100% - values are now English). But **extraction rate** is still ~78%, meaning fields often return `null` when data exists in the text.

## Research Questions

1. Which fields fail to extract most often?
2. Is qwen2.5:1.5b too small for this task?
3. What prompt variations help?
4. Should we use regex pre-extraction for obvious patterns?

## Test Corpus

Real Bulgarian real estate description samples:

### Sample 1: Feature-rich description
```
Напълно обзаведен тристаен апартамент в комплекс с охрана.
Южно изложение с гледка към Витоша.
Площ 85 кв.м., 2 спални, 1 баня.
Паркомясто в подземен гараж. Асансьор.
Централно отопление ТЕЦ.
```

Expected:
- rooms: 3
- bedrooms: 2
- bathrooms: 1
- furnishing: "furnished"
- orientation: "south"
- has_view: true
- view_type: "mountain"
- has_parking: true
- parking_type: "underground"
- has_elevator: true
- has_security: true
- heating_type: "district"

### Sample 2: Minimal description
```
Двустаен апартамент, необзаведен, източно изложение.
```

Expected:
- rooms: 2
- furnishing: "unfurnished"
- orientation: "east"

### Sample 3: Price-focused description
```
Четиристаен апартамент с тераса и мазе.
Частично обзаведен. Газово отопление.
Гараж в двора. Ново строителство 2023.
```

Expected:
- rooms: 4
- has_balcony: true
- has_storage: true
- furnishing: "partially"
- heating_type: "gas"
- has_parking: true
- parking_type: "outdoor"
- condition: "new"

## Test Results

**Test Date**: 2025-12-26
**Model**: qwen2.5:1.5b (current primary)

### Per-Field Accuracy (5 samples, 39 expected values)

| Field | Correct | Total | Accuracy | Notes |
|-------|---------|-------|----------|-------|
| rooms | 4 | 5 | 80% | Good - has Bulgarian hints in prompt |
| bedrooms | 1 | 2 | 50% | Missing "спални" hint |
| bathrooms | 0 | 2 | **0%** | Missing "баня" hint |
| furnishing | 4 | 5 | 80% | Has hints, mostly works |
| condition | 2 | 3 | 67% | Confuses renovated/new |
| has_parking | 3 | 3 | 100% | Works |
| parking_type | 2 | 3 | **67%** | Confuses outdoor/garage |
| has_elevator | 0 | 1 | **0%** | Missing "асансьор" hint |
| has_security | 2 | 2 | 100% | Works |
| has_balcony | 1 | 1 | 100% | Works |
| has_storage | 1 | 1 | 100% | Works |
| orientation | 3 | 4 | **75%** | Missing "източно/западно" hints |
| has_view | 2 | 2 | 100% | Works |
| view_type | 1 | 2 | **50%** | Confuses mountain/park |
| heating_type | 1 | 3 | **33%** | Confuses district/electric/gas |

**OVERALL: 27/39 = 69%**

### Model Comparison

| Model | Accuracy | Notes |
|-------|----------|-------|
| **qwen2.5:1.5b** | **61%** | Winner |
| qwen2.5:3b | 30% | Worse - initial timeout, not more accurate |

**Conclusion**: Model size is NOT the problem.

## Root Cause Analysis

### Fields WITH Bulgarian hints (in prompt) - HIGH accuracy
- `rooms`: (едностаен=1, двустаен=2...) → 80%
- `furnishing`: (обзаведен → furnished...) → 80%
- `has_parking`, `has_balcony`, `has_storage` → 100%

### Fields WITHOUT Bulgarian hints - LOW accuracy
- `bathrooms`: No "баня" hint → 0%
- `has_elevator`: No "асансьор" hint → 0%
- `orientation`: No "източно/западно" hints → 75%
- `heating_type`: Hints exist but confused → 33%
- `view_type`: No "Витоша → mountain" hint → 50%

## Solution: Add Comprehensive Bulgarian Hints

The current prompt has hints for some fields but not others. The fix is:

1. Add Bulgarian word hints for ALL fields
2. Include common variations (e.g., "баня", "бани", "санитарен възел")
3. Include proper nouns (e.g., "Витоша" → mountain view)

### Proposed Prompt Additions

```
- bathrooms: number or null
  (баня/бани=count bathrooms, санитарен възел=bathroom)
- has_elevator: boolean or null
  (true for асансьор/лифт)
- orientation: "north" | "south" | "east" | "west" | null
  (север=north, юг=south, изток/източно=east, запад/западно=west)
- view_type: "city" | "mountain" | "park" | null
  (град=city, планина/Витоша/Рила=mountain, парк/градина=park)
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
  (ТЕЦ/централно топлоснабдяване=district, газ/газово=gas, ток/електричество=electric, климатик=air_conditioner)
- parking_type: "underground" | "outdoor" | "garage" | null
  (подземен/паркинг под=underground, двор/открит=outdoor, гараж=garage)
```

## Solution Designed

**Spec 110: Dynamic Bulgarian Dictionary** (supersedes static hint approach)

### Approach
1. Create `config/bulgarian_dictionary.yaml` with Bulgarian→English mappings
2. Before LLM call, regex scan input text for dictionary matches
3. Inject ONLY relevant hints into prompt (shorter, focused)
4. Pre-extract numeric values with regex (more reliable than LLM)
5. Log unknown Bulgarian words for future dictionary updates

### Benefits
- Shorter prompts (only relevant hints)
- Growable dictionary (add words as discovered)
- Less LLM cognitive load
- Maintainable (dictionary separate from code)
- Learning capability (unknown word logging)

### Files to Create
- `config/bulgarian_dictionary.yaml` - Dictionary source of truth
- `llm/dictionary.py` - Scanner and hint builder

### Files to Modify
- `llm/prompts.py` - Base templates with {hints} placeholder
- `llm/llm_main.py` - Integrate dictionary scanning

## Status

**Research**: Complete
**Spec**: 110_DYNAMIC_BULGARIAN_DICTIONARY.md (ready for implementation)
**Next**: Implement dictionary approach
