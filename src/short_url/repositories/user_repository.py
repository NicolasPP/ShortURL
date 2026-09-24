from dataclasses import dataclass

from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.models import User
from short_url.repositories.repository import PostgresRepository
from short_url.repositories.result import Result


@dataclass(slots=True, frozen=True)
class PostgresUserRepository(PostgresRepository):
    @staticmethod
    def _get_user_query(email: str, lock: bool) -> Select[tuple[User]]:
        if lock:
            return Select(User).where(User.email == email).with_for_update()
        return Select(User).where(User.email == email)

    def add(self, email: str) -> Result[User]:
        user = User(email=email)
        try:
            self._session.add(user)
            self._session.flush()
            return Result.success(user)
        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))

    def get(self, email: str, lock: bool = False) -> Result[User]:
        try:
            query: Select[tuple[User]] = PostgresUserRepository._get_user_query(email, lock)
            if (user := self._session.scalar(query)) is None:
                return Result.failure(f"User with email: {email} not found")

            return Result.success(user)

        except DBAPIError as err:
            return Result.failure(str(err))
