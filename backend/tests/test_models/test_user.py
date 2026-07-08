import pytest
from sqlalchemy import select

from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    saved = result.scalar_one()

    assert saved.email == "test@example.com"
    assert saved.display_name == "Test User"
    assert saved.role == UserRole.USER
    assert saved.id is not None
    assert saved.created_at is not None


@pytest.mark.asyncio
async def test_user_role_default(db_session):
    user = User(
        email="default@example.com",
        password_hash="hashed",
        display_name="Default",
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "default@example.com"))
    saved = result.scalar_one()

    assert saved.role == UserRole.USER


@pytest.mark.asyncio
async def test_oauth_user_no_password(db_session):
    user = User(
        email="oauth@example.com",
        display_name="OAuth User",
        oauth_provider="google",
        oauth_id="google-123",
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "oauth@example.com"))
    saved = result.scalar_one()

    assert saved.password_hash is None
    assert saved.oauth_provider == "google"
