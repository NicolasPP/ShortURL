from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config_manager import PostgresParams, get_postgres_params

POSTGRES_URL_TEMPLATE: str = "postgresql+psycopg2://{user_name}:{password}@{host}:{port}/{database_name}"


@dataclass(slots=True, init=False)
class DatabaseManager:
    _database_url: str
    _engine: Engine
    _session_factory: sessionmaker[Session]

    def __init__(self) -> None:
        params: PostgresParams = get_postgres_params()
        self._database_url = POSTGRES_URL_TEMPLATE.format(
            user_name=params.user_name,
            password=params.password,
            port=params.port,
            host=params.host,
            database_name=params.database_name
        )
        self._engine = create_engine(
            self._database_url,
            execution_options={"schema_translate_map": {None: "short_url"}},
            pool_pre_ping=True
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )

    def close(self) -> None:
        self._engine.dispose()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
