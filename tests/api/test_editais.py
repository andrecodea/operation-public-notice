import pytest
import httpx
from httpx import ASGITransport
from api.main import app
from api.dependencies import load_editais, load_evaluations

EDITAL_A = {
    "titulo": "Edital A", "orgao": "FAPDF", "fonte": "fapdf",
    "link_edital": "https://fapdf.gov.br/edital-a",
    "id": "abc123", "extraido_em": "2026-01-01T00:00:00",
    "publico_alvo": [], "areas_tematicas": [], "documentos_exigidos": [],
    "cronograma": [], "links_anexos": [],
}
EDITAL_B = {
    "titulo": "Edital B", "orgao": "FUNCAP", "fonte": "funcap",
    "link_edital": "https://funcap.gov.br/edital-b",
    "id": "def456", "extraido_em": "2026-01-01T00:00:00",
    "publico_alvo": [], "areas_tematicas": [], "documentos_exigidos": [],
    "cronograma": [], "links_anexos": [],
}
EVAL_A = {
    "edital_id": "abc123", "source": "fapdf", "field_scores": {},
    "overall_score": 0.9, "corrected": False,
    "score_before_correction": None, "score_after_correction": None,
    "filled_fields": 8, "null_fields": 4, "json_valid": True,
    "text_truncated": False, "evaluated_at": "2026-01-01T00:00:00",
}


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_data_ab():
    app.dependency_overrides[load_editais] = lambda: [EDITAL_A, EDITAL_B]
    app.dependency_overrides[load_evaluations] = lambda: [EVAL_A]
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_data_a_only():
    app.dependency_overrides[load_editais] = lambda: [EDITAL_A]
    app.dependency_overrides[load_evaluations] = lambda: [EVAL_A]
    yield
    app.dependency_overrides.clear()


async def test_get_editais_returns_list(client, mock_data_ab):
    resp = await client.get("/editais")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == "abc123"


async def test_get_editais_filter_by_fonte(client, mock_data_ab):
    resp = await client.get("/editais?fonte=fapdf")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["fonte"] == "fapdf"


async def test_get_editais_filter_by_min_score(client, mock_data_ab):
    resp = await client.get("/editais?min_score=0.85")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "abc123"


async def test_get_edital_by_id_returns_detail(client, mock_data_a_only):
    resp = await client.get("/editais/abc123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["edital"]["id"] == "abc123"
    assert data["evaluation"]["overall_score"] == 0.9


async def test_get_edital_by_id_returns_404(client):
    app.dependency_overrides[load_editais] = lambda: [EDITAL_A]
    app.dependency_overrides[load_evaluations] = lambda: []
    try:
        resp = await client.get("/editais/nonexistent")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404
