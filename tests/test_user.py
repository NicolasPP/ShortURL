from short_url.api import Result, ShortUrlApi
from short_url.models import User

TEST_EMAIL: str = "add_user_test@email.com"


def test_add_user_success(api: ShortUrlApi) -> None:
    user: Result[User] = api.add_user(TEST_EMAIL)

    assert not user.failed, "Expected add_user to be successful"
    assert isinstance(user.value, User), (f"Expected value to be {User.__name__}, "
                                          f"got: {type(user.value).__name__}")
    assert user.value.email == TEST_EMAIL, (f"Expected user email to be {TEST_EMAIL}"
                                       f"got: {user.value.email}")


def test_add_user_failure(api: ShortUrlApi) -> None:
    user: Result[User] = api.add_user(TEST_EMAIL)
    assert not user.failed, "Expected add_user to be successful"

    user = api.add_user(TEST_EMAIL)
    assert user.failed, "Expected add_user to fail"
    expected_reason: str = ("duplicate key value violates unique constraint \"users_email_key\"\n"
                            "DETAIL:  Key (email)=(add_user_test@email.com) already exists.\n")
    assert user.reason == expected_reason, "Expected add_user to fail because Email already exists"


def test_get_user_success(api: ShortUrlApi) -> None:
    add_user: Result[User] = api.add_user(TEST_EMAIL)
    assert not add_user.failed, "Expected add_user to be successful"

    user: Result[User] = api.get_user(TEST_EMAIL)
    assert not user.failed, "Expected get_user to be successful"
    assert isinstance(user.value, User), (f"Expected value to be {User.__name__}, "
                                          f"got: {type(user.value).__name__}")
    assert user.value.email == TEST_EMAIL, (f"Expected user email to be {TEST_EMAIL}"
                                       f"got: {user.value.email}")


def test_get_user_failure(api: ShortUrlApi) -> None:
    user: Result[User] = api.get_user(TEST_EMAIL)
    assert user.failed, "Expected get_user to fail"
    assert user.reason == "User with email: add_user_test@email.com not found"
