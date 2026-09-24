from dataclasses import dataclass, field
from typing import Optional

from redis import ConnectionPool
from sqlalchemy.orm import Session

from short_url.repositories import ClickRepository, SurlRepository, UrlRepository, UserRepository


class InvalidSessionError(RuntimeError):
    """Raised when user tries to use Api class after its been invalidated"""

    def __init__(self) -> None:
        super().__init__("Session is no longer valid!")


@dataclass(slots=True, init=True)
class PostgresShortUrlApi:
    _session: Optional[Session]
    _users: Optional[UserRepository] = field(init=False, default=None)
    _urls: Optional[UrlRepository] = field(init=False, default=None)
    _surls: Optional[SurlRepository] = field(init=False, default=None)
    _clicks: Optional[ClickRepository] = field(init=False, default=None)

    @property
    def session(self) -> Session:
        if self._session is None:
            raise InvalidSessionError()

        return self._session

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self.session)

        return self._users

    @property
    def urls(self) -> UrlRepository:
        if self._urls is None:
            self._urls = UrlRepository(self.session)

        return self._urls

    @property
    def surls(self) -> SurlRepository:
        if self._surls is None:
            self._surls = SurlRepository(self.session)

        return self._surls

    @property
    def clicks(self) -> ClickRepository:
        if self._clicks is None:
            self._clicks = ClickRepository(self.session)

        return self._clicks

    def invalidate(self) -> None:
        self._session = None
        self._users = None
        self._urls = None
        self._surls = None
        self._clicks = None


@dataclass(slots=True, init=True)
class RedisShortUrlApi:
    _pool: Optional[ConnectionPool]
    _surls: Optional[SurlRepository] = field(init=False, default=None)
    _clicks: Optional[ClickRepository] = field(init=False, default=None)
