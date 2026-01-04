import os
import requests
import time
import sys
import getpass

from . import tunnel_manager, utils, config, p2p_server

class ShareNotesClient:
    def __init__(self, username, password=None, port=config.DEFAULT_PORT, folder=config.DEFAULT_FOLDER):
        self.user_id = None
        self.username = username
        self.password = password
        self.access_token = None
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

    def login(self):
        """Login with username and password, get JWT token"""

        print(f"Logging in as '{self.username}'...")

        if not self.password:
            self.password = getpass.getpass("Enter password: ")
        

        try:
            url = f"{config.TRACKER_SERVER_URL}/login"
            
            payload = {
                "username": self.username,
                "password": self.password
            }

            resp = requests.post(url, json=payload)

            if resp.status_code == 401:
                print("Invalid username or password.")
                sys.exit(1)
            resp.raise_for_status()

            data = resp.json()

            self.access_token = data['access_token']
            self.user_id = data['user']['user_id']
            print(f"Successfully logged in as {data['user']['username']}")
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")


    def initialize(self):
        """Setup folder and start server"""
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            print(f"Created shared folder at: {self.folder}")
        self.server.start()
    
    def announce_files(self):
        """Scans files and announce them to tracker server"""
        print(f"Scanning folder {self.folder}...")
        files = utils.scan_folder(self.folder)

        if not files:
            print("No files to share")
            return
        
        ngrok_url = tunnel_manager.start_ngrok_tunnel(self.port, auth_token=os.getenv("NGROK_AUTHTOKEN"))
        
        payload = {
            "user_id": self.user_id,
            "port": self.port,
            "ip_address": self.local_ip,
            "public_url": ngrok_url,
            "files": files
        }

        try:
            url = f"{config.TRACKER_SERVER_URL}/announce"
            resp = requests.post(url, json=payload, headers=self._get_headers())
            resp.raise_for_status()
            print(f"Announced {len(files)} to tracker server")
        except Exception as e:
            print(f"Failed to announce: {e}")

    def send_heartbeat(self):
        """Ping the server to keep the session alive"""
        try:
            url = f"{config.TRACKER_SERVER_URL}/ping"
            requests.post(url, headers=self._get_headers())
        except Exception as e:
            print("Ping failed (Tracker might be down)")
    
    def run_forever(self):
        """Main Loop"""
        self.login()
        self.initialize()
        self.announce_files()

        print("\nClient is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(30)
                self.send_heartbeat()
        except KeyboardInterrupt:
            print("\nShutting down...")
