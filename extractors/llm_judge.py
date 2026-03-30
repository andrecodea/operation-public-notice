import json
import logging
from datetime import datetime

from config.settings import LLMConfig
from models.edital import Edital
from models.evaluation import EvaluationResult, FieldScore
from providers.base import complete_with_fallback
from extractors.llm_extractor import _strip_markdown

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """
Você é um avaliador de extração de editais de fomento brasileiros.
Você receberá o texto bruto do PDF e o JSON extraído.
Para cada campo solicitado, avalie:
    - fidelidade (0.0-1.0): o valor extraído está presente no texto original?
    - completude (0.0-1.0): havia informação no texto que deveria preencher esse
    campo mas foi ignorada ou extraída parcialmente (omissão).
    - trecho_referencia: o trecho exato do PDF que embasou sua avaliação (ou null se NA)
Retorne APENAS JSON válido. Se um campo não puder ser avaliado, retorne fidelidade: null e completude: null
"""

CRITICAL_FIELDS: set[str] = {  # O(1) lookup
    "titulo", "orgao", "objetivo", "prazo_submissao",
    "valor_financiamento", "elegibilidade", "publico_alvo", "modalidade_fomento",
}

SECONDARY_FIELDS: set[str] = {
    "areas_tematicas", "criterios_avaliacao",
    "documentos_exigidos", "cronograma",
}

EVALUABLE_FIELDS = CRITICAL_FIELDS | SECONDARY_FIELDS
CRITICAL_WEIGHT = 2
SECONDARY_WEIGHT = 1

async def evaluate(
    edital: Edital,
    source_text: str,
    config: LLMConfig,
    json_valid: bool = True,
    text_truncated: bool = False,
    extraction_model: str | None = None,
) -> EvaluationResult:
    edital_dict = edital.model_dump(exclude={"id"})
    fields_to_eval = {k: v for k, v in edital_dict.items() if k in EVALUABLE_FIELDS}

    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Texto do PDF:\n{source_text}\n\n"
            f"JSON extraído: \n{json.dumps(fields_to_eval, ensure_ascii=False, indent=2)}\n\n"
            "Avalie os campos acima. Retorne o JSON no formato:\n"
            '{"campo": {"fidelidade": 0.0, "completude": 0.0,'
            '"justificativa": "...", "trecho_referencia": "..."}}'
            ),
        },
    ]

    raw, judge_model = await complete_with_fallback(messages, config)
    try:
        scores_raw: dict = json.loads(_strip_markdown(raw))
    except json.JSONDecodeError:
        logger.error("Judge retornou JSON inválido: %r", raw[:200])
        raise

    field_scores: dict[str, FieldScore] = {}
    for field, data in scores_raw.items():
        if field in EVALUABLE_FIELDS and isinstance(data, dict):
            field_scores[field] = FieldScore(
                fidelidade=data.get("fidelidade"),
                completude=data.get("completude"),
                justificativa=data.get("justificativa", ""),
                trecho_referencia=data.get("trecho_referencia"),
            )

    overall_score = _compute_overall_score(field_scores)

    # métricas determinísticas: conta apenas os campos avaliáveis
    evaluated_values = {k: v for k, v in edital_dict.items() if k in EVALUABLE_FIELDS}
    filled = sum(
        1 for v in evaluated_values.values()
        if v is not None and v != [] and v != ""
    )

    return EvaluationResult(
        edital_id=edital.id,
        source=edital.fonte,
        field_scores=field_scores,
        overall_score=overall_score,
        filled_fields=filled,
        null_fields=len(evaluated_values) - filled,
        json_valid=json_valid,
        text_truncated=text_truncated,
        evaluated_at=datetime.now(),
        extraction_model=extraction_model,
        judge_model=judge_model,
    )

def _compute_overall_score(scores: dict[str, FieldScore]) -> float:
    total_weight = 0.0
    total_score = 0.0

    for field, score in scores.items():
        if score.fidelidade is None or score.completude is None:
            continue
        weight = CRITICAL_WEIGHT if field in CRITICAL_FIELDS else SECONDARY_WEIGHT
        field_score = (score.fidelidade + score.completude) / 2
        total_score += field_score * weight
        total_weight += weight

    return round(total_score / total_weight, 4) if total_weight > 0 else 0.0
