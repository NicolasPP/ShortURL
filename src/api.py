from dataclasses import dataclass, field
from typing import Optional, Self

from sqlalchemy.exc import IntegrityError

from database_manager import DatabaseManager
from models import User


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
    def expect(self) -> T:
        assert self._value is not None
        return self._value


@dataclass(slots=True)
class ShortUrlApi:
    _database: DatabaseManager = field(init=False, default_factory=DatabaseManager)

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
