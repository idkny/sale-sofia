# Subprocess Cleanup Analysis - Technical Documentation

## Current Implementation Review

### File: `/home/wow/Projects/sale-sofia/proxies/tasks.py`

## Task: `check_proxy_chunk_task` (Lines 94-206)

### Current Subprocess Management

**Location**: Lines 124-126

```python
cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
```

### Potential Issue: Orphan Subprocesses on Parent Death

#### Problem Description

When `subprocess.run()` is called, it creates a child process. However, if the Celery worker dies (SIGKILL) while this subprocess is running, the subprocess may not be properly terminated.

**Scenario**:
1. Celery worker starts `check_proxy_chunk_task`
2. Task spawns mubeng via `subprocess.run()`
3. Mubeng is running and checking proxies
4. Celery worker is killed (SIGKILL) - e.g., system crash, OOM kill, manual kill
5. **Question**: Does mubeng terminate, or become an orphan?

#### Analysis of Current Code

**Good Practices Already in Place**:
- Uses `timeout=120` to prevent infinite hangs
- Uses `finally` block to clean up temp files (lines 202-204)
- Uses `subprocess.run()` which waits for completion

**Potential Risk**:
- `subprocess.run()` blocks the task but doesn't guarantee cleanup on **parent death**
- If Celery worker is killed with SIGKILL, the signal doesn't propagate to child processes by default
- The `script` wrapper adds another layer of process hierarchy

#### Process Hierarchy

When the task runs:
```
celery worker (PID 1000)
  └─ Python task (PID 1001)
      └─ script -q /dev/null -c ... (PID 1002)
          └─ sh -c "mubeng ..." (PID 1003)
              └─ mubeng (PID 1004)
```

If Celery worker (PID 1000) is killed with SIGKILL:
- PID 1001 dies immediately
- PID 1002, 1003, 1004 may become **orphans** (reparented to init/systemd)

### Test to Confirm Issue

**Test 5** (`test5_mid_task_kill.py`) will definitively answer this question:
1. Start task with large chunk (takes time)
2. Verify mubeng is running
3. Kill Celery worker with SIGKILL
4. Check if mubeng is still running

**Expected Results**:
- **If orphans found**: Confirms subprocess cleanup issue
- **If no orphans**: Current implementation is safe

---

## Comparison: `scrape_new_proxies_task` (Lines 21-60)

### Subprocess Management in Scraping Task

**Location**: Lines 42-49

```python
cmd = [str(PSC_EXECUTABLE_PATH), "-o", str(psc_output_file)]
subprocess.run(
    cmd,
    cwd=str(PROXY_CHECKER_DIR),
    check=True,
    capture_output=True,
    text=True,
    timeout=300,  # 5 min timeout for scraping
)
```

**Same potential issue**: `subprocess.run()` without explicit process group management.

**Process hierarchy**:
```
celery worker (PID 2000)
  └─ Python task (PID 2001)
      └─ proxy-scraper-checker (PID 2002)
```

If worker dies, PSC (PID 2002) may become orphan.

---

## Root Cause: No Process Group Management

### Why Subprocesses May Orphan

By default:
- `subprocess.run()` doesn't create a new process group
- Child processes don't automatically die when parent is killed
- Linux doesn't send SIGKILL to child processes when parent dies

### Solution Options

#### Option 1: Use Process Groups (Recommended)
```python
import os
import signal

# Start subprocess in new process group
proc = subprocess.Popen(
    cmd,
    preexec_fn=os.setpgrp,  # Create new process group
    # ... other args
)

try:
    stdout, stderr = proc.communicate(timeout=120)
finally:
    # Kill entire process group
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except:
        os.killpg(proc.pid, signal.SIGKILL)
```

**Pros**:
- Ensures all child processes are killed
- Handles process trees (script → sh → mubeng)

**Cons**:
- More complex code
- Need to handle exceptions carefully

#### Option 2: Signal Handler Cleanup
```python
import signal
import atexit

mubeng_proc = None

def cleanup_subprocess():
    global mubeng_proc
    if mubeng_proc and mubeng_proc.poll() is None:
        mubeng_proc.terminate()
        try:
            mubeng_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mubeng_proc.kill()

# Register cleanup
signal.signal(signal.SIGTERM, lambda s, f: cleanup_subprocess())
atexit.register(cleanup_subprocess)

# Run subprocess
mubeng_proc = subprocess.Popen(cmd, ...)
```

**Pros**:
- Handles graceful shutdown (SIGTERM)
- Cleanup on normal exit (atexit)

**Cons**:
- Doesn't handle SIGKILL (can't be caught)
- Global state management

#### Option 3: Context Manager (Cleanest)
```python
from contextlib import contextmanager

@contextmanager
def managed_subprocess(cmd, **kwargs):
    proc = subprocess.Popen(cmd, **kwargs)
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

# Usage
with managed_subprocess(cmd, ...) as proc:
    stdout, stderr = proc.communicate(timeout=120)
```

**Pros**:
- Clean, Pythonic
- Guaranteed cleanup in all code paths

**Cons**:
- Still doesn't handle parent SIGKILL
- Need to convert `subprocess.run()` to `Popen()`

#### Option 4: Celery Task Revocation Handler
```python
from celery.exceptions import SoftTimeLimitExceeded, WorkerLostError

@celery_app.task(bind=True)
def check_proxy_chunk_task(self, proxy_chunk):
    proc = None
    try:
        proc = subprocess.Popen(cmd, ...)
        # ... do work
    except (SoftTimeLimitExceeded, WorkerLostError):
        # Task is being revoked/killed
        if proc:
            proc.terminate()
            proc.wait(timeout=5)
        raise
    finally:
        if proc and proc.poll() is None:
            proc.kill()
```

**Pros**:
- Celery-specific handling
- Can catch task revocation

**Cons**:
- Doesn't handle worker crash (SIGKILL)
- More Celery-specific code

---

## Recommended Solution

### Hybrid Approach: Process Groups + Context Manager

```python
import os
import signal
from contextlib import contextmanager

@contextmanager
def managed_process_group(cmd, **kwargs):
    """
    Context manager that runs subprocess in new process group
    and ensures cleanup even if parent is killed.
    """
    # Create subprocess in new process group
    proc = subprocess.Popen(
        cmd,
        preexec_fn=os.setpgrp,  # New process group
        **kwargs
    )

    try:
        yield proc
    finally:
        # Cleanup: Kill entire process group
        if proc.poll() is None:
            try:
                # Try graceful termination first
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                # Force kill if needed
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Already dead

# Usage in check_proxy_chunk_task
with managed_process_group(cmd, capture_output=True, text=True) as proc:
    try:
        stdout, stderr = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        # Timeout handling - context manager will cleanup
        raise
```

**Benefits**:
- Handles entire process tree (script → sh → mubeng)
- Guaranteed cleanup in normal and error paths
- Clean, reusable code
- Works with existing timeout logic

**Limitations**:
- **Still can't prevent orphans on parent SIGKILL** (nothing can)
- But minimizes the risk by cleaning up on all catchable signals

---

## What Test 5 Will Reveal

### Scenario A: Orphans Found (Expected)
```
CRITICAL FAIL: Orphan mubeng processes found!
Count: 3
```

**Interpretation**: Current implementation doesn't clean up subprocesses on parent death.

**Action Required**: Implement recommended solution above.

### Scenario B: No Orphans (Unexpected)
```
OK: No orphan mubeng processes
=== RESULT: PASS ===
```

**Interpretation**:
- Either Linux is handling cleanup automatically (unlikely)
- Or process hierarchy is working differently than expected
- Or `subprocess.run()` has built-in cleanup we didn't know about

**Action**: Document why it works, but still consider implementing explicit cleanup for safety.

---

## Additional Considerations

### The `script` Wrapper Issue

**Current code** (line 124):
```python
cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
```

This adds an extra layer: `script` → `sh -c` → `mubeng`

**Problem**: Even harder to clean up entire chain.

**Alternative**: Remove `script` wrapper if possible
- **Why it's used**: "mubeng hangs without terminal" (comment line 123)
- **Question**: Is this still needed? Test without it.

**If script is required**, process group cleanup becomes even more critical.

---

## Monitoring Recommendations

### Production Monitoring for Orphans

```bash
# Check for orphan mubeng processes
# Run every 5 minutes via cron
pgrep -af mubeng | grep -v celery && echo "ALERT: Orphan mubeng detected"

# Count processes over time
watch -n 10 'echo "Mubeng: $(pgrep -f mubeng | wc -l), Celery: $(pgrep -f celery | wc -l)"'
```

### Systemd Service Cleanup

If running Celery as systemd service:

```ini
[Service]
# Kill all processes in control group on stop
KillMode=control-group
# Use SIGTERM first
KillSignal=SIGTERM
# After 10s, use SIGKILL
TimeoutStopSec=10
```

This ensures systemd kills all child processes when Celery service stops.

---

## Next Steps

1. **Run Test 5** to confirm if orphan issue exists
2. **If orphans found**:
   - Implement process group management
   - Test again to verify fix
3. **If no orphans**:
   - Document why current implementation is safe
   - Still consider adding explicit cleanup for defensive programming
4. **Production deployment**:
   - Add orphan process monitoring
   - Configure systemd for proper cleanup
   - Set up alerts for process count anomalies

---

## Files to Review After Testing

If Test 5 fails, these are the exact lines to fix:

1. `/home/wow/Projects/sale-sofia/proxies/tasks.py`:
   - Lines 124-126: `check_proxy_chunk_task` subprocess call
   - Lines 42-49: `scrape_new_proxies_task` subprocess call

Both need the same fix: process group management or context manager approach.

---

## Conclusion

**Current State**: Potential subprocess orphaning on parent death.

**Test 5 Will Determine**: If this is a real issue or theoretical concern.

**Recommended Fix**: Process group management with context manager (code provided above).

**Timeline**:
1. Run tests (5 minutes)
2. Review results (5 minutes)
3. Implement fix if needed (15 minutes)
4. Re-test to verify (5 minutes)
5. Deploy to production with monitoring (ongoing)

**Priority**: High - orphan processes can accumulate and cause resource exhaustion.
