from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv
from datetime import datetime, UTC, timezone

from . import database, models, schemas

app = FastAPI()
load_dotenv()

@app.get("/")
async def root():
    return {"message": "Hello! This is root for share-notes server"}

@app.post("/announce")
async def announce_files(
    payload: schemas.FileAnnounce,  # handles JSON body
    request: Request,   # gets IP address of the client
    db: Session = Depends(database.get_db)
):

    client_ip = request.client.host

    print(f"User {payload.user_id} is online at {client_ip}:{payload.port}")

    # Validate if the user exits
    user = db.scalar(select(models.User).where(models.User.user_id == payload.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for file in payload.files:
        # insert file if not exits
        file_stmt = insert(models.File).values(
            file_hash=file.file_hash,
            file_name=file.file_name,
            file_size=file.file_size
        ).on_conflict_do_nothing(
            index_elements=['file_hash']
        )
        db.execute(file_stmt)

        # upsert ActivePeers
        peer_stmt = insert(models.ActivePeer).values(
            user_id=payload.user_id,
            file_hash=file.file_hash,
            ip_address=client_ip,
            port=payload.port,
            last_heartbeat=datetime.now(timezone.utc)
        ).on_conflict_do_update(
            constraint='active_peers_user_id_file_hash_key',
            set_={ "last_heartbeat": datetime.now(timezone.utc)}
        )
        db.execute(peer_stmt)
    db.commit()
    return { "status": "success", "announced": len(payload.files)}
        

@app.post("/ping/{user_id}")
async def peer_ping(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    stmt = (
        update(models.ActivePeer)
        .where(models.ActivePeer.user_id == user_id)
        .values(last_heartbeat=datetime.now(timezone.utc))
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        return {"status": "warning", "message": "No active sessions found for this user"}

    return {"status": "success"}

