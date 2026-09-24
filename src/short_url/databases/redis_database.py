from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Self

from redis import ConnectionPool, Redis

from short_url.config_manager import RedisParams, get_redis_params

REDIS_PREFIX: str = "ShorUrl.{key}"


@dataclass(slots=True, frozen=True)
class RedisDatabase:
    @classmethod
    def production(cls) -> Self:
        params: RedisParams = get_redis_params()
        pool: ConnectionPool = ConnectionPool(
            host=params.host,
            port=params.port,
            username=params.user_name,
            password=params.password,
            decode_responses=True,
            max_connections=20,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            health_check_interval=30,
        )
        return cls(pool, REDIS_PREFIX)

    _pool: ConnectionPool
    _prefix: str

    def get_key(self, key: str) -> str:
        return self._prefix.format(key=key)

    def close(self) -> None:
        self._pool.disconnect()

    @contextmanager
    def get_client(self) -> Iterator[Redis]:
        client: Redis = Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            client.close()
