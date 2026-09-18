from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Self

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from short_url.config_manager import PostgresParams, get_postgres_params

POSTGRES_URL_TEMPLATE: str = "postgresql+psycopg2://{user_name}:{password}@{host}:{port}/{database_name}"


@dataclass(slots=True, frozen=True)
class DatabaseManager:

    @classmethod
    def production(cls) -> Self:
        params: PostgresParams = get_postgres_params()
        database_url: str = POSTGRES_URL_TEMPLATE.format(
            user_name=params.user_name,
            password=params.password,
            port=params.port,
            host=params.host,
            database_name=params.database_name
        )
        return cls(
            _database_url=database_url,
            _engine=(engine := DatabaseManager._create_engine(database_url)),
            _session_factory=DatabaseManager._create_session_factory(engine)
        )

    @classmethod
    def testing(cls, database_url: str) -> Self:
        return cls(
            _database_url=database_url,
            _engine=(engine := DatabaseManager._create_engine(database_url)),
            _session_factory=DatabaseManager._create_session_factory(engine)
        )

    @staticmethod
    def _create_engine(database_url: str) -> Engine:
        return create_engine(
            database_url,
            execution_options={"schema_translate_map": {None: "short_url"}},
            pool_pre_ping=True
        )

    @staticmethod
    def _create_session_factory(engine: Engine) -> sessionmaker[Session]:
        return sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False
        )

    _database_url: str
    _engine: Engine
    _session_factory: sessionmaker[Session]

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
