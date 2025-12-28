"""Unit tests for ScrapingKeys Redis key generation."""

import pytest
from scraping.redis_keys import ScrapingKeys


class TestScrapingKeysPrefix:
    """Test the PREFIX constant."""

    def test_prefix_value(self):
        """Test PREFIX is 'scraping'."""
        assert ScrapingKeys.PREFIX == "scraping"


class TestScrapingKeysKeyGeneration:
    """Test individual key generation methods."""

    def test_status_key(self):
        """Test status() generates correct key."""
        assert ScrapingKeys.status("job123") == "scraping:job123:status"

    def test_total_chunks_key(self):
        """Test total_chunks() generates correct key."""
        assert ScrapingKeys.total_chunks("job123") == "scraping:job123:total_chunks"

    def test_completed_chunks_key(self):
        """Test completed_chunks() generates correct key."""
        assert ScrapingKeys.completed_chunks("job123") == "scraping:job123:completed_chunks"

    def test_total_urls_key(self):
        """Test total_urls() generates correct key."""
        assert ScrapingKeys.total_urls("job123") == "scraping:job123:total_urls"

    def test_result_count_key(self):
        """Test result_count() generates correct key."""
        assert ScrapingKeys.result_count("job123") == "scraping:job123:result_count"

    def test_error_count_key(self):
        """Test error_count() generates correct key."""
        assert ScrapingKeys.error_count("job123") == "scraping:job123:error_count"

    def test_started_at_key(self):
        """Test started_at() generates correct key."""
        assert ScrapingKeys.started_at("job123") == "scraping:job123:started_at"

    def test_completed_at_key(self):
        """Test completed_at() generates correct key."""
        assert ScrapingKeys.completed_at("job123") == "scraping:job123:completed_at"


class TestScrapingKeysWithDifferentJobIds:
    """Test key generation with various job_id formats."""

    @pytest.mark.parametrize("job_id,expected_suffix", [
        ("simple", "simple"),
        ("job-with-hyphens", "job-with-hyphens"),
        ("job_with_underscores", "job_with_underscores"),
        ("job123numbers", "job123numbers"),
        ("UPPERCASE", "UPPERCASE"),
        ("Mixed-Case_123", "Mixed-Case_123"),
    ])
    def test_status_with_various_job_ids(self, job_id, expected_suffix):
        """Test status() with different job_id formats."""
        expected = f"scraping:{expected_suffix}:status"
        assert ScrapingKeys.status(job_id) == expected

    @pytest.mark.parametrize("job_id,expected_suffix", [
        ("test-job", "test-job"),
        ("test_job", "test_job"),
        ("testJob123", "testJob123"),
    ])
    def test_all_methods_with_special_characters(self, job_id, expected_suffix):
        """Test all methods handle special characters correctly."""
        assert ScrapingKeys.status(job_id) == f"scraping:{expected_suffix}:status"
        assert ScrapingKeys.total_chunks(job_id) == f"scraping:{expected_suffix}:total_chunks"
        assert ScrapingKeys.completed_chunks(job_id) == f"scraping:{expected_suffix}:completed_chunks"
        assert ScrapingKeys.total_urls(job_id) == f"scraping:{expected_suffix}:total_urls"
        assert ScrapingKeys.result_count(job_id) == f"scraping:{expected_suffix}:result_count"
        assert ScrapingKeys.error_count(job_id) == f"scraping:{expected_suffix}:error_count"
        assert ScrapingKeys.started_at(job_id) == f"scraping:{expected_suffix}:started_at"
        assert ScrapingKeys.completed_at(job_id) == f"scraping:{expected_suffix}:completed_at"


class TestScrapingKeysUniqueness:
    """Test that keys are unique and don't collide."""

    def test_all_keys_unique_for_same_job_id(self):
        """Test all methods generate unique keys for the same job_id."""
        job_id = "test_job"
        keys = [
            ScrapingKeys.status(job_id),
            ScrapingKeys.total_chunks(job_id),
            ScrapingKeys.completed_chunks(job_id),
            ScrapingKeys.total_urls(job_id),
            ScrapingKeys.result_count(job_id),
            ScrapingKeys.error_count(job_id),
            ScrapingKeys.started_at(job_id),
            ScrapingKeys.completed_at(job_id),
        ]

        # All keys should be unique
        assert len(keys) == len(set(keys))

    def test_different_job_ids_generate_different_keys(self):
        """Test different job_ids generate different keys for same method."""
        job_id_1 = "job1"
        job_id_2 = "job2"

        assert ScrapingKeys.status(job_id_1) != ScrapingKeys.status(job_id_2)
        assert ScrapingKeys.total_chunks(job_id_1) != ScrapingKeys.total_chunks(job_id_2)
        assert ScrapingKeys.completed_chunks(job_id_1) != ScrapingKeys.completed_chunks(job_id_2)


class TestScrapingKeysKeyFormat:
    """Test key format consistency."""

    def test_all_keys_have_correct_structure(self):
        """Test all keys follow the pattern 'prefix:job_id:field'."""
        job_id = "test_job"

        all_keys = [
            ScrapingKeys.status(job_id),
            ScrapingKeys.total_chunks(job_id),
            ScrapingKeys.completed_chunks(job_id),
            ScrapingKeys.total_urls(job_id),
            ScrapingKeys.result_count(job_id),
            ScrapingKeys.error_count(job_id),
            ScrapingKeys.started_at(job_id),
            ScrapingKeys.completed_at(job_id),
        ]

        for key in all_keys:
            parts = key.split(":")
            # All keys should have exactly 3 parts: prefix, job_id, field
            assert len(parts) == 3
            # First part should always be the PREFIX
            assert parts[0] == ScrapingKeys.PREFIX
            # Second part should be the job_id
            assert parts[1] == job_id

    def test_keys_start_with_prefix(self):
        """Test all keys start with the correct prefix."""
        job_id = "test_job"

        all_keys = [
            ScrapingKeys.status(job_id),
            ScrapingKeys.total_chunks(job_id),
            ScrapingKeys.completed_chunks(job_id),
            ScrapingKeys.total_urls(job_id),
            ScrapingKeys.result_count(job_id),
            ScrapingKeys.error_count(job_id),
            ScrapingKeys.started_at(job_id),
            ScrapingKeys.completed_at(job_id),
        ]

        for key in all_keys:
            assert key.startswith(f"{ScrapingKeys.PREFIX}:")
