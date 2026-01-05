import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Constants
TRACKER_SERVER_URL = "https://share-notes-fh45.onrender.com"
APP_DIR = Path.home() / ".peer-share"
CONFIG_FILE = APP_DIR / "config.json"

# Defaults
DEFAULT_CONFIG = {
    "tracker_server_url": "https://share-notes-fh45.onrender.com",
    "port": 8001,
    "shared_folder": os.path.abspath("./shared_folder"),
    "download_folder": os.path.abspath("./downloads"),
    "ngrok_authtoken": "",
}


class ConfigManager:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self._ensure_app_dir()
        self._load()

    def _ensure_app_dir(self):
        if not APP_DIR.exists():
            try:
                APP_DIR.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create app directory: {e}")

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved_config = json.load(f)
                    self._config.update(saved_config)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")

    def get(self, key: str) -> Any:
        return self._config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any):
        self._config[key] = value
        self.save()

    @property
    def TRACKER_SERVER_URL(self) -> str:
        return self.get("tracker_server_url")

    @property
    def PORT(self) -> int:
        return int(self.get("port"))

    @property
    def SHARED_FOLDER(self) -> str:
        return self.get("shared_folder")

    @property
    def DOWNLOAD_FOLDER(self) -> str:
        return self.get("download_folder")

    @property
    def NGROK_TOKEN(self) -> str:
        return self.get("ngrok_authtoken")


# Singleton instance
settings = ConfigManager()

CHUNK_SIZE = 4096
