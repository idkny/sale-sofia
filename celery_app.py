# celery_app.py - Celery configuration for background tasks
#
# Used for running proxy-scraper-checker and mubeng in the background.
#
# Start Redis: redis-server
# Start Worker: celery -A celery_app worker --loglevel=info

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", "0")
REDIS_RESULT_DB = os.getenv("REDIS_RESULT_DB", "1")

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULT_DB}"

# Create Celery app
celery_app = Celery(
    "sale_sofia",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["proxies.tasks", "scraping.tasks"],  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="Europe/Sofia",
    enable_utc=True,

    # Beat scheduler - store schedule in data/celery/
    beat_schedule_filename="data/celery/celerybeat-schedule",

    # Task settings
    task_track_started=True,
    task_time_limit=1800,  # 30 min max per task (chunks take 2-5 min each)
    task_soft_time_limit=1740,  # Soft limit at 29 min

    # Result settings
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,  # Fair task distribution
    worker_concurrency=8,  # Number of worker processes (handles 16 chunk tasks)
)

# Celery Beat schedule for automatic proxy maintenance
# Ensures we ALWAYS have fresh, validated proxies available
celery_app.conf.beat_schedule = {
    # Scrape + validate proxies every 6 hours using a proper chain
    # The chain ensures check ALWAYS runs after scrape completes
    # REMOVED: Separate check-proxies-every-2h (caused stale data issues)
    "refresh-proxies-every-6h": {
        "task": "proxies.tasks.scrape_and_check_chain_task",
        "schedule": 21600.0,  # Every 6 hours (6 * 60 * 60)
        "options": {"queue": "sale_sofia"},
    },
}

# To start Celery Beat (scheduler), run:
# celery -A celery_app beat --loglevel=info
#
# Or run worker + beat together:
# celery -A celery_app worker --beat --loglevel=info
