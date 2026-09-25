from dataclasses import dataclass

from redis import Redis
from sqlalchemy.orm import Session

REDIS_PREFIX: str = "ShortUrl.{name}.{key}"


@dataclass(slots=True, frozen=True)
class PostgresRepository:
    _session: Session


@dataclass(slots=True, frozen=True)
class RedisRepository:
    _client: Redis
    _name: str

    def get_key(self, key: str) -> str:
        return REDIS_PREFIX.format(
            name=self._name,
            key=key
        )
