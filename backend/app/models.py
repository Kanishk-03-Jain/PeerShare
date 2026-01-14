from sqlalchemy import (
    Integer,
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from .database import Base
from typing import List
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship to peers (One user can be active on multiple devices/files)
    active_peers: Mapped[List["ActivePeer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"

    file_hash: Mapped[str] = mapped_column(
        String(64), primary_key=True, index=True
    )  # SHA-256
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    peer_holding: Mapped[List["ActivePeer"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "file_size >= 0", name="ck_file_size_non_negative"
        ),
    )


class ActivePeer(Base):
    __tablename__ = "active_peers"

    peer_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("files.file_hash"), nullable=False
    )

    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False
    )  # Stores IPv4 or IPv6
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    public_url: Mapped[str] = mapped_column(String, nullable=True)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    # Relationships
    user: Mapped[List["User"]] = relationship(back_populates="active_peers")
    file: Mapped[List["File"]] = relationship(back_populates="peer_holding")

    # Constraint: A user can't be listed twice for the same file
    __table_args__ = (
        UniqueConstraint(
            "user_id", "file_hash", name="active_peers_user_id_file_hash_key"
        ),
    )
