# Share Notes - Backend (Tracker Server)

The Backend acts as the "Tracker" for the Share Notes P2P network. It stores user information and an index of available files, allowing clients to find each other.

## Features
-   User Authentication (JWT).
-   File Indexing & Search.
-   Peer Discovery (Who has which file?).
-   Heartbeat system to track active peers.

## Tech Stack
-   **Framework**: FastAPI
-   **Database**: PostgreSQL
-   **ORM**: SQLAlchemy
-   **Auth**: OAuth2 with Password (Bearer token)

## Prerequisites
-   Python 3.10+
-   PostgreSQL installed and running.

## Installation

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a `.env` file in the `backend` directory.
2.  Add the following environment variables:

    ```env
    # Database Connection
    SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost/share_notes_db
    
    # Security
    SECRET_KEY=your_super_secret_key_here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

    *Note: Replace `user`, `password`, and `share_notes_db` with your actual PostgreSQL credentials.*

## Running the Server

Start the development server:

```bash
fastapi dev app/main.py
```

Or using Uvicorn directly:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

> **Important**: If you are running the Client and Backend on the same machine, you **must** run the Backend on a different port (e.g., 8002) because the Client uses port 8000.
>
> ```bash
> uvicorn app.main:app --reload --port 8002 
> ```

## API Documentation
Once the server is running, you can view the interactive API docs at:
-   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (or 8002)
-   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
