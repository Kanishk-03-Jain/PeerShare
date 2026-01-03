from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import List, Tuple

from . import database, models, schemas, crud

app = FastAPI()
load_dotenv()

@app.get("/")
async def root():
    return {"message": "Hello! This is root for share-notes server"}

@app.get("/user/{username}")
async def get_user_id(
    username: str,
    db: Session = Depends(database.get_db)
):
    """get userid from username"""
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"user_id": user.user_id}


@app.post("/announce")
async def announce_files(
    payload: schemas.FileAnnounce,  # handles JSON body
    request: Request,   # gets IP address of the client
    db: Session = Depends(database.get_db)
):
    """Clients announces the files they have to the server"""

    # Validate if the user exits
    user = crud.get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Determining the IP of the client
    client_ip = payload.ip_address if payload.ip_address else request.client.host
    print(f"User {payload.user_id} is online at {client_ip}:{payload.port}")

    # announce the files to the server and update db
    count = crud.upsert_file_announcement(db, payload, client_ip)

    return { "status": "success", "announced": count}
        

@app.post("/ping/{user_id}")
async def peer_ping(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """used to know if the user is active or not"""

    # Update the last hartbeat of the user if still active
    rows = crud.update_last_heartbeat(db, user_id)

    if rows == 0:
        return {"status": "warning", "message": "No active sessions found for this user"}

    return {"status": "success"}

@app.get("/search", response_model=List[schemas.SearchResult])
async def search_files(
    q: str,
    db: Session = Depends(database.get_db)
):
    """search for the files"""

    # Remove ghost entries in db
    crud.remove_inactive_peers(db)

    # Search database for the required files
    results: List[Tuple[models.File, models.ActivePeer, models.User]] = crud.search_files(db, q)
    
    grouped_files = {}

    for file_obj, peer_obj, user_obj in results:
        if file_obj.file_hash not in grouped_files:
            grouped_files[file_obj.file_hash] = {
                "file_name": file_obj.file_name,
                "file_hash": file_obj.file_hash,
                "file_size": file_obj.file_size,
                "peers": []
            }

        grouped_files[file_obj.file_hash]["peers"].append({
            "user_id": peer_obj.user_id,
            "ip_address": peer_obj.ip_address,
            "port": peer_obj.port,
            "username": user_obj.username,
            "last_heartbeat": peer_obj.last_heartbeat 
        })

    return list(grouped_files.values())