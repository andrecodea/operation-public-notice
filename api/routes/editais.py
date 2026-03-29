from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import load_editais, load_evaluations

router = APIRouter()


@router.get("/editais")
def get_editais(
    fonte: str | None = None,
    min_score: float | None = None,
    editais: list[dict] = Depends(load_editais),
    evaluations: list[dict] = Depends(load_evaluations),
) -> list[dict]:
    scores = {ev["edital_id"]: ev["overall_score"] for ev in evaluations}

    result = []
    for edital in editais:
        if fonte and edital.get("fonte") != fonte:
            continue
        score = scores.get(edital.get("id"))
        if min_score is not None:
            if score is None or score < min_score:
                continue
        result.append({**edital, "overall_score": score})
    return result


@router.get("/editais/{edital_id}")
def get_edital(
    edital_id: str,
    editais: list[dict] = Depends(load_editais),
    evaluations: list[dict] = Depends(load_evaluations),
) -> dict:
    edital = next((e for e in editais if e.get("id") == edital_id), None)
    if edital is None:
        raise HTTPException(status_code=404, detail="Edital not found")
    evaluation = next((ev for ev in evaluations if ev.get("edital_id") == edital_id), None)
    return {"edital": edital, "evaluation": evaluation}
