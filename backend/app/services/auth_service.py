from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import create_access_token, create_refresh_token, hash_password, verify_password


class AuthService:
    async def register(
        self, db: AsyncSession, email: str, password: str, display_name: str
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def login(
        self, db: AsyncSession, email: str, password: str
    ) -> tuple[User, str, str]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return user, access_token, refresh_token
