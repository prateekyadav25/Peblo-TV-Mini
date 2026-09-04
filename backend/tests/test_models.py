import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from app.models.base import Base
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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

@pytest.mark.asyncio
async def test_published_show_must_have_section(db_session: AsyncSession):
    # This should fail because section is NULL and status is 'published'
    show = Show(title="Test Show", slug="test-show", status="published", section=None)
    db_session.add(show)
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_draft_show_can_have_null_section(db_session: AsyncSession):
    # This should succeed because status is 'draft'
    show = Show(title="Test Show 2", slug="test-show-2", status="draft", section=None)
    db_session.add(show)
    await db_session.commit()
    assert show.id is not None

@pytest.mark.asyncio
async def test_published_episode_must_have_duration(db_session: AsyncSession):
    show = Show(title="Show", slug="show-1", status="draft")
    db_session.add(show)
    await db_session.flush()

    season = Season(show_id=show.id, season_number=1)
    db_session.add(season)
    await db_session.flush()

    # This should fail because duration_seconds is NULL and status is 'published'
    ep = Episode(
        season_id=season.id,
        episode_number=1,
        title="Ep 1",
        language="en",
        content_group="group1",
        status="published",
        duration_seconds=None
    )
    db_session.add(ep)
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_episode_content_group_language_unique(db_session: AsyncSession):
    show = Show(title="Show", slug="show-2", status="draft")
    db_session.add(show)
    await db_session.flush()

    season = Season(show_id=show.id, season_number=1)
    db_session.add(season)
    await db_session.flush()

    ep1 = Episode(
        season_id=season.id,
        episode_number=1,
        title="Ep 1",
        language="en",
        content_group="group_duplicate",
        status="draft"
    )
    db_session.add(ep1)
    await db_session.commit()

    ep2 = Episode(
        season_id=season.id,
        episode_number=2,
        title="Ep 2",
        language="en",
        content_group="group_duplicate", # Duplicate content_group + language
        status="draft"
    )
    db_session.add(ep2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
