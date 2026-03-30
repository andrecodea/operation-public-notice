import json
import logging
from datetime import datetime

from config.settings import LLMConfig
from models.edital import Edital
from models.evaluation import FieldScore
from providers.base import complete_with_fallback

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return text.strip()

SYSTEM_PROMPT = """
Você é um extrator especializado em editais de fomento brasileiros.
Analise o conteúdo fornecido e retorne APENAS um objeto json válido com os campos especificados.
Não inclua markdown, explicações ou texto fora do JSON.
Campos não encontrados devem ser null.
"""

SCHEMA_DESCRIPTION = """{
    "titulo": "string",
    "orgao": "string",
    "objetivo": "string ou null",
    "publico_alvo": ["string"],
    "areas_tematica": ["string"],
    "elegibilidade": "string ou null",
    "prazo_submissao": "string ou null",
    "valor_financiamento": "string ou null",
    "modalidade_fomento": "string ou null",
    "documentos_exigidos": ["string"],
    "criterios_avaliacao": "string ou null",
    "cronograma": [{"evento": "string", "data": "string"}],
    "link_edital": "string (URL da página do edital)",
    "link_pdf_principal": "string ou null",
    "links_anexos": ["string"],
    "observacoes": "string ou null",
    "fonte": "string",
    "extraido_em": "datetime ISO string"
}"""

async def extract_edital(
    pdf_text: str,
    link_edital: str,
    fonte: str,
    config: LLMConfig
) -> tuple[Edital, list[dict], str]:
    """"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Extraia as informações do edital abaixo\n"
                f"link_edital: {link_edital}\n"
                f"fonte: {fonte}\n"
                f"extraido_em: {datetime.now().isoformat()}\n\n"
                f"Schema esperado:\n{SCHEMA_DESCRIPTION}\n\n"
                f"Texto do edital:\n{pdf_text}"
            )
        }
    ]

    raw, model = await complete_with_fallback(messages, config)
    messages = messages + [{"role": "assistant", "content": raw}]
    data = json.loads(_strip_markdown(raw))
    edital = Edital.model_validate(data)
    return edital, messages, model

async def correct_edital(
    messages: list[dict],
    field_scores: dict[str, FieldScore],
    config: LLMConfig,
) -> tuple[Edital, str]:
    """"""
    correction_prompt = build_correction_prompt(field_scores)
    correction_messages = messages + [{"role": "user", "content": correction_prompt}]

    raw, model = await complete_with_fallback(correction_messages, config)
    data = json.loads(_strip_markdown(raw))
    return Edital.model_validate(data), model

def build_correction_prompt(field_scores: dict[str, FieldScore]) -> str:
    """"""
    low_fields = {
        field: score
        for field, score in field_scores.items()
        if score.fidelidade is not None
        and score.completude is not None
        and (score.fidelidade + score.completude) / 2 < 0.6
    }

    if not low_fields:
        return "A extração anterior está correta. Retorne o mesmo JSON SEM ALTERAÇÕES."
    
    lines = [
        "Os seguintes campos foram avaliados com qualidade insuficiente.",
        "Corrija-os e retorne o JSON completo:\n",
    ]

    for field, score in low_fields.items():
        lines.append(f"- {field}: {score.justificativa}")
        if score.trecho_referencia:
            lines.append(f"Trecho relevante no documento: ```{score.trecho_referencia}```")

    lines.append("\nRetorne o JSON completo corrigido.")
    return "\n".join(lines)