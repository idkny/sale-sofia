"""
Checkpoint manager for scraping session recovery.

Saves and restores scraping progress to enable crash recovery.
Checkpoints are saved periodically (batched) to avoid I/O overhead.

Spec: docs/specs/112_SCRAPER_RESILIENCE.md (Section 3.1)
"""

import json
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import CHECKPOINT_BATCH_SIZE, CHECKPOINT_DIR


class CheckpointManager:
    """
    Save and restore scraping progress for crash recovery.

    Usage:
        checkpoint = CheckpointManager("imot_bg_2025-01-15")

        # Check for existing checkpoint
        state = checkpoint.load()
        if state:
            scraped_urls = set(state["scraped"])
            pending_urls = list(state["pending"])

        # Save progress periodically
        for url in urls:
            scrape(url)
            scraped_urls.add(url)
            checkpoint.save(scraped_urls, pending_urls)

        # Clear when done
        checkpoint.clear()
    """

    def __init__(self, name: str, checkpoint_dir: Path | None = None):
        """
        Initialize checkpoint manager.

        Args:
            name: Session name (e.g., 'imot_bg_2025-01-15')
            checkpoint_dir: Directory for checkpoint files (default: CHECKPOINT_DIR)
        """
        self.name = name
        self.dir = Path(checkpoint_dir) if checkpoint_dir else Path(CHECKPOINT_DIR)
        self._ensure_directory()
        self.file = self.dir / f"{name}_checkpoint.json"
        self._counter = 0
        self.batch_size = CHECKPOINT_BATCH_SIZE

    def _ensure_directory(self) -> None:
        """Create checkpoint directory if it doesn't exist."""
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, scraped: set[str], pending: list[str], force: bool = False) -> None:
        """
        Save checkpoint (batched unless force=True).

        Args:
            scraped: Set of already-scraped URLs
            pending: List of pending URLs to scrape
            force: If True, save immediately regardless of batch counter
        """
        self._counter += 1

        if not force and self._counter % self.batch_size != 0:
            return

        self._write_checkpoint(scraped, pending)

    def _write_checkpoint(self, scraped: set[str], pending: list[str]) -> None:
        """Write checkpoint data to file."""
        try:
            data = {
                "scraped": list(scraped),
                "pending": pending,
                "timestamp": time.time(),
                "name": self.name,
            }
            with open(self.file, "w") as f:
                json.dump(data, f)
            logger.debug(f"Checkpoint saved: {len(scraped)} scraped, {len(pending)} pending")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def load(self) -> Optional[dict]:
        """
        Load existing checkpoint if any.

        Returns:
            Checkpoint data dict or None if not found/failed
        """
        if not self.file.exists():
            return None

        try:
            with open(self.file) as f:
                data = json.load(f)
            logger.info(
                f"Loaded checkpoint: {len(data.get('scraped', []))} scraped, "
                f"{len(data.get('pending', []))} pending"
            )
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def clear(self) -> None:
        """Remove checkpoint file (call when scraping complete)."""
        if self.file.exists():
            try:
                self.file.unlink()
                logger.info(f"Checkpoint cleared: {self.name}")
            except Exception as e:
                logger.warning(f"Failed to clear checkpoint: {e}")
