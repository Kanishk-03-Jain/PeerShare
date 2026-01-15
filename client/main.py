import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import requests
from client_app import config, downloader, schemas
from client_app.core import AuthenticationError, PeerShareClient
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Logging is configured in client_app.core, but we ensure it here too just in case
handlers = [
    logging.StreamHandler(),
    logging.FileHandler("client.log"),
]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers,
    force=True,
)
logger = logging.getLogger(__name__)


client_service: Optional[PeerShareClient] = None
client_thread: Optional[threading.Thread] = None
stop_event = threading.Event()


def start_background_service():
    # Start P2P Server and Heartbeat in background
    global client_service, client_service, stop_event
    stop_event.clear()

    def run_client_background():
        logger.info("Starting background P2P service...")
        # Initial announce
        try:
            if client_service:
                client_service.announce_files()
        except Exception as e:
            logger.error(f"Failed to announce files: {e}")

        while not stop_event.is_set():
            try:
                if client_service:
                    client_service.send_heartbeat()
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")

            # Sleep in small chunks to allow quick shutdown
            for _ in range(30):
                if stop_event.is_set():
                    break
                time.sleep(1)

        logger.info("Background P2P service stopped.")

    client_thread = threading.Thread(target=run_client_background, daemon=True)
    client_thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client_service

    try:
        saved_token = config.settings.JWT_TOKEN
        saved_username = config.settings.USERNAME
        saved_user_id = config.settings.USER_ID

        if saved_token and saved_username and saved_user_id != -1:
            logger.info(f"Restoring session of user: {saved_username}")

            client_service = PeerShareClient(
                user_id=saved_user_id, username=saved_username, jwt_token=saved_token
            )

            client_service.initialize()
            start_background_service()

            logger.info("Session restored successfully")
    except Exception as e:
        logger.error(f"Failed to restore session: {e}")
        client_service = None
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "This is the client server"}


@app.post("/api/signup")
def signup(payload: dict):
    try:
        url = f"{config.settings.TRACKER_SERVER_URL}/signup"
        resp = requests.post(url, json=payload)

        if resp.status_code == 400:
            raise HTTPException(
                status_code=400, detail="Username or email already exists"
            )

        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Successfully signed up as {data.get('user', {}).get('username')}")
        logger.info(f"logging in with the same credentials")
        login(payload=payload)
        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            detail = e.response.json()
            raise HTTPException(status_code=422, detail=detail)
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@app.post("/api/auth/login")
def login(payload: dict):
    """
    Logs in the user and starts the P2P server in a background thread.
    """
    global client_service, client_thread, stop_event

    if client_service is not None:
        return {
            "message": "Already logged in",
            "user": {
                "username": client_service.username,
                "user_id": client_service.user_id,
            },
        }

    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    # Initialize client
    try:
        client_service = PeerShareClient(username=username, password=password)
        user_data = client_service.login()
        client_service.initialize()

        start_background_service()

        return {"status": "success", "user": user_data}

    except AuthenticationError as e:
        client_service = None
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        client_service = None
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
def logout():
    global client_service, stop_event, client_thread

    if client_service is None:
        return {"status": "ignored", "message": "Not logged in"}

    stop_event.set()

    # Gracefully stop the P2P server to release the port
    if client_service and client_service.server:
        client_service.server.stop()

    # We don't join/wait here to avoid blocking api, but thread will die soon.

    client_service = None
    config.settings.set("jwt_token", "")
    config.settings.set("username", "")
    config.settings.set("user_id", -1)
    return {"status": "success", "message": "Logged out and server stopped"}


@app.get("/api/status")
def get_status():
    """Returns the current status of the client."""
    if client_service is None:
        return {"online": False, "status": "Offline"}

    return {
        "online": True,
        "username": client_service.username,
        "user_id": client_service.user_id,
        "port": client_service.port,
        "shared_folder": client_service.folder,
        "local_ip": client_service.local_ip,
    }


# --- Configuration Endpoints ---


@app.get("/api/config")
def get_config():
    """Return current configuration"""
    return {
        "tracker_server_url": config.settings.TRACKER_SERVER_URL,
        "port": config.settings.PORT,
        "shared_folder": config.settings.SHARED_FOLDER,
        "download_folder": config.settings.DOWNLOAD_FOLDER,
        "ngrok_configured": config.settings.NGROK_TOKEN,
        "jwt_token": config.settings.JWT_TOKEN,
        "username": config.settings.USERNAME,
        "user_id": config.settings.USER_ID,
    }


@app.post("/api/config")
def update_config(payload: dict):
    """
    Update configuration settings.
    Payload can contain: port, shared_folder, download_folder, ngrok_authtoken
    """
    allowed_keys = [
        "tracker_server_url",
        "port",
        "shared_folder",
        "download_folder",
        "ngrok_authtoken",
    ]
    try:
        updated_keys = []
        for key in allowed_keys:
            if key in payload:
                # Optional: Check if value actually changed to avoid unnecessary re-announce
                current_val = config.settings.get(key)
                new_val = payload[key]

                if str(current_val) != str(new_val):
                    config.settings.set(key, new_val)
                    logger.info(f"updated: {key} -> {new_val}")
                    updated_keys.append(key)

        if len(updated_keys) > 0:
            count = 0
            if client_service:
                # Synchronous update - blocks until re-announced
                count = client_service.update_configuration(updated_keys)
            return {
                "status": "success",
                "message": f"Configuration updated. Services restarted. Announced {count} files.",
            }
        else:
            return {
                "status": "ignored",
                "message": "No valid keys found or no changes detected",
            }

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {e}")


# --- File Management ----


@app.get("/api/search")
def search(q: str):
    results = downloader.search_tracker(q)
    return results


@app.post("/api/download")
def trigger_download(file_info: dict, background_tasks: BackgroundTasks):
    if client_service is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    try:
        search_result = schemas.SearchResult(**file_info)
        background_tasks.add_task(
            downloader.download_file_strategy,
            file_data=search_result,
            destination=str(config.settings.DOWNLOAD_FOLDER),  # Use config setting
        )
        return {"status": "Download started", "file": search_result.file_name}
    except Exception as e:
        logger.error(f"Download trigger failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid file info: {e}")
