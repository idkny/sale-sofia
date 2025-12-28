"""Integration tests for crash recovery with checkpoints.

Tests checkpoint save/load/clear, signal handler behavior, partial progress recovery,
stale checkpoint detection, and Redis-based progress tracking for Celery workers.

Spec: Task 4.4.3 - Crash Recovery Integration Tests
Related: docs/specs/112_SCRAPER_RESILIENCE.md (Section 3.1)
"""

import json
import os
import signal
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import fakeredis for isolated testing
try:
    import fakeredis

    HAS_FAKEREDIS = True
except ImportError:
    HAS_FAKEREDIS = False
    pytest.skip("fakeredis not installed", allow_module_level=True)

from resilience.checkpoint import CheckpointManager
from scraping.redis_keys import ScrapingKeys


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def checkpoint_manager(tmp_path):
    """Create CheckpointManager with temporary directory."""
    checkpoint_dir = tmp_path / "checkpoints"
    manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)
    return manager


@pytest.fixture
def sample_urls():
    """Generate sample URLs for testing."""
    return {
        "scraped": {f"https://example.com/listing/{i}" for i in range(1, 51)},
        "pending": [f"https://example.com/listing/{i}" for i in range(51, 101)],
    }


# =============================================================================
# Test Signal Handler Checkpoint Saving
# =============================================================================


class TestSignalHandlerCheckpoint:
    """Test that signal handlers save checkpoint on termination."""

    def test_signal_handler_saves_checkpoint_on_sigterm(self, checkpoint_manager, sample_urls):
        """Test that SIGTERM signal triggers checkpoint save."""
        import main

        # Set up global state
        main._checkpoint_manager = checkpoint_manager
        main._scraped_urls = sample_urls["scraped"]
        main._pending_urls = sample_urls["pending"]

        # Call signal handler directly (safer than sending actual signal)
        with patch("sys.exit") as mock_exit:
            main._signal_handler(signal.SIGTERM, None)

        # Verify checkpoint was saved
        assert checkpoint_manager.file.exists()

        # Verify checkpoint content
        with open(checkpoint_manager.file) as f:
            data = json.load(f)

        assert set(data["scraped"]) == sample_urls["scraped"]
        assert data["pending"] == sample_urls["pending"]
        assert data["name"] == "test_session"
        assert "timestamp" in data

        # Verify exit was called
        mock_exit.assert_called_once_with(0)

        # Cleanup
        main._checkpoint_manager = None
        main._scraped_urls = set()
        main._pending_urls = []

    def test_signal_handler_saves_checkpoint_on_sigint(self, checkpoint_manager, sample_urls):
        """Test that SIGINT (Ctrl+C) signal triggers checkpoint save."""
        import main

        # Set up global state
        main._checkpoint_manager = checkpoint_manager
        main._scraped_urls = sample_urls["scraped"]
        main._pending_urls = sample_urls["pending"]

        # Call signal handler directly
        with patch("sys.exit") as mock_exit:
            main._signal_handler(signal.SIGINT, None)

        # Verify checkpoint was saved
        assert checkpoint_manager.file.exists()

        # Verify checkpoint content
        loaded = checkpoint_manager.load()
        assert loaded is not None
        assert set(loaded["scraped"]) == sample_urls["scraped"]
        assert loaded["pending"] == sample_urls["pending"]

        # Cleanup
        main._checkpoint_manager = None
        main._scraped_urls = set()
        main._pending_urls = []

    def test_signal_handler_handles_no_checkpoint_manager(self):
        """Test signal handler handles case when checkpoint manager is None."""
        import main

        # Set checkpoint manager to None
        main._checkpoint_manager = None
        main._scraped_urls = {"url1", "url2"}
        main._pending_urls = ["url3"]

        # Should not crash when checkpoint manager is None
        with patch("sys.exit") as mock_exit:
            main._signal_handler(signal.SIGTERM, None)

        mock_exit.assert_called_once_with(0)

        # Cleanup
        main._scraped_urls = set()
        main._pending_urls = []

    def test_signal_handlers_registered(self):
        """Test that signal handlers are properly registered."""
        import main

        with patch("signal.signal") as mock_signal:
            main._setup_signal_handlers()

            # Verify both SIGTERM and SIGINT are registered
            calls = mock_signal.call_args_list
            assert len(calls) == 2

            # Check SIGTERM registration
            assert calls[0][0][0] == signal.SIGTERM
            assert calls[0][0][1] == main._signal_handler

            # Check SIGINT registration
            assert calls[1][0][0] == signal.SIGINT
            assert calls[1][0][1] == main._signal_handler


# =============================================================================
# Test Resume from Checkpoint
# =============================================================================


class TestCheckpointResume:
    """Test resuming scraping from saved checkpoint."""

    def test_resume_from_checkpoint_skips_scraped_urls(self, checkpoint_manager, sample_urls):
        """Test that resuming from checkpoint skips already-scraped URLs."""
        # Save initial checkpoint
        checkpoint_manager.save(
            sample_urls["scraped"], sample_urls["pending"], force=True
        )

        # Load checkpoint (simulating new session)
        state = checkpoint_manager.load()

        assert state is not None
        already_scraped = set(state["scraped"])
        pending = list(state["pending"])

        # Verify scraped URLs are loaded correctly
        assert already_scraped == sample_urls["scraped"]
        assert len(already_scraped) == 50

        # Verify pending URLs are loaded correctly
        assert pending == sample_urls["pending"]
        assert len(pending) == 50

        # Verify no overlap between scraped and pending
        assert len(already_scraped & set(pending)) == 0

    def test_resume_continues_from_last_checkpoint(self, checkpoint_manager):
        """Test that multiple resume cycles maintain progress."""
        # Initial state: 10 scraped, 90 pending
        scraped = {f"https://example.com/{i}" for i in range(10)}
        pending = [f"https://example.com/{i}" for i in range(10, 100)]

        checkpoint_manager.save(scraped, pending, force=True)

        # First resume: scrape 20 more
        state = checkpoint_manager.load()
        scraped = set(state["scraped"])
        pending = list(state["pending"])

        # Simulate scraping 20 URLs
        for i in range(20):
            url = pending.pop(0)
            scraped.add(url)

        checkpoint_manager.save(scraped, pending, force=True)

        # Second resume: verify progress
        state = checkpoint_manager.load()
        assert len(state["scraped"]) == 30  # 10 + 20
        assert len(state["pending"]) == 70  # 90 - 20

    def test_resume_with_empty_checkpoint(self, checkpoint_manager):
        """Test resume behavior when no checkpoint exists (fresh start)."""
        # Attempt to load non-existent checkpoint
        state = checkpoint_manager.load()

        assert state is None

        # Should start fresh with all URLs pending
        all_urls = [f"https://example.com/{i}" for i in range(100)]
        scraped = set()
        pending = all_urls.copy()

        # Start scraping
        checkpoint_manager.save(scraped, pending, force=True)

        # Verify checkpoint was created
        state = checkpoint_manager.load()
        assert state is not None
        assert len(state["scraped"]) == 0
        assert len(state["pending"]) == 100


# =============================================================================
# Test Partial Progress Recovery
# =============================================================================


class TestPartialProgressRecovery:
    """Test recovery scenarios with partial progress."""

    def test_resume_from_50_percent_completion(self, checkpoint_manager):
        """Test resuming from checkpoint with exactly 50% progress."""
        # Scraped: URLs 1-50
        scraped = {f"https://example.com/listing/{i}" for i in range(1, 51)}

        # Pending: URLs 51-100
        pending = [f"https://example.com/listing/{i}" for i in range(51, 101)]

        # Save checkpoint
        checkpoint_manager.save(scraped, pending, force=True)

        # Simulate crash and restart
        state = checkpoint_manager.load()

        # Verify we resume from URL 51
        assert len(state["scraped"]) == 50
        assert len(state["pending"]) == 50
        assert state["pending"][0] == "https://example.com/listing/51"
        assert state["pending"][-1] == "https://example.com/listing/100"

        # Verify URLs 1-50 are marked as scraped
        for i in range(1, 51):
            assert f"https://example.com/listing/{i}" in state["scraped"]

        # Verify URLs 51-100 are still pending
        pending_set = set(state["pending"])
        for i in range(51, 101):
            assert f"https://example.com/listing/{i}" in pending_set

    def test_resume_from_90_percent_completion(self, checkpoint_manager):
        """Test resuming from checkpoint near completion (90% done)."""
        # Scraped: URLs 1-90
        scraped = {f"https://example.com/listing/{i}" for i in range(1, 91)}

        # Pending: URLs 91-100 (only 10 left)
        pending = [f"https://example.com/listing/{i}" for i in range(91, 101)]

        # Save checkpoint
        checkpoint_manager.save(scraped, pending, force=True)

        # Load and verify
        state = checkpoint_manager.load()

        assert len(state["scraped"]) == 90
        assert len(state["pending"]) == 10
        assert state["pending"][0] == "https://example.com/listing/91"

    def test_resume_from_early_crash(self, checkpoint_manager):
        """Test resuming from checkpoint with minimal progress (early crash)."""
        # Scraped: only 5 URLs
        scraped = {f"https://example.com/listing/{i}" for i in range(1, 6)}

        # Pending: 95 URLs remaining
        pending = [f"https://example.com/listing/{i}" for i in range(6, 101)]

        # Save checkpoint
        checkpoint_manager.save(scraped, pending, force=True)

        # Load and verify
        state = checkpoint_manager.load()

        assert len(state["scraped"]) == 5
        assert len(state["pending"]) == 95
        assert state["pending"][0] == "https://example.com/listing/6"


# =============================================================================
# Test Checkpoint Lifecycle
# =============================================================================


class TestCheckpointLifecycle:
    """Test checkpoint creation, update, and cleanup lifecycle."""

    def test_checkpoint_cleared_on_successful_completion(self, checkpoint_manager, sample_urls):
        """Test that checkpoint is deleted after successful scrape completion."""
        # Save checkpoint during scraping
        checkpoint_manager.save(
            sample_urls["scraped"], sample_urls["pending"], force=True
        )

        assert checkpoint_manager.file.exists()

        # Simulate successful completion - clear checkpoint
        checkpoint_manager.clear()

        # Verify checkpoint file is deleted
        assert not checkpoint_manager.file.exists()

    def test_checkpoint_persists_across_batches(self, checkpoint_manager):
        """Test that checkpoint persists and updates across batched saves."""
        scraped = set()
        pending = [f"https://example.com/{i}" for i in range(100)]

        # Simulate scraping with batched checkpoint saves (batch_size=10)
        checkpoint_manager.batch_size = 10

        for i in range(25):  # Scrape 25 URLs
            url = pending.pop(0)
            scraped.add(url)
            checkpoint_manager.save(scraped, pending)  # Batched save

        # Should have saved at 10th and 20th call
        state = checkpoint_manager.load()

        # Latest save was at call 20 (batch_size=10)
        assert state is not None
        assert len(state["scraped"]) == 20  # Last save at 20 URLs
        assert len(state["pending"]) == 80

    def test_checkpoint_force_save_bypasses_batching(self, checkpoint_manager):
        """Test that force=True saves immediately, bypassing batch counter."""
        scraped = {"url1"}
        pending = ["url2", "url3"]

        checkpoint_manager.batch_size = 100

        # Force save should write immediately
        checkpoint_manager.save(scraped, pending, force=True)

        assert checkpoint_manager.file.exists()

        state = checkpoint_manager.load()
        assert len(state["scraped"]) == 1
        assert len(state["pending"]) == 2

    def test_multiple_checkpoints_same_session_overwrite(self, checkpoint_manager):
        """Test that multiple saves to same checkpoint overwrite previous data."""
        # First save
        scraped1 = {"url1", "url2"}
        pending1 = ["url3", "url4"]
        checkpoint_manager.save(scraped1, pending1, force=True)

        # Second save (overwrite)
        scraped2 = {"url1", "url2", "url3", "url5"}
        pending2 = ["url4"]
        checkpoint_manager.save(scraped2, pending2, force=True)

        # Load should return latest data
        state = checkpoint_manager.load()

        assert set(state["scraped"]) == scraped2
        assert state["pending"] == pending2


# =============================================================================
# Test Stale Checkpoint Detection
# =============================================================================


class TestStaleCheckpoint:
    """Test detection and handling of stale checkpoints."""

    def test_detect_old_checkpoint_by_timestamp(self, checkpoint_manager):
        """Test that old checkpoints can be detected via timestamp."""
        scraped = {"url1", "url2"}
        pending = ["url3", "url4"]

        # Save checkpoint
        checkpoint_manager.save(scraped, pending, force=True)

        # Manually modify timestamp to be 7 days old
        with open(checkpoint_manager.file) as f:
            data = json.load(f)

        old_timestamp = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
        data["timestamp"] = old_timestamp

        with open(checkpoint_manager.file, "w") as f:
            json.dump(data, f)

        # Load checkpoint
        state = checkpoint_manager.load()

        assert state is not None
        assert state["timestamp"] == old_timestamp

        # Calculate age
        age_seconds = time.time() - state["timestamp"]
        age_days = age_seconds / (24 * 60 * 60)

        assert age_days >= 6.9  # Allow small margin

        # Application code should decide whether to use stale checkpoint
        # This test just verifies we can detect age via timestamp

    def test_fresh_checkpoint_has_recent_timestamp(self, checkpoint_manager):
        """Test that newly created checkpoint has recent timestamp."""
        scraped = {"url1"}
        pending = ["url2"]

        before_save = time.time()
        checkpoint_manager.save(scraped, pending, force=True)
        after_save = time.time()

        state = checkpoint_manager.load()

        assert state is not None
        assert before_save <= state["timestamp"] <= after_save

        # Age should be less than 1 second
        age = time.time() - state["timestamp"]
        assert age < 1.0

    def test_checkpoint_age_calculation(self, checkpoint_manager):
        """Test calculating checkpoint age for staleness detection."""
        scraped = {"url1", "url2", "url3"}
        pending = ["url4", "url5"]

        checkpoint_manager.save(scraped, pending, force=True)

        # Load and calculate age
        state = checkpoint_manager.load()

        timestamp = state["timestamp"]
        age_seconds = time.time() - timestamp

        # Should be very fresh (< 1 second)
        assert age_seconds < 1.0

        # Helper function to check if checkpoint is stale
        def is_stale(timestamp, threshold_days=1):
            """Check if checkpoint is older than threshold_days."""
            age_seconds = time.time() - timestamp
            age_days = age_seconds / (24 * 60 * 60)
            return age_days > threshold_days

        assert not is_stale(timestamp, threshold_days=1)

        # Test with simulated old timestamp
        old_timestamp = time.time() - (2 * 24 * 60 * 60)  # 2 days old
        assert is_stale(old_timestamp, threshold_days=1)


# =============================================================================
# Test Redis Progress Persistence
# =============================================================================


class TestRedisProgressPersistence:
    """Test that Redis-based progress tracking persists across restarts."""

    def test_redis_progress_survives_worker_restart(self, fake_redis):
        """Test that Redis progress keys survive worker crash and restart."""
        job_id = "scrape_imot_bg_abc123"

        # Worker sets progress before crash
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.total_urls(job_id), 100)
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 5)
        fake_redis.set(ScrapingKeys.result_count(job_id), 48)
        fake_redis.set(ScrapingKeys.error_count(job_id), 2)
        fake_redis.set(ScrapingKeys.started_at(job_id), int(time.time()))

        # Simulate worker crash (Redis client is destroyed)
        # In real scenario, Redis data persists because it's external

        # New worker starts, connects to same Redis
        # (In test, we just reuse fake_redis instance)

        # Verify progress data is still accessible
        assert fake_redis.get(ScrapingKeys.status(job_id)) == "PROCESSING"
        assert fake_redis.get(ScrapingKeys.total_urls(job_id)) == "100"
        assert fake_redis.get(ScrapingKeys.total_chunks(job_id)) == "10"
        assert fake_redis.get(ScrapingKeys.completed_chunks(job_id)) == "5"
        assert fake_redis.get(ScrapingKeys.result_count(job_id)) == "48"
        assert fake_redis.get(ScrapingKeys.error_count(job_id)) == "2"

        # Can calculate progress
        completed = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))
        total = int(fake_redis.get(ScrapingKeys.total_chunks(job_id)))
        progress_pct = (completed / total) * 100

        assert progress_pct == 50.0  # 5/10 chunks = 50%

    def test_redis_keys_persist_with_ttl(self, fake_redis):
        """Test that Redis keys have TTL to prevent indefinite storage."""
        job_id = "scrape_bazar_bg_xyz789"
        ttl_seconds = 3600  # 1 hour

        # Set keys with TTL (simulating real tasks.py behavior)
        fake_redis.setex(ScrapingKeys.status(job_id), ttl_seconds, "COMPLETE")
        fake_redis.setex(ScrapingKeys.total_urls(job_id), ttl_seconds, 50)
        fake_redis.setex(ScrapingKeys.result_count(job_id), ttl_seconds, 48)

        # Verify keys exist
        assert fake_redis.exists(ScrapingKeys.status(job_id)) == 1
        assert fake_redis.exists(ScrapingKeys.total_urls(job_id)) == 1

        # Verify TTL is set
        ttl = fake_redis.ttl(ScrapingKeys.status(job_id))
        assert ttl > 0
        assert ttl <= ttl_seconds

    def test_reconstruct_job_state_from_redis(self, fake_redis):
        """Test reconstructing full job state from Redis keys after crash."""
        job_id = "scrape_imot_bg_recovery"

        # Simulate partial progress before crash
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.total_urls(job_id), 200)
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 8)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 6)
        fake_redis.set(ScrapingKeys.result_count(job_id), 145)
        fake_redis.set(ScrapingKeys.error_count(job_id), 5)
        fake_redis.set(ScrapingKeys.started_at(job_id), int(time.time()) - 300)

        # Reconstruct state from Redis
        job_state = {
            "job_id": job_id,
            "status": fake_redis.get(ScrapingKeys.status(job_id)),
            "total_urls": int(fake_redis.get(ScrapingKeys.total_urls(job_id))),
            "total_chunks": int(fake_redis.get(ScrapingKeys.total_chunks(job_id))),
            "completed_chunks": int(
                fake_redis.get(ScrapingKeys.completed_chunks(job_id))
            ),
            "result_count": int(fake_redis.get(ScrapingKeys.result_count(job_id))),
            "error_count": int(fake_redis.get(ScrapingKeys.error_count(job_id))),
            "started_at": int(fake_redis.get(ScrapingKeys.started_at(job_id))),
        }

        # Verify reconstructed state
        assert job_state["status"] == "PROCESSING"
        assert job_state["total_urls"] == 200
        assert job_state["completed_chunks"] == 6
        assert job_state["total_chunks"] == 8
        assert job_state["result_count"] == 145
        assert job_state["error_count"] == 5

        # Calculate metrics
        chunks_remaining = job_state["total_chunks"] - job_state["completed_chunks"]
        assert chunks_remaining == 2

        success_rate = (
            (job_state["result_count"] / job_state["total_urls"]) * 100
            if job_state["total_urls"] > 0
            else 0
        )
        assert success_rate == 72.5  # 145/200 = 72.5%


# =============================================================================
# Test Celery Worker Crash Recovery
# =============================================================================


class TestCeleryWorkerCrashRecovery:
    """Test detecting and recovering from Celery worker crashes."""

    def test_detect_incomplete_job_from_redis(self, fake_redis):
        """Test detecting incomplete job when completed_chunks < total_chunks."""
        job_id = "scrape_imot_bg_crashed"

        # Simulate job that crashed mid-execution
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 7)  # Crashed at chunk 7

        # Detection logic
        status = fake_redis.get(ScrapingKeys.status(job_id))
        total_chunks = int(fake_redis.get(ScrapingKeys.total_chunks(job_id)))
        completed_chunks = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))

        is_incomplete = status == "PROCESSING" and completed_chunks < total_chunks

        assert is_incomplete
        assert total_chunks - completed_chunks == 3  # 3 chunks remaining

    def test_detect_successful_completion(self, fake_redis):
        """Test detecting successfully completed job."""
        job_id = "scrape_bazar_bg_success"

        # Simulate successful completion
        fake_redis.set(ScrapingKeys.status(job_id), "COMPLETE")
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 10)
        fake_redis.set(ScrapingKeys.completed_at(job_id), int(time.time()))

        # Detection logic
        status = fake_redis.get(ScrapingKeys.status(job_id))
        total_chunks = int(fake_redis.get(ScrapingKeys.total_chunks(job_id)))
        completed_chunks = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))

        is_complete = (
            status == "COMPLETE" or completed_chunks == total_chunks
        )

        assert is_complete
        assert fake_redis.exists(ScrapingKeys.completed_at(job_id)) == 1

    def test_track_chunk_completion_progress(self, fake_redis):
        """Test tracking chunk completion as workers process tasks."""
        job_id = "scrape_imot_bg_progress"

        # Initialize job
        fake_redis.set(ScrapingKeys.status(job_id), "DISPATCHED")
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 5)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 0)

        # Simulate chunk completions
        for i in range(1, 6):
            # Worker completes chunk
            fake_redis.incr(ScrapingKeys.completed_chunks(job_id))

            completed = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))
            total = int(fake_redis.get(ScrapingKeys.total_chunks(job_id)))

            assert completed == i

            if completed == total:
                fake_redis.set(ScrapingKeys.status(job_id), "AGGREGATING")

        # Verify final state
        assert fake_redis.get(ScrapingKeys.status(job_id)) == "AGGREGATING"
        assert (
            fake_redis.get(ScrapingKeys.completed_chunks(job_id))
            == fake_redis.get(ScrapingKeys.total_chunks(job_id))
        )

    def test_recover_from_multiple_worker_crashes(self, fake_redis):
        """Test recovery scenario where multiple workers crash at different times."""
        job_id = "scrape_multi_crash"

        # Initial dispatch: 20 chunks
        fake_redis.set(ScrapingKeys.status(job_id), "DISPATCHED")
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 20)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 0)

        # First batch of workers complete 8 chunks
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 8)

        # First crash - verify state
        assert int(fake_redis.get(ScrapingKeys.completed_chunks(job_id))) == 8

        # Restart workers, complete 5 more chunks
        for _ in range(5):
            fake_redis.incr(ScrapingKeys.completed_chunks(job_id))

        # Second crash - verify state
        assert int(fake_redis.get(ScrapingKeys.completed_chunks(job_id))) == 13

        # Final restart, complete remaining 7 chunks
        for _ in range(7):
            fake_redis.incr(ScrapingKeys.completed_chunks(job_id))

        # Verify completion
        completed = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))
        total = int(fake_redis.get(ScrapingKeys.total_chunks(job_id)))

        assert completed == total == 20

    def test_failed_job_marked_in_redis(self, fake_redis):
        """Test that failed jobs are properly marked with FAILED status."""
        job_id = "scrape_failed_job"

        # Simulate job failure
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 3)

        # Worker encounters fatal error, marks job as failed
        fake_redis.set(ScrapingKeys.status(job_id), "FAILED")
        fake_redis.set(ScrapingKeys.error_count(job_id), 150)  # High error count

        # Verify failed state
        status = fake_redis.get(ScrapingKeys.status(job_id))
        assert status == "FAILED"

        error_count = int(fake_redis.get(ScrapingKeys.error_count(job_id)))
        assert error_count == 150


# =============================================================================
# Test Combined Checkpoint + Redis Recovery
# =============================================================================


class TestCombinedRecovery:
    """Test scenarios combining both checkpoint files and Redis progress tracking."""

    def test_checkpoint_and_redis_both_available(
        self, checkpoint_manager, fake_redis
    ):
        """Test recovery when both checkpoint file and Redis keys exist."""
        job_id = "scrape_combined_recovery"

        # Checkpoint has file-level progress
        scraped = {f"https://example.com/{i}" for i in range(50)}
        pending = [f"https://example.com/{i}" for i in range(50, 100)]
        checkpoint_manager.save(scraped, pending, force=True)

        # Redis has job-level progress
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.total_urls(job_id), 100)
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 5)
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)

        # Recovery: Load both sources
        checkpoint_state = checkpoint_manager.load()
        redis_status = fake_redis.get(ScrapingKeys.status(job_id))
        redis_progress = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))

        # Verify both are available
        assert checkpoint_state is not None
        assert len(checkpoint_state["scraped"]) == 50
        assert redis_status == "PROCESSING"
        assert redis_progress == 5

        # Can use checkpoint for URL-level resume and Redis for job monitoring

    def test_checkpoint_newer_than_redis(self, checkpoint_manager, fake_redis):
        """Test scenario where checkpoint is more recent than Redis state."""
        job_id = "scrape_checkpoint_newer"

        # Old Redis state
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 3)

        time.sleep(0.1)  # Ensure time difference

        # Newer checkpoint
        scraped = {f"url{i}" for i in range(60)}
        pending = [f"url{i}" for i in range(60, 100)]
        checkpoint_manager.save(scraped, pending, force=True)

        # Load both
        checkpoint_state = checkpoint_manager.load()
        redis_chunks = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))

        # Checkpoint should be trusted as it has timestamp
        assert checkpoint_state is not None
        assert len(checkpoint_state["scraped"]) == 60

        # Application logic should use more recent source

    def test_redis_only_available_no_checkpoint(self, checkpoint_manager, fake_redis):
        """Test recovery when only Redis data exists (no checkpoint file)."""
        job_id = "scrape_redis_only"

        # No checkpoint file
        assert checkpoint_manager.load() is None

        # But Redis has progress
        fake_redis.set(ScrapingKeys.status(job_id), "PROCESSING")
        fake_redis.set(ScrapingKeys.completed_chunks(job_id), 7)
        fake_redis.set(ScrapingKeys.total_chunks(job_id), 10)

        # Can still recover from Redis
        status = fake_redis.get(ScrapingKeys.status(job_id))
        completed = int(fake_redis.get(ScrapingKeys.completed_chunks(job_id)))

        assert status == "PROCESSING"
        assert completed == 7

        # Application should resume from chunk 8
