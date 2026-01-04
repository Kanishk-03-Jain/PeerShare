import requests
import os
import logging
from tqdm import tqdm
from typing import List

from . import config, schemas

logger = logging.getLogger(__name__)

def search_tracker(query: str) -> List[schemas.SearchResult]:
    """Queries the tracker and returns a list of files."""
    try:
        response = requests.get(
            f"{config.TRACKER_SERVER_URL}/search", params={"q": query}
        )
        response.raise_for_status()
        raw_results = response.json()
        
        return [schemas.SearchResult(**item) for item in raw_results]
        
    except Exception as e:
        logger.error(f"Tracker search failed: {e}")
        return []


def download_from_peer(
    download_url: str,
    timeout: int,
    filename: str,
    filesize: int,
    destination: str,
    method_name: str,
    save_path: str,
) -> bool:
    try:
        # Stream the download so we don't crash RAM on big files
        with requests.get(
            download_url, params={"name": filename}, stream=True, timeout=timeout
        ) as r:
            r.raise_for_status()
            logger.info(f"Connected via {method_name}!")

            # Ensure download directory exists
            if not os.path.exists(destination):
                os.makedirs(destination)

            with tqdm(
                total=filesize, unit="B", unit_scale=True, desc=filename
            ) as progress_bar:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress_bar.update(len(chunk))

        logger.info(f"Download Complete! Saved to: {save_path}")
        return True

    except Exception as e:
        logger.warning(f"Error during {method_name}: {e}")

    return False


def download_file_strategy(
    file_data: schemas.SearchResult, destination: str
) -> bool:
    """Tries local tranfer first, if fails switches to public url"""
    
    filename = file_data.file_name
    filesize = file_data.file_size

    # Ensure download directory exists
    if not os.path.exists(destination):
        os.makedirs(destination)
        
    save_path = os.path.join(destination, filename)

    # Try every peer until one works
    for peer in file_data.peers:
        candidates = []
        
        # 1. Local LAN
        local_url = f"http://{peer.ip_address}:{peer.port}"
        candidates.append((local_url, "Local LAN"))
        
        # 2. Public Tunnel (Ngrok)
        if peer.public_url:
            public_url = peer.public_url
            if not public_url.startswith("http"):
                public_url = f"http://{public_url}"
            candidates.append((public_url, "Public Tunnel"))
            
        for base_url, method_name in candidates:
            timeout = 3 if method_name == "Local LAN" else 15
            download_url = f"{base_url}/download"
            
            if download_from_peer(
                download_url,
                timeout,
                filename,
                filesize,
                destination,
                method_name,
                save_path,
            ):
                return True

    logger.error("All connection methods failed for all peers.")
    return False
