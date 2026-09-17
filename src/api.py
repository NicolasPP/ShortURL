import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from config_manager import ConfigManager
from database_manager import DatabaseManager
from models import Surl, SurlStatus, Url, User
from surl_generator import generate_surl

type DatabaseSession = Annotated[AsyncSession, Depends(database_manager.get_session)]
CONFIG_FILE: str = "config.ini"

ConfigManager.get().load(CONFIG_FILE)
router: APIRouter = APIRouter()
surl_generator: Iterator[str] = generate_surl()
database_manager: DatabaseManager = DatabaseManager()


class CreateUserRequest(BaseModel):
    email: EmailStr


class CreateUserResponse(BaseModel):
    id: uuid.UUID
    email: str


class RegisterSurlRequest(BaseModel):
    user_id: uuid.UUID
    original_url: HttpUrl
    validity_days: int = 30


class RegisterSurlResponse(BaseModel):
    surl: str
    original_url: str
    expires_at: datetime


@router.post(
    "/users",
    response_model=CreateUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New User",
)
async def create_user(request: CreateUserRequest, database: DatabaseSession) -> CreateUserResponse:
    duplicate_email: Result[tuple[User]] = await database.execute(
        select(User).where(User.email == request.email)
    )
    if duplicate_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already being used",
        )

    user: User = User(email=request.email)
    database.add(user)

    await database.commit()
    await database.refresh(user)

    return CreateUserResponse(
        id=user.id,
        email=user.email
    )


@router.post(
    "/surl",
    response_model=RegisterSurlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a New SURL",
)
async def register_surl(request: RegisterSurlRequest, database: DatabaseSession) -> RegisterSurlResponse:
    user_exists: Result[tuple[User]] = await database.execute(
        select(User).where(User.id == request.user_id)
    )
    if not user_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist",
        )

    max_retries: int = 5
    current_attempt: int = 0
    surl: Optional[str] = None

    while current_attempt <= max_retries:
        candidate: str = next(surl_generator)
        candidate_exists: Result[tuple[Surl]] = await database.execute(
            select(Surl.surl).where(Surl.surl == candidate)
        )

        if not candidate_exists.scalar_one_or_none():
            surl = candidate
            break

        current_attempt += 1

    if surl is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a unique short URL key. Please try again.",
        )

    original_url: str = str(request.original_url)
    url_exists: Result[tuple[Url]] = await database.execute(
        select(Url).where(Url.original_url == original_url)
    )

    url: Optional[Url] = url_exists.scalar_one_or_none()
    if url is None:
        url = Url(original_url=original_url)
        database.add(url)
        await database.flush()

    expires_at: datetime = datetime.now(timezone.utc) + timedelta(days=request.validity_days)
    new_surl = Surl(
        surl=surl,
        user_id=request.user_id,
        url_id=url.id,
        status=SurlStatus.ACTIVE,
        expires_at=expires_at,
    )

    database.add(new_surl)
    await database.commit()

    return RegisterSurlResponse(
        surl=surl,
        original_url=original_url,
        expires_at=expires_at,
    )
