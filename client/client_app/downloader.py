import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import requests
from tqdm import tqdm

from . import config, schemas

logger = logging.getLogger(__name__)


def search_tracker(query: str) -> List[schemas.SearchResult]:
    """Queries the tracker and returns a list of files."""
    try:
        response = requests.get(
            f"{config.settings.TRACKER_SERVER_URL}/search", params={"q": query}
        )
        response.raise_for_status()
        raw_results = response.json()

        return [schemas.SearchResult(**item) for item in raw_results]

    except Exception as e:
        logger.error(f"Tracker search failed: {e}")
        return []


def download_chunk(
    download_url: str,
    start: int,
    end: int,
    filename: str,
    save_path: str,
    timeout: int,
    pbar: tqdm,  # Added pbar argument
):
    headers = {"Range": f"bytes={start}-{end}"}

    try:
        with requests.get(
            download_url,
            params={"name": filename},
            headers=headers,
            stream=True,
            timeout=timeout,
        ) as r:
            r.raise_for_status()

            with open(save_path, "r+b") as f:
                f.seek(start)
                # Use iter_content for progress updates and memory efficiency
                for chunk in r.iter_content(chunk_size=config.CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
    except Exception as e:
        # Re-raise so the executor knows it failed
        logger.error(f"Chunk download failed ({start}-{end}): {e}")
        raise e


def parallel_download(
    download_url: str,
    timeout: int,
    filename: str,
    filesize: int,
    destination: str,
    method_name: str,
    save_path: str,
) -> bool:
    if not os.path.exists(destination):
        os.makedirs(destination)

    # pre-allocate file
    try:
        with open(save_path, "wb") as f:
            f.seek(filesize - 1)
            f.write(b"\0")
    except Exception as e:
        logger.error(f"Failed to allocate file: {e}")
        return False

    # calculate chunks
    chunk_size = filesize // config.CHUNK_COUNT
    futures = []
    logger.info(f"Connected via {method_name}! Starting parallel download...")

    # Create a shared progress bar
    with tqdm(
        total=filesize, unit="B", unit_scale=True, desc=filename, unit_divisor=1024
    ) as pbar:
        with ThreadPoolExecutor(max_workers=config.CHUNK_COUNT) as executor:
            for i in range(config.CHUNK_COUNT):
                start = i * chunk_size
                end = (
                    filesize - 1
                    if i == config.CHUNK_COUNT - 1
                    else (start + chunk_size - 1)
                )

                futures.append(
                    executor.submit(
                        download_chunk,
                        download_url,
                        start,
                        end,
                        filename,
                        save_path,
                        timeout,
                        pbar,
                    )
                )

            # Wait for all chunks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Download failed: {e}")
                    return False

    logger.info(f"Download Complete! Saved to: {save_path}")
    return True


def download_file_strategy(file_data: schemas.SearchResult, destination: str) -> bool:
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

            if parallel_download(
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
