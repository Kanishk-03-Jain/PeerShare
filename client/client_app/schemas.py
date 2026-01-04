from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import re

# --- Shared Models (Mirroring Backend) ---

class UserSignup(BaseModel):
    """Schema for user registration"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    def validate_username(cls, v: str):
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username must be alphanumeric or contain underscores")
        return v.lower()


class User(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class FileBase(BaseModel):
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)

    @field_validator("file_hash")
    def validate_hash(cls, v: str):
         if not re.match(r"^[0-9a-fA-F]{64}$", v, re.IGNORECASE):
            raise ValueError("Invalid SHA-256 hash")
         return v.lower()

class FileAnnounce(BaseModel):
    user_id: int
    port: int
    ip_address: Optional[str] = None
    public_url: Optional[str] = None
    files: List[FileBase]

# --- Search Models ---

class PeerInfo(BaseModel):
    user_id: int
    ip_address: str
    port: int
    public_url: Optional[str] = None
    username: str
    last_heartbeat: datetime

class SearchResult(BaseModel):
    file_hash: str
    file_name: str
    file_size: int
    peers: List[PeerInfo]
