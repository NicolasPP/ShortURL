from short_url.api import Result, ShortUrlApi
from short_url.models import User


def test_add_user_success(api: ShortUrlApi) -> None:
    email: str = "add_user_test@email.com"
    user: Result[User] = api.add_user(email)

    assert not user.failed, "Expected add_user to be successful"
    assert isinstance(user.value, User), (f"Expected values to be {User.__name__}, "
                                          f"got: {type(user.value).__name__}")
    assert user.value.email == email, (f"Expected user email to be {email}"
                                       f"got: {user.value.email}")


def test_add_user_failure(api: ShortUrlApi) -> None:
    email: str = "add_user_test@email.com"
    user: Result[User] = api.add_user(email)
    assert not user.failed, "Expected add_user to be successful"

    user = api.add_user(email)
    assert user.failed, "Expected add_user to fail"
    expected_reason: str = ("Error occurred while creating an User, duplicate key value violates unique constraint "
                            "\"users_email_key\"\nDETAIL:  Key (email)=(add_user_test@email.com) already exists.\n")
    assert user.reason == expected_reason, "Expected add_user to fail because Email already exists"


def test_get_user_success(api: ShortUrlApi) -> None:
    email: str = "add_user_test@email.com"
    add_user: Result[User] = api.add_user(email)
    assert not add_user.failed, "Expected add_user to be successful"

    user: Result[User] = api.get_user(email)
    assert not user.failed, "Expected get_user to be successful"
    assert isinstance(user.value, User), (f"Expected values to be {User.__name__}, "
                                          f"got: {type(user.value).__name__}")
    assert user.value.email == email, (f"Expected user email to be {email}"
                                       f"got: {user.value.email}")


def test_get_user_failure(api: ShortUrlApi) -> None:
    email: str = "add_user_test@email.com"
    user: Result[User] = api.get_user(email)
    assert user.failed, "Expected get_user to fail"
    assert user.reason == "User with email: add_user_test@email.com not found"
