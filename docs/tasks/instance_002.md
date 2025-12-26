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

### 2025-12-26 (Session 22 - Ollama Phase 5 Complete)

| Task | Status |
|------|--------|
| Add extraction cache | Complete |
| Add confidence threshold to config | Complete |
| Add metrics logging | Complete |
| Performance test (100 listings) | Complete |
| Research page change detection | Complete |
| Create Spec 111 | Complete |
| Update SCRAPER_GUIDE.md | Complete |

**Summary**: Completed Ollama Phase 5 (Production Hardening). Added Redis-based extraction cache (7-day TTL, 3700+ extractions/sec on cache hit), configurable confidence threshold, and metrics logging API. Researched page change detection from autobiz project, created Spec 111 for future implementation. Updated SCRAPER_GUIDE.md with LLM integration documentation.

**Files Modified**:
- `config/ollama.yaml:11` - added `confidence_threshold: 0.7`
- `llm/llm_main.py:36-45, 393-441` - metrics tracking, get_confidence_threshold()
- `llm/__init__.py` - exported new functions
- `websites/imot_bg/imot_scraper.py:22,97` - use configurable threshold
- `tests/llm/test_performance.py` - new performance test
- `docs/research/page_change_detection.md` - new research
- `docs/specs/111_PAGE_CHANGE_DETECTION.md` - new spec
- `websites/SCRAPER_GUIDE.md` - added LLM integration section

---

### 2025-12-26 (Session 17 - Scrapling Integration)

| Task | Status |
|------|--------|
| Phase 3: Temperature = 0 | Complete (no effect) |
| Phase 4: Scrapling Integration | Complete |

**Summary**: Tested Phase 3 (temperature 0.1→0.0) - no effect on accuracy. Implemented Phase 4 Scrapling Integration: added `use_llm` flag, integrated LLM extraction into imot_scraper.py. LLM fills gaps where CSS returns None (e.g., orientation). Tested end-to-end with 0.95 confidence.

**Files Modified**:
- `config/ollama.yaml` - temperature 0.1 → 0.0
- `websites/scrapling_base.py:216` - added `use_llm` flag
- `websites/imot_bg/imot_scraper.py:20-25, 92-118` - LLM import + enrichment logic

**Usage**: `scraper.use_llm = True` enables LLM enrichment after CSS extraction.

---

### 2025-12-26 (Session 10 - Phase 2 Few-Shot Examples)

| Task | Status |
|------|--------|
| Test few-shot examples for boolean fields | Complete |
| Evaluate impact on accuracy | Complete |
| Decision: Skip Phase 2 | Complete |

**Summary**: Tested few-shot examples to fix `has_elevator` (0% accuracy). Examples fixed `has_elevator` but caused regressions in other fields (heating_type 67%, orientation 75%). Decided to skip Phase 2 since 97.4% already exceeds target and few-shot examples hurt more than help.

**Findings**:
- Few-shot examples made model too conservative
- Model returned `null` for fields that previously worked
- Net effect was negative on overall accuracy

**Decision**: Skip Phase 2. Remaining options: Phase 3 (temperature=0), Phase 4 (hybrid CSS/LLM), Phase 5 (field-specific prompts).

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
