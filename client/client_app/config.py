import os

TRACKER_SERVER_URL = "https://share-notes-fh45.onrender.com"
# TRACKER_SERVER_URL = "http://127.0.0.1:8000"

DEFAULT_PORT = 8001
DEFAULT_FOLDER = os.path.abspath("./shared_folder")
DOWNLOAD_FOLDER = os.path.abspath("./downloads")

CHUNK_SIZE = 4096  # 4KB
