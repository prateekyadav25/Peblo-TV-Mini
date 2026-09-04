import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select

from app.api.deps import require_admin, require_editor
from app.database import get_db
from app.models.user import User
from app.services.catalogue_service import CatalogueService
from app.storage import get_storage_backend

router = APIRouter(tags=["Catalog"])


# ─── Admin endpoints ────────────────────────────────────────────────

@router.post("/admin/catalog/publish")
async def publish_catalog(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    """
    Atomically publish a new catalogue snapshot.

    Only admins may trigger this. Editors can CRUD content but not
    publish. The endpoint:

    1. Acquires an in-process publish lock (returns 409 if busy).
    2. Queries all published shows/seasons/episodes.
    3. Collapses content_group variants into single entries.
    4. Writes the JSON to a staging key.
    5. Atomically renames staging -> live (os.replace).
    6. Records the outcome in the publish_runs table.

    Readers hitting GET /api/catalogue always see either the previous
    valid catalogue or the new one — never a partial write.
    """
    storage = get_storage_backend()
    run = await CatalogueService.publish(db, storage, current_user.id, idempotency_key)

    return {
        "status": run.status,
        "user": current_user.username,
        "run_id": str(run.id),
        "shows_count": run.shows_count,
        "episodes_count": run.episodes_count,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/admin/catalog/status")
async def publish_status(current_user: User = Depends(require_editor)):
    """Return a simple status check (placeholder for richer status later)."""
    return {"message": "Status OK", "user": current_user.username}

from app.services.validation_service import DBValidator

@router.get("/admin/validation-report")
async def validation_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Get a structured validation report for the CMS.
    """
    report = await DBValidator.generate_report(db)
    return report


# ─── Public viewer endpoint ─────────────────────────────────────────

@router.get("/api/catalog")
@router.get("/api/catalogue")
async def get_catalogue():
    """
    Public endpoint. Returns the live catalogue JSON.
    No authentication required — this is what the Viewer app reads.
    Returns 404 if no catalogue has been published yet.
    """
    storage = get_storage_backend()
    data = await CatalogueService.get_live_catalogue(storage)
    if data is None:
        raise HTTPException(status_code=404, detail="No catalogue published yet.")
    return JSONResponse(
        content=json.loads(data),
        media_type="application/json",
    )

from app.services.search_service import SearchService
from app.models.publish_run import PublishRun

@router.get("/api/catalog/search")
async def search_catalog(
    q: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    section: Optional[str] = None
):
    """
    Search the live catalogue.
    """
    storage = get_storage_backend()
    results = await SearchService.search(storage, q, category, language, section)
    return results


@router.get("/admin/catalog/runs")
async def publish_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    result = await db.execute(
        select(PublishRun).order_by(desc(PublishRun.started_at)).limit(50)
    )
    return {
        "items": [
            {
                "id": str(run.id),
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "shows_count": run.shows_count,
                "episodes_count": run.episodes_count,
                "error_message": run.error_message,
                "is_current": run.is_current,
            }
            for run in result.scalars().all()
        ]
    }
