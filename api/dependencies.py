import json
from pathlib import Path

OUTPUT_DIR = Path("output")


def load_editais() -> list[dict]:
    path = OUTPUT_DIR / "editais.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_evaluations() -> list[dict]:
    path = OUTPUT_DIR / "evaluation.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)
