from . import downloader, config

def run_cli():
    print("\n--- ShareNotes Downloader ---")
    query = input("Enter filename to search: ").strip()
    if not query:
        print("Empty query.")
        return
    
    results = downloader.search_tracker(query)

    if not results:
        print("No files found.")
        return
    
    # Display Results
    print(f"\nFound {len(results)} files:")
    for i, file in enumerate(results):
        print(f"{i+1}. {file['file_name']} ({file['file_size']} bytes)")
        print(f"   --> Available from {len(file['peers'])} peer(s)")

    # User Selects File
    try:
        choice = int(input("\nSelect a file number to download: ")) - 1
        if choice < 0 or choice >= len(results):
            raise ValueError
        selected_file = results[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return
    
    peer = selected_file['peers'][0]

    print(f"\nConnecting to Peer '{peer['username']}' at {peer['ip_address']}...")

    # 5. Trigger Download
    downloader.download_file_strategy(
        peer_data=peer,
        filename=selected_file['file_name'],
        filesize=selected_file['file_size'],
        destination=str(config.DOWNLOAD_FOLDER)
    )