import enum
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SurlStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RECLAIMED = "RECLAIMED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    surls: Mapped[List["Surl"]] = relationship(
        "Surl",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Url(Base):
    __tablename__ = "url"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )

    surls: Mapped[List["Surl"]] = relationship(
        "Surl",
        back_populates="url"
    )


class Surl(Base):
    __tablename__ = "surl"

    surl: Mapped[str] = mapped_column(
        String(7),
        primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    url_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("url.id", ondelete="RESTRICT"),
        nullable=False
    )
    status: Mapped[SurlStatus] = mapped_column(
        Enum(SurlStatus, name="surl_status"),
        default=SurlStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="surls"
    )
    url: Mapped["Url"] = relationship(
        "Url",
        back_populates="surls"
    )
