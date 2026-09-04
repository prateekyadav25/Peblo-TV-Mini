import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_episode_crud_and_validation(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create Show
        show_res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show-episode",
            "title": "Test Show Episode",
            "status": "draft"
        })
        show_id = show_res.json()["id"]

        # Create Season
        season_res = await ac.post(f"/admin/shows/{show_id}/seasons", headers={"Authorization": f"Bearer {auth_token}"}, json={"season_number": 1})
        season_id = season_res.json()["id"]

        # Create Episode (draft)
        ep1_res = await ac.post(f"/admin/seasons/{season_id}/episodes", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "episode_number": 1,
            "title": "Ep 1",
            "content_group": "group1",
            "language": "en"
        })
        assert ep1_res.status_code == 200
        ep1_id = ep1_res.json()["id"]

        # Test duplicate content_group + language (should return 400)
        ep2_res = await ac.post(f"/admin/seasons/{season_id}/episodes", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "episode_number": 2,
            "title": "Ep 2",
            "content_group": "group1",
            "language": "en"
        })
        assert ep2_res.status_code == 400
        assert "already exists" in ep2_res.json()["detail"]

        # Update Episode to published WITHOUT duration (should fail)
        pub_res = await ac.put(f"/admin/episodes/{ep1_id}", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "status": "published"
        })
        assert pub_res.status_code == 400
        assert "duration" in pub_res.json()["detail"].lower()

        # Update Episode with duration but NO artwork (should fail)
        pub_res2 = await ac.put(f"/admin/episodes/{ep1_id}", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "duration_seconds": 3600,
            "status": "published"
        })
        assert pub_res2.status_code == 400
        assert "artwork" in pub_res2.json()["detail"].lower()
