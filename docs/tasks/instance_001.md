# Instance 1 Session

**You are Instance 1.** Work independently.

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
2. Claim task with `[Instance 1]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 1] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 1] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 1] Implement proxy rotation
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
3. **Claim in TASKS.md** - Add `[Instance 1]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_002.md** - Other instance file is off-limits

---

## Session History

### 2025-12-30 (Session 59 - Mubeng & SSL Investigation)

| Task | Status |
|------|--------|
| Research mubeng tool (online) | ✅ Complete |
| Explore mubeng usage in codebase | ✅ Complete |
| Analyze git history for SSL certificate | ✅ Complete |
| Create research file | ✅ Complete |
| Add task to TASKS.md backlog | ✅ Complete |

**Summary**:
Deep investigation into mubeng proxy tool and SSL certificate necessity. Researched online (GitHub, Camoufox issues, Mozilla docs) and analyzed git history (commits 159b7e8, 3a11b91). Finding: mubeng binary only used for `--check` mode in Celery (can be replaced with ~25 lines Python). SSL certificate was needed for old mubeng server mode (MITM) but NOT for current direct proxy architecture. Recommendation: remove mubeng binary, keep certificate infrastructure.

#### Files Created
| File | Purpose |
|------|---------|
| `docs/research/MUBENG_SSL_INVESTIGATION.md` | Full investigation report with findings |

#### Files Modified
| File | Changes |
|------|---------|
| `docs/tasks/TASKS.md` | Added "Remove Mubeng Binary Dependency" task to backlog |

---

### 2025-12-30 (Session 52 - Proxy Settings Cleanup)

| Task | Status |
|------|--------|
| Find proxy validation functions & settings | ✅ Complete |
| Rename MAX_PROXY_RETRIES → MAX_URL_RETRIES | ✅ Complete |
| Add Failed URL Tracking task | ✅ Complete |
| Add Simplify Proxy Scoring task | ✅ Complete |
| Add Cleanup PROXY_WAIT_TIMEOUT task | ✅ Complete |

**Summary**:
Explored proxy system settings and identified confusing/overlapping mechanisms. Renamed `MAX_PROXY_RETRIES` to `MAX_URL_RETRIES` for clarity (it's about retrying URLs, not proxies). Added 3 new cleanup tasks to TASKS.md: Failed URL Tracking (persist failed URLs to DB), Simplify Proxy Scoring (remove complex score math), Cleanup PROXY_WAIT_TIMEOUT (dead code - replaced by Celery chord signals).

#### Files Modified
| File | Changes |
|------|---------|
| `config/settings.py` | Renamed MAX_PROXY_RETRIES → MAX_URL_RETRIES |
| `main.py` | Updated all references to MAX_URL_RETRIES |
| `tests/debug/test_phase5_retry_logic.py` | Updated all references |
| `docs/tasks/TASKS.md` | Added 3 new task sections |

---

### 2025-12-30 (Session 51 - OLX.bg Live Test + Enhanced Parsers)

| Task | Status |
|------|--------|
| Fetch OLX.bg search results page | ✅ Complete (Camoufox) |
| Fetch OLX.bg listing detail page | ✅ Complete (Camoufox) |
| Create `config/sites/olx_bg.yaml` | ✅ Complete |
| Test offline extraction | ✅ Complete |
| Add `:contains()` selector | ✅ Complete |
| Add `label_value/number/floor` parsers | ✅ Complete |
| Test live fetch | ⚠️ Blocked by captcha (needs proxy) |

**Summary**:
First REAL WEBSITE test of Generic Scraper Framework on OLX.bg. Offline extraction works: title, description, images, sqm, floor, floor_total all extracted. Enhanced `selector_chain.py` with `:contains()` pseudo-selector and `label_*` composite parsers. Live fetch blocked by OLX.bg captcha - needs mubeng proxy rotation.

#### Files Created
| File | Purpose |
|------|---------|
| `config/sites/olx_bg.yaml` | Full OLX.bg scraper config |
| `tests/debug/fetch_olx.py` | Fetch search page with Camoufox |
| `tests/debug/fetch_olx_detail.py` | Fetch detail page with Camoufox |
| `tests/debug/test_olx_real.py` | Offline extraction test |
| `tests/debug/test_olx_live.py` | Live fetch test (captcha blocked) |

#### Files Modified
| File | Changes |
|------|---------|
| `websites/generic/selector_chain.py` | +`:contains()` selector, +`label_value/number/floor` parsers |
| `websites/generic/config_scraper.py` | +explicit `floor_total` handling |

#### Test Results
- 148 generic scraper tests PASSED
- OLX.bg offline extraction: ✅ PASS (sqm=64, floor=6/7, 16 images)
- OLX.bg live fetch: ❌ Captcha (needs proxy rotation)

*(Session 50 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
