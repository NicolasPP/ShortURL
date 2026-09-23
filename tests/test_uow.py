import pytest

from short_url.api import InvalidSessionError, ShortUrlApi
from short_url.unit_of_work import NestedTransactionError, UnitOfWork


def test_nested_session(uow: UnitOfWork) -> None:
    with uow.transaction():
        with pytest.raises(NestedTransactionError):
            with uow.transaction():
                pass


def test_invalid_api(uow: UnitOfWork) -> None:
    with uow.transaction() as api:
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
