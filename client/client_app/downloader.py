import requests
import os
from tqdm import tqdm

from . import config

def search_tracker(query: str):
    """Queries the tracker and returns a list of files."""
    try:
        response = requests.get(f"{config.TRACKER_SERVER_URL}/search", params={"q": query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Tracker error: {e}")
        return []

def download_from_peer(ip: str, port: int, filename: str, file_size: int, destination: str):
    """Downloads a file from a peer with a progress bar."""
    download_url = f"http://{ip}:{port}/download"
    save_path = os.path.join(destination, filename)

    # Ensure download directory exists
    if not os.path.exists(destination):
        os.makedirs(destination)

    try:
        # Stream the download so we don't crash RAM on big files
        with requests.get(download_url, params={"name": filename}, stream=True, timeout=10) as r:
            r.raise_for_status()
            
            # Ensure download directory exists
            if not os.path.exists(destination):
                os.makedirs(destination)
            
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as progress_bar:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress_bar.update(len(chunk))
                    
        print(f"Download Complete! Saved to: {save_path}")
        return True
        
    except requests.exceptions.Timeout:
        print("\nError: Connection timed out. The peer might be behind a firewall.")
    except Exception as e:
        print(f"\nDownload Failed: {e}")
    
    return False

