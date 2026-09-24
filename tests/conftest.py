from typing import Iterator

import pytest
from sqlalchemy import schema, text
from sqlalchemy.orm import Session
from testcontainers.community.postgres import PostgresContainer

from short_url.databases import Postgres
from short_url.models import Base, SCHEMA_NAME
from short_url.unit_of_work import PostgresUnitOfWork

TRUNCATE_QUERY: str = 'TRUNCATE TABLE "{schema}"."{table_name}" CASCADE;'


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16.2-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres(postgres_container: PostgresContainer) -> Iterator[Postgres]:
    url: str = postgres_container.get_connection_url()
    pg: Postgres = Postgres.testing(url)

    with pg._engine.connect() as conn:
        conn.execute(schema.CreateSchema(SCHEMA_NAME, if_not_exists=True))
        conn.commit()

    Base.metadata.create_all(bind=pg._engine)

    yield pg

    pg.close()


@pytest.fixture(scope="function")
def session(postgres: Postgres) -> Iterator[Session]:
    with postgres.get_session() as session:
        yield session
        session.rollback()


@pytest.fixture(scope="function", autouse=True)
def clean_tables(postgres: Postgres) -> Iterator[None]:
    yield  # Needs yield to so it runs after the test
    with postgres._engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(text(TRUNCATE_QUERY.format(
                schema=SCHEMA_NAME,
                table_name=table.name
            )))


@pytest.fixture(scope="function")
def postgres_uow(postgres: Postgres) -> PostgresUnitOfWork:
    return PostgresUnitOfWork(postgres)
