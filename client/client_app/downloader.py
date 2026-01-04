import requests
import os
from tqdm import tqdm

from . import config


def search_tracker(query: str):
    """Queries the tracker and returns a list of files."""
    try:
        response = requests.get(
            f"{config.TRACKER_SERVER_URL}/search", params={"q": query}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Tracker error: {e}")
        return []


def download_from_peer(
    download_url: str,
    timeout: int,
    filename: str,
    filesize: int,
    destination: str,
    method_name: str,
    save_path: str,
):
    try:
        # Stream the download so we don't crash RAM on big files
        with requests.get(
            download_url, params={"name": filename}, stream=True, timeout=timeout
        ) as r:
            r.raise_for_status()
            print(f"Connected via {method_name}!")

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

        print(f"Download Complete! Saved to: {save_path}")
        return True

    except Exception as e:
        print(f"Error during {method_name}: {e}")

    return False


def download_file_strategy(
    peer_data: dict, filename: str, filesize: int, destination: str
):
    """Tries local tranfer first, if fails switches to public url"""

    candidates = []

    local_url = f"http://{peer_data['ip_address']}:{peer_data['port']}"
    candidates.append((local_url, "Local LAN"))

    print(peer_data)
    if peer_data.get("public_url"):
        public_url = peer_data["public_url"]
        if not public_url.startswith("http"):
            public_url = f"http://{public_url}"
        candidates.append((public_url, "Public Tunnel"))

    save_path = os.path.join(destination, filename)
    # Ensure download directory exists
    if not os.path.exists(destination):
        os.makedirs(destination)

    for base_url, method_name in candidates:
        print(f"Trying {method_name} connection ({base_url})...")
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
    print("All connection methods failed.")
    return False
