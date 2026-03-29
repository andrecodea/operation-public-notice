import pytest
import httpx
from httpx import ASGITransport
from unittest.mock import patch
from api.main import app

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


async def test_get_editais_returns_list(client):
    with (
        patch("api.routes.editais.load_editais", return_value=[EDITAL_A, EDITAL_B]),
        patch("api.routes.editais.load_evaluations", return_value=[EVAL_A]),
    ):
        resp = await client.get("/editais")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == "abc123"


async def test_get_editais_filter_by_fonte(client):
    with (
        patch("api.routes.editais.load_editais", return_value=[EDITAL_A, EDITAL_B]),
        patch("api.routes.editais.load_evaluations", return_value=[EVAL_A]),
    ):
        resp = await client.get("/editais?fonte=fapdf")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["fonte"] == "fapdf"


async def test_get_editais_filter_by_min_score(client):
    with (
        patch("api.routes.editais.load_editais", return_value=[EDITAL_A, EDITAL_B]),
        patch("api.routes.editais.load_evaluations", return_value=[EVAL_A]),
    ):
        resp = await client.get("/editais?min_score=0.85")
    assert resp.status_code == 200
    data = resp.json()
    # Only EDITAL_A has score 0.9 >= 0.85; EDITAL_B has no evaluation
    assert len(data) == 1
    assert data[0]["id"] == "abc123"


async def test_get_edital_by_id_returns_detail(client):
    with (
        patch("api.routes.editais.load_editais", return_value=[EDITAL_A]),
        patch("api.routes.editais.load_evaluations", return_value=[EVAL_A]),
    ):
        resp = await client.get("/editais/abc123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["edital"]["id"] == "abc123"
    assert data["evaluation"]["overall_score"] == 0.9


async def test_get_edital_by_id_returns_404(client):
    with (
        patch("api.routes.editais.load_editais", return_value=[EDITAL_A]),
        patch("api.routes.editais.load_evaluations", return_value=[]),
    ):
        resp = await client.get("/editais/nonexistent")
    assert resp.status_code == 404
