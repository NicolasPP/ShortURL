from dataclasses import dataclass

from short_url.models import Surl
from short_url.repositories import Result
from short_url.unit_of_work import PostgresUnitOfWork, RedisUnitOfWork


@dataclass(slots=True, frozen=True)
class App:
    _postgres: PostgresUnitOfWork
    _redis: RedisUnitOfWork

    def resolve_surl(self, surl_code: str) -> Result[str]:
        with self._redis.transaction() as redis:
            if not (url_result := redis.surls.resolve(surl_code)).failure:
                return url_result

        with self._postgres.transaction() as postgres:
            if not (surl_result := postgres.surls.get(surl_code)).failure:
                return Result.failure(surl_result.reason)

            surl: Surl = surl_result.value
            if surl.url is None or surl.url.original_url is None:
                return Result.failure("Url relationship failed!!")

            url: str = surl.url.original_url

        with self._redis.transaction() as redis:
            redis.surls.add(surl_code, url)

        return Result.success(url)
