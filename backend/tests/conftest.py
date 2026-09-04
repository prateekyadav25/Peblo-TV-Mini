import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base
from app.models.user import User
from app.models.show import Show
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.models.publish_run import PublishRun

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_pytest.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

from app.database import get_db
from app.main import app

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

from app.models.user import User
from app.services.auth_service import AuthService

@pytest_asyncio.fixture
async def setup_users(db_session):
    admin = User(
        username="admin_test@peblo.tv",
        password_hash=AuthService.get_password_hash("admin"),
        role="admin"
    )
    editor = User(
        username="editor_test@peblo.tv",
        password_hash=AuthService.get_password_hash("editor"),
        role="editor"
    )
    db_session.add(admin)
    db_session.add(editor)
    await db_session.commit()

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture
async def auth_token(setup_users, db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/admin/auth/token", data={"username": "admin_test@peblo.tv", "password": "admin"})
        return res.json()["access_token"]

@pytest_asyncio.fixture
async def editor_token(setup_users, db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/admin/auth/token", data={"username": "editor_test@peblo.tv", "password": "editor"})
        return res.json()["access_token"]

