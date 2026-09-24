from short_url.models import User
from short_url.repositories import Result
from short_url.unit_of_work import PostgresUnitOfWork

TEST_EMAIL: str = "add_user_test@email.com"


def test_add_user_success(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        result: Result[User] = api.users.add(TEST_EMAIL)
        assert not result.failed, "Expected add to succeed"
        assert isinstance(result.value, User), \
            f"Expected type {User.__name__}, got {type(result.value).__name__}"
        assert result.value.email == TEST_EMAIL, \
            f"Expected email {TEST_EMAIL}, got {result.value.email}"
        assert result.value.id is not None, "Expected primary key ID after flush"


def test_add_user_duplicate_failure(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        assert not api.users.add(TEST_EMAIL).failed, "Expected initial add to succeed"

    with postgres_uow.transaction() as api:
        duplicate: Result[User] = api.users.add(TEST_EMAIL)
        assert duplicate.failed, "Expected duplicate email insertion to fail"
        correct_reason: bool = "users_email_key" in duplicate.reason \
                               or "unique constraint" in duplicate.reason.lower()
        assert correct_reason, f"Expected constraint failure reason, got: {duplicate.reason}"


def test_get_user_success(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        api.users.add(TEST_EMAIL)

    with postgres_uow.transaction() as api:
        user: Result[User] = api.users.get(TEST_EMAIL)
        assert not user.failed, "Expected get_user to succeed"
        assert isinstance(user.value, User), \
            f"Expected value type {User.__name__}, got {type(user.value).__name__}"
        assert user.value.email == TEST_EMAIL, \
            f"Expected email to be {TEST_EMAIL}, got {user.value.email}"


def test_get_user_not_found(postgres_uow: PostgresUnitOfWork) -> None:
    with postgres_uow.transaction() as api:
        user: Result[User] = api.users.get("nonexistent@email.com")

        assert user.failed, "Expected get_user to fail for non-existent user"
        assert user.reason == "User with email: nonexistent@email.com not found"
