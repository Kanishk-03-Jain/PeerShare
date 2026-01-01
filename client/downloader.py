import requests
import os

from client_app import config
TRACKER_URL = config.TRACKER_SERVER_URL
DOWNLOAD_DIR = "./downloads"

def search_and_download():
    query = input("Enter filename to search: ").strip()
    if not query:
        print("Empty query.")
        return
    
    try:
        response = requests.get(f"{TRACKER_URL}/search", params={"q": query})
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"❌ Tracker error: {e}")
        return

    if not results:
        print("No files found.")
        return
    
    # 3. Display Results
    print(f"\nFound {len(results)} files:")
    for i, file in enumerate(results):
        print(f"{i+1}. {file['file_name']} ({file['file_size']} bytes)")
        print(f"   --> Available from {len(file['peers'])} peer(s)")

    # 4. User Selects File
    try:
        choice = int(input("\nSelect a file number to download: ")) - 1
        selected_file = results[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return
    
    peer = selected_file['peers'][0]
    peer_ip = peer['ip_address']
    peer_port = peer['port']
    filename = selected_file['file_name']

    print(f"\n⚡ Connecting to Peer {peer['username']} at {peer_ip}:{peer_port}...")

    # 6. Download from Peer (P2P Transfer)
    download_url = f"http://{peer_ip}:{peer_port}/download"

    try:
        # Stream the download so we don't crash RAM on big files
        with requests.get(download_url, params={"name": filename}, stream=True) as r:
            r.raise_for_status()
            
            # Ensure download directory exists
            if not os.path.exists(DOWNLOAD_DIR):
                os.makedirs(DOWNLOAD_DIR)
            
            save_path = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        print(f"✅ Download Complete! Saved to: {save_path}")
        
    except Exception as e:
        print(f"❌ P2P Download Failed: {e}")
        print("The peer might be offline or blocked by a firewall.")

if __name__ == "__main__":
    search_and_download()