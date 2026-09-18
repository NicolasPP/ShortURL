from typing import Iterator

from short_url.api import MAX_SURL_RETRIES, Result, ShortUrlApi
from short_url.models import Surl, SurlStatus, Url, User

TEST_SURL: str = "cOvUZx3"
TEST_URL: str = "test_url.com"
TEST_EMAIL: str = "user_test_email@email.com"


def dummy_surl_generator() -> Iterator[str]:
    while True:
        yield TEST_SURL


def test_register_surl_success(api: ShortUrlApi) -> None:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to succeed"

    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to succeed"

    # Must use this hacky solution because the class is frozen ;(
    object.__setattr__(api, "_surl_generator", dummy_surl_generator())
    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert not register_surl.failed, "Expected register_surl to succeed"

    user: User = add_user.value
    url: Url = add_url.value
    surl: Surl = register_surl.value

    assert surl.surl == TEST_SURL, f"Expected surl to be {TEST_SURL}, got: {surl.surl}"
    assert surl.user_id == user.id, f"Expected user id {user.id}, got {surl.user_id}"
    assert surl.url_hash == url.url_hash, f"Expected url_hash to be {url.url_hash}, got {surl.url_hash}"
    assert surl.status == SurlStatus.ACTIVE, f"Expected status to be {SurlStatus.ACTIVE}, got {surl.status}"
    assert isinstance(surl, Surl), f"Expected type {Surl.__name__}, got {type(surl).__name__}"


def test_register_surl_failure_no_user(api: ShortUrlApi) -> None:
    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to succeed"

    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert register_surl.failed, "Expected register_surl to fail"
    assert register_surl.reason == f"User with email: {TEST_EMAIL} not found"


def test_register_surl_failure_no_url(api: ShortUrlApi) -> None:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to succeed"

    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert register_surl.failed, "Expected register_surl to fail"
    assert register_surl.reason == f"Could not find url: {TEST_URL}"


def test_register_surl_failure_surl_generation_failed(api: ShortUrlApi) -> None:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to succeed"

    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to succeed"

    # Must use this hacky solution because the class is frozen ;(
    object.__setattr__(api, "_surl_generator", dummy_surl_generator())
    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert not register_surl.failed, "Expected register_surl to succeed"

    register_surl = api.register_surl(TEST_URL, TEST_EMAIL)
    assert register_surl.failed, "Expected register_surl to fail"
    assert register_surl.reason == f"Could not create SURL after {MAX_SURL_RETRIES} attempts"


def test_get_surl_success(api: ShortUrlApi) -> None:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to succeed"

    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to succeed"

    # Must use this hacky solution because the class is frozen ;(
    object.__setattr__(api, "_surl_generator", dummy_surl_generator())
    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert not register_surl.failed, "Expected register_surl to succeed"

    user: User = add_user.value
    url: Url = add_url.value
    get_surl: Result[Surl] = api.get_surl(TEST_SURL)
    surl: Surl = get_surl.value
    assert not get_surl.failed, "Expected get_surl to be successful"
    assert surl.surl == TEST_SURL, f"Expected surl to be {TEST_SURL}, got: {surl.surl}"
    assert surl.user_id == user.id, f"Expected user id {user.id}, got {surl.user_id}"
    assert surl.url_hash == url.url_hash, f"Expected url_hash to be {url.url_hash}, got {surl.url_hash}"
    assert surl.status == SurlStatus.ACTIVE, f"Expected status to be {SurlStatus.ACTIVE}, got {surl.status}"
    assert isinstance(surl, Surl), f"Expected type {Surl.__name__}, got {type(surl).__name__}"


def test_get_surl_failure(api: ShortUrlApi) -> None:
    surl: Result[Surl] = api.get_surl(TEST_SURL)
    assert surl.failed, "Expected get_url to fail"
    assert surl.reason == f"Could not find active surl: {TEST_SURL}"
