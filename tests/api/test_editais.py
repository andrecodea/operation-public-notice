import pytest
import httpx
from httpx import ASGITransport
from api.main import app


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_check_returns_200(client):
    resp = await client.get("/editais")
    assert resp.status_code == 200
