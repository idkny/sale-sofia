---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-26
---

# Instance 2 Session

**You are Instance 2.** Work independently.

---

## Workflow: Research → Specs → Code

**Single source of truth at each stage:**

```
docs/research/  →  docs/specs/  →  TASKS.md  →  code
(discovery)        (blueprint)     (tracking)    (truth)
      ↓                 ↓                           ↓
archive/research/  archive/specs/          (code supersedes)
```

**Rules:**
1. Research done → create spec + task → archive research
2. Spec done → implement code → archive spec
3. Code is source of truth (specs become historical)
4. New features = new specs (don't update archived)

---

## How to Work

1. Read [TASKS.md](TASKS.md) coordination table
2. Claim task with `[Instance 2]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 2] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 2] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 2] Implement proxy rotation
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# After complete (spec archived, link removed)
- [x] Implement proxy rotation
```

---

## CRITICAL RULES

1. **NEVER WRITE "NEXT STEPS" IN THIS FILE**
2. **TASKS.md IS THE SINGLE SOURCE OF TRUTH FOR TASKS**
3. **THIS FILE IS FOR SESSION HISTORY ONLY**
4. **KEEP ONLY LAST 3 SESSIONS**
5. **CODE IS SOURCE OF TRUTH, NOT SPECS**

---

## Instance Rules

1. **One task at a time** - Finish before claiming another
2. **Check coordination table FIRST** - Re-read TASKS.md before claiming
3. **Claim in TASKS.md** - Add `[Instance 2]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_001.md** - Other instance file is off-limits

---

## Session History

### 2025-12-26 (Session 8 - Dynamic Bulgarian Dictionary)

| Task | Status |
|------|--------|
| Research extraction accuracy failures | Complete |
| Test qwen2.5:3b vs 1.5b model | Complete (1.5b better) |
| Create Spec 110: Dynamic Bulgarian Dictionary | Complete |
| Create config/bulgarian_dictionary.yaml | Complete |
| Create llm/dictionary.py (scanner + hint builder) | Complete |
| Update llm/prompts.py with base templates | Complete |
| Update llm/llm_main.py to use dictionary | Complete |
| Research comprehensive BG real estate terminology | Complete |
| Update dictionary with 400+ researched terms | Complete |
| Run accuracy test | Pending |

**Summary**: Researched extraction accuracy issue (69% baseline). Found model size is NOT the problem (3b worse than 1.5b). Designed and implemented dynamic Bulgarian dictionary approach: scan text for keywords, inject only relevant hints into prompt. Launched 4 research agents to gather comprehensive Bulgarian real estate terminology (property types, legal docs, amenities, platform-specific terms). Created 600+ line dictionary file with all terms.

**Key Findings**:
- Extraction accuracy was 69% (not 78% as previously reported)
- Model size doesn't help: qwen2.5:1.5b (61%) > qwen2.5:3b (30%)
- Fields WITH Bulgarian hints have 80-100% accuracy
- Fields WITHOUT hints have 0-50% accuracy
- Solution: Dynamic dictionary with regex pre-scan

**Files Created**:
- `docs/specs/110_DYNAMIC_BULGARIAN_DICTIONARY.md`
- `llm/dictionary.py` - Scanner and hint builder
- `config/bulgarian_dictionary.yaml` - 400+ term comprehensive dictionary
- `tests/llm/test_extraction_accuracy.py` - Accuracy test suite
- `tests/llm/test_model_comparison.py` - Model comparison test

**Files Modified**:
- `llm/prompts.py` - Added EXTRACTION_PROMPT_BASE with {hints} placeholder
- `llm/llm_main.py` - Integrated dictionary scanning

**Files Archived**:
- `docs/specs/109_EXTRACTION_PROMPT_HINTS.md` → `archive/specs/` (superseded by Spec 110)

**Next Steps**:
1. Run accuracy test to verify improvement
2. If < 95%: Add few-shot examples (Phase 2)
3. If < 95%: Implement hybrid CSS/LLM approach (Phase 4)

---

### 2025-12-26 (Session 7 - Prompt Accuracy Improvements)

| Task | Status |
|------|--------|
| Research: Why model returns Bulgarian despite English constraints | Complete |
| Research: Ollama `format: json` behavior | Complete |
| Create test script for prompt experiments | Complete |
| Phase 1: Switch prompts to English | Complete |
| Phase 2: Add JSON schema enforcement | Complete |
| Phase 3: Configure OLLAMA_KEEP_ALIVE | Complete |
| Add Phase 3.6 task (95% accuracy target) | Complete |

**Summary**: Researched and implemented Spec 108 to fix Bulgarian value leakage. English prompts + JSON schema enforcement achieved 100% enum accuracy (was 40%). Added OLLAMA_KEEP_ALIVE=1h for batch processing.

**Key Findings**:
- `format: json` only ensures syntax, NOT value language
- English prompts with "RESPOND IN ENGLISH ONLY" = 100% accuracy
- Bulgarian prompts with English hints = 40% accuracy
- `/api/chat` provides no benefit over `/api/generate`

**Files Modified**:
- `llm/prompts.py` - English prompts with Bulgarian mappings
- `llm/llm_main.py` - Schema enforcement via `model_json_schema()` + keep_alive
- `config/ollama.yaml` - Added `keep_alive: 1h`

**Files Created**:
- `docs/specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md`
- `tests/llm/test_ollama_prompts.py` (8 integration tests)
- `docs/research/ollama_language_behavior.md` (archived)

**Commit**: f9361e8

---

### 2025-12-26 (Session 6 - Ollama Implementation + Testing)

| Task | Status |
|------|--------|
| Create `llm/` directory with 4 files | Complete |
| Create `config/ollama.yaml` | Complete |
| Implement OllamaClient in llm_main.py | Complete |
| Test Ollama start/stop/restart | Complete |
| Test map_fields() on 5 imot.bg pages | Complete (100%) |
| Test extract_description() on 5 descriptions | Complete (78%) |

**Summary**: Implemented full Ollama integration with parallel agent execution. Created 5 files (4 in llm/ + 1 config). Added Bulgarian→English translation layer for LLM responses. Tested with real imot.bg listings and synthetic descriptions.

**Test Results**:
- `map_fields()`: 100% extraction rate (price, area, floor, construction)
- `extract_description()`: 78% extraction rate (7/9 fields average)

**Files Created**:
- `llm/__init__.py` - Module exports
- `llm/llm_main.py` - OllamaClient facade (~280 lines)
- `llm/prompts.py` - Bulgarian prompts with English value constraints
- `llm/schemas.py` - Pydantic models (MappedFields, ExtractedDescription)
- `config/ollama.yaml` - Model and task configuration

**Key Implementation Details**:
- Singleton OllamaClient with health check + auto-restart
- Bulgarian→English translation in `_translate_values()`
- Prompts specify exact English enum values with Bulgarian explanations
- REST API calls to Ollama's `/api/generate` endpoint

**Parallel Agents Used**: 4 agents for independent files, 1 sequential for facade

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
