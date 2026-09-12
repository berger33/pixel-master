"""Ponto de entrada da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Pixel Master — motor de geração de personagens e criaturas em pixel art "
        "para o jogo Vandoria. Geração procedural determinística, importação de "
        "renders de IA, animação (idle/walk 4 direções/death) e exportação de "
        "atlas + ficha funcional prontos para o motor do jogo."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["system"])
def root() -> dict[str, object]:
    return {
        "app": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }
