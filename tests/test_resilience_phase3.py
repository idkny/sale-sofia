"""Unit tests for resilience Phase 3 - Checkpoint Manager.

Tests checkpoint save/load/clear functionality and recovery scenarios.
"""

import json
import time
import pytest
from pathlib import Path

from resilience.checkpoint import CheckpointManager


# =============================================================================
# Checkpoint Manager Tests
# =============================================================================


class TestCheckpointManager:
    """Test core CheckpointManager functionality."""

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates checkpoint directory."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        assert checkpoint_dir.exists()
        assert checkpoint_dir.is_dir()

    def test_save_batched_skips_before_batch_size(self, tmp_path):
        """Test that batched saves skip writes before batch_size."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)
        manager.batch_size = 5

        scraped = {"url1", "url2"}
        pending = ["url3", "url4"]

        # Save 4 times - should not write (batch_size is 5)
        for _ in range(4):
            manager.save(scraped, pending)

        assert not manager.file.exists()

    def test_save_batched_writes_at_batch_size(self, tmp_path):
        """Test that batched saves write at batch_size."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)
        manager.batch_size = 5

        scraped = {"url1", "url2"}
        pending = ["url3", "url4"]

        # Save 5 times - should write on 5th call
        for _ in range(5):
            manager.save(scraped, pending)

        assert manager.file.exists()

        # Verify content
        with open(manager.file) as f:
            data = json.load(f)

        assert set(data["scraped"]) == scraped
        assert data["pending"] == pending

    def test_save_force_writes_immediately(self, tmp_path):
        """Test that force=True bypasses batching."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)
        manager.batch_size = 100

        scraped = {"url1", "url2"}
        pending = ["url3"]

        # Single save with force=True should write immediately
        manager.save(scraped, pending, force=True)

        assert manager.file.exists()

        # Verify content
        with open(manager.file) as f:
            data = json.load(f)

        assert set(data["scraped"]) == scraped
        assert data["pending"] == pending

    def test_load_returns_none_if_no_checkpoint(self, tmp_path):
        """Test that load returns None when no checkpoint exists."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        result = manager.load()

        assert result is None

    def test_load_returns_data_if_checkpoint_exists(self, tmp_path):
        """Test that load returns data when checkpoint exists."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        scraped = {"url1", "url2", "url3"}
        pending = ["url4", "url5"]

        # Save checkpoint
        manager.save(scraped, pending, force=True)

        # Load checkpoint
        loaded = manager.load()

        assert loaded is not None
        assert set(loaded["scraped"]) == scraped
        assert loaded["pending"] == pending
        assert "timestamp" in loaded
        assert loaded["name"] == "test_session"

    def test_load_handles_corrupted_json(self, tmp_path):
        """Test that load handles corrupted JSON gracefully."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        # Write corrupted JSON to file
        with open(manager.file, "w") as f:
            f.write("{ invalid json content }}")

        result = manager.load()

        assert result is None

    def test_clear_removes_checkpoint_file(self, tmp_path):
        """Test that clear removes checkpoint file."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        scraped = {"url1"}
        pending = ["url2"]

        # Create checkpoint
        manager.save(scraped, pending, force=True)
        assert manager.file.exists()

        # Clear checkpoint
        manager.clear()

        assert not manager.file.exists()

    def test_clear_handles_missing_file(self, tmp_path):
        """Test that clear handles missing file gracefully."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        # Clear non-existent file should not raise error
        manager.clear()

        assert not manager.file.exists()

    def test_checkpoint_data_format(self, tmp_path):
        """Test that checkpoint data has correct JSON structure."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("test_session", checkpoint_dir=checkpoint_dir)

        scraped = {"url1", "url2"}
        pending = ["url3", "url4", "url5"]

        before_time = time.time()
        manager.save(scraped, pending, force=True)
        after_time = time.time()

        # Load and verify structure
        with open(manager.file) as f:
            data = json.load(f)

        assert "scraped" in data
        assert "pending" in data
        assert "timestamp" in data
        assert "name" in data

        # Verify types
        assert isinstance(data["scraped"], list)
        assert isinstance(data["pending"], list)
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["name"], str)

        # Verify values
        assert set(data["scraped"]) == scraped
        assert data["pending"] == pending
        assert before_time <= data["timestamp"] <= after_time
        assert data["name"] == "test_session"


# =============================================================================
# Checkpoint Recovery Tests
# =============================================================================


class TestCheckpointRecovery:
    """Test checkpoint recovery scenarios."""

    def test_resume_from_checkpoint(self, tmp_path):
        """Test resuming scraping from checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        session_name = "recovery_test"

        # Simulate first session
        manager1 = CheckpointManager(session_name, checkpoint_dir=checkpoint_dir)
        scraped = {"url1", "url2", "url3"}
        pending = ["url4", "url5", "url6"]
        manager1.save(scraped, pending, force=True)

        # Simulate recovery session
        manager2 = CheckpointManager(session_name, checkpoint_dir=checkpoint_dir)
        state = manager2.load()

        assert state is not None
        assert set(state["scraped"]) == scraped
        assert state["pending"] == pending
        assert state["name"] == session_name

    def test_checkpoint_updated_after_progress(self, tmp_path):
        """Test that checkpoint updates as scraping progresses."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("progress_test", checkpoint_dir=checkpoint_dir)

        # Initial state
        scraped = {"url1"}
        pending = ["url2", "url3", "url4"]
        manager.save(scraped, pending, force=True)

        # Simulate progress
        scraped.add("url2")
        pending.remove("url2")
        manager.save(scraped, pending, force=True)

        # Load and verify
        state = manager.load()

        assert set(state["scraped"]) == {"url1", "url2"}
        assert "url2" not in state["pending"]
        assert set(state["pending"]) == {"url3", "url4"}

    def test_multiple_sessions_same_name(self, tmp_path):
        """Test that multiple sessions with same name overwrite checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        session_name = "same_name"

        # First session
        manager1 = CheckpointManager(session_name, checkpoint_dir=checkpoint_dir)
        manager1.save({"url1"}, ["url2"], force=True)

        # Second session with same name
        manager2 = CheckpointManager(session_name, checkpoint_dir=checkpoint_dir)
        manager2.save({"url3"}, ["url4"], force=True)

        # Load should return second session data
        state = manager2.load()

        assert set(state["scraped"]) == {"url3"}
        assert state["pending"] == ["url4"]


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestCheckpointEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_scraped_set(self, tmp_path):
        """Test checkpoint with empty scraped set."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("empty_scraped", checkpoint_dir=checkpoint_dir)

        scraped = set()
        pending = ["url1", "url2"]

        manager.save(scraped, pending, force=True)
        state = manager.load()

        assert state is not None
        assert state["scraped"] == []
        assert state["pending"] == pending

    def test_empty_pending_list(self, tmp_path):
        """Test checkpoint with empty pending list."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("empty_pending", checkpoint_dir=checkpoint_dir)

        scraped = {"url1", "url2"}
        pending = []

        manager.save(scraped, pending, force=True)
        state = manager.load()

        assert state is not None
        assert set(state["scraped"]) == scraped
        assert state["pending"] == []

    def test_large_url_list(self, tmp_path):
        """Test checkpoint with large number of URLs (1000+)."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("large_list", checkpoint_dir=checkpoint_dir)

        # Generate 1000 URLs
        scraped = {f"https://example.com/scraped/{i}" for i in range(500)}
        pending = [f"https://example.com/pending/{i}" for i in range(500)]

        manager.save(scraped, pending, force=True)
        state = manager.load()

        assert state is not None
        assert len(state["scraped"]) == 500
        assert len(state["pending"]) == 500
        assert set(state["scraped"]) == scraped
        assert set(state["pending"]) == set(pending)

    def test_special_characters_in_urls(self, tmp_path):
        """Test checkpoint with URLs containing special characters."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("special_chars", checkpoint_dir=checkpoint_dir)

        scraped = {
            "https://example.com/page?id=123&name=test",
            "https://example.com/path/with spaces/page",
            "https://example.com/unicode/кирилица",
        }
        pending = [
            "https://example.com/query?param=value&other=123",
            "https://example.com/fragment#section",
        ]

        manager.save(scraped, pending, force=True)
        state = manager.load()

        assert state is not None
        assert set(state["scraped"]) == scraped
        assert set(state["pending"]) == set(pending)

    def test_unicode_in_checkpoint_name(self, tmp_path):
        """Test checkpoint with unicode characters in name."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager("session_кирилица", checkpoint_dir=checkpoint_dir)

        scraped = {"url1"}
        pending = ["url2"]

        manager.save(scraped, pending, force=True)
        state = manager.load()

        assert state is not None
        assert state["name"] == "session_кирилица"
        assert manager.file.name == "session_кирилица_checkpoint.json"
