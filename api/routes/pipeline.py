from fastapi import APIRouter, BackgroundTasks, HTTPException
from main import run_pipeline

router = APIRouter()

_pipeline_running: bool = False


async def _run_and_reset() -> None:
    global _pipeline_running
    try:
        await run_pipeline()
    finally:
        _pipeline_running = False


@router.post("/pipeline/run", status_code=202)
async def trigger_pipeline(background_tasks: BackgroundTasks) -> dict:
    global _pipeline_running
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    _pipeline_running = True
    background_tasks.add_task(_run_and_reset)
    return {"status": "started", "message": "Pipeline running in background"}
