# Instance 3 Session

**You are Instance 3.** Work independently.

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
2. Claim task with `[Instance 3]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 3] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 3] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 3] Implement proxy rotation
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
3. **Claim in TASKS.md** - Add `[Instance 3]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_001.md or instance_002.md** - Other instance files are off-limits

---

## Session History

### 2025-12-26 (Session 1 - Proxy Scoring System Analysis)

| Task | Status |
|------|--------|
| Set up Instance 3 | ✅ Complete |
| Analyze main.py and orchestrator.py | ✅ Complete |
| Investigate automatic proxy refresh | ✅ Complete |
| Investigate proxy removal on failure | ✅ Complete |
| Investigate JIT proxy validation | ✅ Complete |
| Document findings in TASKS.md | ✅ Complete |

**Summary**: Deep analysis of proxy management system revealed two critical bugs that make the scoring system non-functional.

**Finding 1: Wrong Proxy Being Tracked**
- `main.py` uses mubeng (`localhost:8089`) as proxy
- `record_result()` receives mubeng URL, not actual proxy
- Scoring system tracks wrong entity → does nothing

**Finding 2: Proxy Removal Doesn't Persist**
- `remove_proxy()` removes from memory only
- Does NOT update `live_proxies.json`
- Bad proxies return on next session reload

**Root Cause**: Architecture mismatch - `ScoredProxyPool` designed for direct proxy usage, but system uses mubeng as intermediary.

**Proposed Solutions**:
- A: Bypass mubeng for scraping (recommended)
- B: Get actual proxy from mubeng headers
- C: Separate concerns (mubeng for checking, direct for scraping)
- D: Fix persistence only (partial)

**Finding 3: No Just-In-Time Proxy Validation**
- No liveness check before using proxy for scraping
- Dead proxies waste 15-30s per request
- No retry with different proxy on failure
- Mubeng's `--rotate-on-error` is reactive, not proactive

**Blocker**: Automatic threshold-based refresh cannot work until scoring is fixed. JIT validation depends on scoring fix.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Instance 1 (don't edit)
- [instance_002.md](instance_002.md) - Instance 2 (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
