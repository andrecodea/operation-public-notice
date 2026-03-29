import json
import pytest 
from datetime import datetime
from unittest.mock import AsyncMock, patch
from config.settings import LLMConfig
from models.edital import Edital
from models.evaluation import FieldScore
from extractors.llm_extractor import extract_edital, correct_edital, build_correction_prompt

@pytest.fixture
def config():
    return LLMConfig()

def _edital_json(link="https://fap.df.gov.br/1") -> str:
    """Generates a mock notice for testing."""
    return json.dumps({
        "titulo": "Edital Teste",
        "orgao": "FAPDF",
        "objetivo": None,
        "publico_alvo": [],
        "areas_tematicas": [],
        "elegibilidade": None,
        "prazo_submissao": "30/04/2026",
        "valor_financiamento": "R$ 100.000",
        "modalidade_fomento": None,
        "documentos_exigidos": [],
        "criterios_avaliacao": None,
        "cronograma": [],
        "link_edital": link,
        "link_pdf_principal": None,
        "links_anexos": [],
        "observacoes": None,
        "fonte": "fapdf",
        "extraido_em": datetime.now().isoformat()
    })

async def test_extract_notice_successfuly(config):
    """Asserts that LLM extraction of the PDF structure occurs successfuly."""
    with patch("extractors.llm_extractor.complete_with_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _edital_json()
        edital, messages = await extract_edital(
            "texto do pdf",
            "https://fap.df.gov.br/1",
            "fapdf",
            config)
        assert isinstance(edital, Edital)
        assert edital.titulo == "Edital Teste"
        assert edital.fonte == "fapdf"
        assert len(messages) == 3
        assert messages[2]["role"] == "assistant"

async def test_messages_preserve_history_for_correction(config):
    """Assures that the message history is preserved for LLM judge multi-turn correction."""
    with patch("extractors.llm_extractor.complete_with_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _edital_json()
        _, messages = await extract_edital(
            "texto do pdf",
            "https://fap.df.gov.br/1",
            "fapdf",
            config
        )

        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

def test_build_correction_prompt_includes_low_fields():
    """Asserts that the correction prompt has the right low score fields for correction
    with correct text excerpt, and does not include the high score fields.
    """
    scores = {
        # field 1: ok
        "titulo": FieldScore(
            fidelidade=1.0,
            completude=1.0,
            justificativa="ok",
            trecho_referencia=None
            ),

        # field 2: wrong date
        "prazo_submissao": FieldScore(
            fidelidade=0.3,
            completude=0.4,
            justificativa="data errada",
            trecho_referencia="prazo 30 de abril de 2026"
        ),
    }

    prompt = build_correction_prompt(scores)

    assert "prazo_submissao" in prompt
    assert "titulo" not in prompt # musn't show up with high scores
    assert "30 de abril de 2026" in prompt # trecho_referencia included

def test_build_correction_prompt_with_no_low_fields():
    """Asserts that correction prompt returns the same JSON as what the LLM was provided with."""
    scores = {
        "titulo": FieldScore(
            fidelidade=1.0,
            completude=1.0,
            justificativa="ok",
            trecho_referencia=None
            ),
    }
    prompt = build_correction_prompt(scores)
    assert "Retorne o mesmo JSON" in prompt
