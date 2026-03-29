import pytest
import httpx
from httpx import ASGITransport
from unittest.mock import AsyncMock, patch
from api.main import app
import api.routes.pipeline as pipeline_module


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def reset_pipeline_flag():
    pipeline_module._pipeline_running = False
    yield
    pipeline_module._pipeline_running = False


async def test_pipeline_run_returns_started(client):
    with patch("api.routes.pipeline.run_pipeline", new=AsyncMock()):
        resp = await client.post("/pipeline/run")
    assert resp.status_code == 202
    assert resp.json()["status"] == "started"


async def test_pipeline_run_returns_409_when_already_running(client):
    pipeline_module._pipeline_running = True
    resp = await client.post("/pipeline/run")
    assert resp.status_code == 409
    assert "already running" in resp.json()["detail"]
