#!/bin/bash
# Test 2: PSC ungraceful kill with SIGKILL

echo "=== Test 2: PSC SIGKILL ==="
echo "Starting PSC..."

/home/wow/Projects/sale-sofia/proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker -o /tmp/psc_kill.json &
PSC_PID=$!
echo "PSC PID: $PSC_PID"

sleep 3

echo "Sending SIGKILL..."
kill -9 $PSC_PID

sleep 2

pgrep -af proxy-scraper || echo "No orphan PSC processes - PASS"
