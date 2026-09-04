import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import settings
from app.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Peblo TV Mini")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/")
def root():
    return {"message": "Peblo TV Mini API"}

from app.routers import auth, catalog, artwork, shows, seasons, episodes
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(artwork.router)
app.include_router(artwork.episode_router)
app.include_router(shows.router)
app.include_router(seasons.router)
app.include_router(episodes.router)

