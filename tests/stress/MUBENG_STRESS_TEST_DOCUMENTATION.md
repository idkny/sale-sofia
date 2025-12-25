# Mubeng Stress Test Documentation

## Overview
This document tracks the behavior of Mubeng under various stress conditions to understand:
- Exit codes and their meanings
- Process lifecycle management
- Error handling
- Resource cleanup
- Edge cases

## Test Execution

Run the comprehensive test suite:
```bash
chmod +x test_mubeng_stress.sh
./test_mubeng_stress.sh
```

All logs will be saved to `/tmp/mubeng_stress_tests/`

## Test Cases

### Test 1: Normal Operation (Check Mode)
**Purpose**: Baseline behavior with valid proxies

**Input**:
- Valid proxy list (http://1.1.1.1:80, http://8.8.8.8:80)
- Timeout: 5s
- Mode: --check

**Expected Behaviors**:
- Exit code 0 on success
- Creates output file with working proxies
- Completes within timeout
- No orphan processes

**Key Observations to Record**:
- Does it produce output even if all proxies fail?
- What happens if no proxies are reachable?
- Does it respect the timeout parameter?

---

### Test 2: Direct vs Script Wrapper Execution
**Purpose**: Understand PTY requirements and process control

**Test 2A - Direct Execution**:
```bash
timeout 10 ./mubeng --check -f proxies.txt -o out1.txt -t 3s
```

**Test 2B - Script Wrapper**:
```bash
timeout 10 script -q /dev/null -c "./mubeng --check -f proxies.txt -o out2.txt -t 3s"
```

**Key Observations to Record**:
- Exit code differences between direct and wrapper
- Output file creation differences
- STDOUT/STDERR behavior
- Does Mubeng require PTY (pseudo-terminal)?
- Which method is more reliable?

---

### Test 3: Empty Proxy File
**Purpose**: Edge case handling

**Input**: Empty file (just newline)

**Expected Behaviors**:
- Should fail gracefully
- Exit code likely non-zero
- No output file or empty output file
- Clear error message

**Key Observations to Record**:
- Actual exit code
- Error message format
- Does it hang or exit immediately?

---

### Test 4: Invalid Input
**Purpose**: Error handling and validation

**Input**: Malformed proxy entries
- "not-a-proxy"
- "invalid:port"
- "http://invalid"

**Expected Behaviors**:
- Should skip invalid entries or fail
- Exit code indicates error
- May produce partial output
- Error messages for invalid entries

**Key Observations to Record**:
- Does it skip invalid entries or abort?
- Exit code value
- Error message clarity
- Partial output file behavior

---

### Test 5: Multiple Simultaneous Processes
**Purpose**: Resource contention and concurrency

**Test**: 5 parallel Mubeng processes checking same proxy file

**Expected Behaviors**:
- All processes should complete
- No file locking issues
- Independent output files
- No orphan processes after completion

**Key Observations to Record**:
- Do processes interfere with each other?
- File locking errors?
- Memory/CPU consumption
- Orphan process count

---

### Test 6: Kill Mid-Execution
**Purpose**: Process termination and cleanup

**Test**: Start Mubeng with 30s timeout, kill after 2s with SIGKILL

**Expected Behaviors**:
- Process terminates immediately
- Partial output file may exist
- No orphan processes
- Clean resource cleanup

**Key Observations to Record**:
- Does SIGKILL leave orphans?
- Partial output file state
- File corruption risk
- Goroutine cleanup

---

### Test 7: Rotator Mode Start/Stop
**Purpose**: Daemon mode lifecycle

**Test**: Start rotator, verify listening, stop gracefully

**Expected Behaviors**:
- Binds to specified port (18089)
- Responds to SIGTERM gracefully
- Cleans up port binding
- No orphan processes

**Key Observations to Record**:
- Port binding success
- SIGTERM response time
- Port cleanup
- Orphan process behavior
- Does it need SIGKILL or SIGTERM is enough?

---

## Critical Exit Codes

Document all exit codes encountered:

| Exit Code | Meaning | Context |
|-----------|---------|---------|
| 0 | Success | Normal completion |
| 1 | ? | (To be documented) |
| 124 | Timeout | From `timeout` command |
| 137 | SIGKILL | Killed by signal 9 |
| 143 | SIGTERM | Terminated by signal 15 |
| ? | ? | Other codes to document |

## Known Issues & Workarounds

### Issue: [To be filled after testing]
**Symptom**:
**Root Cause**:
**Workaround**:

## Process Management Insights

### Orphan Process Scenarios
Document when orphan processes occur:
1. [ ] Normal exit
2. [ ] SIGTERM
3. [ ] SIGKILL
4. [ ] Timeout
5. [ ] Parent process dies

### Resource Cleanup
- [ ] File handles closed properly?
- [ ] Network connections cleaned?
- [ ] Goroutines terminated?
- [ ] Memory released?

## Integration Recommendations

Based on test results, document best practices:

### For Check Mode:
```python
# Recommended approach
# (To be filled after testing)
```

### For Rotator Mode:
```python
# Recommended approach
# (To be filled after testing)
```

## Test Results Location

All test outputs saved to: `/tmp/mubeng_stress_tests/`

Files:
- `test1.log` - Normal operation logs
- `test2a.log` - Direct execution logs
- `test2b.log` - Script wrapper logs
- `test3.log` - Empty file test logs
- `test4.log` - Invalid input logs
- `test5_proc_*.log` - Parallel process logs
- `test6.log` - Kill test logs
- `test7.log` - Rotator mode logs
- `*.txt` - Various output files

## Next Steps

After running tests:
1. Fill in actual exit codes and behaviors
2. Document any unexpected behaviors
3. Update `ProxyValidator` based on findings
4. Update process management in `ProxyRotator` if needed
5. Add specific error handling for discovered edge cases
