from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from typing import Iterator, overload

from short_url.api import ShortUrlApi
from short_url.database_manager import DatabaseManager


class NestedTransactionError(RuntimeError):
    """Raised when uow.transaction() is called inside an existing transaction block."""

    def __init__(self) -> None:
        super().__init__("Nested transactions are strictly prohibited")


@dataclass(slots=True)
class UnitOfWork:
    _database: DatabaseManager
    _session_active: bool = field(init=False, default=False)

    @overload
    def transaction(self) -> AbstractContextManager[ShortUrlApi]:
        ...

    @contextmanager
    def transaction(self) -> Iterator[ShortUrlApi]:
        if self._session_active:
            raise NestedTransactionError()

        with self._database.get_session() as session:
            self._session_active = True
            api: ShortUrlApi = ShortUrlApi(session)
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
