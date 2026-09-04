import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_login_success(setup_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/admin/auth/token", data={
            "username": "admin_test@peblo.tv",
            "password": "admin"
        })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_failure(setup_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/admin/auth/token", data={
            "username": "admin_test@peblo.tv",
            "password": "wrong"
        })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_rbac_admin_can_publish(setup_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login as admin
        login_res = await ac.post("/admin/auth/token", data={"username": "admin_test@peblo.tv", "password": "admin"})
        token = login_res.json()["access_token"]
        
        # Access publish
        res = await ac.post("/admin/catalog/publish", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["user"] == "admin_test@peblo.tv"

@pytest.mark.asyncio
async def test_rbac_editor_cannot_publish(setup_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login as editor
        login_res = await ac.post("/admin/auth/token", data={"username": "editor_test@peblo.tv", "password": "editor"})
        token = login_res.json()["access_token"]
        
        # Access publish (should fail)
        res = await ac.post("/admin/catalog/publish", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403
        assert res.json()["detail"] == "Not enough permissions"

@pytest.mark.asyncio
async def test_rbac_editor_can_check_status(setup_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login as editor
        login_res = await ac.post("/admin/auth/token", data={"username": "editor_test@peblo.tv", "password": "editor"})
        token = login_res.json()["access_token"]
        
        # Access status (allowed for admin and editor)
        res = await ac.get("/admin/catalog/status", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_rbac_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/admin/catalog/publish")
        assert res.status_code == 401
