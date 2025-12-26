Look up documentation for a library from local cache.

**Usage:** `/docs <library> [topic]`

**Steps:**
1. Check if `docs/libs/$ARGUMENTS.md` exists
2. If exists, read and search for relevant content
3. If not found, suggest running: `./admin/scripts/docs/sync_docs.sh --lib <library>`

**Available libraries:** Check `docs/libs/` directory or run `./admin/scripts/docs/sync_docs.sh --list`

**To sync docs:**
- Sync all: `./admin/scripts/docs/sync_docs.sh`
- Sync one: `./admin/scripts/docs/sync_docs.sh --lib <library>`

Read: `docs/libs/$ARGUMENTS.md`
