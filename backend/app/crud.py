from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone, timedelta

from . import models, schemas

def get_user_by_username(db: Session, username: str):
    return db.scalar(select(models.User).where(models.User.username == username))

def get_user(db: Session, user_id: int):
    return db.scalar(select(models.User).where(models.User.user_id == user_id))

def upsert_file_announcement(db: Session, payload: schemas.FileAnnounce, client_ip: str):
    """Handles adding files and updating active peer status"""
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
            public_url=payload.public_url,
            last_heartbeat=datetime.now(timezone.utc)
        ).on_conflict_do_update(
            constraint='active_peers_user_id_file_hash_key',
            set_={ 
                    "last_heartbeat": datetime.now(timezone.utc),
                    "ip_address": client_ip,
                    "port": payload.port,
                    "public_url": payload.public_url
                }
        )
        db.execute(peer_stmt)
    db.commit()
    return len(payload.files)


def update_last_heartbeat(db: Session, user_id: int):
    stmt = (
        update(models.ActivePeer)
        .where(models.ActivePeer.user_id == user_id)
        .values(last_heartbeat=datetime.now(timezone.utc))
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def search_files(db: Session, query: str):
    stmt = (
        select(models.File, models.ActivePeer, models.User)
        .join(models.ActivePeer, models.File.file_hash == models.ActivePeer.file_hash)
        .join(models.User, models.ActivePeer.user_id == models.User.user_id)
        .where(models.File.file_name.ilike(f"%{query}%"))
    )
    return db.execute(stmt).all()

def remove_inactive_peers(db: Session, threshold_seconds: int = 60):
    """Delete the ghost entries in table"""

    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)

    stmt = delete(models.ActivePeer).where(models.ActivePeer.last_heartbeat < cutoff_time)

    result = db.execute(stmt)
    db.commit()
    return result.rowcount