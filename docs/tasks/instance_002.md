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

### 2025-12-25 (Session 3 - File Enforcement, Docs Reorg, Git Init)

| Task | Status |
|------|--------|
| Implement file placement enforcement (ZohoCentral-style) | Complete |
| Add max_depth (3) and block_root_files rules | Complete |
| Split ARCHITECTURE.md into focused documents | Complete |
| Initialize git repository | Complete |
| Create initial commit (253 files) | Complete |

**Summary**: Implemented automated file placement enforcement with manifest.json, Python validator, and Claude hooks. Added rules to block files in docs/ root and limit depth to 3. Split 821-line ARCHITECTURE.md into 5 focused docs (131 lines core + 4 detailed docs). Initialized git with comprehensive .gitignore.

**Files Created**:
- `admin/config/project_structure_manifest.json` - File placement rules
- `admin/scripts/hooks/validate_file_placement.py` - Validation logic
- `admin/scripts/hooks/pre_write_validate.sh` - Hook wrapper
- `.claude/settings.json` - Hook configuration
- `docs/architecture/DESIGN_PATTERNS.md` - 8 design patterns
- `docs/architecture/DATA_FLOW.md` - Pipeline diagrams
- `docs/architecture/ADDING_COMPONENTS.md` - Extension guides
- `docs/architecture/CONVENTIONS.md` - Coding standards

**Files Modified**:
- `CLAUDE.md` - FILE PLACEMENT RULES section
- `.gitignore` - Enhanced with proxy/db/log exclusions
- `docs/architecture/ARCHITECTURE.md` - Slimmed to 131 lines with links

**Git**: Initialized on `main` branch, 2 commits

---

### 2025-12-25 (Session 2 - Architecture & File Structure Documentation)

| Task | Status |
|------|--------|
| Document project architecture (ARCHITECTURE.md) | Complete |
| Add Quality Checker deep dive section | Complete |
| Create file placement rules (FILE_STRUCTURE.md) | Complete |
| Update CLAUDE.md with file placement rules | Complete |
| Clean up misplaced files (stress_test_results.md) | Complete |

**Summary**: Created comprehensive architecture documentation (769 lines) with 8 design patterns, data flow diagrams, and component guides. Created FILE_STRUCTURE.md with decision tree for file placement. Updated CLAUDE.md with file rules to prevent future misplaced files.

**Files Created/Modified**:
- `docs/architecture/ARCHITECTURE.md` - Full architecture guide
- `docs/architecture/FILE_STRUCTURE.md` - File placement rules
- `CLAUDE.md` - Added FILE PLACEMENT RULES section

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
