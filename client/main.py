import argparse
import sys
from client_app.core import ShareNotesClient
from client_app.config import DEFAULT_PORT, DEFAULT_FOLDER

def main():
    parser = argparse.ArgumentParser(description="ShareNotes p2p client")
    parser.add_argument("--uname", type=int, help="Your Username")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--folder", type=str, default=DEFAULT_FOLDER, help="Folder to share")

    args = parser.parse_args()

    username = args.uname
    if not username:
        try:
            username = input("Enter your User Name: ")
        except ValueError:
            print("Error: User ID must be a number.")
            sys.exit(1)
    port = args.port
    client = ShareNotesClient(username=username, port=port, folder=args.folder)
    client.run_forever()

if __name__ == "__main__":
    main()