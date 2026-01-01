import os
import requests
import time
import sys

from . import utils, config, p2p_server

class ShareNotesClient:
    def __init__(self, username, port=config.DEFAULT_PORT, folder=config.DEFAULT_FOLDER):
        self.user_id = None
        self.username = username
        self.port = port
        self.folder = folder

        self.local_ip = utils.get_local_ip()
        self.server = p2p_server.P2PServer(port, folder)

    def login(self):
        """Resolve userid from usrname"""
        print(f"Logging in as '{self.username}'...")
        try:
            url = f"{config.TRACKER_SERVER_URL}/user/{self.username}"
            resp = requests.get(url)

            if resp.status_code == 404:
                print("User not found. Please register first.")
                sys.exit(1)
            
            resp.raise_for_status()
            self.user_id = resp.json()['user_id']
        except Exception as e:
            print(f"Login failed: {e}")
            sys.exit(1)


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
        
        payload = {
            "user_id": self.user_id,
            "port": self.port,
            "ip_address": self.local_ip,
            "files": files
        }

        try:
            url = f"{config.TRACKER_SERVER_URL}/announce"
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            print(f"Announced {len(files)} to tracker server")
        except Exception as e:
            print(f"Failed to announce: {e}")

    def send_heartbeat(self):
        """Ping the server to keep the session alive"""
        try:
            url = f"{config.TRACKER_SERVER_URL}/ping/{self.user_id}"
            requests.post(url)
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
