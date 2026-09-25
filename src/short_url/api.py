from dataclasses import dataclass, field
from typing import Optional

from redis import Redis
from sqlalchemy.orm import Session

from short_url.repositories import (
    PostgresClickRepository,
    PostgresSurlRepository,
    PostgresUrlRepository,
    PostgresUserRepository,
    RedisSurlRepository
)


class InvalidSessionError(RuntimeError):
    """Raised when user tries to use Api class after its been invalidated"""

    def __init__(self) -> None:
        super().__init__("Session is no longer valid!")


class InvalidPoolError(RuntimeError):
    """Raised when user tries to use Api class after its been invalidated"""

    def __init__(self) -> None:
        super().__init__("Pool is no longer valid!")


@dataclass(slots=True, init=True)
class PostgresShortUrlApi:
    _session: Optional[Session]
    _users: Optional[PostgresUserRepository] = field(init=False, default=None)
    _urls: Optional[PostgresUrlRepository] = field(init=False, default=None)
    _surls: Optional[PostgresSurlRepository] = field(init=False, default=None)
    _clicks: Optional[PostgresClickRepository] = field(init=False, default=None)

    @property
    def session(self) -> Session:
        if self._session is None:
            raise InvalidSessionError()

        return self._session

    @property
    def users(self) -> PostgresUserRepository:
        if self._users is None:
            self._users = PostgresUserRepository(self.session)

        return self._users

    @property
    def urls(self) -> PostgresUrlRepository:
        if self._urls is None:
            self._urls = PostgresUrlRepository(self.session)

        return self._urls

    @property
    def surls(self) -> PostgresSurlRepository:
        if self._surls is None:
            self._surls = PostgresSurlRepository(self.session)

        return self._surls

    @property
    def clicks(self) -> PostgresClickRepository:
        if self._clicks is None:
            self._clicks = PostgresClickRepository(self.session)

        return self._clicks

    def invalidate(self) -> None:
        self._session = None
        self._users = None
        self._urls = None
        self._surls = None
        self._clicks = None


@dataclass(slots=True, init=True)
class RedisShortUrlApi:
    _client: Optional[Redis]
    _surls: Optional[RedisSurlRepository] = field(init=False, default=None)

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise InvalidPoolError()

        return self._client

    @property
    def surls(self) -> RedisSurlRepository:
        if self._surls is None:
            self._surls = RedisSurlRepository.new(self.client)

        return self._surls

    def invalidate(self) -> None:
        self._client = None
        self._surls = None
