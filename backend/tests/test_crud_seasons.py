import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_season(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create show
        show_res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show-season",
            "title": "Test Show for Season",
            "status": "draft"
        })
        show_id = show_res.json()["id"]

        # 2. Create season 1
        season_res = await ac.post(f"/admin/shows/{show_id}/seasons", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "season_number": 1
        })
        assert season_res.status_code == 200
        season_id = season_res.json()["id"]
        assert season_res.json()["season_number"] == 1

        # 3. Create season 0 (Trailer constraint allowed)
        season0_res = await ac.post(f"/admin/shows/{show_id}/seasons", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "season_number": 0
        })
        assert season0_res.status_code == 200

        # 4. Fetch seasons
        get_res = await ac.get(f"/admin/shows/{show_id}/seasons", headers={"Authorization": f"Bearer {auth_token}"})
        assert get_res.status_code == 200
        assert get_res.json()["total"] == 2
