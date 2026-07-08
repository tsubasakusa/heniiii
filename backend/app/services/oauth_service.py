from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class OAuthService:
    async def get_or_create_user(
        self,
        db: AsyncSession,
        provider: str,
        oauth_id: str,
        email: str,
        display_name: str,
        avatar_url: str | None,
    ) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            if display_name:
                user.display_name = display_name
            if avatar_url:
                user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)
            return user

        user = User(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            oauth_provider=provider,
            oauth_id=oauth_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
