from short_url.models import Url
from short_url.repositories import Result
from short_url.unit_of_work import UnitOfWork

TEST_URL: str = "test_url.com"


def test_add_url_success(uow: UnitOfWork) -> None:
    with uow.transaction() as api:
        url: Result[Url] = api.urls.add(TEST_URL)

        assert not url.failed, "Expected add_url to be successful"
        assert isinstance(url.value, Url), \
            f"Expected value to be {Url.__name__}, got: {type(url.value).__name__}"
        assert url.value.original_url == TEST_URL, \
            f"Expected url to be {TEST_URL}, got: {url.value.original_url}"


def test_add_url_failure(uow: UnitOfWork) -> None:
    with uow.transaction() as api:
        url: Result[Url] = api.urls.add(TEST_URL)
        assert not url.failed, "Expected add_url to be successful"
        url_hash: str = url.value.url_hash

    with uow.transaction() as api:
        duplicate_url: Result[Url] = api.urls.add(TEST_URL)
        assert duplicate_url.failed, "Expected add_url to fail"

        reason: str = 'duplicate key value violates unique constraint "url_pkey"'
        assert reason in duplicate_url.reason, \
            f"Expected reason for failure: {reason}"


def test_get_url_success(uow: UnitOfWork) -> None:
    with uow.transaction() as api:
        add_url: Result[Url] = api.urls.add(TEST_URL)
        assert not add_url.failed, "Expected add_url to be successful"

    with uow.transaction() as api:
        url: Result[Url] = api.urls.get(TEST_URL)
        assert not url.failed, "Expected get_url to be successful"
        assert isinstance(url.value, Url), \
            f"Expected value to be {Url.__name__}, got: {type(url.value).__name__}"
        assert url.value.original_url == TEST_URL, \
            f"Expected url to be {TEST_URL}, got: {url.value.original_url}"


def test_get_url_failure(uow: UnitOfWork) -> None:
    with uow.transaction() as api:
        url: Result[Url] = api.urls.get(TEST_URL)
        assert url.failed, "Expected get_url to fail"
        assert url.reason == f"Could not find url: {TEST_URL}"
