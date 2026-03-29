import pytest
import httpx
from httpx import ASGITransport
from api.main import app
from api.dependencies import load_editais, load_evaluations

EVAL_1 = {
    "edital_id": "abc123", "source": "fapdf", "overall_score": 0.8,
    "corrected": False, "score_before_correction": None, "score_after_correction": None,
    "filled_fields": 10, "null_fields": 2, "json_valid": True, "text_truncated": False,
    "evaluated_at": "2026-01-01T00:00:00",
    "field_scores": {
        "titulo": {"fidelidade": 0.9, "completude": 0.9, "justificativa": "ok", "trecho_referencia": None},
        "objetivo": {"fidelidade": 0.5, "completude": 0.4, "justificativa": "parcial", "trecho_referencia": None},
    },
}
EVAL_2 = {
    "edital_id": "def456", "source": "funcap", "overall_score": 0.6,
    "corrected": True, "score_before_correction": 0.4, "score_after_correction": 0.6,
    "filled_fields": 7, "null_fields": 5, "json_valid": True, "text_truncated": True,
    "evaluated_at": "2026-01-01T00:00:00",
    "field_scores": {
        "titulo": {"fidelidade": 0.8, "completude": 0.8, "justificativa": "ok", "trecho_referencia": None},
        "objetivo": {"fidelidade": 0.4, "completude": 0.3, "justificativa": "ruim", "trecho_referencia": None},
    },
}


@pytest.fixture
async def client():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_two_evals():
    app.dependency_overrides[load_editais] = lambda: [{}, {}]
    app.dependency_overrides[load_evaluations] = lambda: [EVAL_1, EVAL_2]
    yield
    app.dependency_overrides.clear()


async def test_get_evaluation_returns_list(client, mock_two_evals):
    resp = await client.get("/evaluation")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_summary_total_editais(client, mock_two_evals):
    resp = await client.get("/evaluation/summary")
    assert resp.status_code == 200
    assert resp.json()["total_editais"] == 2


async def test_summary_avg_score(client, mock_two_evals):
    data = (await client.get("/evaluation/summary")).json()
    assert abs(data["avg_score"] - 0.7) < 0.01


async def test_summary_avg_score_by_source(client, mock_two_evals):
    data = (await client.get("/evaluation/summary")).json()
    assert data["avg_score_by_source"]["fapdf"] == pytest.approx(0.8)
    assert data["avg_score_by_source"]["funcap"] == pytest.approx(0.6)


async def test_summary_low_fidelidade_fields(client, mock_two_evals):
    data = (await client.get("/evaluation/summary")).json()
    # objetivo avg fidelidade = (0.5 + 0.4) / 2 = 0.45 < 0.7
    assert "objetivo" in data["fields_with_low_fidelidade"]
    assert "titulo" not in data["fields_with_low_fidelidade"]


async def test_summary_pct_metrics(client, mock_two_evals):
    data = (await client.get("/evaluation/summary")).json()
    assert data["json_valid_pct"] == pytest.approx(1.0)
    assert data["text_truncated_pct"] == pytest.approx(0.5)
    assert data["corrected_pct"] == pytest.approx(0.5)
    assert data["avg_filled_fields"] == pytest.approx(8.5)
