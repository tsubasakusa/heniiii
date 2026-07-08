from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.auth import TokenResponse
from app.services.oauth_service import OAuthService
from app.utils.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])
oauth_service = OAuthService()

PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": "openid email profile",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": "read:user user:email",
    },
    "line": {
        "auth_url": "https://access.line.me/oauth2/v2.1/authorize",
        "token_url": "https://api.line.me/oauth2/v2.1/token",
        "userinfo_url": "https://api.line.me/v2/profile",
        "scopes": "profile openid email",
    },
}


def _validate_provider(provider: str) -> None:
    if provider not in PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")


def _get_client_credentials(provider: str) -> tuple[str, str]:
    creds = {
        "google": (settings.google_client_id, settings.google_client_secret),
        "github": (settings.github_client_id, settings.github_client_secret),
        "line": (settings.line_channel_id, settings.line_channel_secret),
    }
    client_id, client_secret = creds[provider]
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider} OAuth not configured",
        )
    return client_id, client_secret


def _build_redirect_uri(provider: str) -> str:
    return f"{settings.frontend_url}/auth/callback/{provider}"


def _extract_userinfo(provider: str, data: dict) -> tuple[str, str, str | None, str]:
    if provider == "google":
        return data["email"], data.get("name", ""), data.get("picture"), data["id"]
    if provider == "github":
        return data.get("email", ""), data.get("login", ""), data.get("avatar_url"), str(data["id"])
    if provider == "line":
        return data.get("email", ""), data.get("displayName", ""), data.get("pictureUrl"), data["userId"]
    raise ValueError(f"Unknown provider: {provider}")


@router.get("/{provider}")
async def oauth_redirect(provider: str):
    _validate_provider(provider)

    client_id, _ = _get_client_credentials(provider)
    config = PROVIDERS[provider]
    redirect_uri = _build_redirect_uri(provider)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": config["scopes"],
        "response_type": "code",
    }
    return {"redirect_url": f"{config['auth_url']}?{urlencode(params)}"}


async def _exchange_code_for_token(
    http: AsyncClient, config: dict, client_id: str, client_secret: str, code: str, redirect_uri: str
) -> str:
    token_resp = await http.post(
        config["token_url"],
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json"},
    )
    token_data = token_resp.json()
    oauth_token = token_data.get("access_token")
    if not oauth_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get OAuth token")
    return oauth_token


@router.post("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    _validate_provider(provider)

    client_id, client_secret = _get_client_credentials(provider)
    config = PROVIDERS[provider]
    redirect_uri = _build_redirect_uri(provider)

    async with AsyncClient() as http:
        oauth_token = await _exchange_code_for_token(
            http, config, client_id, client_secret, code, redirect_uri
        )

        userinfo_resp = await http.get(
            config["userinfo_url"],
            headers={"Authorization": f"Bearer {oauth_token}"},
        )
        userinfo = userinfo_resp.json()

    email, display_name, avatar_url, oauth_id = _extract_userinfo(provider, userinfo)

    user = await oauth_service.get_or_create_user(
        db, provider, oauth_id, email, display_name, avatar_url
    )

    token_payload = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
