"""Defines evaluation result and evaluation field score Pydantic models"""

from datetime import datetime
from pydantic import BaseModel

class FieldScore(BaseModel):
    """Determines the evaluation's score's fields for LLM-as-a-judge.

    Field names stay in Portuguese — they appear directly in the judge's LLM prompt.
    fidelidade: does the extracted value exist in the source text?
    completude: content generation completeness (was everything included?).
    justificativa: reasoning behind scores.
    trecho_referencia: PDF excerpt that served as a base for eval.
    """
    fidelidade: float | None  # None if field is not evaluable
    completude: float | None  # None if field is not evaluable
    justificativa: str
    trecho_referencia: str | None

class EvaluationResult(BaseModel):
    """Determines the evaluation result fields."""
    edital_id: str               # sha256(link_edital)[:12] -> links to Edital.id
    source: str                  # notice source
    field_scores: dict[str, FieldScore]  # scores per field
    overall_score: float         # weighted avg across evaluable fields
    corrected: bool = False      # True if multi-turn correction was attempted
    score_before_correction: float | None = None  # overall_score before correction
    score_after_correction: float | None = None   # overall_score after correction

    # Deterministic metrics (12 evaluable fields):
    filled_fields: int
    null_fields: int
    json_valid: bool             # did Pydantic validate without errors?
    text_truncated: bool         # was the PDF truncated at 15 pages?
    evaluated_at: datetime

    # LLM tracking
    extraction_model: str | None = None   # model used for extraction (primary or fallback)
    judge_model: str | None = None        # model used for LLM judge
