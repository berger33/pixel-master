"""Repositório de personagens."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select

from app.db.database import characters, session_scope
from app.domain.models import CharacterAsset

__all__ = ["CharacterRepository"]


def _row_to_asset(row: Any) -> CharacterAsset:
    return CharacterAsset.model_validate_json(row.asset_json)


class CharacterRepository:
    @staticmethod
    def save(asset: CharacterAsset) -> CharacterAsset:
        now = datetime.now(UTC)
        with session_scope() as conn:
            existing = conn.execute(
                select(characters.c.id).where(characters.c.id == asset.id)
            ).first()
            payload = {
                "id": asset.id,
                "slug": asset.slug,
                "name": asset.name,
                "kind": asset.kind,
                "species": asset.species,
                "rarity": asset.rarity.value,
                "origin": asset.origin.value,
                "seed": str(asset.seed),
                "asset_json": asset.model_dump_json(),
                "updated_at": now,
            }
            if existing is None:
                conn.execute(characters.insert().values(**payload, created_at=now))
            else:
                conn.execute(
                    characters.update().where(characters.c.id == asset.id).values(**payload)
                )
        return asset

    @staticmethod
    def get(asset_id: str) -> CharacterAsset | None:
        with session_scope() as conn:
            row = conn.execute(select(characters).where(characters.c.id == asset_id)).first()
        return _row_to_asset(row) if row else None

    @staticmethod
    def list_all(limit: int = 200) -> list[CharacterAsset]:
        with session_scope() as conn:
            rows = conn.execute(
                select(characters).order_by(characters.c.updated_at.desc()).limit(limit)
            ).all()
        return [_row_to_asset(r) for r in rows]

    @staticmethod
    def delete(asset_id: str) -> bool:
        with session_scope() as conn:
            result = conn.execute(delete(characters).where(characters.c.id == asset_id))
        return result.rowcount > 0

    @staticmethod
    def count() -> int:
        with session_scope() as conn:
            from sqlalchemy import func

            return int(conn.execute(select(func.count()).select_from(characters)).scalar() or 0)


def dumps(asset: CharacterAsset) -> str:
    return json.dumps(asset.model_dump(mode="json"), ensure_ascii=False)
