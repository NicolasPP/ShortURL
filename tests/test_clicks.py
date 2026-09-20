from datetime import timedelta
from typing import Iterator

from short_url.api import Result, ShortUrlApi
from short_url.models import Click, Surl, Url, User

TEST_SURL: str = "cOvUZx3"
TEST_URL: str = "test_url.com"
TEST_EMAIL: str = "user_test_email@email.com"


def dummy_surl_generator() -> Iterator[str]:
    while True:
        yield TEST_SURL


def _create_surl(api: ShortUrlApi) -> Result[Surl]:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to succeed"

    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to succeed"

    object.__setattr__(api, "_surl_generator", dummy_surl_generator())
    register_surl: Result[Surl] = api.register_surl(TEST_URL, TEST_EMAIL)
    assert not register_surl.failed, "Expected register_surl to succeed"

    return register_surl


def test_add_click_success(api: ShortUrlApi) -> None:
    _create_surl(api)

    add_click: Result[Click] = api.add_click(TEST_SURL)
    assert not add_click.failed, "Expected add_click to succeed"

    click: Click = add_click.value
    assert click.surl == TEST_SURL, f"Expected click surl to be {TEST_SURL}, got: {click.surl}"
    assert isinstance(click, Click), f"Expected type {Click.__name__}, got {type(click).__name__}"


def test_add_click_failure_invalid_surl(api: ShortUrlApi) -> None:
    add_click: Result[Click] = api.add_click(TEST_SURL)
    assert add_click.failed, "Expected add_click to fail"
    assert add_click.reason == f"Could not find active surl: {TEST_SURL}"

def test_get_click_count_success(api: ShortUrlApi) -> None:
    _create_surl(api)

    get_count_empty: Result[int] = api.get_click_count(TEST_SURL)
    assert not get_count_empty.failed, "Expected get_click_count to succeed"
    assert get_count_empty.value == 0, f"Expected click count to be 0, got: {get_count_empty.value}"

    add_click_1: Result[Click] = api.add_click(TEST_SURL)
    assert not add_click_1.failed, "Expected add_click to succeed"

    add_click_2: Result[Click] = api.add_click(TEST_SURL)
    assert not add_click_2.failed, "Expected add_click to succeed"

    get_count: Result[int] = api.get_click_count(TEST_SURL)
    assert not get_count.failed, "Expected get_click_count to succeed"
    assert get_count.value == 2, f"Expected click count to be 2, got: {get_count.value}"


def test_get_click_count_failure_invalid_surl(api: ShortUrlApi) -> None:
    get_count: Result[int] = api.get_click_count(TEST_SURL)
    assert get_count.failed, "Expected get_click_count to fail"
    assert get_count.reason == f"Could not find active surl: {TEST_SURL}"

def test_get_click_traffic_success(api: ShortUrlApi) -> None:
    _create_surl(api)

    for _ in range(10):
        add_click: Result[Click] = api.add_click(TEST_SURL)
        assert not add_click.failed, "Expected add_click to succeed"

    time_window: timedelta = timedelta(minutes=5)
    get_traffic: Result[float] = api.get_click_traffic(TEST_SURL, time_window)
    assert not get_traffic.failed, "Expected get_click_traffic to succeed"

    expected_rate: float = 10 / 5.0
    assert get_traffic.value == expected_rate, f"Expected traffic rate to be {expected_rate}, got: {get_traffic.value}"


def test_get_click_traffic_failure_invalid_window(api: ShortUrlApi) -> None:
    _create_surl(api)

    time_window: timedelta = timedelta(minutes=0)
    get_traffic: Result[float] = api.get_click_traffic(TEST_SURL, time_window)
    assert get_traffic.failed, "Expected get_click_traffic to fail"
    assert get_traffic.reason == "Time Window must be greater than 0"


def test_get_click_traffic_failure_invalid_surl(api: ShortUrlApi) -> None:
    time_window: timedelta = timedelta(minutes=5)
    get_traffic: Result[float] = api.get_click_traffic(TEST_SURL, time_window)
    assert get_traffic.failed, "Expected get_click_traffic to fail"
    assert get_traffic.reason == f"Could not find active surl: {TEST_SURL}"