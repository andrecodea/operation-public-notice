from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import editais, evaluation, pipeline

app = FastAPI(title="Operação Edital API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(editais.router)
app.include_router(evaluation.router)
app.include_router(pipeline.router)

# Serve React build when it exists (production / .exe mode)
_STATIC = Path(__file__).parent.parent / "frontend" / "dist"
if _STATIC.exists():
    app.mount("/assets", StaticFiles(directory=_STATIC / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        return FileResponse(_STATIC / "index.html")
