"""Defines evaluation result and evaluation field score Pydantic models"""

from datetime import datetime
from pydantic import BaseModel

class FieldScore(BaseModel):
    """Determines the evaluation's score's fields for LLM-as-a-judge
    
    fidelidade: does the extracted value exist in the source text?
    completude: content generation completeness (was everything included?).
    justificativa: reasoning behind scores.
    trecho_referencia: PDF excerpt that served as a base for eval.
    """
    fidelidade: float | None # None if field is not evaluable
    completude: float | None # None if field is not evaluable
    justificativa: str
    trecho_referencia: str | None

class EvaluationResult(BaseModel):
    """Determines the evaluation result fields."""
    edital_id: str # sha256(link_edital)[:12] -> links to Edital.id
    fonte: str # Notice source
    scores_por_campo: dict[str, FieldScore] # Scores per field
    score_geral: float # Weighted avg across evaluable fields
    corrigido: bool = False # True if multi-turn correction was attempted
    score_antes_correcao: float | None = None # score_geral before correction
    score_pos_correcao: float | None = None # score_geral after correction

    # Deterministic metrics (12 valid fields):
    campos_preenchidos: int
    campos_nulos: int 
    json_valido: bool # Idid Pydantic validate without errors?
    texto_truncado: bool # was the PDF truncated at 15 pages?
    avaliado_em: datetime