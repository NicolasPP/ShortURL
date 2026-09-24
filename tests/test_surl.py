from decimal import Decimal
from typing import Iterator

from short_url.models import Surl, SurlStatus, Url, User
from short_url.repositories import Result
from short_url.repositories.surl_repository import MAX_SURL_RETRIES
from short_url.unit_of_work import PostgresUnitOfWork

TEST_SURL: str = "cOvUZx3"
TEST_URL: str = "test_url.com"
TEST_EMAIL: str = "user_test_email@email.com"


def dummy_surl_generator() -> Iterator[str]:
    while True:
        yield TEST_SURL


def test_register_surl_success(postgres_uow: PostgresUnitOfWork) -> None:
    # 1. Setup prerequisites in setup transaction
    with postgres_uow.transaction() as api:
        add_user: Result[User] = api.users.add(TEST_EMAIL)
        assert not add_user.failed, "Expected add_user to succeed"

        add_url: Result[Url] = api.urls.add(TEST_URL)
        assert not add_url.failed, "Expected add_url to succeed"

        user: User = add_user.value
        user.balance = Decimal("5.00")
        url: Url = add_url.value

    with postgres_uow.transaction() as api:
        register_surl: Result[Surl] = api.surls.add(url, user, dummy_surl_generator())
        assert not register_surl.failed, "Expected register_surl to succeed"

        surl: Surl = register_surl.value
        assert surl.surl == TEST_SURL, f"Expected surl to be {TEST_SURL}, got: {surl.surl}"
        assert surl.user_id == user.id, f"Expected user id {user.id}, got {surl.user_id}"
        assert surl.url_hash == url.url_hash, f"Expected url_hash to be {url.url_hash}, got {surl.url_hash}"
        assert surl.status == SurlStatus.ACTIVE, f"Expected status to be {SurlStatus.ACTIVE}, got {surl.status}"
        assert isinstance(surl, Surl), f"Expected type {Surl.__name__}, got {type(surl).__name__}"


def test_register_surl_failure_surl_generation_failed(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        user: Result[User] = api.users.add(TEST_EMAIL)
        user.value.balance = Decimal("10.00")
        assert not user.failed, "Expected add_user to succeed"

        url: Result[Url] = api.urls.add(TEST_URL)
        assert not url.failed, "Expected add_url to succeed"

    with postgres_uow.transaction() as api:
        surl: Result[Surl] = api.surls.add(url.value, user.value, dummy_surl_generator())
        assert not surl.failed, "Expected register_surl to succeed"

    with postgres_uow.transaction() as api:
        duplicate_surl: Result[Surl] = api.surls.add(url.value, user.value, dummy_surl_generator())
        assert duplicate_surl.failed, "Expected register_surl to fail due to collisions"
        assert duplicate_surl.reason == f"Could not create SURL after {MAX_SURL_RETRIES} attempts"


def test_get_surl_success(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        add_user: Result[User] = api.users.add(TEST_EMAIL)
        assert not add_user.failed, "Expected add_user to succeed"

        add_url: Result[Url] = api.urls.add(TEST_URL)
        assert not add_url.failed, "Expected add_url to succeed"

        user: User = add_user.value
        user.balance = Decimal("5.00")
        url: Url = add_url.value

        register_surl: Result[Surl] = api.surls.add(url, user, dummy_surl_generator())
        assert not register_surl.failed, "Expected register_surl to succeed"

    with postgres_uow.transaction() as api:
        get_surl: Result[Surl] = api.surls.get(TEST_SURL)
        assert not get_surl.failed, "Expected get_surl to be successful"

        surl: Surl = get_surl.value
        assert surl.surl == TEST_SURL, f"Expected surl to be {TEST_SURL}, got: {surl.surl}"
        assert surl.user_id == user.id, f"Expected user id {user.id}, got {surl.user_id}"
        assert surl.url_hash == url.url_hash, f"Expected url_hash to be {url.url_hash}, got {surl.url_hash}"
        assert surl.status == SurlStatus.ACTIVE, f"Expected status to be {SurlStatus.ACTIVE}, got {surl.status}"
        assert isinstance(surl, Surl), f"Expected type {Surl.__name__}, got {type(surl).__name__}"


def test_get_surl_failure(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        surl: Result[Surl] = api.surls.get(TEST_SURL)

        assert surl.failed, "Expected get_url to fail"
        assert surl.reason == f"Could not find active surl: {TEST_SURL}"
