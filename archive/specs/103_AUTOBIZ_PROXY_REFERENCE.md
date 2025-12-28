# AutoBiz vs Current Implementation - Proxy System Comparison

**Source**: `archive/extraction/proxies/proxies_AutoBiz.md` (from github.com/idkny/Auto-Biz)

---

## Function Comparison

### 1. SCRAPE TASK

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `scrape_new_proxies_task()` | `scrape_new_proxies_task()` |
| **Location** | `auto_biz/tasks/proxies.py` | `proxies/tasks.py:21-60` |
| **Auto-trigger** | YES - calls `check_scraped_proxies_task.delay()` | NO - uses explicit chains |
| **Timeout** | None specified | 300s (5 min) |

**AutoBiz Code:**
```python
@celery_app.task
def scrape_new_proxies_task() -> Optional[str]:
    cmd = [str(PSC_EXECUTABLE_PATH), "-o", str(psc_output_file)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    # Auto-trigger checking
    check_scraped_proxies_task.delay()
    return f"Scraped {proxies_found} potential proxies."
```

**Current Code:**
```python
@celery_app.task
def scrape_new_proxies_task(_previous_result=None):
    cmd = [str(PSC_EXECUTABLE_PATH), "-o", str(psc_output_file)]
    subprocess.run(cmd, cwd=str(PROXY_CHECKER_DIR), check=True,
                   capture_output=True, text=True, timeout=300)
    # Does NOT auto-trigger - uses chains instead
    return f"Scraped {proxies_found} potential proxies."
```

---

### 2. DISPATCHER TASK (The Key Difference)

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `check_scraped_proxies_task()` | `check_scraped_proxies_task()` |
| **Pattern** | `chord(group)(chain)` | `(group \| callback).delay()` |
| **Callback** | Multi-step: combine → dispatch_quality → final | Single: process_results |

**AutoBiz Code (CHORD pattern):**
```python
@celery_app.task
def check_scraped_proxies_task() -> str:
    chunk_size = 100
    proxy_chunks = [all_proxies[i:i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]

    # CHORD: parallel checks -> combine -> dispatch quality checks
    header = group(mubeng_check_chunk_task.s(chunk) for chunk in proxy_chunks)
    callback_chain = chain(
        combine_mubeng_results_task.s(),      # Step 1: Combine all chunk results
        dispatch_quality_checks_task.s()       # Step 2: Fan-out to quality checks
    )
    chord(header)(callback_chain)

    return f"Dispatched {len(proxy_chunks)} chunks for validation"
```

**Current Code (GROUP | CALLBACK pattern):**
```python
@celery_app.task
def check_scraped_proxies_task(_previous_result=None):
    chunk_size = 100
    proxy_chunks = [all_proxies[i:i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]

    # GROUP with single callback
    parallel_tasks = group(check_proxy_chunk_task.s(chunk) for chunk in proxy_chunks)
    callback = process_check_results_task.s()
    (parallel_tasks | callback).delay()

    return f"Dispatched {len(proxy_chunks)} chunks for processing."
```

**Difference**: AutoBiz has a 2-step callback chain, Current has single callback.

---

### 3. MUBENG CHECK TASK

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `mubeng_check_chunk_task()` | `check_proxy_chunk_task()` |
| **PTY Wrapper** | NO | YES - `script -q /dev/null` |
| **Quality inline** | NO - separate task | YES - anonymity + quality inline |
| **Timeout** | 120s | 120s |

**AutoBiz Code (simple, mubeng only):**
```python
@celery_app.task
def mubeng_check_chunk_task(proxy_chunk: list[dict]) -> list[dict]:
    temp_input_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt")
    temp_output_file = tempfile.NamedTemporaryFile(mode='r', delete=False, suffix=".txt")

    for proxy in proxy_chunk:
        protocol = proxy.get("protocol", "http")
        temp_input_file.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")
    temp_input_file.close()

    # Direct mubeng call (no PTY wrapper)
    cmd = [str(MUBENG_EXECUTABLE_PATH), "--check", "-f", temp_input_file.name, "-o", temp_output_file.name]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)

    # Return only live proxies
    return live_proxies_in_chunk
```

**Current Code (PTY wrapper + inline quality):**
```python
@celery_app.task
def check_proxy_chunk_task(proxy_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # ... write temp files ...

    mubeng_cmd = [str(MUBENG_EXECUTABLE_PATH), "--check", "-f", str(temp_input_path),
                  "-o", str(temp_output_path), "-t", "10s"]

    # PTY wrapper (mubeng hangs without terminal)
    cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)

    # ... parse results ...

    # INLINE: Anonymity check
    for proxy in live_proxies_in_chunk:
        enrich_proxy_with_anonymity(proxy, timeout=10)

    # INLINE: Filter /24 subnet matches
    live_proxies_in_chunk = [p for p in live_proxies_in_chunk
                             if not p.get("exit_ip", "").startswith(real_ip_prefix)]

    # INLINE: Quality check
    for proxy in quality_candidates:
        enrich_proxy_with_quality(proxy, timeout=60)

    return live_proxies_in_chunk
```

---

### 4. QUALITY CHECK TASK

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `sequential_quality_check_task()` | INLINE in `check_proxy_chunk_task()` |
| **Pattern** | Separate task, called via chord | Inline function call |
| **Checks** | ipify + Google | anonymity + quality_checker |

**AutoBiz Code (separate task):**
```python
@celery_app.task
def sequential_quality_check_task(proxy: dict) -> Optional[dict]:
    proxy_url = f"{proxy.get('protocol', 'http')}://{proxy['host']}:{proxy['port']}"

    # Stage 2: Simple liveness check
    requests.get("https://api.ipify.org?format=json", proxies={"http": proxy_url, "https": proxy_url}, timeout=30)

    # Stage 3: Google quality check (REMOVED - not needed for this project)
    return proxy
```

**Current Code (inline):**
```python
# Inside check_proxy_chunk_task():
for proxy in live_proxies_in_chunk:
    enrich_proxy_with_anonymity(proxy, timeout=10)  # Uses anonymity_checker.py

for proxy in quality_candidates:
    enrich_proxy_with_quality(proxy, timeout=60)    # Uses quality_checker.py
```

---

### 5. FINAL RESULTS TASK

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `process_final_results_task()` | `process_check_results_task()` |
| **Output** | `live_proxies.json` | `live_proxies.json` + `live_proxies.txt` |
| **Filtering** | None (done earlier) | Filters Transparent proxies |

Both are similar - combine results from chunks and save to file.

---

### 6. MUBENG SERVER (Rotator)

| Aspect | AutoBiz | Current (sale-sofia) |
|--------|---------|----------------------|
| **Function** | `start_mubeng_rotator()` | `start_mubeng_rotator_server()` |
| **Location** | `proxies/mubeng_manager.py` | `proxies/mubeng_manager.py` |
| **Flags** | `-a`, `-f`, `-t`, `--max-errors` | `-a`, `-f`, `-t`, `--max-errors`, `--rotate-on-error`, `-m random`, `-s` |

**AutoBiz Code:**
```python
def start_mubeng_rotator(live_proxy_file: Path, desired_port: int,
                         mubeng_timeout: str = "15s", max_errors: int = 3):
    mubeng_command = [
        str(MUBENG_EXECUTABLE_PATH),
        "-a", f"localhost:{desired_port}",
        "-f", str(live_proxy_file),
        "-t", mubeng_timeout,
        "--max-errors", str(max_errors),
    ]
    process = subprocess.Popen(mubeng_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return process
```

**Current has more flags** - adds `--rotate-on-error`, `-m random`, `-s` (sync mode).

---

## Key Differences Summary

| Aspect | AutoBiz | Current | Better? |
|--------|---------|---------|---------|
| **Orchestration** | `chord(group)(chain)` | `(group \| callback)` | Same effect |
| **Quality check** | Separate task | Inline | **Current** (less overhead) |
| **PTY wrapper** | None | `script -q /dev/null` | **Current** (fixes hang) |
| **Mubeng server flags** | Basic | Extended | **Current** (more control) |
| **Anonymity filter** | None | Yes | **Current** (filters Transparent) |
| **Real IP filter** | None | Yes (/24 subnet) | **Current** (better protection) |

---

## Conclusion

**Current implementation is actually MORE complete than AutoBiz:**
1. ✅ Has PTY wrapper to prevent mubeng hang
2. ✅ Has inline anonymity + quality checks (less Celery overhead)
3. ✅ Filters Transparent proxies and /24 subnet matches
4. ✅ More mubeng server flags for better rotation

**Both use the same core pattern:**
```
PSC scrape → chunks → mubeng --check → combine → save → mubeng server
```

**Potential issue to test:** Does `(group | callback).delay()` properly wait for all chunks before callback? (It should - this is equivalent to chord)
