from dataclasses import dataclass

from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.models import User
from short_url.repositories.repository import Repository
from short_url.repositories.result import Result


@dataclass(slots=True, frozen=True)
class UserRepository(Repository):

    def add(self, email: str) -> Result[User]:
        user = User(email=email)
        try:
            self._session.add(user)
            self._session.flush()
            return Result.success(user)
        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))

    def get(self, email: str) -> Result[User]:
        try:
            query: Select[tuple[User]] = Select(User).where(User.email == email)
            if (user := self._session.scalar(query)) is None:
                return Result.failure(f"User with email: {email} not found")

            return Result.success(user)

        except DBAPIError as err:
            return Result.failure(str(err))
