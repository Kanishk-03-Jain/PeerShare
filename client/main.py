import argparse
import sys
from client_app.core import ShareNotesClient
from client_app.config import DEFAULT_PORT, DEFAULT_FOLDER, TRACKER_SERVER_URL
import getpass
import requests


def signup():
    """Register a new user"""
    print("Signing up...")
    username = input("Enter your User Name: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)
    email = input("Enter your Email (optional): ").strip()
    password = getpass.getpass("Enter your Password: ")
    if not password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    try:
        url = f"{TRACKER_SERVER_URL}/signup"
        payload = {"username": username, "email": email, "password": password}
        resp = requests.post(url, json=payload)

        if resp.status_code == 400:
            print("Error: Username already exists")
            sys.exit(1)

        resp.raise_for_status()
        data = resp.json()
        print(f"Successfully signed up as {data['user']['username']}")
        return data
    except requests.exceptions.HTTPError as e:
        # 422 errors return a JSON body explaining exactly what went wrong
        if e.response.status_code == 422:
            print("Validation Error:", e.response.json())
        else:
            print(f"HTTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Signup failed: {e}")
        sys.exit(1)


def main():
    newuser = input("want to register (y/r)")
    if newuser == "y":
        data = signup()
    username = input("Enter username: ")
    password = input("enter password: ")
    client = ShareNotesClient(username=username, password=password)
    client.run_forever()


if __name__ == "__main__":
    main()
