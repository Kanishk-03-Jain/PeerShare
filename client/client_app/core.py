import logging
import os
import sys
from typing import List, Optional

import requests
from watchdog.observers import Observer

from . import config, p2p_server, schemas, tunnel_manager, utils, watcher

# Configure logging
handlers = [
    logging.StreamHandler(sys.stdout),
    logging.FileHandler("client.log"),
]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers,
    force=True,  # Ensure we override any existing configuration
)
logger = logging.getLogger(__name__)


class PeerShareError(Exception):
    """Base exception for client errors"""

    pass


class AuthenticationError(PeerShareError):
    """Raised when login fails"""

    pass


class PeerShareClient:
    def __init__(
        self,
        user_id: int = config.settings.USER_ID,
        username: str = config.settings.USERNAME,
        password: Optional[str] = None,
        port: int = config.settings.PORT,
        folder: str = config.settings.SHARED_FOLDER,
        jwt_token: str = config.settings.JWT_TOKEN,
    ):
        self.user_id: Optional[int] = user_id
        self.username = username
        self.password = password
        self.access_token: Optional[str] = jwt_token

        self.port = port
        self.folder = folder

        self.local_ip = utils.get_local_ip()
        self.server = p2p_server.P2PServer(port, folder)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def login(self) -> schemas.UserResponse:
        """Login with username and password, get JWT token"""
        logger.info(f"Logging in as '{self.username}'...")

        if not self.password:
            raise AuthenticationError("Password is required")

        try:
            url = f"{config.settings.TRACKER_SERVER_URL}/login"
            payload = {"username": self.username, "password": self.password}

            resp = requests.post(url, json=payload)

            if resp.status_code == 401:
                raise AuthenticationError("Invalid username or password")

            resp.raise_for_status()

            token_resp = schemas.TokenResponse(**resp.json())

            self.access_token = token_resp.access_token
            self.user_id = token_resp.user.user_id

            config.settings.set("jwt_token", self.access_token)
            config.settings.set("user_id", self.user_id)
            config.settings.set("username", self.username)

            logger.info(f"Successfully logged in as {token_resp.user.username}")
            return token_resp.user

        except requests.exceptions.RequestException as e:
            logger.error(f"Login connection failed: {e}")
            raise PeerShareError(f"Login connection failed: {e}")

    def initialize(self):
        """Setup folder and start server"""
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            logger.info(f"Created shared folder at: {self.folder}")

        # Start the P2P server if not already running
        self.server.start()
        self.start_watcher()

    def announce_files(self) -> int:
        """Scans files and announce them to tracker server"""
        logger.info(f"Scanning folder {self.folder}...")
        files_data = utils.scan_folder(self.folder)  # Returns list of dicts

        if not files_data:
            logger.warning("No files to share")
            return 0

        valid_files = [schemas.FileBase(**f) for f in files_data]

        ngrok_url = tunnel_manager.start_ngrok_tunnel(
            self.port, auth_token=config.settings.NGROK_TOKEN
        )

        if self.user_id is None:
            raise RuntimeError(
                "User_id not available, user must be authenticated first"
            )

        announce_payload = schemas.FileAnnounce(
            user_id=self.user_id,
            port=self.port,
            ip_address=self.local_ip,
            public_url=ngrok_url,
            files=valid_files,
        )

        try:
            url = f"{config.settings.TRACKER_SERVER_URL}/announce"
            resp = requests.post(
                url,
                json=announce_payload.model_dump(mode="json"),
                headers=self._get_headers(),
            )
            resp.raise_for_status()

            count = len(valid_files)
            logger.info(f"Announced {count} files to tracker server")
            return count

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to announce: {e}")
            raise PeerShareError(f"Announcement failed: {e}")

    def send_heartbeat(self):
        """Ping the server to keep the session alive"""
        try:
            url = f"{config.settings.TRACKER_SERVER_URL}/ping"
            requests.post(url, headers=self._get_headers())
        except Exception as e:
            logger.warning(f"Ping failed (Tracker might be down): {e}")

    def update_configuration(self, changed_keys: List[str]) -> int:
        """Reloads configuration, handling server restarts and re-authentication"""
        logger.info(f"Updating configuration for keys: {changed_keys}")

        # Update local state from global config
        self.port = config.settings.PORT
        self.folder = config.settings.SHARED_FOLDER

        # Stop everything (Server + Tunnels)
        if self.server:
            self.server.stop()
        tunnel_manager.kill_tunnels()
        self.stop_watcher()

        # Handle Tracker Change or Login (needs re-login before announce)
        if "tracker_server_url" in changed_keys:
            logger.info("Tracker URL changed, re-authenticating...")
            self.login()

        # Start Server
        self.server = p2p_server.P2PServer(self.port, self.folder)
        self.server.start()
        self.start_watcher()

        return self.announce_files()

    def start_watcher(self):
        self.observer = Observer()
        event_handler = watcher.FileEventHandler(self.announce_files)
        self.observer.schedule(event_handler, self.folder, recursive=True)
        self.observer.start()
        logger.info(f"Watching folder {self.folder} for changes...")

    def stop_watcher(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped file watcher")
