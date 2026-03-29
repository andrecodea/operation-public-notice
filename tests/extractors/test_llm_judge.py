import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from config.settings import LLMConfig
from models.edital import Edital
from models.evaluation import EvaluationResult
from extractors.llm_judge import evaluate, _compute_overall_score, CRITICAL_FIELDS
from models.evaluation import FieldScore

@pytest.fixture
def config():
    return LLMConfig()

@pytest.fixture
def edital():
    return Edital.model_validate({
        "titulo": "Edital Teste",
        "orgao": "FAPDF",
        "prazo_submissao": "30/04/2026",
        "valor_financiamento": "R$ 100.000",
        "link_edital": "https://fap.df.gov.br/1",
        "fonte": "fapdf",
        "extraido_em": datetime.now().isoformat(),
    })

def _scores_json(fields: list[str], f=0.9, c=0.9) -> str:
    return json.dumps({
        field: {
            "fidelidade": f,
            "completude": c,
            "justificativa": "ok",
            "trecho_referencia": None} for field in fields
    })

async def test_eval_returns_eval_result(config, edital):
    fields = list(CRITICAL_FIELDS)[:4]
    with patch("extractors.llm_judge.complete_with_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _scores_json(fields)
        result = await evaluate(edital, "texto do pdf", config)

    assert isinstance(result, EvaluationResult)
    assert result.edital_id == edital.id
    assert result.source == "fapdf"
    assert result.json_valid is True
    assert result.text_truncated is False

async def test_eval_with_truncated_text(config, edital):
    with patch("extractors.llm_judge.complete_with_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _scores_json(["titulo"])
        result = await evaluate(edital, "texto", config, text_truncated=True)
        assert result.text_truncated is True

def test_overall_score_weights_critical_fields():
    # campo crítico (peso 2) com score 1.0 e secundário (peso 1) com score 0.0
    scores = {
        "titulo": FieldScore(fidelidade=1.0, completude=1.0, justificativa="", trecho_referencia=None),
        "cronograma": FieldScore(fidelidade=0.0, completude=0.0, justificativa="", trecho_referencia=None),
    }
    score = _compute_overall_score(scores)

    # titulo: weight 2, score 1.0 -> 2.0; cronograma: weight 1, score 0.0 -> 0.0
    # total: 2.0 / 3 = 0.667
    assert abs(score - 2/3) < 0.001

def test_overall_score_ignores_none():
    scores = {
        "titulo": FieldScore(fidelidade=1.0, completude=1.0, justificativa="", trecho_referencia=None),
        "objetivo": FieldScore(fidelidade=None, completude=None, justificativa="não avaliável", trecho_referencia=None),
    }
    score = _compute_overall_score(scores)
    assert score == 1.0

# To run: uv run pytest tests/extractors/test_llm_judge.py -v
