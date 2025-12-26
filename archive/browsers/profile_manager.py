import logging
import random
import time
from pathlib import Path
from typing import Any, Dict

import yaml
from cachetools import TTLCache

logger = logging.getLogger(__name__)

PROFILE_DIR = Path(__file__).parent / "profile" / "camoufox"
DEFAULT_PROFILE_POOL_SIZE = 5


class ProfileManager:
    """Manages the selection and generation of browser profiles (fingerprints)."""

    def __init__(self, profile_dir: Path = PROFILE_DIR):
        self.profile_dir = profile_dir
        self.profile_cache = TTLCache(maxsize=1024, ttl=24 * 60 * 60)  # 24-hour non-reuse
        self._ensure_profile_pool()

    def _ensure_profile_pool(self):
        """Ensures a minimum number of profiles are available."""
        profiles = list(self.profile_dir.glob("*.yaml"))
        if len(profiles) < DEFAULT_PROFILE_POOL_SIZE:
            logger.info(
                f"Profile pool size ({len(profiles)}) is below the minimum "
                f"({DEFAULT_PROFILE_POOL_SIZE}). Generating new profiles."
            )
            for _ in range(DEFAULT_PROFILE_POOL_SIZE - len(profiles)):
                self.generate_and_save_profile()

    def select_profile(self, browser_family: str, profile_name: str | None = None) -> Dict[str, Any]:
        """Selects a random, unused profile for the given browser family, or a specific profile if profile_name is provided."""
        if profile_name:
            profile_path = self.profile_dir / f"{profile_name}.yaml"
            if profile_path.exists():
                try:
                    with open(profile_path) as f:
                        profile = yaml.safe_load(f)
                    self.profile_cache[profile_path] = time.time()
                    logger.debug(f"Selected specific profile: {profile_path.name}")
                    logger.debug(f"Loaded profile data: {profile}")
                    return profile
                except (OSError, yaml.YAMLError) as e:
                    logger.warning(f"Could not load specified profile {profile_path}: {e}")
            else:
                logger.warning(f"Specified profile {profile_name}.yaml not found. Selecting a random profile instead.")

        profiles = list(self.profile_dir.glob("*.yaml"))
        random.shuffle(profiles)

        for profile_path in profiles:
            if profile_path not in self.profile_cache:
                try:
                    with open(profile_path) as f:
                        profile = yaml.safe_load(f)
                    self.profile_cache[profile_path] = time.time()
                    logger.debug(f"Selected profile: {profile_path.name}")
                    logger.debug(f"Loaded profile data: {profile}")
                    return profile
                except (OSError, yaml.YAMLError) as e:
                    logger.warning(f"Could not load profile {profile_path}: {e}")

        # If all profiles are in the cache, generate a new one
        logger.warning("All profiles are currently in the 24h reuse cache. Generating a new one.")
        return self.generate_and_save_profile()

    def generate_and_save_profile(self) -> Dict[str, Any]:
        """Generates a new profile and saves it as a YAML file.
        This is a placeholder implementation.
        """
        profile = self._generate_plausible_profile()
        timestamp = int(time.time() * 1000)
        file_path = self.profile_dir / f"generated_profile_{timestamp}.yaml"
        try:
            with open(file_path, "w") as f:
                yaml.dump(profile, f, default_flow_style=False)
            logger.info(f"Generated and saved new profile: {file_path.name}")
            return profile
        except OSError as e:
            logger.error(f"Failed to save generated profile {file_path}: {e}")
            raise

    def _generate_plausible_profile(self) -> Dict[str, Any]:
        """Generates a plausible, randomized browser profile.
        Simplified for Bulgarian/Sofia scraping - only Bulgarian locale and Europe/Sofia timezone.
        """
        screen_resolutions = ["1920x1080", "1600x900", "2560x1440"]
        gpu_vendors = ["Intel Inc.", "NVIDIA Corporation", "AMD"]

        return {
            "screen": {
                "width": int(random.choice(screen_resolutions).split("x")[0]),
                "height": int(random.choice(screen_resolutions).split("x")[1]),
            },
            "timezone": {"id": "Europe/Sofia"},  # Bulgaria only
            "locale": "bg-BG,bg;q=0.9",  # Bulgarian only
            "webgl": {
                "renderer": f"ANGLE (Unknown, {random.choice(gpu_vendors)}, ...)",
                "vendor": random.choice(gpu_vendors),
            },
            "fonts": {
                "families": random.sample(
                    [
                        "Arial",
                        "Helvetica",
                        "Times New Roman",
                        "Courier New",
                        "Verdana",
                        "Georgia",
                        "Palatino",
                        "Garamond",
                        "Bookman",
                        "Comic Sans MS",
                    ],
                    k=random.randint(5, 10),
                )
            },
            "navigator": {
                "userAgent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/108.0.0.0 Safari/537.36"
                ),
                "platform": "Win32",
                "hardwareConcurrency": random.choice([4, 8, 16]),
            },
        }


# Create some initial profiles for demonstration
def create_initial_profiles():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    manager = ProfileManager()
    if not any(PROFILE_DIR.iterdir()):
        logger.info("No existing profiles found. Creating initial set.")
        for i in range(DEFAULT_PROFILE_POOL_SIZE):
            profile = manager._generate_plausible_profile()
            with open(PROFILE_DIR / f"default_profile_{i + 1}.yaml", "w") as f:
                yaml.dump(profile, f)


create_initial_profiles()
