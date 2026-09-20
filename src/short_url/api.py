from collections.abc import Buffer
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Iterator, Optional, Self

from sqlalchemy import Select, func
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.database_manager import DatabaseManager
from short_url.models import Click, Surl, SurlStatus, Url, User
from short_url.surl_generator import generate_surl

MAX_SURL_RETRIES: int = 5


@dataclass(slots=True, frozen=True)
class Result[T]:

    @classmethod
    def success(cls, value: T) -> Self:
        return cls(value, "")

    @classmethod
    def failure(cls, reason: str) -> Self:
        return cls(None, reason)

    _value: Optional[T]
    reason: str

    @property
    def failed(self) -> bool:
        return self._value is None

    @property
    def value(self) -> T:
        assert self._value is not None
        return self._value


@dataclass(slots=True, frozen=True)
class ShortUrlApi:
    @classmethod
    def production(cls) -> Self:
        return cls(
            _database=DatabaseManager.production(),
            _surl_generator=generate_surl()
        )

    @classmethod
    def testing(cls, database_url: str) -> Self:
        return cls(
            _database=DatabaseManager.testing(database_url),
            _surl_generator=generate_surl()
        )

    @staticmethod
    def hash_url(url: str) -> str:
        payload: Buffer = url.encode("utf-8")
        return sha256(payload).hexdigest()

    _database: DatabaseManager
    _surl_generator: Iterator[str]

    def add_user(self, email: str) -> Result[User]:
        user: User = User(email=email)
        with self._database.get_session() as session:
            try:
                session.add(user)
                session.commit()
                session.refresh(user)
                return Result.success(user)
            except IntegrityError as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def get_user(self, email: str) -> Result[User]:
        with self._database.get_session() as session:
            try:
                query: Select[tuple[User]] = Select(User).where(User.email == email)
                if (user := session.scalar(query)) is None:
                    return Result.failure(f"User with email: {email} not found")

                return Result.success(user)

            except DBAPIError as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def add_url(self, raw_url: str) -> Result[Url]:
        url: Url = Url(
            url_hash=ShortUrlApi.hash_url(raw_url),
            original_url=raw_url,
            created_at=datetime.now(timezone.utc)
        )
        with self._database.get_session() as session:
            try:
                session.add(url)
                session.commit()
                session.refresh(url)
                return Result.success(url)
            except IntegrityError as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def get_url(self, raw_url: str) -> Result[Url]:
        url_hash: str = ShortUrlApi.hash_url(raw_url)
        with self._database.get_session() as session:
            try:
                query: Select[tuple[Url]] = Select(Url).where(Url.url_hash == url_hash)
                if (url := session.scalar(query)) is None:
                    return Result.failure(f"Could not find url: {raw_url}")

                return Result.success(url)

            except DBAPIError as err:
                return Result.failure(f"{err.orig}")

    def register_surl(self, original_url: str, user_email: str) -> Result[Surl]:
        if (get_user := self.get_user(user_email)).failed:
            return Result.failure(get_user.reason)

        if (get_url := self.get_url(original_url)).failed:
            return Result.failure(get_url.reason)

        user: User = get_user.value
        url: Url = get_url.value
        surl: Optional[Surl] = None

        expiry_duration: timedelta = timedelta(days=30)
        for _ in range(MAX_SURL_RETRIES):
            surl_code: str = next(self._surl_generator)
            if not self.get_surl(surl_code).failed:
                # TODO: check if it failed because it couldn't FIND the surl
                continue

            surl = Surl(
                surl=surl_code,
                user_id=user.id,
                url_hash=url.url_hash,
                status=SurlStatus.ACTIVE,
                created_at=(created_at := datetime.now(timezone.utc)),
                expires_at=created_at + expiry_duration
            )
            break

        if surl is None:
            return Result.failure(f"Could not create SURL after {MAX_SURL_RETRIES} attempts")

        with self._database.get_session() as session:
            try:
                session.add(surl)
                session.commit()
                session.refresh(surl)
                return Result.success(surl)

            except (IntegrityError, DBAPIError) as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def get_surl(self, raw_surl: str) -> Result[Surl]:
        with self._database.get_session() as session:
            try:
                query: Select[tuple[Surl]] = Select(Surl) \
                    .where(Surl.surl == raw_surl) \
                    .where(Surl.status == SurlStatus.ACTIVE)
                if (surl := session.scalar(query)) is None:
                    return Result.failure(f"Could not find active surl: {raw_surl}")

                return Result.success(surl)

            except DBAPIError as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def add_click(self, raw_surl: str) -> Result[Click]:
        if (surl := self.get_surl(raw_surl)).failed:
            return Result.failure(surl.reason)

        click: Click = Click(
            surl=surl.value.surl,
            clicked_at=datetime.now()
        )

        with self._database.get_session() as session:
            try:
                session.add(click)
                session.commit()
                session.refresh(click)
                return Result.success(click)

            except (IntegrityError, DBAPIError) as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def get_click_count(self, raw_surl: str) -> Result[int]:
        if (surl := self.get_surl(raw_surl)).failed:
            return Result.failure(surl.reason)

        with self._database.get_session() as session:
            try:
                query: Select[tuple[int]] = Select(func.count(Click.id)) \
                    .where(Click.surl == surl.value.surl)
                click_count: int = session.scalar(query) or 0
                return Result.success(click_count)

            except (IntegrityError, DBAPIError) as err:
                session.rollback()
                return Result.failure(f"{err.orig}")

    def get_click_traffic(self, raw_surl: str, window: timedelta) -> Result[float]:
        if (minutes := window.total_seconds() / 60.0) <= 0:
            return Result.failure("Time Window must be greater than 0")

        if (surl := self.get_surl(raw_surl)).failed:
            return Result.failure(surl.reason)

        with self._database.get_session() as session:
            try:
                query: Select[tuple[int]] = Select(func.count(Click.id)) \
                    .where(Click.surl == surl.value.surl) \
                    .where(Click.clicked_at >= datetime.now() - window)

                clicks: int = session.scalar(query) or 0
                return Result.success(clicks / minutes)

            except (IntegrityError, DBAPIError) as err:
                session.rollback()
                return Result.failure(f"{err.orig}")
