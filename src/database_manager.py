from collections.abc import AsyncGenerator
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config_manager import PostgresParams, get_postgres_params

POSTGRES_URL_TEMPLATE: str = "postgresql+asyncpg://{user_name}:{password}@{host}:{port}/{database_name}"


@dataclass(slots=True, init=False)
class DatabaseManager:
    _database_url: str
    _engine: AsyncEngine
    _session_factory: async_sessionmaker[AsyncSession]

    def __init__(self) -> None:
        params: PostgresParams = get_postgres_params()
        self._database_url = POSTGRES_URL_TEMPLATE.format(
            user_name=params.user_name,
            password=params.password,
            port=params.port,
            host=params.host,
            database_name=params.database_name
        )
        self._engine = create_async_engine(
            self._database_url,
            pool_pre_ping=True
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        await self._engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
