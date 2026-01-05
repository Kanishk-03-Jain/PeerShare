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

You can set up the system in two ways: a **Full Local Setup** (recommended for development) or a **Quick Start** (for immediate testing).

### 1. Full Local Setup (Backend + Client)
To run the complete system entirely on your own infrastructure, you need to set up both the tracker (backend) and the file-sharing application (client).

* **Step 1: Backend Setup**
    The backend allows peers to discover each other and log in.
    👉 **[Read the Backend Guide](./backend/README.md)**

* **Step 2: Client Setup**
    Once the backend is running, set up the client to connect to your local instance.
    👉 **[Read the Client Guide](./client/README.md)**

---

### 2. Quick Start (Client Only)
If you want to try the file-sharing functionality immediately without hosting your own server, you can use our public testing tracker.

1.  Follow the **[Client Setup Guide](./client/README.md)**.
2.  The client is pre-configured to use the public tracker by default.

> **⚠️ Important Notice:** The public tracker is provided strictly for functionality testing. Please do not attempt DDoS attacks, stress testing, or spamming on this server. For production use or heavy load testing, please host your own backend.

## Features

-   **P2P File Transfer**: Direct file sharing between users without storing files on a central server.
-   **User Accounts**: Secure signup and login.
-   **Search**: Find files shared by other users on the network.
-   **Local Management**: Configure your shared folders and download locations.
-   **Real-time Status**: See who is online and what they are sharing.