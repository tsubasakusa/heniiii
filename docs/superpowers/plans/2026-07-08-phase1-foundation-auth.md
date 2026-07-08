# Phase 1：基礎建設 + 認證 — 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 heniiii 語言學習平台的基礎架構，包含 Docker Compose 環境、PostgreSQL 資料庫、FastAPI 後端骨架、SvelteKit 前端骨架、完整的認證系統（帳密 + OAuth），以及角色權限控制。

**Architecture:** 單體架構，FastAPI 後端提供 REST API，SvelteKit 前端以 route group 區分前台/後台。所有服務以 Docker Compose 編排，PostgreSQL 為主資料庫，Redis 用於 session/token 儲存。後端採 Service Layer 模式，將業務邏輯與路由層分離。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, Redis (via redis-py), SvelteKit 2, TypeScript, Docker Compose, PostgreSQL 16

## Global Constraints

- Python >= 3.12，使用 `pyproject.toml` 管理依賴
- Node.js >= 20，使用 pnpm 作為套件管理器
- SQLAlchemy 2.0 async 模式，不使用 legacy query API
- Pydantic v2（使用 `model_validator` 而非 v1 的 `validator`）
- 所有 API 回傳格式統一為 `{"data": ..., "message": "..."}` 或錯誤 `{"detail": "..."}`
- 密碼雜湊使用 bcrypt（passlib）
- JWT 使用 python-jose，算法 HS256
- 所有時間戳使用 UTC，前端顯示時轉換為使用者時區
- commit message 使用 Conventional Commits 格式

---

### Task 1: Docker Compose 環境與專案骨架

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `backend/Dockerfile`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/svelte.config.js`

**Interfaces:**
- Consumes: 無
- Produces: 可啟動的 Docker Compose 環境，FastAPI 回應 `GET /health`，SvelteKit 回應首頁

- [ ] **Step 1: 建立 `.env.example`**

```env
# Database
POSTGRES_USER=heniiii
POSTGRES_PASSWORD=heniiii_dev
POSTGRES_DB=heniiii
DATABASE_URL=postgresql+asyncpg://heniiii:heniiii_dev@db:5432/heniiii

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
LINE_CHANNEL_ID=
LINE_CHANNEL_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# App
APP_ENV=development
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
```

- [ ] **Step 2: 建立 `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    env_file: .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: pnpm dev --host 0.0.0.0

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 3: 建立 `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system -e .

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: 建立 `backend/pyproject.toml`**

```toml
[project]
name = "heniiii-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "redis>=5.0.0",
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
]
```

- [ ] **Step 5: 建立 `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    google_client_id: str = ""
    google_client_secret: str = ""
    line_channel_id: str = ""
    line_channel_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 6: 建立 `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Heniiii API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 7: 建立 SvelteKit 前端專案**

```bash
cd frontend
pnpm create svelte@latest . --template skeleton --types typescript
pnpm install
```

- [ ] **Step 8: 建立 `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

- [ ] **Step 9: 啟動 Docker Compose 驗證**

Run: `cp .env.example .env && docker compose up --build -d`

驗證：
- `curl http://localhost:8000/health` → `{"status": "ok"}`
- 瀏覽器開啟 `http://localhost:5173` → SvelteKit 歡迎頁面

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: 建立 Docker Compose 環境與前後端專案骨架"
```

---

### Task 2: 資料庫連線與 Alembic Migration 設定

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.gitkeep`

**Interfaces:**
- Consumes: `config.settings.database_url`
- Produces: `database.async_engine`, `database.AsyncSessionLocal`, `database.get_db()` async generator（FastAPI dependency）, `database.Base`（SQLAlchemy declarative base）

- [ ] **Step 1: 建立 `backend/app/database.py`**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

async_engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: 初始化 Alembic**

```bash
cd backend
alembic init alembic
```

- [ ] **Step 3: 修改 `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 修改 `backend/alembic.ini`**

將 `sqlalchemy.url` 設為空值（由 env.py 從 settings 讀取）：

```ini
sqlalchemy.url =
```

- [ ] **Step 5: 驗證 Alembic 可運行**

Run: `docker compose exec backend alembic heads`
Expected: 正常輸出，無 error

- [ ] **Step 6: Commit**

```bash
git add backend/app/database.py backend/alembic.ini backend/alembic/
git commit -m "feat: 設定資料庫連線與 Alembic migration"
```

---

### Task 3: User Model 與 Migration

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/alembic/versions/xxxx_create_users_table.py`（auto-generated）
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_models/__init__.py`
- Create: `backend/tests/test_models/test_user.py`

**Interfaces:**
- Consumes: `database.Base`
- Produces: `models.user.User` model（id: UUID, email: str, password_hash: str|None, display_name: str, avatar_url: str|None, role: UserRole, oauth_provider: str|None, oauth_id: str|None, created_at: datetime, updated_at: datetime）, `models.user.UserRole` enum（admin, editor, user）

- [ ] **Step 1: 建立 User model 的測試**

```python
# backend/tests/conftest.py
import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
```

```python
# backend/tests/test_models/test_user.py
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
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `docker compose exec backend pytest tests/test_models/test_user.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.user'`

- [ ] **Step 3: 建立 User model**

```python
# backend/app/models/__init__.py
from app.models.user import User, UserRole

__all__ = ["User", "UserRole"]
```

```python
# backend/app/models/user.py
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, server_default="user"
    )
    oauth_provider: Mapped[str | None] = mapped_column(String(50))
    oauth_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [ ] **Step 4: 加入 aiosqlite 測試依賴**

在 `pyproject.toml` 的 `[project.optional-dependencies]` dev 區加入：

```toml
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
    "aiosqlite>=0.20.0",
]
```

- [ ] **Step 5: 執行測試確認通過**

Run: `docker compose exec backend pytest tests/test_models/test_user.py -v`
Expected: 3 passed

- [ ] **Step 6: 產生 Alembic migration**

```bash
docker compose exec backend alembic revision --autogenerate -m "create users table"
docker compose exec backend alembic upgrade head
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/tests/ backend/alembic/versions/
git commit -m "feat: 建立 User model、migration 與測試"
```

---

### Task 4: Redis 連線與認證 Service — 註冊/登入

**Files:**
- Create: `backend/app/redis.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/security.py`
- Create: `backend/tests/test_services/__init__.py`
- Create: `backend/tests/test_services/test_auth_service.py`

**Interfaces:**
- Consumes: `models.user.User`, `models.user.UserRole`, `database.get_db()`
- Produces:
  - `redis.get_redis()` → `redis.asyncio.Redis`
  - `utils.security.hash_password(password: str) -> str`
  - `utils.security.verify_password(plain: str, hashed: str) -> bool`
  - `utils.security.create_access_token(data: dict) -> str`
  - `utils.security.create_refresh_token(data: dict) -> str`
  - `utils.security.decode_token(token: str) -> dict`
  - `services.auth_service.AuthService.register(db, email, password, display_name) -> User`
  - `services.auth_service.AuthService.login(db, email, password) -> tuple[User, str, str]`
  - `schemas.auth.RegisterRequest(email: str, password: str, display_name: str)`
  - `schemas.auth.LoginRequest(email: str, password: str)`
  - `schemas.auth.TokenResponse(access_token: str, refresh_token: str, token_type: str)`
  - `schemas.auth.UserResponse(id: UUID, email: str, display_name: str, avatar_url: str|None, role: str)`

- [ ] **Step 1: 建立 `backend/app/redis.py`**

```python
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.config import settings

redis_pool = aioredis.ConnectionPool.from_url(settings.redis_url)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
```

- [ ] **Step 2: 建立 `backend/app/utils/security.py`**

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
```

- [ ] **Step 3: 建立 `backend/app/schemas/auth.py`**

```python
import uuid

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    avatar_url: str | None
    role: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: 寫 AuthService 的測試**

```python
# backend/tests/test_services/test_auth_service.py
import pytest
from sqlalchemy import select

from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.security import verify_password, decode_token


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
```

- [ ] **Step 5: 執行測試確認失敗**

Run: `docker compose exec backend pytest tests/test_services/test_auth_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.auth_service'`

- [ ] **Step 6: 建立 `backend/app/services/auth_service.py`**

```python
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
```

- [ ] **Step 7: 加入 email-validator 依賴**

在 `pyproject.toml` 的 dependencies 加入：

```
"email-validator>=2.0.0",
```

- [ ] **Step 8: 執行測試確認通過**

Run: `docker compose exec backend pytest tests/test_services/test_auth_service.py -v`
Expected: 5 passed

- [ ] **Step 9: Commit**

```bash
git add backend/app/redis.py backend/app/utils/ backend/app/schemas/ backend/app/services/ backend/tests/test_services/
git commit -m "feat: 建立認證 Service（註冊/登入）與 JWT token 工具"
```

---

### Task 5: 認證 API Router 與 Middleware

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/dependencies.py`
- Modify: `backend/app/main.py` — 註冊 router
- Create: `backend/tests/test_routers/__init__.py`
- Create: `backend/tests/test_routers/test_auth.py`

**Interfaces:**
- Consumes: `services.auth_service.AuthService`, `schemas.auth.*`, `utils.security.decode_token`, `redis.get_redis`
- Produces:
  - `POST /auth/register` → `TokenResponse`
  - `POST /auth/login` → `TokenResponse`
  - `POST /auth/refresh` → `TokenResponse`
  - `POST /auth/logout` → `{"message": "..."}`
  - `GET /auth/me` → `UserResponse`
  - `dependencies.get_current_user(token, db) -> User`（FastAPI dependency，從 Authorization header 取 JWT 解析出使用者）
  - `dependencies.require_role(*roles: UserRole)` → dependency factory，檢查使用者角色

- [ ] **Step 1: 建立 `backend/app/dependencies.py`**

```python
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker
```

- [ ] **Step 2: 建立 `backend/app/routers/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.redis import get_redis
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.security import create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.register(db, req.email, req.password, req.display_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    _, access_token, refresh_token = await auth_service.login(db, req.email, req.password)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        _, access_token, refresh_token = await auth_service.login(db, req.email, req.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    is_blacklisted = await redis.get(f"blacklist:{refresh_token}")
    if is_blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    token_data = {"sub": payload["sub"], "role": payload["role"]}
    new_access_token = create_access_token(token_data)
    return TokenResponse(access_token=new_access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    refresh_token: str,
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    await redis.set(f"blacklist:{refresh_token}", "1", ex=60 * 60 * 24 * 7)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 3: 修改 `backend/app/main.py` 註冊 router**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth

app = FastAPI(title="Heniiii API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: 寫 API 整合測試**

```python
# backend/tests/test_routers/test_auth.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": "reg@example.com",
        "password": "testpass123",
        "display_name": "Reg User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate(client):
    payload = {"email": "dup2@example.com", "password": "pass", "display_name": "User"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={
        "email": "login2@example.com",
        "password": "mypass",
        "display_name": "User",
    })
    resp = await client.post("/auth/login", json={
        "email": "login2@example.com",
        "password": "mypass",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrong2@example.com",
        "password": "correct",
        "display_name": "User",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrong2@example.com",
        "password": "incorrect",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    reg = await client.post("/auth/register", json={
        "email": "me@example.com",
        "password": "pass123",
        "display_name": "Me User",
    })
    token = reg.json()["access_token"]

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403
```

- [ ] **Step 5: 執行測試確認通過**

Run: `docker compose exec backend pytest tests/test_routers/test_auth.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/dependencies.py backend/app/routers/ backend/tests/test_routers/
git commit -m "feat: 建立認證 API（註冊/登入/refresh/logout/me）與權限 middleware"
```

---

### Task 6: OAuth 登入（Google / LINE / GitHub）

**Files:**
- Create: `backend/app/services/oauth_service.py`
- Create: `backend/app/routers/oauth.py`
- Modify: `backend/app/main.py` — 註冊 oauth router
- Create: `backend/tests/test_services/test_oauth_service.py`

**Interfaces:**
- Consumes: `models.user.User`, `services.auth_service.AuthService`, `utils.security.create_access_token`, `utils.security.create_refresh_token`
- Produces:
  - `services.oauth_service.OAuthService.get_or_create_user(db, provider, oauth_id, email, display_name, avatar_url) -> User`
  - `GET /auth/oauth/{provider}` → redirect URL
  - `POST /auth/oauth/{provider}/callback` → `TokenResponse`

- [ ] **Step 1: 寫 OAuthService 測試**

```python
# backend/tests/test_services/test_oauth_service.py
import pytest
from sqlalchemy import select

from app.models.user import User
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
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `docker compose exec backend pytest tests/test_services/test_oauth_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 建立 `backend/app/services/oauth_service.py`**

```python
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
```

- [ ] **Step 4: 執行測試確認通過**

Run: `docker compose exec backend pytest tests/test_services/test_oauth_service.py -v`
Expected: 3 passed

- [ ] **Step 5: 建立 `backend/app/routers/oauth.py`**

```python
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


def _get_client_credentials(provider: str) -> tuple[str, str]:
    creds = {
        "google": (settings.google_client_id, settings.google_client_secret),
        "github": (settings.github_client_id, settings.github_client_secret),
        "line": (settings.line_channel_id, settings.line_channel_secret),
    }
    client_id, client_secret = creds[provider]
    if not client_id or not client_secret:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"{provider} OAuth not configured")
    return client_id, client_secret


@router.get("/{provider}")
async def oauth_redirect(provider: str):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")

    client_id, _ = _get_client_credentials(provider)
    config = PROVIDERS[provider]
    redirect_uri = f"{settings.frontend_url}/auth/callback/{provider}"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": config["scopes"],
        "response_type": "code",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"redirect_url": f"{config['auth_url']}?{query}"}


@router.post("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")

    client_id, client_secret = _get_client_credentials(provider)
    config = PROVIDERS[provider]
    redirect_uri = f"{settings.frontend_url}/auth/callback/{provider}"

    async with AsyncClient() as http:
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
            raise HTTPException(status_code=400, detail="Failed to get OAuth token")

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


def _extract_userinfo(provider: str, data: dict) -> tuple[str, str, str | None, str]:
    if provider == "google":
        return data["email"], data.get("name", ""), data.get("picture"), data["id"]
    if provider == "github":
        return data.get("email", ""), data.get("login", ""), data.get("avatar_url"), str(data["id"])
    if provider == "line":
        return data.get("email", ""), data.get("displayName", ""), data.get("pictureUrl"), data["userId"]
    raise ValueError(f"Unknown provider: {provider}")
```

- [ ] **Step 6: 修改 `backend/app/main.py` 加入 oauth router**

```python
from app.routers import auth, oauth

# 在 app.include_router(auth.router) 下方加入：
app.include_router(oauth.router)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/oauth_service.py backend/app/routers/oauth.py backend/tests/test_services/test_oauth_service.py backend/app/main.py
git commit -m "feat: 建立 OAuth 登入（Google / LINE / GitHub）"
```

---

### Task 7: SvelteKit 前端骨架 — Layout、認證 Store、API Client

**Files:**
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/stores/auth.ts`
- Create: `frontend/src/routes/+layout.svelte`
- Create: `frontend/src/routes/+layout.ts`
- Create: `frontend/src/routes/+page.svelte`
- Create: `frontend/src/routes/(auth)/login/+page.svelte`
- Create: `frontend/src/routes/(auth)/register/+page.svelte`
- Create: `frontend/src/routes/(auth)/callback/[provider]/+page.svelte`
- Create: `frontend/src/routes/(app)/+layout.svelte`
- Create: `frontend/src/routes/(admin)/+layout.svelte`

**Interfaces:**
- Consumes: FastAPI `/auth/*` endpoints
- Produces:
  - `lib/api/client.ts` — `apiClient.get/post/put/delete(path, data?)` 自動帶 JWT token，自動 refresh
  - `lib/stores/auth.ts` — `authStore`（user, isLoggedIn, login, register, logout, refreshToken）
  - 前台 layout 含 nav bar（首頁/學習/每日挑戰/單字卡/排行榜/部落格/搜尋/登入）
  - `(app)` layout 檢查登入狀態，未登入跳轉 `/login`
  - `(admin)` layout 檢查 admin/editor 角色

- [ ] **Step 1: 建立 `frontend/src/lib/api/client.ts`**

```typescript
import { get } from 'svelte/store';
import { authStore } from '$lib/stores/auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = get(authStore).accessToken;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && token) {
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${get(authStore).accessToken}`;
        const retryResponse = await fetch(`${API_BASE}${path}`, { ...options, headers });
        if (!retryResponse.ok) throw await this.parseError(retryResponse);
        return retryResponse.json();
      }
      authStore.logout();
      window.location.href = '/login';
    }

    if (!response.ok) throw await this.parseError(response);
    return response.json();
  }

  private async tryRefresh(): Promise<boolean> {
    const refreshToken = get(authStore).refreshToken;
    if (!refreshToken) return false;

    try {
      const resp = await fetch(`${API_BASE}/auth/refresh?refresh_token=${refreshToken}`, {
        method: 'POST',
      });
      if (!resp.ok) return false;
      const data = await resp.json();
      authStore.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  private async parseError(response: Response) {
    const body = await response.json().catch(() => ({}));
    return { status: response.status, detail: body.detail || 'Unknown error' };
  }

  get<T>(path: string) {
    return this.request<T>(path);
  }

  post<T>(path: string, data?: unknown) {
    return this.request<T>(path, { method: 'POST', body: JSON.stringify(data) });
  }

  put<T>(path: string, data?: unknown) {
    return this.request<T>(path, { method: 'PUT', body: JSON.stringify(data) });
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
```

- [ ] **Step 2: 建立 `frontend/src/lib/stores/auth.ts`**

```typescript
import { writable, derived } from 'svelte/store';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: {
    id: string;
    email: string;
    display_name: string;
    avatar_url: string | null;
    role: string;
  } | null;
}

function createAuthStore() {
  const stored = typeof localStorage !== 'undefined'
    ? JSON.parse(localStorage.getItem('auth') || 'null')
    : null;

  const { subscribe, set, update } = writable<AuthState>(stored || {
    accessToken: null,
    refreshToken: null,
    user: null,
  });

  function persist(state: AuthState) {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('auth', JSON.stringify(state));
    }
  }

  return {
    subscribe,

    setTokens(accessToken: string, refreshToken: string) {
      update((state) => {
        const newState = { ...state, accessToken, refreshToken };
        persist(newState);
        return newState;
      });
    },

    setUser(user: AuthState['user']) {
      update((state) => {
        const newState = { ...state, user };
        persist(newState);
        return newState;
      });
    },

    logout() {
      const empty: AuthState = { accessToken: null, refreshToken: null, user: null };
      set(empty);
      persist(empty);
    },
  };
}

export const authStore = createAuthStore();
export const isLoggedIn = derived(authStore, ($auth) => !!$auth.accessToken);
export const currentUser = derived(authStore, ($auth) => $auth.user);
```

- [ ] **Step 3: 建立 `frontend/src/routes/+layout.svelte`**

```svelte
<script lang="ts">
  import { isLoggedIn, currentUser, authStore } from '$lib/stores/auth';
  import { page } from '$app/stores';
</script>

<div class="app">
  <nav class="navbar">
    <a href="/" class="logo">Heniiii</a>

    <div class="nav-links">
      <a href="/learn/en">English</a>
      <a href="/learn/ja">日文</a>
      <a href="/learn/tailo">台語</a>
      <a href="/daily">每日挑戰</a>
      <a href="/leaderboard">排行榜</a>
      <a href="/blog">部落格</a>
    </div>

    <div class="nav-auth">
      {#if $isLoggedIn}
        <a href="/flashcards">單字卡</a>
        <a href="/profile">{$currentUser?.display_name}</a>
        <button on:click={() => authStore.logout()}>登出</button>
      {:else}
        <a href="/login">登入</a>
        <a href="/register" class="btn-register">註冊</a>
      {/if}
    </div>
  </nav>

  <main>
    <slot />
  </main>
</div>

<style>
  .app {
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  .navbar {
    display: flex;
    align-items: center;
    padding: 0 2rem;
    height: 64px;
    border-bottom: 1px solid #e5e7eb;
    background: white;
  }

  .logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111;
    text-decoration: none;
    margin-right: 2rem;
  }

  .nav-links {
    display: flex;
    gap: 1.5rem;
    flex: 1;
  }

  .nav-links a, .nav-auth a {
    text-decoration: none;
    color: #374151;
    font-size: 0.9rem;
  }

  .nav-links a:hover, .nav-auth a:hover {
    color: #111;
  }

  .nav-auth {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .btn-register {
    background: #111;
    color: white !important;
    padding: 0.5rem 1rem;
    border-radius: 6px;
  }

  button {
    background: none;
    border: 1px solid #d1d5db;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
</style>
```

- [ ] **Step 4: 建立首頁 `frontend/src/routes/+page.svelte`**

```svelte
<script lang="ts">
  import { isLoggedIn } from '$lib/stores/auth';
</script>

<svelte:head>
  <title>Heniiii — 語言學習平台</title>
</svelte:head>

<section class="hero">
  <h1>學英文、日文、台語</h1>
  <p>透過每日填字挑戰、單字卡和分級課程，讓語言學習成為日常習慣。</p>

  {#if !$isLoggedIn}
    <div class="cta">
      <a href="/register" class="btn-primary">免費開始</a>
      <a href="/daily" class="btn-secondary">先看看每日挑戰</a>
    </div>
  {:else}
    <div class="cta">
      <a href="/daily" class="btn-primary">今日挑戰</a>
      <a href="/flashcards" class="btn-secondary">複習單字卡</a>
    </div>
  {/if}
</section>

<style>
  .hero {
    text-align: center;
    padding: 6rem 2rem;
  }

  h1 {
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 1rem;
    color: #111;
  }

  p {
    font-size: 1.2rem;
    color: #6b7280;
    margin-bottom: 2rem;
  }

  .cta {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .btn-primary {
    background: #111;
    color: white;
    padding: 0.8rem 2rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
  }

  .btn-secondary {
    border: 1px solid #d1d5db;
    color: #374151;
    padding: 0.8rem 2rem;
    border-radius: 8px;
    text-decoration: none;
  }
</style>
```

- [ ] **Step 5: 建立登入頁 `frontend/src/routes/(auth)/login/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client';
  import { authStore } from '$lib/stores/auth';

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    error = '';
    loading = true;
    try {
      const data = await api.post<{ access_token: string; refresh_token: string }>('/auth/login', {
        email,
        password,
      });
      authStore.setTokens(data.access_token, data.refresh_token);

      const user = await api.get<{ id: string; email: string; display_name: string; avatar_url: string | null; role: string }>('/auth/me');
      authStore.setUser(user);

      goto('/');
    } catch (err: any) {
      error = err.detail || '登入失敗';
    } finally {
      loading = false;
    }
  }

  function oauthLogin(provider: string) {
    window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/oauth/${provider}`;
  }
</script>

<svelte:head>
  <title>登入 — Heniiii</title>
</svelte:head>

<div class="auth-page">
  <div class="auth-card">
    <h1>登入</h1>

    {#if error}
      <p class="error">{error}</p>
    {/if}

    <form on:submit|preventDefault={handleLogin}>
      <label>
        Email
        <input type="email" bind:value={email} required />
      </label>

      <label>
        密碼
        <input type="password" bind:value={password} required />
      </label>

      <button type="submit" class="btn-primary" disabled={loading}>
        {loading ? '登入中...' : '登入'}
      </button>
    </form>

    <div class="divider">或</div>

    <div class="oauth-buttons">
      <button on:click={() => oauthLogin('google')}>Google 登入</button>
      <button on:click={() => oauthLogin('line')}>LINE 登入</button>
      <button on:click={() => oauthLogin('github')}>GitHub 登入</button>
    </div>

    <p class="switch">還沒有帳號？<a href="/register">註冊</a></p>
  </div>
</div>

<style>
  .auth-page {
    display: flex;
    justify-content: center;
    padding: 4rem 1rem;
  }

  .auth-card {
    width: 100%;
    max-width: 400px;
  }

  h1 {
    font-size: 1.8rem;
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #374151;
  }

  input {
    display: block;
    width: 100%;
    padding: 0.6rem;
    margin-top: 0.3rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    box-sizing: border-box;
  }

  .btn-primary {
    width: 100%;
    background: #111;
    color: white;
    padding: 0.7rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 0.5rem;
  }

  .btn-primary:disabled {
    opacity: 0.5;
  }

  .divider {
    text-align: center;
    color: #9ca3af;
    margin: 1.5rem 0;
    position: relative;
  }

  .oauth-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .oauth-buttons button {
    padding: 0.6rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .error {
    color: #dc2626;
    background: #fef2f2;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .switch {
    text-align: center;
    margin-top: 1.5rem;
    color: #6b7280;
  }

  .switch a {
    color: #111;
    font-weight: 600;
  }
</style>
```

- [ ] **Step 6: 建立註冊頁 `frontend/src/routes/(auth)/register/+page.svelte`**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client';
  import { authStore } from '$lib/stores/auth';

  let email = '';
  let password = '';
  let displayName = '';
  let error = '';
  let loading = false;

  async function handleRegister() {
    error = '';
    loading = true;
    try {
      const data = await api.post<{ access_token: string; refresh_token: string }>('/auth/register', {
        email,
        password,
        display_name: displayName,
      });
      authStore.setTokens(data.access_token, data.refresh_token);

      const user = await api.get<{ id: string; email: string; display_name: string; avatar_url: string | null; role: string }>('/auth/me');
      authStore.setUser(user);

      goto('/');
    } catch (err: any) {
      error = err.detail || '註冊失敗';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>註冊 — Heniiii</title>
</svelte:head>

<div class="auth-page">
  <div class="auth-card">
    <h1>建立帳號</h1>

    {#if error}
      <p class="error">{error}</p>
    {/if}

    <form on:submit|preventDefault={handleRegister}>
      <label>
        顯示名稱
        <input type="text" bind:value={displayName} required />
      </label>

      <label>
        Email
        <input type="email" bind:value={email} required />
      </label>

      <label>
        密碼
        <input type="password" bind:value={password} required minlength="8" />
      </label>

      <button type="submit" class="btn-primary" disabled={loading}>
        {loading ? '建立中...' : '建立帳號'}
      </button>
    </form>

    <p class="switch">已有帳號？<a href="/login">登入</a></p>
  </div>
</div>

<style>
  .auth-page {
    display: flex;
    justify-content: center;
    padding: 4rem 1rem;
  }

  .auth-card {
    width: 100%;
    max-width: 400px;
  }

  h1 {
    font-size: 1.8rem;
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #374151;
  }

  input {
    display: block;
    width: 100%;
    padding: 0.6rem;
    margin-top: 0.3rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    box-sizing: border-box;
  }

  .btn-primary {
    width: 100%;
    background: #111;
    color: white;
    padding: 0.7rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 0.5rem;
  }

  .btn-primary:disabled {
    opacity: 0.5;
  }

  .error {
    color: #dc2626;
    background: #fef2f2;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .switch {
    text-align: center;
    margin-top: 1.5rem;
    color: #6b7280;
  }

  .switch a {
    color: #111;
    font-weight: 600;
  }
</style>
```

- [ ] **Step 7: 建立 OAuth callback 頁 `frontend/src/routes/(auth)/callback/[provider]/+page.svelte`**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api/client';
  import { authStore } from '$lib/stores/auth';

  let error = '';

  onMount(async () => {
    const provider = $page.params.provider;
    const code = $page.url.searchParams.get('code');

    if (!code) {
      error = '缺少授權碼';
      return;
    }

    try {
      const data = await api.post<{ access_token: string; refresh_token: string }>(
        `/auth/oauth/${provider}/callback?code=${code}`
      );
      authStore.setTokens(data.access_token, data.refresh_token);

      const user = await api.get<{ id: string; email: string; display_name: string; avatar_url: string | null; role: string }>('/auth/me');
      authStore.setUser(user);

      goto('/');
    } catch (err: any) {
      error = err.detail || 'OAuth 登入失敗';
    }
  });
</script>

<div class="callback">
  {#if error}
    <p class="error">{error}</p>
    <a href="/login">返回登入</a>
  {:else}
    <p>登入中...</p>
  {/if}
</div>

<style>
  .callback {
    text-align: center;
    padding: 4rem;
  }

  .error {
    color: #dc2626;
    margin-bottom: 1rem;
  }
</style>
```

- [ ] **Step 8: 建立 `(app)` layout — 登入檢查**

```svelte
<!-- frontend/src/routes/(app)/+layout.svelte -->
<script lang="ts">
  import { isLoggedIn } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  onMount(() => {
    if (!$isLoggedIn) {
      goto('/login');
    }
  });
</script>

{#if $isLoggedIn}
  <slot />
{/if}
```

- [ ] **Step 9: 建立 `(admin)` layout — 角色檢查**

```svelte
<!-- frontend/src/routes/(admin)/+layout.svelte -->
<script lang="ts">
  import { currentUser, isLoggedIn } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  onMount(() => {
    if (!$isLoggedIn) {
      goto('/login');
      return;
    }
    if ($currentUser?.role !== 'admin' && $currentUser?.role !== 'editor') {
      goto('/');
    }
  });
</script>

{#if $isLoggedIn && ($currentUser?.role === 'admin' || $currentUser?.role === 'editor')}
  <slot />
{/if}
```

- [ ] **Step 10: 啟動前端驗證**

Run: `docker compose up frontend -d`

瀏覽器開啟 `http://localhost:5173`：
- 看到首頁 hero section
- 點「登入」跳轉到 `/login` 表單頁面
- 點「註冊」跳轉到 `/register` 頁面
- nav bar 顯示語言、每日挑戰、排行榜等連結

- [ ] **Step 11: Commit**

```bash
git add frontend/src/
git commit -m "feat: 建立 SvelteKit 前端骨架（layout、認證頁面、API client、auth store）"
```

---

### Task 8: Languages 與 Difficulty Levels Seed Data

**Files:**
- Create: `backend/app/models/language.py`
- Create: `backend/app/models/difficulty.py`
- Modify: `backend/app/models/__init__.py` — export 新 model
- Create: `backend/alembic/versions/xxxx_create_languages_and_difficulties.py`（auto-generated）
- Create: `backend/app/seed.py`
- Create: `backend/tests/test_models/test_language.py`

**Interfaces:**
- Consumes: `database.Base`
- Produces:
  - `models.language.Language`（id: int, code: str, name_zh: str, display_system: str）
  - `models.difficulty.DifficultyLevel`（id: int, language_id: FK, slug: str, label_zh: str, sort_order: int）
  - `seed.seed_languages_and_levels(db)` — 寫入 3 語言 + 各自難度分級

- [ ] **Step 1: 寫測試**

```python
# backend/tests/test_models/test_language.py
import pytest
from sqlalchemy import select

from app.models.language import Language
from app.models.difficulty import DifficultyLevel


@pytest.mark.asyncio
async def test_create_language(db_session):
    lang = Language(code="en", name_zh="英文", display_system="alphabet")
    db_session.add(lang)
    await db_session.commit()

    result = await db_session.execute(select(Language).where(Language.code == "en"))
    saved = result.scalar_one()
    assert saved.name_zh == "英文"


@pytest.mark.asyncio
async def test_create_difficulty_level(db_session):
    lang = Language(code="ja", name_zh="日文", display_system="kana_kanji")
    db_session.add(lang)
    await db_session.commit()
    await db_session.refresh(lang)

    level = DifficultyLevel(
        language_id=lang.id, slug="n5", label_zh="N5", sort_order=1
    )
    db_session.add(level)
    await db_session.commit()

    result = await db_session.execute(
        select(DifficultyLevel).where(DifficultyLevel.slug == "n5")
    )
    saved = result.scalar_one()
    assert saved.label_zh == "N5"
    assert saved.language_id == lang.id
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `docker compose exec backend pytest tests/test_models/test_language.py -v`
Expected: FAIL

- [ ] **Step 3: 建立 model 檔案**

```python
# backend/app/models/language.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    name_zh: Mapped[str] = mapped_column(String(50))
    display_system: Mapped[str] = mapped_column(String(50))
```

```python
# backend/app/models/difficulty.py
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DifficultyLevel(Base):
    __tablename__ = "difficulty_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"))
    slug: Mapped[str] = mapped_column(String(50))
    label_zh: Mapped[str] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(default=0)
```

```python
# backend/app/models/__init__.py
from app.models.user import User, UserRole
from app.models.language import Language
from app.models.difficulty import DifficultyLevel

__all__ = ["User", "UserRole", "Language", "DifficultyLevel"]
```

- [ ] **Step 4: 執行測試確認通過**

Run: `docker compose exec backend pytest tests/test_models/test_language.py -v`
Expected: 2 passed

- [ ] **Step 5: 建立 seed 腳本 `backend/app/seed.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.language import Language
from app.models.difficulty import DifficultyLevel

LANGUAGES = [
    {"code": "en", "name_zh": "英文", "display_system": "alphabet"},
    {"code": "ja", "name_zh": "日文", "display_system": "kana_kanji"},
    {"code": "tailo", "name_zh": "台語", "display_system": "tailo_hanzi"},
]

DIFFICULTY_LEVELS = {
    "en": [
        {"slug": "beginner", "label_zh": "初級", "sort_order": 1},
        {"slug": "intermediate", "label_zh": "中級", "sort_order": 2},
        {"slug": "advanced", "label_zh": "高級", "sort_order": 3},
    ],
    "ja": [
        {"slug": "n5", "label_zh": "N5", "sort_order": 1},
        {"slug": "n4", "label_zh": "N4", "sort_order": 2},
        {"slug": "n3", "label_zh": "N3", "sort_order": 3},
        {"slug": "n2", "label_zh": "N2", "sort_order": 4},
        {"slug": "n1", "label_zh": "N1", "sort_order": 5},
    ],
    "tailo": [
        {"slug": "basic", "label_zh": "基礎", "sort_order": 1},
        {"slug": "intermediate", "label_zh": "進階", "sort_order": 2},
        {"slug": "advanced", "label_zh": "高級", "sort_order": 3},
    ],
}


async def seed_languages_and_levels(db: AsyncSession) -> None:
    for lang_data in LANGUAGES:
        result = await db.execute(
            select(Language).where(Language.code == lang_data["code"])
        )
        if result.scalar_one_or_none():
            continue

        lang = Language(**lang_data)
        db.add(lang)
        await db.flush()

        for level_data in DIFFICULTY_LEVELS[lang_data["code"]]:
            level = DifficultyLevel(language_id=lang.id, **level_data)
            db.add(level)

    await db.commit()
```

- [ ] **Step 6: 產生 migration 並執行 seed**

```bash
docker compose exec backend alembic revision --autogenerate -m "create languages and difficulty_levels tables"
docker compose exec backend alembic upgrade head
docker compose exec backend python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.seed import seed_languages_and_levels

async def main():
    async with AsyncSessionLocal() as db:
        await seed_languages_and_levels(db)
        print('Seed complete')

asyncio.run(main())
"
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ backend/app/seed.py backend/alembic/versions/ backend/tests/test_models/test_language.py
git commit -m "feat: 建立 Language、DifficultyLevel model 與 seed data"
```

---

## 計畫摘要

| Task | 內容 | 預估 |
|---|---|---|
| 1 | Docker Compose + 專案骨架 | 15 min |
| 2 | DB 連線 + Alembic | 10 min |
| 3 | User Model + Migration + 測試 | 15 min |
| 4 | Redis + AuthService（註冊/登入）| 20 min |
| 5 | Auth API Router + 權限 Middleware | 20 min |
| 6 | OAuth（Google/LINE/GitHub）| 15 min |
| 7 | SvelteKit 前端骨架 | 25 min |
| 8 | Languages + Difficulty Seed | 10 min |

**Total: ~130 min（約 2 小時）**

Phase 1 完成後，你會有一個可運行的全棧應用，包含完整認證系統與三種語言的基礎資料，可以立即開始 Phase 2-5 的任何一個模組開發。
