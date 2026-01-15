import hashlib
import logging
import os
import socket
from typing import Any, Dict, List

from .config import CHUNK_SIZE

logger = logging.getLogger(__name__)


def get_file_hash(filepath: str) -> str:
    """Calculate SHA-256 hash of a file"""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_local_ip() -> str:
    """Finds the internal WiFi IP address."""

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't actually connect, but forces the OS to find the preferred local IP
        s.connect(("8.8.8.8", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def scan_folder(folder_path: str) -> List[Dict[str, Any]]:
    """Scans the folder and returns a list of file dictionaries."""
    files_payload = []
    if not os.path.exists(folder_path):
        logger.warning(f"Shared folder does not exist: {folder_path}")
        return []

    for root, _, files in os.walk(folder_path):
        for filename in files:
            filepath = os.path.join(root, filename)

            try:
                files_payload.append(
                    {
                        "file_hash": get_file_hash(filepath),
                        "file_name": filename,
                        "file_size": os.path.getsize(filepath),
                    }
                )
            except Exception as e:
                logger.warning(f"Skipping file {filename}: {e}")

    return files_payload
