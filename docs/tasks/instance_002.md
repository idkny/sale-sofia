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

### 2025-12-25 (Session 3 - Automated File Placement Enforcement)

| Task | Status |
|------|--------|
| Explore ZohoCentral enforcement system | Complete |
| Design manifest + validation for sale-sofia | Complete |
| Implement project_structure_manifest.json | Complete |
| Create validate_file_placement.py | Complete |
| Create pre_write_validate.sh hook | Complete |
| Configure Claude Code hooks (.claude/settings.json) | Complete |
| Update CLAUDE.md with automation reference | Complete |

**Summary**: Implemented automated file placement enforcement based on ZohoCentral's system. Created manifest.json (source of truth), Python validator, and shell hook wrapper. Hooks now run BEFORE every Write/Edit to block wrong placements with helpful error messages.

**Files Created**:
- `admin/config/project_structure_manifest.json` - File placement rules (manifest)
- `admin/scripts/hooks/validate_file_placement.py` - Validation logic
- `admin/scripts/hooks/pre_write_validate.sh` - Hook wrapper
- `.claude/settings.json` - Hook configuration

**Files Modified**:
- `CLAUDE.md` - Updated FILE PLACEMENT RULES to reference automation

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

### 2025-12-24 (Session 1 - Project Cleanup & Multi-Instance Setup)

| Task | Status |
|------|--------|
| Clean root directory (move misplaced files) | Complete |
| Create scripts/, docs/tasks/ folders | Complete |
| Create README.md and .gitignore | Complete |
| Implement multi-instance coordination system | Complete |
| Implement research → specs → code workflow | Complete |
| Create /lss and /ess commands | Complete |

**Summary**: Major project reorganization. Cleaned root directory, created multi-instance coordination (TASKS.md, instance files), implemented research/specs/code workflow with archiving.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
