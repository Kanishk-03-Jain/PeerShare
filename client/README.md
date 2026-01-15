# PeerShare - Client

The Client is the user-facing application for PeerShare. It uses a **hybrid architecture** combining a local Python backend for robust networking with a modern Next.js frontend for the UI.

## Architecture

1.  **Local API (Python)**: Runs on your machine. Handles the P2P protocols, file serving, and communicates with the central Tracker Server.
2.  **Web UI (Next.js)**: A website running locally (localhost:3000) that acts as the control panel for the Local API.

## Prerequisites
-   Python 3.10+
-   Node.js (LTS recommended) or Bun.

## Setup Instructions

You need to run **both** the Local API and the Web UI for the client to work.

### Quick Start (Recommended)

You can run both the Local API and the Web UI with a single script:

1.  **Navigate to the client directory:**
    ```bash
    cd client
    ```

2.  **Make the script executable (first time only):**
    ```bash
    chmod +x run_app.sh
    ```

3.  **Run the application:**
    ```bash
    ./run_app.sh
    ```

### Manual Setup
If you prefer to run them manually:

#### Part 1: Start the Local API

The Local API must be running for the Web UI to function.

1.  **Navigate to the client directory:**
    ```bash
    cd client
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Local API:**

    ```bash
    fastapi dev main.py
    ```

    Or using Uvicorn directly:

    ```bash
    uvicorn main:app --reload
    ```
    *The Local API will start on `http://127.0.0.1:8000` (default).*

#### Part 2: Start the Web UI

1.  **Open a new terminal and navigate to the web_ui directory:**
    ```bash
    cd client/web_ui
    ```

2.  **Install Node dependencies:**
    ```bash
    npm install
    # or if you use bun
    bun install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    # or
    bun dev
    ```

4.  **Open the App:**
    Go to [http://localhost:3000](http://localhost:3000) in your browser.

## Configuration

In the Web UI, go to the **Settings** page to configure:

-   **Tracker Server URL**: The URL of the Tracker Server. default: `https://share-notes-fh45.onrender.com`
-   **Port**: The port on which the peer will be connected. default: `8001`
-   **Shared Folder**: The folder containing files you want to share with others.
-   **Download Folder**: Where files from others will be saved.

### Troubleshooting

-   **Port Conflicts**: The Client Local API **must** run on port `8000` because the Web UI is configured to talk to it there. If you have port conflicts, free up port 8000.

-   **Connection Error**: If the Web UI says "Offline", make sure the `main.py` script is running in the background.
