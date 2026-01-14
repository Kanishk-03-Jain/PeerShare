from fastapi import FastAPI, Request, Depends, HTTPException, status
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List, Tuple
from typing import Annotated
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from . import database, models, schemas, crud, auth

import asyncio
import httpx
from .database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def cleanup_task():
    """Background task to remove inactive peers periodically"""
    while True:
        try:
            db = SessionLocal()
            crud.remove_inactive_peers(db)
            db.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        await asyncio.sleep(60)  # Run every 60 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist
    try:
        database.Base.metadata.create_all(bind=database.engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Start background task
    task = asyncio.create_task(cleanup_task())
    yield
    # Cancel background task on shutdown
    task.cancel()


app = FastAPI(lifespan=lifespan)
load_dotenv()


@app.get("/")
async def root():
    return {"message": "Hello! This is root for PeerShare server"}


@app.post(
    "/signup", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED
)
async def signup(user_data: schemas.UserSignup, db: Session = Depends(database.get_db)):
    existing_user = crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if user_data.email:
        existing_email = crud.get_user_by_email(db, email=user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    password_hash = auth.get_password_hash(user_data.password)
    user_create = schemas.UserCreate(
        username=user_data.username, password_hash=password_hash, email=user_data.email
    )

    user = crud.create_user(db, user_create)

    access_token = auth.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserResponse(
            user_id=user.user_id, username=user.username, email=user.email
        ),
        "status": "success",
    }


@app.post("/login", response_model=schemas.TokenResponse)
async def login(credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    """Login and get access token"""
    user = crud.get_user_by_username(db, credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token({"sub": credentials.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserResponse(
            user_id=user.user_id, username=user.username, email=user.email
        ),
    }


@app.post("/announce")
async def announce_files(
    payload: schemas.FileAnnounce,  # handles JSON body
    request: Request,  # gets IP address of the client
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Clients announces the files they have to the server"""

    # Authorization Check
    if payload.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to announce for this user",
        )

    # Determining the IP of the client
    client_ip = payload.ip_address or (
        request.client.host if request.client else "unknown"
    )
    logger.info(f"User {payload.user_id} is online at {client_ip}:{payload.port}")

    # announce the files to the server and update db
    count = crud.upsert_file_announcement(db, payload, client_ip)

    return {"status": "success", "announced": count}


@app.post("/ping")
async def peer_ping(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """used to know if the user is active or not"""

    # Update the last hartbeat of the user if still active
    rows = crud.update_last_heartbeat(db, current_user.user_id)

    if rows == 0:
        return {
            "status": "warning",
            "message": "No active sessions found for this user",
        }

    return {"status": "success"}


@app.get("/search", response_model=List[schemas.SearchResult])
async def search_files(q: str, db: Session = Depends(database.get_db)):
    """search for the files"""

    # Search database for the required files
    results: List[Tuple[models.File, models.ActivePeer, models.User]] = (
        crud.search_files(db, q)
    )

    grouped_files = {}

    for file_obj, peer_obj, user_obj in results:
        if file_obj.file_hash not in grouped_files:
            grouped_files[file_obj.file_hash] = {
                "file_name": file_obj.file_name,
                "file_hash": file_obj.file_hash,
                "file_size": file_obj.file_size,
                "peers": [],
            }

        grouped_files[file_obj.file_hash]["peers"].append(
            {
                "user_id": peer_obj.user_id,
                "ip_address": peer_obj.ip_address,
                "port": peer_obj.port,
                "public_url": peer_obj.public_url,
                "username": user_obj.username,
                "last_heartbeat": peer_obj.last_heartbeat,
            }
        )

    return list(grouped_files.values())


@app.get("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db),
) -> schemas.Token:
    user = auth.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
):
    return current_user
