from typing import Generator

import pytest
from sqlalchemy import delete, schema
from testcontainers.community.postgres import PostgresContainer

from short_url.api import ShortUrlApi
from short_url.database_manager import DatabaseManager
from short_url.models import Base


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16.2-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    database_url: str = postgres_container.get_connection_url()
    database: DatabaseManager = DatabaseManager.testing(database_url)
    with database._engine.connect() as conn:
        conn.execute(schema.CreateSchema("short_url", if_not_exists=True))
        conn.commit()
    Base.metadata.create_all(bind=database._engine)
    database.close()
    return database_url


@pytest.fixture(scope="function")
def api(database_url: str) -> Generator[ShortUrlApi, None, None]:
    short_url_api: ShortUrlApi = ShortUrlApi.testing(database_url)
    yield short_url_api

    database: DatabaseManager = short_url_api._database
    with database._engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(delete(table))

    database.close()
