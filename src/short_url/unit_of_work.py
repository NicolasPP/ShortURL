from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from sqlalchemy.orm import Session

from short_url.database_manager import DatabaseManager


@dataclass(slots=True, frozen=True)
class UnitOfWork:
    _database: DatabaseManager

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        with self._database.get_session() as session:
            try:
                yield session

                if session.is_active:
                    session.commit()

            except Exception:
                session.rollback()
                raise
