---
description: Load Session Start - Workflow and delegation rules
---

# Delegate, Don't Write. Use agents for all implementation work.

## Your Response

After reading this, say:

"I understand. I will:
1. Follow the research → specs → code workflow
2. Delegate each task to a specialized agent
3. Ensure agents don't touch the same files
4. After research → create spec + task in TASKS.md
5. After code complete → archive spec, code is source of truth"

---

## Workflow: Research → Specs → Code

**Single source of truth at each stage:**

```
research/     →    specs/      →    TASKS.md    →    code
(discovery)       (blueprint)       (tracking)       (truth)
     ↓                 ↓                               ↓
archive/research/  archive/specs/              (code supersedes)
```

### Stage 1: Research (`docs/research/`)
- Investigation, discovery, analysis
- Written in words, exploratory
- **When done**: Create spec + add task to TASKS.md, then archive research

### Stage 2: Specs (`docs/specs/`)
- Technical blueprint for implementation
- Middle ground between research and code
- Link in TASKS.md: `(spec: [FILENAME.md](../specs/FILENAME.md))`
- **When done**: Implement code, then archive spec

### Stage 3: Code (source of truth)
- Implementation follows spec (with expected changes)
- Code behavior supersedes spec
- Tests validate actual behavior
- **Specs become historical** once code exists

---

## Critical Rules

1. **Every step links to a task** - No orphan research, specs, or code
2. **Code is source of truth** - Not specs (specs are archived after implementation)
3. **Archive after completion** - Research → archive when spec done, Spec → archive when code done
4. **New features = new specs** - Don't update archived specs, write new ones

---

## Task Linking

```markdown
# Research task
- [ ] Research proxy rotation strategies
  (research: [proxy_rotation_research.md](../research/proxy_rotation_research.md))

# Spec task (after research)
- [ ] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task (after spec)
- [ ] Implement proxy rotation
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# After implementation complete
- [x] Implement proxy rotation
  # spec archived to archive/specs/, link removed
```

---

## Agent Rules

- Small tasks - One focused task per agent
- No conflicts - Agents must not touch the same files
- Sequential if unsure - One agent at a time
- Test before complete - Run tests as proof

---

## Folders

| Folder | Purpose |
|--------|---------|
| `docs/research/` | Active research files |
| `docs/specs/` | Active spec files |
| `docs/tasks/` | TASKS.md + instance files |
| `archive/research/` | Completed research (processed → spec) |
| `archive/specs/` | Completed specs (implemented → code) |
