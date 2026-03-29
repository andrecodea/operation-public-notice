from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
