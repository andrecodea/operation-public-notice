import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from models.edital import Edital
from models.evaluation import EvaluationResult, FieldScore


def _mock_edital(source="fapdf", link="https://fap.df.gov.br/1") -> Edital:
    return Edital.model_validate({
        "titulo": "Edital Teste",
        "orgao": "FAPDF",
        "link_edital": link,
        "fonte": source,
        "extraido_em": datetime.now().isoformat()
    })


def _mock_evaluation(edital: Edital, score=0.9) -> EvaluationResult:
    return EvaluationResult(
        edital_id=edital.id,
        source=edital.fonte,
        field_scores={"titulo": FieldScore(
            fidelidade=score,
            completude=score,
            justificativa="ok",
            trecho_referencia=None
        )},
        overall_score=score,
        filled_fields=10,
        null_fields=2,
        json_valid=True,
        text_truncated=False,
        evaluated_at=datetime.now(),
    )


async def test_pipeline_saves_json(tmp_path):
    from main import run_pipeline

    edital = _mock_edital()
    evaluation = _mock_evaluation(edital)

    with (
        patch("main.FUNCAPScraper") as MockFUNCAP,
        patch("main.FAPDFScraper") as MockFAPDF,
        patch("main.CAPESScraper") as MockCAPES,
        patch("main.extract_text_from_url", new_callable=AsyncMock) as mock_pdf,
        patch("main.extract_edital", new_callable=AsyncMock) as mock_extract,
        patch("main.evaluate", new_callable=AsyncMock) as mock_judge,
    ):
        MockFUNCAP.return_value.get_opportunities = AsyncMock(return_value=[
            {"titulo": "T", "url": "http://x"}
        ])
        MockFUNCAP.return_value.get_documents = AsyncMock(return_value=["http://x/doc.pdf"])

        MockFAPDF.return_value.get_opportunities = AsyncMock(return_value=[])
        MockFAPDF.return_value.get_documents = AsyncMock(return_value=[])

        MockCAPES.return_value.get_opportunities = AsyncMock(return_value=[])
        MockCAPES.return_value.get_documents = AsyncMock(return_value=[])

        mock_pdf.return_value = ("texto do pdf", False)
        mock_extract.return_value = (edital, [])
        mock_judge.return_value = evaluation

        await run_pipeline(output_dir=tmp_path)

    editais_file = tmp_path / "editais.json"
    evaluation_file = tmp_path / "evaluation.json"
    assert editais_file.exists()
    assert evaluation_file.exists()

    editais = json.loads(editais_file.read_text())
    assert len(editais) == 1
    assert editais[0]["titulo"] == "Edital Teste"


async def test_pipeline_continues_after_error(tmp_path):
    """Failure in one opportunity shouldn't stop others"""
    from main import run_pipeline

    edital = _mock_edital()
    evaluation = _mock_evaluation(edital)

    with (
        patch("main.FUNCAPScraper") as MockFUNCAP,
        patch("main.FAPDFScraper") as MockFAPDF,
        patch("main.CAPESScraper") as MockCAPES,
        patch("main.extract_text_from_url", new_callable=AsyncMock) as mock_pdf,
        patch("main.extract_edital", new_callable=AsyncMock) as mock_extract,
        patch("main.evaluate", new_callable=AsyncMock) as mock_judge,
    ):
        MockFUNCAP.return_value.get_opportunities = AsyncMock(return_value=[
            {"titulo": "OK", "url": "http://ok/1"},
            {"titulo": "ERRO", "url": "http://erro/2"},
        ])
        MockFUNCAP.return_value.get_documents = AsyncMock(return_value=["http://x/doc.pdf"])

        MockFAPDF.return_value.get_opportunities = AsyncMock(return_value=[])
        MockFAPDF.return_value.get_documents = AsyncMock(return_value=[])

        MockCAPES.return_value.get_opportunities = AsyncMock(return_value=[])
        MockCAPES.return_value.get_documents = AsyncMock(return_value=[])

        mock_pdf.side_effect = [("texto do pdf", False), Exception("PDF não encontrado")]
        mock_extract.return_value = (edital, [])
        mock_judge.return_value = evaluation

        await run_pipeline(output_dir=tmp_path)

    editais = json.loads((tmp_path / "editais.json").read_text())
    assert len(editais) == 1
