import os
import sys
import asyncio
import json
from io import BytesIO
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.models.artwork import Artwork
from app.services.auth_service import AuthService
from app.storage.local import LocalStorageBackend
from app.config import settings
from sqlalchemy.future import select

async def create_default_users():
    async with AsyncSessionLocal() as db:
        admin_username = os.getenv("ADMIN_EMAIL", "admin_test@peblo.tv")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        editor_username = os.getenv("EDITOR_EMAIL", "editor_test@peblo.tv")
        editor_password = os.getenv("EDITOR_PASSWORD", "editor")

        # Create admin
        result = await db.execute(select(User).where(User.username == admin_username))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                username=admin_username,
                password_hash=AuthService.get_password_hash(admin_password),
                role="admin"
            )
            db.add(admin)

        # Create editor
        result = await db.execute(select(User).where(User.username == editor_username))
        editor = result.scalar_one_or_none()
        if not editor:
            editor = User(
                username=editor_username,
                password_hash=AuthService.get_password_hash(editor_password),
                role="editor"
            )
            db.add(editor)
            
        await db.commit()
        print("Default users created/verified.")


async def seed_content():
    module_path = os.path.abspath(os.path.dirname(__file__))
    seed_candidates = [
        os.path.join(module_path, "..", "..", "seed_shows.json"),
        os.path.join(module_path, "..", "seed_shows.json"),
    ]
    seed_path = next((path for path in seed_candidates if os.path.exists(path)), seed_candidates[0])
    with open(seed_path, "r", encoding="utf-8") as seed_file:
        rows = json.load(seed_file)

    async with AsyncSessionLocal() as db:
        storage = LocalStorageBackend()
        shows: dict[str, Show] = {}
        seasons: dict[tuple[str, int], Season] = {}
        episode_rows: list[tuple[Episode, dict]] = []
        for row in rows:
            slug = row["slug"]
            show = shows.get(slug)
            if show is None:
                result = await db.execute(select(Show).where(Show.slug == slug))
                show = result.scalar_one_or_none()
                if show is None:
                    show = Show(
                        slug=slug,
                        title=row["show_title"],
                        section=row.get("section"),
                        categories=row.get("categories", []),
                        synopsis=row.get("synopsis", ""),
                        status="published" if row.get("section") else "draft",
                    )
                    db.add(show)
                    await db.flush()
                shows[slug] = show

            season_number = row.get("season_number", 1)
            season_key = (slug, season_number)
            season = seasons.get(season_key)
            if season is None:
                result = await db.execute(
                    select(Season).where(
                        Season.show_id == show.id,
                        Season.season_number == season_number,
                    )
                )
                season = result.scalar_one_or_none()
                if season is None:
                    season = Season(show_id=show.id, season_number=season_number)
                    db.add(season)
                    await db.flush()
                seasons[season_key] = season

            result = await db.execute(
                select(Episode).where(
                    Episode.content_group == row["content_group"],
                    Episode.language == row["language"],
                )
            )
            if result.scalar_one_or_none() is None:
                episode = Episode(
                    season_id=season.id,
                    episode_number=row["episode_number"],
                    title=row["episode_title"],
                    duration_seconds=row.get("duration_seconds"),
                    language=row["language"],
                    content_group=row["content_group"],
                    status=row.get("status", "draft"),
                )
                db.add(episode)
                await db.flush()
                episode_rows.append((episode, row))

        for show in shows.values():
            for artwork_type, dimensions in {
                "poster": (600, 900),
                "banner": (1280, 720),
                "thumbnail": (640, 360),
            }.items():
                result = await db.execute(select(Artwork).where(Artwork.show_id == show.id, Artwork.artwork_type == artwork_type))
                if result.scalar_one_or_none() is not None:
                    continue
                content = _placeholder_image(show.title, dimensions)
                key = f"artwork/{show.slug}/{artwork_type}.jpg"
                await storage.put(key, content, "image/jpeg")
                db.add(Artwork(
                    show_id=show.id,
                    artwork_type=artwork_type,
                    storage_key=key,
                    original_name=f"{show.slug}-{artwork_type}.jpg",
                    width=dimensions[0],
                    height=dimensions[1],
                    file_size=len(content),
                    mime_type="image/jpeg",
                ))

        for episode, row in episode_rows:
            result = await db.execute(select(Artwork).where(Artwork.episode_id == episode.id, Artwork.artwork_type == "thumbnail"))
            if result.scalar_one_or_none() is not None:
                continue
            content = _placeholder_image(row["episode_title"], (640, 360))
            key = f"artwork/episodes/{episode.id}/thumbnail.jpg"
            await storage.put(key, content, "image/jpeg")
            db.add(Artwork(
                episode_id=episode.id,
                artwork_type="thumbnail",
                storage_key=key,
                original_name=f"{episode.content_group}-thumbnail.jpg",
                width=640,
                height=360,
                file_size=len(content),
                mime_type="image/jpeg",
            ))

        await db.commit()
        print(f"Seeded {len(shows)} shows and {len(rows)} episode rows with local placeholder artwork.")


def _placeholder_image(label: str, dimensions: tuple[int, int]) -> bytes:
    image = Image.new("RGB", dimensions, (24, 54, 78))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, dimensions[0] - 20, dimensions[1] - 20), outline=(231, 184, 85), width=8)
    draw.text((40, dimensions[1] // 2), label[:48], fill=(255, 255, 255))
    output = BytesIO()
    image.save(output, format="JPEG", quality=75, optimize=True)
    return output.getvalue()

async def seed_all():
    await create_default_users()
    await seed_content()


def main():
    asyncio.run(seed_all())
    print("Seed complete.")

if __name__ == "__main__":
    main()
