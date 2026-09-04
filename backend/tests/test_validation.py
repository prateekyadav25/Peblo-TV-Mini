import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_validation_report(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/admin/validation-report", headers={"Authorization": f"Bearer {auth_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "total_errors" in data
