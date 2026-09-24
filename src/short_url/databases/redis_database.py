from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Self

from redis import ConnectionPool, Redis

from short_url.config_manager import RedisParams, get_redis_params


@dataclass(slots=True, frozen=True)
class RedisDatabase:
    @classmethod
    def production(cls) -> Self:
        params: RedisParams = get_redis_params()
        return cls(ConnectionPool(
            host=params.host,
            port=params.port,
            username=params.user_name,
            password=params.password,
            decode_responses=True,
            max_connections=20,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            health_check_interval=30,
        ))

    _pool: ConnectionPool

    def close(self) -> None:
        self._pool.disconnect()

    @contextmanager
    def get_client(self) -> Iterator[Redis]:
        client: Redis = Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            client.close()
