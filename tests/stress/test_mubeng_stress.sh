#!/bin/bash

# Mubeng Stress Testing Suite
# Purpose: Understand Mubeng behavior under different conditions

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MUBENG_BIN="${SCRIPT_DIR}/proxies/external/mubeng"
TEST_DIR="/tmp/mubeng_stress_tests"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Setup
mkdir -p "$TEST_DIR"
rm -f "$TEST_DIR"/*.txt "$TEST_DIR"/*.log

echo "=========================================="
echo "Mubeng Stress Testing Suite"
echo "=========================================="
echo ""

# ============================================
# Test 1: Normal Operation - Check Mode
# ============================================
echo -e "${YELLOW}Test 1: Mubeng Check Mode - Normal Operation${NC}"
echo -e "http://1.1.1.1:80\nhttp://8.8.8.8:80" > "$TEST_DIR/test_proxies.txt"
echo "Input file:"
cat "$TEST_DIR/test_proxies.txt"
echo ""

echo "Running: mubeng --check -f test_proxies.txt -o mubeng_out.txt -t 5s"
"$MUBENG_BIN" --check -f "$TEST_DIR/test_proxies.txt" -o "$TEST_DIR/mubeng_out.txt" -t 5s 2>&1 | tee "$TEST_DIR/test1.log"
EXIT_CODE=$?
echo -e "${GREEN}Exit code: $EXIT_CODE${NC}"
if [ -f "$TEST_DIR/mubeng_out.txt" ]; then
    echo "Output file content:"
    cat "$TEST_DIR/mubeng_out.txt"
else
    echo -e "${RED}No output file created${NC}"
fi
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 2: Direct vs Script Wrapper
# ============================================
echo -e "${YELLOW}Test 2: Mubeng with Script Wrapper vs Direct${NC}"

# Direct execution
echo "A) Direct execution (10s timeout):"
timeout 10 "$MUBENG_BIN" --check -f "$TEST_DIR/test_proxies.txt" -o "$TEST_DIR/out1.txt" -t 3s 2>&1 | tee "$TEST_DIR/test2a.log"
DIRECT_EXIT=$?
echo -e "${GREEN}Direct exit: $DIRECT_EXIT${NC}"
[ -f "$TEST_DIR/out1.txt" ] && echo "Output created: $(wc -l < "$TEST_DIR/out1.txt") lines"
echo ""

# With script wrapper
echo "B) With script wrapper (10s timeout):"
timeout 10 script -q /dev/null -c "$MUBENG_BIN --check -f $TEST_DIR/test_proxies.txt -o $TEST_DIR/out2.txt -t 3s" 2>&1 | tee "$TEST_DIR/test2b.log"
SCRIPT_EXIT=$?
echo -e "${GREEN}Script exit: $SCRIPT_EXIT${NC}"
[ -f "$TEST_DIR/out2.txt" ] && echo "Output created: $(wc -l < "$TEST_DIR/out2.txt") lines"
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 3: Empty File
# ============================================
echo -e "${YELLOW}Test 3: Mubeng with Empty File${NC}"
echo "" > "$TEST_DIR/empty_proxies.txt"
echo "Input: empty file"
"$MUBENG_BIN" --check -f "$TEST_DIR/empty_proxies.txt" -o "$TEST_DIR/empty_out.txt" -t 3s 2>&1 | tee "$TEST_DIR/test3.log"
EMPTY_EXIT=$?
echo -e "${GREEN}Empty file exit code: $EMPTY_EXIT${NC}"
[ -f "$TEST_DIR/empty_out.txt" ] && echo "Output file exists with $(wc -l < "$TEST_DIR/empty_out.txt") lines"
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 4: Invalid Input
# ============================================
echo -e "${YELLOW}Test 4: Mubeng with Invalid Input${NC}"
echo -e "not-a-proxy\ninvalid:port\nhttp://invalid" > "$TEST_DIR/invalid_proxies.txt"
echo "Input file:"
cat "$TEST_DIR/invalid_proxies.txt"
echo ""
"$MUBENG_BIN" --check -f "$TEST_DIR/invalid_proxies.txt" -o "$TEST_DIR/invalid_out.txt" -t 3s 2>&1 | tee "$TEST_DIR/test4.log"
INVALID_EXIT=$?
echo -e "${GREEN}Invalid input exit code: $INVALID_EXIT${NC}"
[ -f "$TEST_DIR/invalid_out.txt" ] && echo "Output file exists with $(wc -l < "$TEST_DIR/invalid_out.txt") lines"
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 5: Multiple Simultaneous Processes
# ============================================
echo -e "${YELLOW}Test 5: Multiple Mubeng Processes Simultaneously${NC}"
echo "Starting 5 parallel mubeng processes..."
for i in {1..5}; do
  "$MUBENG_BIN" --check -f "$TEST_DIR/test_proxies.txt" -o "$TEST_DIR/mubeng_out_$i.txt" -t 3s > "$TEST_DIR/test5_proc_$i.log" 2>&1 &
  echo "Started process $i (PID: $!)"
done
echo "Waiting for all processes to complete..."
wait
echo -e "${GREEN}All finished${NC}"
pgrep -af mubeng || echo -e "${GREEN}No orphan mubeng processes${NC}"
echo "Output files created:"
ls -lh "$TEST_DIR"/mubeng_out_*.txt 2>/dev/null || echo "No output files"
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 6: Kill Mid-Execution
# ============================================
echo -e "${YELLOW}Test 6: Kill Mubeng Mid-Execution${NC}"
echo "Starting mubeng with 30s timeout..."
"$MUBENG_BIN" --check -f "$TEST_DIR/test_proxies.txt" -o "$TEST_DIR/kill_test.txt" -t 30s > "$TEST_DIR/test6.log" 2>&1 &
MUBENG_PID=$!
echo "Started PID: $MUBENG_PID"
sleep 2
echo "Killing process with SIGKILL..."
kill -9 $MUBENG_PID 2>/dev/null
sleep 1
if pgrep -af mubeng; then
    echo -e "${RED}Orphan mubeng processes found!${NC}"
    pgrep -af mubeng
else
    echo -e "${GREEN}No orphan mubeng processes${NC}"
fi
if [ -f "$TEST_DIR/kill_test.txt" ]; then
    echo "Output file created (partial):"
    ls -lh "$TEST_DIR/kill_test.txt"
    cat "$TEST_DIR/kill_test.txt"
else
    echo "No output file created"
fi
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Test 7: Rotator Mode Start/Stop
# ============================================
echo -e "${YELLOW}Test 7: Mubeng Rotator Mode Start/Stop${NC}"
echo "Starting rotator on localhost:18089..."
"$MUBENG_BIN" -a localhost:18089 -f "$TEST_DIR/test_proxies.txt" -t 5s > "$TEST_DIR/test7.log" 2>&1 &
ROTATOR_PID=$!
echo "Rotator PID: $ROTATOR_PID"
sleep 3

echo "Checking if listening on port 18089..."
if ss -tlnp 2>/dev/null | grep 18089; then
    echo -e "${GREEN}Port 18089 is listening${NC}"
elif netstat -tlnp 2>/dev/null | grep 18089; then
    echo -e "${GREEN}Port 18089 is listening${NC}"
else
    echo -e "${RED}Not listening on port 18089${NC}"
fi

echo "Stopping rotator gracefully (SIGTERM)..."
kill -SIGTERM $ROTATOR_PID 2>/dev/null
sleep 2

# Wait for process to finish
if ps -p $ROTATOR_PID > /dev/null 2>&1; then
    echo -e "${YELLOW}Process still running, forcing kill...${NC}"
    kill -9 $ROTATOR_PID 2>/dev/null
    sleep 1
fi

if pgrep -af mubeng; then
    echo -e "${RED}Orphan processes found!${NC}"
    pgrep -af mubeng
else
    echo -e "${GREEN}No orphan processes${NC}"
fi
echo ""
echo "----------------------------------------"
echo ""

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Test 1 (Normal): Exit code $EXIT_CODE"
echo "Test 2A (Direct): Exit code $DIRECT_EXIT"
echo "Test 2B (Script): Exit code $SCRIPT_EXIT"
echo "Test 3 (Empty): Exit code $EMPTY_EXIT"
echo "Test 4 (Invalid): Exit code $INVALID_EXIT"
echo "Test 5 (Parallel): Multiple processes - check logs"
echo "Test 6 (Kill): Process termination behavior"
echo "Test 7 (Rotator): Start/stop behavior"
echo ""
echo "All logs saved to: $TEST_DIR"
echo "=========================================="

# Check for any remaining orphan processes
if pgrep -af mubeng; then
    echo -e "${RED}WARNING: Orphan mubeng processes detected!${NC}"
    pgrep -af mubeng
    echo "Cleaning up..."
    pkill -9 mubeng
fi
