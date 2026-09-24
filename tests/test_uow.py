import pytest

from short_url.api import InvalidSessionError, ShortUrlApi
from short_url.unit_of_work import NestedTransactionError, PostgresUnitOfWork


def test_nested_session(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction():
        with pytest.raises(NestedTransactionError):
            with postgres_uow.transaction():
                pass


def test_invalid_api(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        invalid_api: ShortUrlApi = api

    with pytest.raises(InvalidSessionError):
        invalid_api.session

    with pytest.raises(InvalidSessionError):
        invalid_api.users

    with pytest.raises(InvalidSessionError):
        invalid_api.urls

    with pytest.raises(InvalidSessionError):
        invalid_api.surls

    with pytest.raises(InvalidSessionError):
        invalid_api.clicks
