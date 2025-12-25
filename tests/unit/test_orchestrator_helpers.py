#!/usr/bin/env python3
"""
Unit tests for orchestrator.py helper functions.

Tests the refactored wait_for_refresh_completion helper functions:
- _wait_for_chain_dispatch
- _parse_dispatch_result
- _wait_via_chord
- _start_progress_thread
- _stop_progress_thread
- _handle_chord_error
- _wait_via_redis_polling
- _wait_via_file_monitoring

Also tests phase transitions in wait_for_refresh_completion.
"""

import os
import sys

# Add project root to path
PROJECT_DIR = "/home/wow/Projects/sale-sofia"
sys.path.insert(0, PROJECT_DIR)

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import dataclass
from typing import Optional


# Import the DispatchResult class structure
@dataclass
class DispatchResult:
    """Result from waiting for chain dispatch to complete."""
    job_id: Optional[str] = None
    chord_id: Optional[str] = None
    total_chunks: int = 0
    success: bool = True
    error: Optional[str] = None


@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator instance with common dependencies mocked."""
    with patch('orchestrator.Orchestrator') as MockOrch:
        orch = MockOrch.return_value
        # Mock common methods
        orch.restart_celery_if_dead = Mock(return_value=True)
        orch.get_task_state = Mock(return_value=("SUCCESS", {"job_id": "test-job"}))
        orch.get_refresh_progress = Mock(return_value={
            "status": "COMPLETE",
            "completed_chunks": 10,
            "total_chunks": 10,
            "progress_pct": 100.0
        })
        orch.get_usable_proxy_count = Mock(return_value=50)
        orch.get_proxy_file_mtime = Mock(return_value=1000.0)
        orch.is_celery_alive = Mock(return_value=True)
        return orch


class TestWaitForChainDispatch:
    """Tests for _wait_for_chain_dispatch helper."""

    def test_no_task_id_returns_empty_result(self):
        """When task_id is None, should return empty DispatchResult immediately."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        with patch.object(orch, 'restart_celery_if_dead'):
            result = orch._wait_for_chain_dispatch(None, time.time(), 15)

            assert result.job_id is None
            assert result.chord_id is None
            assert result.success is True

    def test_task_success_returns_parsed_result(self):
        """When task completes successfully, should parse and return result."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = {"job_id": "job-123", "chord_id": "chord-456", "total_chunks": 5}

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_task_state', return_value=("SUCCESS", task_result)), \
             patch.object(orch, '_parse_dispatch_result') as mock_parse:

            mock_parse.return_value = DispatchResult(
                job_id="job-123",
                chord_id="chord-456",
                total_chunks=5
            )

            result = orch._wait_for_chain_dispatch("task-id", time.time(), 15)

            assert result.job_id == "job-123"
            assert result.chord_id == "chord-456"
            assert result.total_chunks == 5
            mock_parse.assert_called_once_with(task_result)

    def test_task_failure_returns_error_result(self):
        """When task fails, should return DispatchResult with success=False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_task_state', return_value=("FAILURE", "Task error")):

            result = orch._wait_for_chain_dispatch("task-id", time.time(), 15)

            assert result.success is False
            assert result.error == "Task error"

    def test_celery_dead_returns_error_result(self):
        """When Celery can't be restarted, should return error result."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=False):
            result = orch._wait_for_chain_dispatch("task-id", time.time(), 15)

            assert result.success is False
            assert "Celery failed to restart" in result.error


class TestParseDispatchResult:
    """Tests for _parse_dispatch_result helper."""

    def test_dict_with_job_id_and_chord_id(self):
        """Should extract job_id and chord_id from dict result."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = {
            "job_id": "job-789",
            "chord_id": "chord-101",
            "total_chunks": 8
        }

        result = orch._parse_dispatch_result(task_result)

        assert result.job_id == "job-789"
        assert result.chord_id == "chord-101"
        assert result.total_chunks == 8

    def test_dict_with_job_id_only(self):
        """Should extract job_id when chord_id is missing."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = {"job_id": "job-999", "total_chunks": 3}

        result = orch._parse_dispatch_result(task_result)

        assert result.job_id == "job-999"
        assert result.chord_id is None
        assert result.total_chunks == 3

    def test_string_result_parsed_with_ast(self):
        """Should parse string result using ast.literal_eval."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = "{'job_id': 'job-str', 'chord_id': 'chord-str'}"

        result = orch._parse_dispatch_result(task_result)

        assert result.job_id == "job-str"
        assert result.chord_id == "chord-str"

    def test_invalid_result_returns_empty(self):
        """Should return empty DispatchResult when parsing fails."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = "not a valid dict"

        result = orch._parse_dispatch_result(task_result)

        assert result.job_id is None
        assert result.chord_id is None

    def test_dict_without_job_id_returns_empty(self):
        """Should return empty DispatchResult when job_id is missing."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        task_result = {"status": "done", "count": 5}

        result = orch._parse_dispatch_result(task_result)

        assert result.job_id is None


class TestWaitViaChord:
    """Tests for _wait_via_chord helper."""

    def test_chord_success_with_sufficient_proxies(self):
        """When chord completes and usable_count >= min_count, should return True."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        mock_chord_result = MagicMock()
        mock_chord_result.get.return_value = "success"
        mock_chord_result.failed.return_value = False

        with patch('celery.result.AsyncResult', return_value=mock_chord_result), \
             patch.object(orch, '_start_progress_thread') as mock_start, \
             patch.object(orch, '_stop_progress_thread') as mock_stop, \
             patch.object(orch, 'get_usable_proxy_count', return_value=50):

            mock_thread = Mock()
            mock_start.return_value = mock_thread

            result = orch._wait_via_chord(
                chord_id="chord-1",
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is True
            mock_start.assert_called_once()
            mock_stop.assert_called_once()

    def test_chord_success_with_insufficient_proxies(self):
        """When chord completes but usable_count < min_count, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        mock_chord_result = MagicMock()
        mock_chord_result.get.return_value = "success"
        mock_chord_result.failed.return_value = False

        with patch('celery.result.AsyncResult', return_value=mock_chord_result), \
             patch.object(orch, '_start_progress_thread', return_value=Mock()), \
             patch.object(orch, '_stop_progress_thread'), \
             patch.object(orch, 'get_usable_proxy_count', return_value=3):

            result = orch._wait_via_chord(
                chord_id="chord-1",
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_chord_failed(self):
        """When chord fails, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        mock_chord_result = MagicMock()
        mock_chord_result.get.return_value = "error"
        mock_chord_result.failed.return_value = True

        with patch('celery.result.AsyncResult', return_value=mock_chord_result), \
             patch.object(orch, '_start_progress_thread', return_value=Mock()), \
             patch.object(orch, '_stop_progress_thread'):

            result = orch._wait_via_chord(
                chord_id="chord-1",
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_chord_timeout(self):
        """When chord.get() times out, should handle error and return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        mock_chord_result = MagicMock()
        mock_chord_result.get.side_effect = TimeoutError("Chord timeout")

        with patch('celery.result.AsyncResult', return_value=mock_chord_result), \
             patch.object(orch, '_start_progress_thread', return_value=Mock()), \
             patch.object(orch, '_stop_progress_thread'), \
             patch.object(orch, '_handle_chord_error', return_value=False) as mock_error:

            result = orch._wait_via_chord(
                chord_id="chord-1",
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False
            mock_error.assert_called_once()


class TestProgressThread:
    """Tests for _start_progress_thread and _stop_progress_thread."""

    def test_start_progress_thread_creates_daemon_thread(self):
        """Should create and start a daemon thread."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        stop_event = threading.Event()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_refresh_progress', return_value={
                 'completed_chunks': 5,
                 'total_chunks': 10,
                 'progress_pct': 50.0
             }):

            thread = orch._start_progress_thread(stop_event, "job-1", time.time(), 1)

            assert isinstance(thread, threading.Thread)
            assert thread.daemon is True
            assert thread.is_alive()

            # Clean up
            stop_event.set()
            thread.join(timeout=2)

    def test_stop_progress_thread_sets_event_and_joins(self):
        """Should set stop event and join thread."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        stop_event = threading.Event()
        mock_thread = Mock(spec=threading.Thread)

        orch._stop_progress_thread(stop_event, mock_thread)

        assert stop_event.is_set()
        mock_thread.join.assert_called_once_with(timeout=2)


class TestHandleChordError:
    """Tests for _handle_chord_error helper."""

    def test_timeout_error_handling(self):
        """Should recognize and log timeout errors."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        result = orch._handle_chord_error(TimeoutError("timeout"), time.time(), 60)

        assert result is False

    def test_generic_error_handling(self):
        """Should handle non-timeout errors."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        result = orch._handle_chord_error(ValueError("some error"), time.time(), 60)

        assert result is False


class TestWaitViaRedisPolling:
    """Tests for _wait_via_redis_polling helper."""

    def test_job_complete_with_sufficient_proxies(self):
        """When job completes and usable_count >= min_count, should return True."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_refresh_progress', return_value={
                 'status': 'COMPLETE',
                 'completed_chunks': 10,
                 'total_chunks': 10,
                 'progress_pct': 100.0
             }), \
             patch.object(orch, 'get_usable_proxy_count', return_value=50):

            result = orch._wait_via_redis_polling(
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is True

    def test_job_complete_with_insufficient_proxies(self):
        """When job completes but usable_count < min_count, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_refresh_progress', return_value={
                 'status': 'COMPLETE',
                 'completed_chunks': 10,
                 'total_chunks': 10,
                 'progress_pct': 100.0
             }), \
             patch.object(orch, 'get_usable_proxy_count', return_value=3):

            result = orch._wait_via_redis_polling(
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_job_failed(self):
        """When job status is FAILED, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_refresh_progress', return_value={
                 'status': 'FAILED',
                 'completed_chunks': 5,
                 'total_chunks': 10,
                 'progress_pct': 50.0
             }):

            result = orch._wait_via_redis_polling(
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_timeout_exceeded(self):
        """When timeout is exceeded, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_refresh_progress', return_value={
                 'status': 'PROCESSING',
                 'completed_chunks': 5,
                 'total_chunks': 10,
                 'progress_pct': 50.0
             }), \
             patch.object(orch, 'is_celery_alive', return_value=True), \
             patch('time.sleep'):  # Mock sleep to speed up test

            # Set start_time in the past so timeout is immediate
            result = orch._wait_via_redis_polling(
                job_id="job-1",
                start_time=time.time() - 100,  # 100 seconds ago
                timeout=60,  # 60 second timeout
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_celery_dead_returns_false(self):
        """When Celery can't be restarted, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=False):
            result = orch._wait_via_redis_polling(
                job_id="job-1",
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False


class TestWaitViaFileMonitoring:
    """Tests for _wait_via_file_monitoring helper."""

    def test_file_updated_with_sufficient_proxies(self):
        """When file mtime changes and usable_count >= min_count, should return True."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        mtime_before = 1000.0

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_proxy_file_mtime', return_value=2000.0), \
             patch.object(orch, 'get_usable_proxy_count', return_value=50):

            result = orch._wait_via_file_monitoring(
                mtime_before=mtime_before,
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is True

    def test_file_updated_with_insufficient_proxies_continues_waiting(self):
        """When file updates but usable_count < min_count, should continue waiting."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        mtime_before = 1000.0

        # First call: file updated but not enough proxies
        # Second call: timeout exceeded
        call_count = [0]

        def get_mtime_side_effect():
            call_count[0] += 1
            return 2000.0  # File always updated

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_proxy_file_mtime', side_effect=get_mtime_side_effect), \
             patch.object(orch, 'get_usable_proxy_count', return_value=3), \
             patch.object(orch, 'is_celery_alive', return_value=True), \
             patch('time.sleep'):

            # Set start_time in the past so timeout is immediate
            result = orch._wait_via_file_monitoring(
                mtime_before=mtime_before,
                start_time=time.time() - 100,
                timeout=60,
                min_count=10,
                check_interval=15
            )

            # Should timeout and return False
            assert result is False

    def test_timeout_exceeded(self):
        """When timeout is exceeded, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()
        mtime_before = 1000.0

        with patch.object(orch, 'restart_celery_if_dead', return_value=True), \
             patch.object(orch, 'get_proxy_file_mtime', return_value=1000.0), \
             patch.object(orch, 'is_celery_alive', return_value=True), \
             patch('time.sleep'):

            result = orch._wait_via_file_monitoring(
                mtime_before=mtime_before,
                start_time=time.time() - 100,
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False

    def test_celery_dead_returns_false(self):
        """When Celery can't be restarted, should return False."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        with patch.object(orch, 'restart_celery_if_dead', return_value=False):
            result = orch._wait_via_file_monitoring(
                mtime_before=1000.0,
                start_time=time.time(),
                timeout=60,
                min_count=10,
                check_interval=15
            )

            assert result is False


class TestPhaseTransitions:
    """Tests for wait_for_refresh_completion phase transition logic."""

    def test_chord_path_when_chord_id_available(self):
        """When dispatch returns chord_id, should use _wait_via_chord."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        dispatch_result = DispatchResult(
            job_id="job-1",
            chord_id="chord-1",
            total_chunks=5,
            success=True
        )

        with patch.object(orch, '_wait_for_chain_dispatch', return_value=dispatch_result), \
             patch.object(orch, '_wait_via_chord', return_value=True) as mock_chord, \
             patch.object(orch, '_wait_via_redis_polling') as mock_redis, \
             patch.object(orch, '_wait_via_file_monitoring') as mock_file:

            result = orch.wait_for_refresh_completion(
                mtime_before=1000.0,
                min_count=10,
                timeout=60,
                task_id="task-1"
            )

            assert result is True
            mock_chord.assert_called_once()
            mock_redis.assert_not_called()
            mock_file.assert_not_called()

    def test_redis_path_when_only_job_id_available(self):
        """When dispatch returns job_id but no chord_id, should use _wait_via_redis_polling."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        dispatch_result = DispatchResult(
            job_id="job-1",
            chord_id=None,  # No chord_id
            total_chunks=5,
            success=True
        )

        with patch.object(orch, '_wait_for_chain_dispatch', return_value=dispatch_result), \
             patch.object(orch, '_wait_via_chord') as mock_chord, \
             patch.object(orch, '_wait_via_redis_polling', return_value=True) as mock_redis, \
             patch.object(orch, '_wait_via_file_monitoring') as mock_file:

            result = orch.wait_for_refresh_completion(
                mtime_before=1000.0,
                min_count=10,
                timeout=60,
                task_id="task-1"
            )

            assert result is True
            mock_chord.assert_not_called()
            mock_redis.assert_called_once()
            mock_file.assert_not_called()

    def test_file_path_when_neither_id_available(self):
        """When dispatch returns neither chord_id nor job_id, should use _wait_via_file_monitoring."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        dispatch_result = DispatchResult(
            job_id=None,
            chord_id=None,
            total_chunks=0,
            success=True
        )

        with patch.object(orch, '_wait_for_chain_dispatch', return_value=dispatch_result), \
             patch.object(orch, '_wait_via_chord') as mock_chord, \
             patch.object(orch, '_wait_via_redis_polling') as mock_redis, \
             patch.object(orch, '_wait_via_file_monitoring', return_value=True) as mock_file:

            result = orch.wait_for_refresh_completion(
                mtime_before=1000.0,
                min_count=10,
                timeout=60,
                task_id="task-1"
            )

            assert result is True
            mock_chord.assert_not_called()
            mock_redis.assert_not_called()
            mock_file.assert_called_once()

    def test_dispatch_failure_returns_false_immediately(self):
        """When dispatch fails, should return False without trying other methods."""
        from orchestrator import Orchestrator

        orch = Orchestrator()

        dispatch_result = DispatchResult(
            job_id=None,
            chord_id=None,
            total_chunks=0,
            success=False,
            error="Dispatch failed"
        )

        with patch.object(orch, '_wait_for_chain_dispatch', return_value=dispatch_result), \
             patch.object(orch, '_wait_via_chord') as mock_chord, \
             patch.object(orch, '_wait_via_redis_polling') as mock_redis, \
             patch.object(orch, '_wait_via_file_monitoring') as mock_file:

            result = orch.wait_for_refresh_completion(
                mtime_before=1000.0,
                min_count=10,
                timeout=60,
                task_id="task-1"
            )

            assert result is False
            mock_chord.assert_not_called()
            mock_redis.assert_not_called()
            mock_file.assert_not_called()
