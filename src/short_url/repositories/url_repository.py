from collections.abc import Buffer
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import Select
from sqlalchemy.exc import DBAPIError, IntegrityError

from short_url.models import Url
from short_url.repositories.repository import PostgresRepository
from short_url.repositories.result import Result


@dataclass(slots=True, frozen=True)
class PostgresUrlRepository(PostgresRepository):
    @staticmethod
    def hash_url(url: str) -> str:
        payload: Buffer = url.encode("utf-8")
        return sha256(payload).hexdigest()

    def add(self, url_code: str) -> Result[Url]:
        url: Url = Url(
            url_hash=PostgresUrlRepository.hash_url(url_code),
            original_url=url_code,
            created_at=datetime.now(timezone.utc)
        )
        try:
            self._session.add(url)
            self._session.flush()
            return Result.success(url)
        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))

    def get(self, url_code: str) -> Result[Url]:
        url_hash: str = PostgresUrlRepository.hash_url(url_code)
        try:
            query: Select[tuple[Url]] = Select(Url).where(Url.url_hash == url_hash)
            if (url := self._session.scalar(query)) is None:
                return Result.failure(f"Could not find url: {url_code}")

            return Result.success(url)

        except (IntegrityError, DBAPIError) as err:
            return Result.failure(str(err))
