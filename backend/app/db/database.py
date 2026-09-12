"""Persistência (SQLAlchemy Core) — SQLite por padrão, PostgreSQL em produção.

Usamos Core (``Table``) em vez de ORM para manter o esquema explícito e fácil de
inspecionar; o personagem é armazenado como um documento JSON (o blueprint é a
fonte da verdade e regenera a arte byte a byte).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings

metadata = MetaData()

characters = Table(
    "characters",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("slug", String(96), index=True, nullable=False),
    Column("name", String(96), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("species", String(64), nullable=False),
    Column("rarity", String(16), nullable=False),
    Column("origin", String(16), nullable=False),
    Column("seed", String(32), nullable=False),
    Column("asset_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
        metadata.create_all(_engine)
    return _engine


@contextmanager
def session_scope() -> Iterator:
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def reset_engine() -> None:
    """Utilitário de teste: descarta o engine (permite apontar para outro DB)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
