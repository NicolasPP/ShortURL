import enum
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

COMMON_TABLE_ARGS: dict[str, str] = dict(schema="short_url")


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        # TODO: fix this mess
        columns: list[str] = []
        for col in self.__table__.columns:
            columns += f"{col.name}={getattr(self, col.name)!r}"

        return f"<{self.__class__.__name__}({''.join(columns)})>"


class SurlStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RECLAIMED = "RECLAIMED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = dict().update(COMMON_TABLE_ARGS)

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
    __table_args__ = dict().update(COMMON_TABLE_ARGS)

    url_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True
    )
    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )

    surls: Mapped[List["Surl"]] = relationship("Surl", back_populates="url")


class Surl(Base):
    __tablename__ = "surl"
    __table_args__ = dict(

    ).update(COMMON_TABLE_ARGS)

    surl: Mapped[str] = mapped_column(
        String(7),
        primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    url_hash: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("url.url_hash", ondelete="RESTRICT"),
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

    user: Mapped["User"] = relationship("User", back_populates="surls")
    url: Mapped["Url"] = relationship("Url", back_populates="surls")


class Click(Base):
    __tablename__ = "clicks"
    __table_args__ = (
        Index("click_rate", "surl", "clicked_at"),
        COMMON_TABLE_ARGS
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    surl: Mapped[str] = mapped_column(
        String(7),
        ForeignKey("surl.surl", ondelete="CASCADE"),
        nullable=False
    )

    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )


