"""Schemas de requisição/resposta da API HTTP."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import (
    CharacterAsset,
    ExportOptions,
    ProceduralBlueprint,
    Rarity,
)

__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "MetaResponse",
    "MessageResponse",
    "BatchExportRequest",
    "BatchExportResult",
]


class BatchExportRequest(BaseModel):
    """``ids=None`` exporta todos os personagens salvos."""

    ids: list[str] | None = None
    options: ExportOptions | None = None


class BatchExportResult(BaseModel):
    filename: str
    size_bytes: int
    download_url: str
    character_count: int
    files: list[str]


class GenerateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=96)
    kind: str = "character"
    rarity: Rarity = Rarity.COMMON
    level: int = Field(default=1, ge=1, le=255)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    seed: int | None = None
    blueprint: ProceduralBlueprint


class PreviewUrls(BaseModel):
    pose: dict[str, str]
    strip: dict[str, str]
    sheet: str
    gif: str
    manifest: str


class GenerateResponse(BaseModel):
    asset: CharacterAsset
    preview: PreviewUrls
    frame_count: int
    color_count: int


class MetaResponse(BaseModel):
    species: list[dict]
    archetypes: list[str]
    hair_styles: list[str]
    headgear: list[str]
    weapons: list[str]
    offhands: list[str]
    outfits: list[str]
    horns: list[str]
    tails: list[str]
    palettes: dict[str, list[str]]
    rarities: list[str]
    directions: list[str]
    animations: list[str]
    abilities: list[dict]


class MessageResponse(BaseModel):
    ok: bool
    message: str
