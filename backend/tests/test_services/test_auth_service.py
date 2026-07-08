import pytest

from app.services.auth_service import AuthService
from app.utils.security import decode_token, verify_password


@pytest.mark.asyncio
async def test_register_creates_user(db_session):
    service = AuthService()
    user = await service.register(
        db=db_session,
        email="new@example.com",
        password="securepass123",
        display_name="New User",
    )

    assert user.email == "new@example.com"
    assert user.display_name == "New User"
    assert user.password_hash is not None
    assert verify_password("securepass123", user.password_hash)


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(db_session):
    service = AuthService()
    await service.register(db_session, "dup@example.com", "pass123", "User1")

    with pytest.raises(ValueError, match="Email already registered"):
        await service.register(db_session, "dup@example.com", "pass456", "User2")


@pytest.mark.asyncio
async def test_login_returns_tokens(db_session):
    service = AuthService()
    await service.register(db_session, "login@example.com", "mypass", "Login User")

    user, access_token, refresh_token = await service.login(
        db=db_session, email="login@example.com", password="mypass"
    )

    assert user.email == "login@example.com"
    payload = decode_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"

    refresh_payload = decode_token(refresh_token)
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_login_wrong_password_raises(db_session):
    service = AuthService()
    await service.register(db_session, "wrong@example.com", "correct", "User")

    with pytest.raises(ValueError, match="Invalid email or password"):
        await service.login(db_session, "wrong@example.com", "incorrect")


@pytest.mark.asyncio
async def test_login_nonexistent_email_raises(db_session):
    service = AuthService()

    with pytest.raises(ValueError, match="Invalid email or password"):
        await service.login(db_session, "nobody@example.com", "anypass")
