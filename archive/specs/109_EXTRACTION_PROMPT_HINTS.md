# Spec 109: Extraction Prompt Bulgarian Hints

**Created**: 2025-12-26
**Status**: Ready for Implementation
**Priority**: P1 - Critical accuracy improvement (69% → 95%+)
**Depends On**: Spec 108 (Ollama Prompt Improvements)

---

## 1. Problem Statement

### Current State

The EXTRACTION_PROMPT has Bulgarian→English hints for some fields but not others:

**Fields WITH hints (high accuracy)**:
- `rooms`: 80% (has едностаен=1, двустаен=2...)
- `furnishing`: 80% (has обзаведен → furnished)
- `has_parking`, `has_storage`: 100%

**Fields WITHOUT hints (low accuracy)**:
- `bathrooms`: 0% (no "баня" hint)
- `has_elevator`: 0% (no "асансьор" hint)
- `orientation`: 75% (missing "източно/западно")
- `view_type`: 50% (missing "Витоша → mountain")
- `heating_type`: 33% (hints confused)

**Overall extraction accuracy**: 69%

### Research Finding

Model comparison (qwen2.5:1.5b vs 3b) showed **model size is NOT the problem**. The 3b model performed worse (30% vs 61%). The solution is **better prompts**, not bigger models.

### Target State

Add comprehensive Bulgarian hints to all fields → 95%+ accuracy.

---

## 2. Solution: Comprehensive Bulgarian Hints

### 2.1 Current EXTRACTION_PROMPT (from llm/prompts.py)

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
  (едностаен=1, двустаен=2, тристаен=3, четиристаен=4, петстаен=5)
- bedrooms: number or null
- bathrooms: number or null
- furnishing: "furnished" | "partially" | "unfurnished" | null
  (use "furnished" for обзаведен/напълно обзаведен, "partially" for частично, "unfurnished" for необзаведен)
- condition: "new" | "renovated" | "needs_renovation" | null
  (use "new" for нов, "renovated" for ремонтиран, "needs_renovation" for за ремонт)
- has_parking: boolean or null
- parking_type: "underground" | "outdoor" | "garage" | null
  (use "underground" for подземен, "outdoor" for двор, "garage" for гараж)
- has_elevator: boolean or null (true for асансьор)
- has_security: boolean or null (true for охрана)
- has_balcony: boolean or null (true for тераса/балкон)
- has_storage: boolean or null (true for мазе)
- orientation: "north" | "south" | "east" | "west" | null
  (use "north" for север, "south" for юг, "east" for изток, "west" for запад)
- has_view: boolean or null (true for гледка)
- view_type: "city" | "mountain" | "park" | null
  (use "city" for град, "mountain" for планина, "park" for парк)
- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
  (use "district" for ТЕЦ/централно, "gas" for газ, "electric" for ток, "air_conditioner" for климатик)
- payment_options: "cash" | "installments" | "mortgage" | null
- confidence: number (0.0-1.0)

Return ONLY valid JSON with these exact field names and enum values.
RESPOND IN ENGLISH ONLY. Your JSON values must be in English, not Bulgarian.
"""
```

### 2.2 Issues Found

| Field | Current Hint | Missing Variations |
|-------|--------------|-------------------|
| bedrooms | None | спалня, спални |
| bathrooms | None | баня, бани, санитарен възел |
| has_elevator | "асансьор" only | лифт |
| orientation | изток only | източно, западно |
| view_type | планина only | Витоша, Рила, Пирин |
| heating_type | ТЕЦ/централно | централно топлоснабдяване, газово |
| parking_type | двор only | открит, на двора |
| condition | за ремонт | нуждае се от ремонт |

---

## 3. Implementation

### 3.1 Updated EXTRACTION_PROMPT

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

NUMERIC FIELDS:
- rooms: number or null
  (едностаен=1, двустаен=2, тристаен=3, четиристаен=4, петстаен=5, многостаен=5+)
- bedrooms: number or null
  (спалня/спални - count them, e.g., "2 спални" = 2)
- bathrooms: number or null
  (баня/бани/санитарен възел - count them, e.g., "1 баня" = 1)

ENUM FIELDS (use EXACT English values):
- furnishing: "furnished" | "partially" | "unfurnished" | null
  (обзаведен/напълно обзаведен/с мебели = "furnished")
  (частично обзаведен = "partially")
  (необзаведен/без обзавеждане/празен = "unfurnished")

- condition: "new" | "renovated" | "needs_renovation" | null
  (нов/ново строителство/новопостроен = "new")
  (ремонтиран/обновен/реновиран = "renovated")
  (за ремонт/нуждае се от ремонт = "needs_renovation")

- orientation: "north" | "south" | "east" | "west" | null
  (север/северно изложение = "north")
  (юг/южно изложение = "south")
  (изток/източно изложение = "east")
  (запад/западно изложение = "west")

- parking_type: "underground" | "outdoor" | "garage" | null
  (подземен паркинг/подземно паркомясто = "underground")
  (двор/открит/на двора/паркомясто в двора = "outdoor")
  (гараж = "garage")

- view_type: "city" | "mountain" | "park" | null
  (град/градска гледка = "city")
  (планина/Витоша/Рила/Пирин/планинска гледка = "mountain")
  (парк/градина/зелена площ = "park")

- heating_type: "district" | "gas" | "electric" | "air_conditioner" | null
  (ТЕЦ/централно/централно топлоснабдяване/парно = "district")
  (газ/газово/газов котел = "gas")
  (ток/електричество/електрически/електрическо = "electric")
  (климатик/климатици = "air_conditioner")

- payment_options: "cash" | "installments" | "mortgage" | null

BOOLEAN FIELDS (true if keyword present):
- has_parking: true if паркомясто/паркинг/гараж mentioned
- has_elevator: true if асансьор/лифт mentioned
- has_security: true if охрана/СОТ/24-часова охрана mentioned
- has_balcony: true if тераса/балкон mentioned
- has_storage: true if мазе/склад/таван mentioned
- has_view: true if гледка mentioned

- confidence: number (0.0-1.0, your extraction confidence)

Return ONLY valid JSON with these exact field names and enum values.
"""
```

### 3.2 Key Changes

1. **Grouped fields by type** (numeric, enum, boolean) for clarity
2. **Added bedrooms hint**: "спалня/спални - count them"
3. **Added bathrooms hint**: "баня/бани/санитарен възел"
4. **Expanded orientation**: Added "източно/западно изложение" forms
5. **Expanded view_type**: Added "Витоша/Рила/Пирин" mountain names
6. **Expanded heating_type**: Added "парно", "газов котел", "електрически"
7. **Expanded parking_type**: Added "на двора", "паркомясто в двора"
8. **Expanded condition**: Added "новопостроен", "нуждае се от ремонт"
9. **Expanded furnishing**: Added "с мебели", "без обзавеждане", "празен"
10. **Added elevator variations**: "лифт"
11. **Removed redundant ending** (was duplicating "RESPOND IN ENGLISH ONLY")

---

## 4. Testing Plan

### 4.1 Test Script

Use existing `tests/llm/test_extraction_accuracy.py` with same 5 samples.

### 4.2 Expected Improvements

| Field | Before | After (Target) |
|-------|--------|----------------|
| bathrooms | 0% | 100% |
| has_elevator | 0% | 100% |
| heating_type | 33% | 90%+ |
| view_type | 50% | 90%+ |
| orientation | 75% | 90%+ |
| parking_type | 67% | 90%+ |
| bedrooms | 50% | 90%+ |
| **OVERALL** | **69%** | **95%+** |

### 4.3 Success Criteria

- [ ] Overall accuracy ≥ 95%
- [ ] No field below 80% accuracy
- [ ] No regression on currently working fields
- [ ] All tests pass in `tests/llm/test_ollama_prompts.py`

---

## 5. Files to Modify

| File | Changes |
|------|---------|
| `llm/prompts.py` | Replace EXTRACTION_PROMPT with enhanced version |

**Lines changed**: ~40 lines (prompt rewrite)

---

## 6. Rollback Plan

If accuracy drops or breaks:

```bash
git checkout llm/prompts.py
```

---

## 7. Implementation Checklist

- [ ] Update EXTRACTION_PROMPT in llm/prompts.py
- [ ] Run accuracy test: `python tests/llm/test_extraction_accuracy.py`
- [ ] Verify ≥ 95% overall accuracy
- [ ] Run existing tests: `pytest tests/llm/test_ollama_prompts.py`
- [ ] Archive research file
- [ ] Update TASKS.md
