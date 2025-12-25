#!/bin/bash
# Test 1: PSC graceful shutdown with SIGTERM

echo "=== Test 1: PSC SIGTERM ==="
echo "Starting PSC..."

/home/wow/Projects/sale-sofia/proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker -o /tmp/psc_test.json &
PSC_PID=$!
echo "PSC PID: $PSC_PID"

sleep 5

echo "Sending SIGTERM..."
kill -SIGTERM $PSC_PID
wait $PSC_PID 2>/dev/null
echo "Exit code: $?"

sleep 2

pgrep -af proxy-scraper || echo "No orphan PSC processes - PASS"
