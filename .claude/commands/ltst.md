# Live Test Command (/ltst)

Run scraper live tests with proper output management to avoid filling Claude's context window.

## Problem
Live tests produce massive bash output that fills context quickly. Solution: run in background, save output to timestamped files, then investigate via agent.

## How to Run a Live Test

### 1. Create timestamped output file
```bash
TIMESTAMP=$(date +"%m-%d-%Y-%H:%M:%S")
OUTPUT_FILE="/home/wow/Projects/sale-sofia/data/logs/test_output_${TIMESTAMP}.log"
```

### 2. Run the test in background
Use `run_in_background: true` with Bash tool. Redirect all output to the timestamped file:

```bash
cd /home/wow/Projects/sale-sofia && source venv/bin/activate && python main.py > "${OUTPUT_FILE}" 2>&1
```

### 3. Logger Configuration
Logger is already configured in `utils/log_config.py`:
- Console: INFO level
- File: DEBUG level (JSON format)
- Log file: `data/logs/app.log`
- Rotation: 5 MB, retention: 5 days

### 4. Investigate Results
After test completes, spawn an agent to investigate:

Use the **Task tool** with `subagent_type: "unit-testing:debugger"` to:
- Read the bash output file: `data/logs/test_output_${TIMESTAMP}.log`
- Read the app log: `data/logs/app.log`
- Analyze errors, warnings, and test results
- Report findings back

## Quick Reference

| File | Purpose |
|------|---------|
| `data/logs/test_output_*.log` | Bash stdout/stderr from test runs |
| `data/logs/app.log` | Loguru DEBUG logs (JSON format) |

## Example Workflow

When user asks to run a live test:

1. Generate timestamp and output filename
2. Run bash command in background with output redirected
3. Wait for completion or check status with TaskOutput
4. Spawn debugger agent to analyze:
   - The timestamped bash output file
   - The app.log for DEBUG details
5. Report summary to user

## Important Notes
- ALWAYS run tests in background to preserve context
- ALWAYS redirect output to timestamped file
- NEVER let raw test output flood the conversation
- Use the debugger agent to parse and summarize results
