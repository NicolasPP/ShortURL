from short_url.api import Result, ShortUrlApi
from short_url.models import Url

TEST_URL: str = "test_url.com"

def test_add_url_success(api: ShortUrlApi) -> None:
    url: Result[Url] = api.add_url(TEST_URL)

    assert not url.failed, "Expected add_url to be successful"
    assert isinstance(url.value, Url), (f"Expected value to be {Url.__name__}, "
                                        f"got: {type(url.value).__name__}")
    assert url.value.original_url == TEST_URL, (f"Expected url to be {TEST_URL}"
                                               f"got: {url.value.original_url}")


def test_add_url_failure(api: ShortUrlApi) -> None:
    url: Result[Url] = api.add_url(TEST_URL)
    assert not url.failed, "Expected add_url to be successful"
    url_hash: str = url.value.url_hash

    url = api.add_url(TEST_URL)
    assert url.failed, "Expected add_url to fail"
    expected_reason: str = ("duplicate key value violates unique constraint \"url_pkey\"\n"
                            f"DETAIL:  Key (url_hash)=({url_hash}) already exists.\n")
    assert url.reason == expected_reason, "Expected add_user to fail because Email already exists"


def test_get_url_success(api: ShortUrlApi) -> None:
    add_url: Result[Url] = api.add_url(TEST_URL)
    assert not add_url.failed, "Expected add_url to be successful"

    url: Result[Url] = api.get_url(TEST_URL)
    assert not url.failed, "Expected get_url to be successful"
    assert isinstance(url.value, Url), (f"Expected value to be {Url.__name__}, "
                                        f"got: {type(url.value).__name__}")
    assert url.value.original_url == TEST_URL, (f"Expected url to be {TEST_URL}"
                                               f"got: {url.value.original_url}")


def test_get_url_failure(api: ShortUrlApi) -> None:
    url: Result[Url] = api.get_url(TEST_URL)
    assert url.failed, "Expected get_url to fail"
    assert url.reason == f"Could not find url: {TEST_URL}"
