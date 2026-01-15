import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# --- Token / Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


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


class UserLogin(BaseModel):
    """Schema for user login"""

    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password_hash: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


# --- File Schemas ---
class FileBase(BaseModel):
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., ge=0, le=10**12)

    @field_validator("file_hash")
    def validate_hash(cls, v: str):
        if not re.match(r"^[0-9a-fA-F]{64}$", v, re.IGNORECASE):
            raise ValueError("Invalid SHA-256 hash")
        return v.lower()

    @field_validator("file_name")
    def validate_filename(cls, v: str):
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename")
        return v


class FileAnnounce(BaseModel):
    """What the client sends to say 'I have this file'"""

    user_id: int
    port: int  # port on which client is listening on
    ip_address: str | None = None
    public_url: str | None = None  # Ngrok url
    files: List[FileBase]


# --- Search Result Schemas ---
class PeerInfo(BaseModel):
    """Returns who has the file"""

    user_id: int
    ip_address: str
    port: int
    public_url: str | None = None
    username: str
    last_heartbeat: datetime


class SearchResult(BaseModel):
    file_hash: str
    file_name: str
    file_size: int
    peers: List[PeerInfo]  # list on peers who have the file


class PeerPing(BaseModel):
    """Schema for peer ping"""

    ip_address: str | None = None
    port: int
