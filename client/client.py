import os
import hashlib
import requests
import sys
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

# CONFIGURATION
SERVER_URL = "http://127.0.0.1:8000"
MY_FOLDER = os.path.abspath("./shared_folder")  # Create this folder and put some dummy PDF/TXT files in it
USER_ID = 1  # Matches the ID in your database
MY_PORT = 8001 # The port we WILL serve files on later

class PeerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL /download?name=test.txt
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        if parsed_url.path == "/download":
            filename = params.get('name', [None])[0]

            if not filename or "/" in filename or "\\" in filename:
                self.send_error(400, "Invalid filename")
                return
            
            # Check if we actually have this file
            file_path = os.path.join(MY_FOLDER, filename)
            print(file_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                print(f"⚡ Uploading {filename} to {self.client_address[0]}...")
                # 4. Send the headers
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                file_size = os.path.getsize(file_path)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                with open(file_path, 'rb') as f:
                    try:
                        while chunk := f.read(4096):
                            self.wfile.write(chunk)
                    except BrokenPipeError:
                        pass # Client disconnected early
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Unknown endpoint")

def start_peer_server():
    """Starts the P2P server in a background thread"""
    handler = PeerRequestHandler
    # allow_resuse_address prevents "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", MY_PORT), handler) as httpd:
        print(f"🌍 P2P Node started. Listening on port {MY_PORT}...")
        httpd.serve_forever()


def get_file_hash(filepath):
    """Calculate SHA-256 hash of a file"""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        while chunk := file.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def scan_and_announce():
    files_payload = []

    print(f"Scanning folder {MY_FOLDER}")

    for root, dirs, files in os.walk(MY_FOLDER):
        for filename in files:
            filepath = os.path.join(root, filename)
            filesize = os.path.getsize(filepath)
            filehash = get_file_hash(filepath)

            files_payload.append({
                "file_hash": filehash,
                "file_name": filename,
                "file_size": filesize
            })

            print(f"Found: {filename} ({filesize} bytes)")

    if not files_payload:
        print("No files found to share!")
        return
    
    # 2. Send to Server
    payload = {
        "user_id": USER_ID,
        "port": MY_PORT,
        "files": files_payload
    }

    try:
        response = requests.post(f"{SERVER_URL}/announce", json=payload)
        response.raise_for_status()
        print("\n✅ Success! Server response:", response.json())
    except Exception as e:
        print(f"\n❌ Failed to connect to server: {e}")

if __name__ == "__main__":
    # Create the folder if it doesn't exist
    if not os.path.exists(MY_FOLDER):
        os.makedirs(MY_FOLDER)
        print(f"Created folder '{MY_FOLDER}'. Put some files in there and run this again.")
    else:
        server_thread = threading.Thread(target=start_peer_server, daemon=True)
        server_thread.start()

        scan_and_announce()

        try:
            while True:
                # Todo: Add your "Ping" logic here (sleep 30s -> ping)
                pass 
        except KeyboardInterrupt:
            print("\nShutting down node...")
