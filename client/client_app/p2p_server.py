import os
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

class PeerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL /download?name=test.txt
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/download":
            return self.send_error(404, "Endpoint not found")
        
        params = parse_qs(parsed_url.query)
        filename = params.get('name', [None])[0]

        if not filename:
            return self.send_error(400, "Invalid filename")
            
        # Server instance is avalaible here
        try:
            folder = self.server.shared_folder
        except AttributeError:
            # Fallback if it wasn't set correctly (prevents the crash you just saw)
            print("Error: shared_folder not set on server instance")
            return self.send_error(500, "Server Configuration Error")
        
        file_path = os.path.join(folder, filename)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self._send_file(file_path, filename)
        else:
            self.send_error(404, "File not found")


    def _send_file(self, file_path: str, filename: str):
        
        try:
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            file_size = os.path.getsize(file_path)
            self.send_header("Content-Length", str(file_size))
            self.end_headers()

            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    self.wfile.write(chunk)
            print(f"Served: {filename} -> {self.client_address[0]}")
        except Exception as e:
            print("Upload error: {e}")


class P2PServer:
    def __init__(self, port: int, shared_folder: str):
        self.port = port
        self.shared_folder = shared_folder
        self.server_thread = None
        self.httpd = None

    def start(self):
        """Starts the server in background thread"""
        socketserver.TCPServer.allow_reuse_address = True

        # create the server with the standard class
        self.httpd = socketserver.TCPServer(("", self.port), PeerRequestHandler)

        # Attach the custom shared folder the the server instance
        self.httpd.shared_folder = self.shared_folder

        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        print(f"🌍 File Server running on port {self.port}")
    

    