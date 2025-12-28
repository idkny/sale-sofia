#!/bin/bash
# Start Celery Flower monitoring UI
# Usage: ./scripts/start_flower.sh

set -e

# Get project root (1 level up from this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load settings from Python
FLOWER_PORT=$(python -c "from config.settings import FLOWER_PORT; print(FLOWER_PORT)" 2>/dev/null || echo "5555")
BROKER_API=$(python -c "from config.settings import FLOWER_BROKER_API; print(FLOWER_BROKER_API)" 2>/dev/null || echo "redis://localhost:6379/0")

echo "Starting Celery Flower..."
echo "  Port: $FLOWER_PORT"
echo "  Broker: $BROKER_API"
echo "  UI: http://localhost:$FLOWER_PORT"
echo ""

# Start Flower
exec celery -A celery_app flower \
    --port="$FLOWER_PORT" \
    --broker_api="$BROKER_API"
