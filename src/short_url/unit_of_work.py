from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from typing import Iterator, overload

from short_url.api import PostgresShortUrlApi
from short_url.databases import Postgres, RedisDatabase


class NestedTransactionError(RuntimeError):
    """Raised when uow.transaction() is called inside an existing transaction block."""

    def __init__(self) -> None:
        super().__init__("Nested transactions are strictly prohibited")


@dataclass(slots=True)
class PostgresUnitOfWork:
    _postgres: Postgres
    _session_active: bool = field(init=False, default=False)

    @overload
    def transaction(self) -> AbstractContextManager[PostgresShortUrlApi]:
        ...

    @contextmanager
    def transaction(self) -> Iterator[PostgresShortUrlApi]:
        if self._session_active:
            raise NestedTransactionError()

        with self._postgres.get_session() as session:
            self._session_active = True
            api: PostgresShortUrlApi = PostgresShortUrlApi(session)
            try:
                yield api

                if session.is_active:
                    session.commit()

            except Exception:
                session.rollback()
                raise

            finally:
                api.invalidate()
                self._session_active = False


# @dataclass(slots=True)
# class RedisUnitOfWork:
#     _redis: RedisDatabase
#     _session_active: bool = field(init=False, default=False)
#
#     @overload
#     def transaction(self) -> AbstractContextManager[ShortUrlApi]:
#         ...
#
#     @contextmanager
#     def transaction(self) -> Iterator[ShortUrlApi]:
#         if self._session_active:
#             raise NestedTransactionError()
#
#         with self._redis.get_client() as session:
#             self._session_active = True
#             api: ShortUrlApi = ShortUrlApi(session)
#             try:
#                 yield api
#
#                 if session.is_active:
#                     session.commit()
#
#             except Exception:
#                 session.rollback()
#                 raise
#
#             finally:
#                 api.invalidate()
#                 self._session_active = False
