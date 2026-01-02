from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to peers (One user can be active on multiple devices/files)
    active_peers = relationship("ActivePeer", back_populates="user", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"

    file_hash = Column(String(64), primary_key=True, index=True) # SHA-256
    file_name = Column(String(255), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    #Relationship
    peer_holding = relationship("ActivePeer", back_populates="file", cascade="all, delete-orphan")

class ActivePeer(Base):
    __tablename__ = "active_peers"

    peer_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    file_hash = Column(String(64), ForeignKey("files.file_hash"), nullable=False)

    ip_address = Column(String(45), nullable=False) # Stores IPv4 or IPv6
    port = Column(Integer, nullable=False)
    public_url = Column(String, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="active_peers")
    file = relationship("File", back_populates="peer_holding")

    # Constraint: A user can't be listed twice for the same file
    __table_args__ = (UniqueConstraint('user_id', 'file_hash', name='active_peers_user_id_file_hash_key'),)