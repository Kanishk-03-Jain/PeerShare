from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Token / Auth Schemas ---
class UserCreate(BaseModel):
    username: str
    password_hash: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    user_id: int
    username: str
    class Config:
        from_attributes = True

# --- File Schemas ---
class FileBase(BaseModel):
    file_hash: str
    file_name: str
    file_size: int

class FileAnnounce(BaseModel):
    """What the client sends to say 'I have this file'"""
    user_id: int
    port: int   # port on which client is listening on
    ip_address: str | None = None

    files: List[FileBase]

# --- Search Result Schemas ---
class PeerInfo(BaseModel):
    """Returns who has the file"""
    ip_address: str
    port: int
    username: str
    last_heartbeat: datetime

class SearchResult(BaseModel):
    file_hash: str
    file_name: str
    file_size: int
    peers: List[PeerInfo] # list on peers who have the file    