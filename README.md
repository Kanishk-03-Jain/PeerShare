# PeerShare

PeerShare is a Peer-to-Peer (P2P) file sharing application designed to allow users to easily share notes and files directly with each other. It uses a central tracker server to discover peers and files, while the actual file transfer happens directly between clients.

## Architecture

The project consists of two main components:

1.  **Backend (Tracker Server)**: A centralized server that acts as a directory.
    -   Manages user authentication.
    -   Indexes files available on the network.
    -   Tracks active peers (users currently online).
    -   **Tech Stack**: Python (FastAPI), PostgreSQL, SQLAlchemy.

2.  **Client**: The application that users run on their machines.
    -   **Local API**: A lightweight Python server that runs locally to handle P2P networking, file management, and communication with the Tracker Server.
    -   **Web UI**: A modern web interface built with Next.js that users interact with. It communicates with the Local API.
    -   **Tech Stack**: Python (FastAPI), Next.js (React), Tailwind CSS.

## Getting Started

To run the full system locally, you will need to set up both the backend (tracker) and the client.

### 1. Backend Setup
The backend is required for the client to log in and find other peers.
👉 **[Read the Backend Guide](./backend/README.md)**

### 2. Client Setup
The client is the actual application you use to share files.
👉 **[Read the Client Guide](./client/README.md)**

## Features

-   **P2P File Transfer**: Direct file sharing between users without storing files on a central server.
-   **User Accounts**: Secure signup and login.
-   **Search**: Find files shared by other users on the network.
-   **Local Management**: Configure your shared folders and download locations.
-   **Real-time Status**: See who is online and what they are sharing.