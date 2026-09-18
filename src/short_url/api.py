from dataclasses import dataclass
from typing import Optional, Self

from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.database_manager import DatabaseManager
from short_url.models import User


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
            _database=DatabaseManager.production()
        )

    @classmethod
    def testing(cls, database_url: str) -> Self:
        return cls(
            _database=DatabaseManager.testing(database_url)
        )

    _database: DatabaseManager

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
                return Result.failure(f"Error occurred while creating an User, {err.orig}")

    def get_user(self, email: str) -> Result[User]:
        with self._database.get_session() as session:
            try:
                query: Select[tuple[User]] = Select(User).where(User.email == email)
                if (user := session.scalar(query)) is None:
                    return Result.failure(f"User with email: {email} not found")

                return Result.success(user)

            except DBAPIError as err:
                session.rollback()
                return Result.failure(f"Error occurred while getting a User: {err.orig}")
