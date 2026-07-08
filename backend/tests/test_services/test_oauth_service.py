import pytest

from app.services.oauth_service import OAuthService


@pytest.mark.asyncio
async def test_create_new_oauth_user(db_session):
    service = OAuthService()
    user = await service.get_or_create_user(
        db=db_session,
        provider="google",
        oauth_id="google-abc",
        email="oauth@gmail.com",
        display_name="OAuth User",
        avatar_url="https://example.com/avatar.png",
    )

    assert user.email == "oauth@gmail.com"
    assert user.oauth_provider == "google"
    assert user.oauth_id == "google-abc"
    assert user.password_hash is None
    assert user.avatar_url == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_existing_oauth_user_returns_same(db_session):
    service = OAuthService()
    user1 = await service.get_or_create_user(
        db_session, "github", "gh-123", "gh@test.com", "GH User", None
    )
    user2 = await service.get_or_create_user(
        db_session, "github", "gh-123", "gh@test.com", "GH User Updated", None
    )

    assert user1.id == user2.id
    assert user2.display_name == "GH User Updated"


@pytest.mark.asyncio
async def test_same_email_different_provider_links(db_session):
    service = OAuthService()
    user1 = await service.get_or_create_user(
        db_session, "google", "g-1", "same@test.com", "User", None
    )
    user2 = await service.get_or_create_user(
        db_session, "line", "l-1", "same@test.com", "User", None
    )

    assert user1.id == user2.id
