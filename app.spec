# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Operação Edital.

Before building:
    cd frontend && npm run build && cd ..
    pip install pyinstaller

Build:
    pyinstaller app.spec
"""

from pathlib import Path

ROOT = Path(".").resolve()
FRONTEND_DIST = ROOT / "frontend" / "dist"

a = Analysis(
    ["run_app.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # React build output
        (str(FRONTEND_DIST), "frontend/dist"),
        # Playwright browsers are large — exclude and document separately
    ],
    hiddenimports=[
        # FastAPI / Starlette internals
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "starlette.routing",
        # pydantic v2
        "pydantic.deprecated.class_validators",
        # project modules
        "api.routes.editais",
        "api.routes.evaluation",
        "api.routes.pipeline",
        "providers.openai_provider",
        "providers.claude_provider",
        "scrapers.funcap_scraper",
        "scrapers.fapdf_scraper",
        "scrapers.capes_scraper",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="operacao-edital",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # set False for no terminal window (loses log output)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="operacao-edital",
)
