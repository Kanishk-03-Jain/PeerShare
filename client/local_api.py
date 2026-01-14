from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import threading
import time
from typing import Optional

from client_app.core import PeerShareClient, AuthenticationError
from client_app import downloader, config, schemas

# Logging is configured in client_app.core, but we ensure it here too just in case
handlers = [
    logging.StreamHandler(),
    logging.FileHandler("client.log"),
]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers,
    force=True
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client_service: Optional[PeerShareClient] = None
client_thread: Optional[threading.Thread] = None
stop_event = threading.Event()


@app.get("/")
async def root():
    return {"message": "This is the client server"}


@app.post("/api/signup")
async def signup(payload: dict):
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
        await login(payload=payload)
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
async def login(payload: dict):
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
        client_service = PeerShareClient(username, password)
        user_data = client_service.login()
        client_service.initialize()

        # Start P2P Server and Heartbeat in background
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

        return {"status": "success", "user": user_data}

    except AuthenticationError as e:
        client_service = None
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        client_service = None
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
async def logout():
    global client_service, stop_event, client_thread

    if client_service is None:
        return {"status": "ignored", "message": "Not logged in"}

    stop_event.set()

    # Gracefully stop the P2P server to release the port
    if client_service and client_service.server:
        client_service.server.stop()

    # We don't join/wait here to avoid blocking api, but thread will die soon.

    client_service = None
    return {"status": "success", "message": "Logged out and server stopped"}


@app.get("/api/status")
async def get_status():
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
async def get_config():
    """Return current configuration"""
    return {
        "tracker_server_url": config.settings.TRACKER_SERVER_URL,
        "port": config.settings.PORT,
        "shared_folder": config.settings.SHARED_FOLDER,
        "download_folder": config.settings.DOWNLOAD_FOLDER,
        "ngrok_configured": config.settings.NGROK_TOKEN,
    }


@app.post("/api/config")
async def update_config(payload: dict):
    """
    Update configuration settings.
    Payload can contain: port, shared_folder, download_folder, ngrok_authtoken
    """
    print("payload: ", payload)
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
async def search(q: str):
    results = downloader.search_tracker(q)
    return results


@app.post("/api/download")
async def trigger_download(file_info: dict, background_tasks: BackgroundTasks):
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
