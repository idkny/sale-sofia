---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-25
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

### 2025-12-26 (Session 5 - Ollama Integration Planning)

| Task | Status |
|------|--------|
| Research ZohoCentral Ollama implementation | Complete |
| Create Spec 107 (Ollama Integration) | Complete |
| Review project architecture patterns | Complete |
| Simplify spec architecture (12→5 files) | Complete |
| Update manifest.json for `llm/` folder | Complete |
| Update FILE_STRUCTURE.md for `llm/` folder | Complete |
| Remove duplicate tasks from spec (single source of truth) | Complete |

**Summary**: Researched ZohoCentral's Ollama integration (health check, port killer, model selection). Created Spec 107 for Ollama integration with 5-phase plan. Simplified architecture from 12 files to 5 files following `proxies/proxies_main.py` facade pattern. Updated project structure documentation.

**Key Decisions**:
- **Pattern**: `llm/` folder with facade pattern (same as `proxies/`)
- **Files**: 4 files only (`__init__.py`, `llm_main.py`, `prompts.py`, `schemas.py`)
- **Model**: `qwen2.5:1.5b` (1.2GB VRAM, good for Bulgarian/Cyrillic)
- **Use cases**: Page content → DB field mapping, Description → structured data

**Files Created/Modified**:
- `docs/specs/107_OLLAMA_INTEGRATION.md` - Full integration spec
- `admin/config/project_structure_manifest.json` - Added `llm/` folder rule
- `docs/architecture/FILE_STRUCTURE.md` - Added `llm/` documentation
- `docs/tasks/TASKS.md` - Added Ollama integration phases

**To Continue (Next Session)**:
1. Create `llm/` directory with 4 files
2. Create `config/ollama.yaml`
3. Implement OllamaClient (port from ZohoCentral)
4. Test Ollama start/stop/restart
5. Pull model: `ollama pull qwen2.5:1.5b`

---

### 2025-12-25 (Session 4 - Scrapling Integration & Crawler Plan)

| Task | Status |
|------|--------|
| Create crawler validation plan (Spec 106) | Complete |
| Add Scrapling integration (Phase 0) to spec | Complete |
| Install Scrapling v0.2.99 | Complete |
| Create `websites/scrapling_base.py` adapter | Complete |
| Test Scrapling with imot.bg | Complete |
| Migrate imot_scraper.py to Scrapling | Not Started |

**Summary**: Created comprehensive 5-phase crawler plan in Spec 106. Integrated Scrapling library for adaptive scraping with auto-encoding detection. Built and tested `scrapling_base.py` adapter that handles Bulgarian windows-1251 encoding automatically. Successfully extracted data from imot.bg (price: 170400 EUR, area: 71 sqm, floor: 4/6, building: brick).

**Why Scrapling?**
- **Adaptive scraping**: Auto-relocates selectors when sites change HTML
- **Anti-bot bypass**: StealthyFetcher with Camoufox (fingerprint spoofing)
- **774x faster** than BeautifulSoup for parsing
- **LLM integration**: MCP server for AI extraction (Ollama)

**Files Created**:
- `websites/scrapling_base.py` - Scrapling adapter with:
  - `detect_encoding()` - Auto-detects windows-1251, UTF-8 from headers/meta/chardet
  - `fetch_with_encoding()` - Fetches with proper Bulgarian text handling
  - `ScraplingMixin` class with `fetch()`, `css()`, `css_first()`, `get_page_text()`
  - StealthyFetcher integration for anti-bot bypass
- `docs/specs/106_CRAWLER_VALIDATION_PLAN.md` - Comprehensive 5-phase plan:
  - Phase 0: Scrapling Integration (partially complete)
  - Phase 1: Scraper Validation
  - Phase 2: Description Extraction (regex + LLM)
  - Phase 3: Change Detection & History (tracks ALL field changes)
  - Phase 3.5: Cross-Site Duplicate Detection & Merging
  - Phase 4: Rate Limiting & Async Orchestration
  - Phase 5: Full Pipeline Integration

**Key Decisions Made**:
1. **Encoding is flexible** - windows-1251 is Cyrillic (Bulgarian), auto-detected per site
2. **Change tracking** - Track ALL field changes, not just price (new `listing_changes` table)
3. **Cross-site merging** - Same property on multiple sites → merge data, track sources
4. **LLM for descriptions** - Use Ollama locally for extracting structured data

**What Works**:
```python
from websites.scrapling_base import ScraplingMixin

class MyScraper(ScraplingMixin):
    def __init__(self):
        self.site_name = 'imot.bg'
        super().__init__()

scraper = MyScraper()
page = scraper.fetch("https://www.imot.bg/...")  # Auto-detects encoding
text = scraper.get_page_text(page)  # Clean text for regex extraction
```

**To Continue (Next Session)**:
1. Migrate `websites/imot_bg/imot_scraper.py` to use ScraplingMixin
2. Migrate `websites/bazar_bg/bazar_scraper.py` to use ScraplingMixin
3. Test StealthyFetcher with mubeng proxy
4. Enable adaptive mode (`auto_save=True`, `auto_match=True`)

**Dependencies Added**:
- `scrapling[all]>=0.2.9` (already installed in venv)
- `chardet` (for encoding detection, installed)

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
