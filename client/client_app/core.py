import os
import requests
import time
import getpass
import logging
from typing import List, Optional

from . import tunnel_manager, utils, config, p2p_server, schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ShareNotesError(Exception):
    """Base exception for client errors"""

    pass


class AuthenticationError(ShareNotesError):
    """Raised when login fails"""

    pass


class ShareNotesClient:
    def __init__(
        self,
        username: str,
        password: str = None,
        port: int = config.settings.PORT,
        folder: str = config.settings.SHARED_FOLDER,
    ):
        self.user_id: Optional[int] = None
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None

        self.port = port
        self.folder = folder

        self.local_ip = utils.get_local_ip()
        self.server = p2p_server.P2PServer(port, folder)

    def _get_headers(self):
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

            logger.info(f"Successfully logged in as {token_resp.user.username}")
            return token_resp.user

        except requests.exceptions.RequestException as e:
            logger.error(f"Login connection failed: {e}")
            raise ShareNotesError(f"Login connection failed: {e}")

    def initialize(self):
        """Setup folder and start server"""
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            logger.info(f"Created shared folder at: {self.folder}")

        # Start the P2P server if not already running
        self.server.start()

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
            raise ShareNotesError(f"Announcement failed: {e}")

    def send_heartbeat(self):
        """Ping the server to keep the session alive"""
        try:
            url = f"{config.settings.TRACKER_SERVER_URL}/ping"
            requests.post(url, headers=self._get_headers())
        except Exception as e:
            logger.warning(f"Ping failed (Tracker might be down): {e}")

    def run_forever(self):
        """Main Loop - kept for legacy CLI usage"""
        try:
            self.login()
            self.initialize()
            self.announce_files()

            logger.info("Client is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(30)
                self.send_heartbeat()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except ShareNotesError as e:
            logger.error(f"Fatal Client Error: {e}")
