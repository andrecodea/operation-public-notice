"""Tests evaluation Pydantic model"""

from datetime import datetime
from models.evaluation import FieldScore, EvaluationResult

def _field_score(f=1.0, c=1.0) -> FieldScore:
    """Defines mock field scores."""
    return FieldScore(
        fidelidade=f,
        completude=c,
        justificativa="ok",
        trecho_referencia=None
        )

def _evaluation_result(**kwargs) -> EvaluationResult:
    """Defines mock evaluation results."""
    defaults = {
        "edital_id": "abc123",
        "fonte": "fapdf",
        "scores_por_campo": {"titulo": _field_score()},
        "score_geral": 1.0,
        "campos_preenchidos": 8,
        "campos_nulos": 4,
        "json_valido": True,
        "texto_truncado": False,
        "avaliado_em": datetime.now(),
    }
    return EvaluationResult(**{**defaults, **kwargs})

def test_field_score_accepts_none():
    """Asserts that FieldScore accepts None for invalid metrics."""
    score = FieldScore(
        fidelidade=None,
        completude=None,
        justificativa="não avaliável",
        trecho_referencia=None
        )
    assert score.fidelidade is None
    assert score.completude is None

def test_evaluation_result_corrected_default_false():
    """Asserts that the default of EvaluationResult's correction status is False
    and the eval scores are None."""
    result = _evaluation_result()
    assert result.corrigido is False
    assert result.score_antes_correcao is None
    assert result.score_pos_correcao is None

def test_evaluation_result_with_correction():
    """Asserts that corrections are accurately identified by Pydantic."""
    result = _evaluation_result(
        corrigido=True,
        score_antes_correcao=0.45,
        score_pos_correcao=0.72,
        score_geral=0.72
    )
    assert result.corrigido is True
    assert result.score_antes_correcao == 0.45

# To run: uv run pytest tests/models/test_evaluation.py -v
# To run all: uv run pytest tests/models/ -v