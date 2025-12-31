import os
import hashlib
import requests
import sys

# CONFIGURATION
SERVER_URL = "http://127.0.0.1:8000"
MY_FOLDER = "./shared_folder"  # Create this folder and put some dummy PDF/TXT files in it
USER_ID = 1  # Matches the ID in your database
MY_PORT = 6000 # The port we WILL serve files on later

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
        scan_and_announce()
