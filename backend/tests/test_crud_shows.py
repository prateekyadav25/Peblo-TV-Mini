import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_show(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show",
            "title": "Test Show",
            "status": "draft"
        })
    assert res.status_code == 200
    assert res.json()["slug"] == "test-show"

@pytest.mark.asyncio
async def test_published_show_requires_section(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show-pub",
            "title": "Test Show Pub",
            "status": "published"
        })
    assert res.status_code == 400
    assert "section" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_show(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show-upd",
            "title": "Test Show Upd"
        })
        show_id = create_res.json()["id"]
        
        # update title
        upd_res = await ac.put(f"/admin/shows/{show_id}", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "title": "New Title"
        })
        assert upd_res.status_code == 200
        assert upd_res.json()["title"] == "New Title"

@pytest.mark.asyncio
async def test_delete_show_as_editor(editor_token, auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_res = await ac.post("/admin/shows", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "slug": "test-show-del",
            "title": "Test Show Del"
        })
        show_id = create_res.json()["id"]
        
        # Editor delete fails
        del_res = await ac.delete(f"/admin/shows/{show_id}", headers={"Authorization": f"Bearer {editor_token}"})
        assert del_res.status_code == 403

        # Admin delete succeeds
        del_res2 = await ac.delete(f"/admin/shows/{show_id}", headers={"Authorization": f"Bearer {auth_token}"})
        assert del_res2.status_code == 204
