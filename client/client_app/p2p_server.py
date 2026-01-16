import http.server
import logging
import os
import socketserver
import threading
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlparse

from . import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PeerTCPServer(socketserver.TCPServer):
    def __init__(self, server_address, handler, shared_folder: str):
        super().__init__(server_address, handler)
        self.shared_folder: str = shared_folder


class PeerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL /download?name=test.txt
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/download":
            return self.send_error(404, "Endpoint not found")

        params = parse_qs(parsed_url.query)
        filename = params.get("name", [None])[0]

        if not filename:
            return self.send_error(400, "Invalid filename")

        # Security: Sanitize filename to prevent path traversal
        # Remove any path components (../, /, \)
        filename = os.path.basename(filename)
        if ".." in filename or "/" in filename or "\\" in filename:
            return self.send_error(400, "Invalid filename")

        # Server instance is avalaible here
        try:
            folder = cast(PeerTCPServer, self.server).shared_folder
        except AttributeError:
            # Fallback if it wasn't set correctly (prevents the crash you just saw)
            logging.error("Error: shared_folder not set on server instance")
            return self.send_error(500, "Server Configuration Error")

        # Resolve paths to prevent path traversal
        shared_folder = Path(folder).resolve()
        file_path = (shared_folder / filename).resolve()

        # Security check: ensure file is within shared folder
        if not str(file_path).startswith(str(shared_folder)):
            return self.send_error(403, "Access denied")

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self._send_file(file_path, filename)
        else:
            self.send_error(404, "File not found")

    def _send_file(self, file_path: Path, filename: str):

        try:
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            file_size = os.path.getsize(file_path)
            self.send_header("Content-Length", str(file_size))
            self.end_headers()

            with open(file_path, "rb") as f:
                while chunk := f.read(config.CHUNK_SIZE):
                    self.wfile.write(chunk)
            logging.info(f"Served: {filename} -> {self.client_address[0]}")
        except Exception as e:
            logging.error(f"Upload error: {e}")


class P2PServer:
    def __init__(self, port: int, shared_folder: str):
        self.port = port
        self.shared_folder = shared_folder
        self.server_thread = None
        self.httpd = None

    def start(self):
        """Starts the server in background thread"""
        socketserver.TCPServer.allow_reuse_address = True

        # create the server with the custom class with custom shared folder
        self.httpd = PeerTCPServer(
            ("", self.port), PeerRequestHandler, self.shared_folder
        )

        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()
        logging.info(f"File Server running on port {self.port}")

    def stop(self):
        """Stops the server and releases the port"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            logging.info("File Server stopped")
        if self.server_thread:
            self.server_thread.join()
            self.server_thread = None
