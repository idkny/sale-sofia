# End Session

End your work session so another instance can continue seamlessly.

---

## Checklist

### 1. Tasks (TASKS.md)

- [ ] Mark completed tasks with `[x]`
- [ ] Unclaim tasks if not finished (remove `[Instance N]`)
- [ ] Add any new tasks discovered during session
- [ ] Update coordination table (mark yourself as Available)

### 2. Research (docs/research/)

**If research is done and spec was created:**
- [ ] Move research file to `archive/research/`
- [ ] Update task link or remove if no longer needed

**If research NOT yet converted to spec:**
- [ ] Keep in `docs/research/`
- [ ] Add note: "needs spec" to the task

### 3. Specs (docs/specs/) - CRITICAL

**Code is source of truth, not specs.**

**If task with spec link is marked `[x]` complete:**
- [ ] Spec is now STALE (code may have changed)
- [ ] Move spec to `archive/specs/`
- [ ] Remove spec link from TASKS.md (just `[x] Task Name`)

**If adding features to existing code:**
- [ ] Write NEW spec (don't update archived ones)
- [ ] Add new task with link to new spec

### 4. Instance File

Update your `docs/tasks/instance_00X.md`:
- [ ] Add session entry to Session History (at top)
- [ ] Keep only last 3 sessions (archive older to `archive/sessions/`)

---

## Verification Questions

Answer before ending:

1. **Task-Spec Links**: Did you create or link specs for tasks you worked on?
   - If NO spec exists → create it or mark task "needs spec"

2. **Orphan Specs**: Did you create a spec without adding implementation task?
   - If YES → add task to TASKS.md with spec link

3. **Research Processed**: Is any research file older than 2 sessions?
   - If YES → convert to spec/task and archive it

4. **Completed Specs**: Did you complete a task that has a spec link?
   - If YES → archive spec, remove link from task

5. **Orphan Code**: Did you write code without a task?
   - If YES → add task to TASKS.md retroactively

6. **Next Instance Ready**: Can another instance continue your work?
   - Current status clear?
   - Blockers documented?

---

## Session Entry Format

```markdown
### YYYY-MM-DD (Session N - Brief Title)

| Task | Status |
|------|--------|
| Task 1 | Complete |
| Task 2 | In Progress |

**Summary**: 1-2 sentences about what was accomplished.
```

---

## Workflow Reminder

```
research/ → specs/ → TASKS.md → code
    ↓          ↓                  ↓
archive/   archive/         (source of truth)
```

**Rule**: Code supersedes specs. Archive specs after implementation.
