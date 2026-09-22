from typing import Iterator

import pytest
from sqlalchemy import schema, text
from sqlalchemy.orm import Session
from testcontainers.community.postgres import PostgresContainer

from short_url.database_manager import DatabaseManager
from short_url.models import Base, SCHEMA_NAME
from short_url.unit_of_work import UnitOfWork

TRUNCATE_QUERY: str = 'TRUNCATE TABLE "{schema}"."{table_name}" CASCADE;'


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16.2-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def database(postgres_container: PostgresContainer) -> Iterator[DatabaseManager]:
    url: str = postgres_container.get_connection_url()
    manager = DatabaseManager.testing(url)

    with manager._engine.connect() as conn:
        conn.execute(schema.CreateSchema(SCHEMA_NAME, if_not_exists=True))
        conn.commit()

    Base.metadata.create_all(bind=manager._engine)

    yield manager

    manager.close()


@pytest.fixture(scope="function")
def session(database: DatabaseManager) -> Iterator[Session]:
    with database.get_session() as session:
        yield session
        session.rollback()


@pytest.fixture(scope="function", autouse=True)
def clean_tables(database: DatabaseManager) -> Iterator[None]:
    yield  # Needs yield to so it runs after the test
    with database._engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(text(TRUNCATE_QUERY.format(
                schema=SCHEMA_NAME,
                table_name=table.name
            )))


@pytest.fixture(scope="function")
def uow(database: DatabaseManager) -> UnitOfWork:
    return UnitOfWork(database)
