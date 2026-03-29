from collections import defaultdict
from fastapi import APIRouter, Depends
from api.dependencies import load_editais, load_evaluations

router = APIRouter()


@router.get("/evaluation")
def get_evaluation(evaluations: list[dict] = Depends(load_evaluations)) -> list[dict]:
    return evaluations


@router.get("/evaluation/summary")
def get_evaluation_summary(
    editais: list[dict] = Depends(load_editais),
    evaluations: list[dict] = Depends(load_evaluations),
) -> dict:
    if not evaluations:
        return {
            "total_editais": len(editais), "avg_score": 0.0,
            "avg_score_by_source": {}, "fields_with_low_fidelidade": [],
            "fields_with_low_completude": [], "json_valid_pct": 0.0,
            "text_truncated_pct": 0.0, "avg_filled_fields": 0.0, "corrected_pct": 0.0,
        }

    n = len(evaluations)
    avg_score = sum(ev["overall_score"] for ev in evaluations) / n

    by_source: dict[str, list[float]] = defaultdict(list)
    for ev in evaluations:
        by_source[ev["source"]].append(ev["overall_score"])
    avg_score_by_source = {src: sum(scores) / len(scores) for src, scores in by_source.items()}

    field_fidelidade: dict[str, list[float]] = defaultdict(list)
    field_completude: dict[str, list[float]] = defaultdict(list)
    for ev in evaluations:
        for field, score in ev.get("field_scores", {}).items():
            if score.get("fidelidade") is not None:
                field_fidelidade[field].append(score["fidelidade"])
            if score.get("completude") is not None:
                field_completude[field].append(score["completude"])

    fields_with_low_fidelidade = [
        f for f, vals in field_fidelidade.items() if sum(vals) / len(vals) < 0.7
    ]
    fields_with_low_completude = [
        f for f, vals in field_completude.items() if sum(vals) / len(vals) < 0.7
    ]

    return {
        "total_editais": len(editais),
        "avg_score": round(avg_score, 3),
        "avg_score_by_source": {k: round(v, 3) for k, v in avg_score_by_source.items()},
        "fields_with_low_fidelidade": fields_with_low_fidelidade,
        "fields_with_low_completude": fields_with_low_completude,
        "json_valid_pct": round(sum(ev["json_valid"] for ev in evaluations) / n, 3),
        "text_truncated_pct": round(sum(ev["text_truncated"] for ev in evaluations) / n, 3),
        "avg_filled_fields": round(sum(ev["filled_fields"] for ev in evaluations) / n, 1),
        "corrected_pct": round(sum(ev["corrected"] for ev in evaluations) / n, 3),
    }
