Look up documentation for a library from local cache or installed packages.

**Usage:** `/docs <library> [topic]`

**Steps:**
1. Check if `docs/libs/$ARGUMENTS.md` exists (GitHub-synced docs)
2. If not found, check `docs/libs/LOCAL_PACKAGES.md` for local package reference
3. For local packages, use: `venv/bin/python -c "import <lib>; help(<lib>)"`

**Available docs:**

| Library | Source | File |
|---------|--------|------|
| scrapling | GitHub | `docs/libs/scrapling.md` |
| pydantic | GitHub | `docs/libs/pydantic.md` |
| httpx | GitHub | `docs/libs/httpx.md` |
| camoufox | GitHub | `docs/libs/camoufox.md` |
| mubeng | GitHub | `docs/libs/mubeng.md` |
| celery | Local | `docs/libs/LOCAL_PACKAGES.md` |
| loguru | Local | `docs/libs/LOCAL_PACKAGES.md` |
| streamlit | Local | `docs/libs/LOCAL_PACKAGES.md` |
| pandas | Local | `docs/libs/LOCAL_PACKAGES.md` |
| pytest | Local | `docs/libs/LOCAL_PACKAGES.md` |
| playwright | Local | `docs/libs/LOCAL_PACKAGES.md` |

**To sync GitHub docs:**
```bash
GITHUB_TOKEN=$(gh auth token) ./admin/scripts/docs/sync_docs.sh
```

Read: `docs/libs/$ARGUMENTS.md`
