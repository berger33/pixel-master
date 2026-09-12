"""Modelos de domínio do Pixel Master.

Tudo que atravessa a API é definido aqui. Os modelos são deliberadamente
serializáveis e livres de objetos de imagem: a arte é sempre *derivada* do
blueprint (procedural) ou do resultado de importação (foto), o que garante que
um personagem salvo possa ser regenerado byte a byte a partir do seu registro.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "Direction",
    "AnimationKind",
    "BodyArchetype",
    "Origin",
    "Rarity",
    "StatBlock",
    "AbilitySpec",
    "PaletteChoice",
    "ProceduralBlueprint",
    "ImageImportParams",
    "CharacterAsset",
    "ExportFormat",
    "ExportOptions",
    "ExportBundle",
    "AnimationSpec",
    "utcnow",
]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Direction(StrEnum):
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"


class AnimationKind(StrEnum):
    IDLE = "idle"
    WALK = "walk"
    DEATH = "death"


class BodyArchetype(StrEnum):
    """Arquétipos anatômicos suportados pelo gerador procedural."""

    BIPED = "biped"
    QUADRUPED = "quadruped"
    ARACHNID = "arachnid"
    SERPENT = "serpent"
    FLYER = "flyer"
    BLOB = "blob"
    HUMANOID_BRUTE = "humanoid_brute"


class Origin(StrEnum):
    """Como o sprite foi obtido."""

    PROCEDURAL = "procedural"
    IMAGE = "image"


class Rarity(StrEnum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ExportFormat(StrEnum):
    PHASER_HASH = "phaser_hash"
    PHASER_ARRAY = "phaser_array"
    SPARROW_XML = "sparrow_xml"
    UNIFORM_GRID = "uniform_grid"
    ASEPRITE_SHEET = "aseprite_sheet"


# ----------------------------------------------------------------------
# Gameplay
# ----------------------------------------------------------------------
class StatBlock(BaseModel):
    """Atributos de jogo do personagem/criatura.

    O Pixel Master entrega a *ficha funcional*: além da arte, o jogo recebe os
    números prontos para alimentar o sistema de combate do Vandoria.
    """

    model_config = ConfigDict(extra="forbid")

    level: int = Field(default=1, ge=1, le=255)
    health: int = Field(default=40, ge=1, le=100_000)
    mana: int = Field(default=0, ge=0, le=100_000)
    attack: int = Field(default=6, ge=0, le=10_000)
    defense: int = Field(default=4, ge=0, le=10_000)
    magic_attack: int = Field(default=0, ge=0, le=10_000)
    magic_defense: int = Field(default=0, ge=0, le=10_000)
    speed: int = Field(default=5, ge=0, le=1_000)
    stamina: int = Field(default=10, ge=0, le=10_000)
    accuracy: int = Field(default=70, ge=0, le=100)
    evasion: int = Field(default=5, ge=0, le=100)
    experience_reward: int = Field(default=10, ge=0, le=10_000_000)
    gold_reward: int = Field(default=0, ge=0, le=10_000_000)

    def power_rating(self) -> int:
        """Índice sintético de força, usado para balanceamento e raridade."""
        return int(
            self.health * 0.30
            + self.attack * 2.0
            + self.defense * 2.0
            + self.magic_attack * 1.8
            + self.magic_defense * 1.5
            + self.speed * 1.2
            + self.level * 6
        )


class AbilitySpec(BaseModel):
    """Habilidade especial associada ao personagem/criatura."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=96)
    description: str = Field(default="", max_length=512)
    kind: Literal["attack", "buff", "debuff", "heal", "passive", "summon"] = "attack"
    power: int = Field(default=10, ge=0, le=10_000)
    cooldown: float = Field(default=4.0, ge=0.0, le=600.0)
    cost: int = Field(default=0, ge=0, le=10_000)


# ----------------------------------------------------------------------
# Aparência
# ----------------------------------------------------------------------
class PaletteChoice(BaseModel):
    """Seleção de rampas de cor aplicadas ao sprite."""

    model_config = ConfigDict(extra="forbid")

    # ``None`` = usar o padrão da espécie; qualquer valor nomeado sobrescreve
    skin: str | None = None
    hair: str | None = None
    cloth: str | None = None
    metal: str | None = None
    leather: str | None = None
    accent: str | None = None
    eyes: str | None = None
    creature: str | None = None
    outline: tuple[int, int, int] = (24, 22, 32)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ProceduralBlueprint(BaseModel):
    """Receita determinística de um personagem gerado proceduralmente.

    Dado o mesmo ``seed`` e os mesmos parâmetros, o resultado é idêntico —
    propriedade coberta por testes.
    """

    model_config = ConfigDict(extra="forbid")

    seed: int = Field(default=0, ge=0)
    species: str = Field(default="human", min_length=1, max_length=64)
    archetype: BodyArchetype = BodyArchetype.BIPED
    gender: Literal["male", "female", "neutral"] = "neutral"
    body_size: float = Field(default=1.0, ge=0.6, le=1.5)
    head_size: float = Field(default=1.0, ge=0.6, le=1.6)
    limb_thickness: float = Field(default=1.0, ge=0.6, le=1.6)
    hair_style: str | None = None
    hair_length: float = Field(default=0.5, ge=0.0, le=1.0)
    facial_hair: bool = False
    eyes_style: str = "normal"
    skin_tone: str | None = None
    outfit: str = "adventurer"
    armor_level: int = Field(default=1, ge=0, le=4)
    headgear: str | None = None
    weapon: str | None = None
    offhand: str | None = None
    cape: bool = False
    wings: bool = False
    horns: str | None = None
    tail: str | None = None
    extra_limbs: int = Field(default=0, ge=0, le=8)
    spikes: int = Field(default=0, ge=0, le=16)
    palette: PaletteChoice = Field(default_factory=PaletteChoice)
    custom_colors: dict[str, tuple[int, int, int]] = Field(default_factory=dict)
    outline: bool = True
    shading: bool = True

    @field_validator("species", "outfit")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class ImageImportParams(BaseModel):
    """Parâmetros do pipeline *foto de IA -> personagem jogável*."""

    model_config = ConfigDict(extra="forbid")

    # --- recorte -------------------------------------------------------
    background: Literal["auto", "alpha", "solid", "keep"] = "auto"
    background_color: tuple[int, int, int] | None = None
    background_tolerance: int = Field(default=38, ge=0, le=255)
    auto_crop: bool = True
    padding: int = Field(default=3, ge=0, le=16)

    # --- pixelização ---------------------------------------------------
    target_size: int = Field(default=48, ge=16, le=64)
    palette_size: int = Field(default=14, ge=2, le=32)
    pixel_mode: Literal["dominant", "average", "box"] = "dominant"
    outline: bool = True
    outline_strength: float = Field(default=0.42, ge=0.1, le=1.0)
    cleanup: bool = True
    despeckle: int = Field(default=2, ge=0, le=16)

    # --- direções ------------------------------------------------------
    source_view: Literal["front", "side", "back", "auto"] = "auto"
    synthesize_directions: bool = True
    side_squeeze: float = Field(default=0.74, ge=0.5, le=1.0)
    fidelity: float = Field(default=1.0, ge=0.0, le=1.0)

    # --- animação ------------------------------------------------------
    animations: list[AnimationKind] = Field(
        default_factory=lambda: [AnimationKind.IDLE, AnimationKind.WALK, AnimationKind.DEATH]
    )
    idle_frames: int = Field(default=4, ge=2, le=8)
    walk_frames: int = Field(default=4, ge=2, le=8)
    death_frames: int = Field(default=6, ge=3, le=12)
    idle_fps: int = Field(default=6, ge=1, le=30)
    walk_fps: int = Field(default=8, ge=1, le=30)
    death_fps: int = Field(default=10, ge=1, le=30)

    # --- rigging -------------------------------------------------------
    auto_rig: bool = True
    rig_override: dict[str, dict[str, float]] | None = None

    @field_validator("animations")
    @classmethod
    def _unique(cls, v: list[AnimationKind]) -> list[AnimationKind]:
        seen: list[AnimationKind] = []
        for item in v:
            if item not in seen:
                seen.append(item)
        return seen


class AnimationSpec(BaseModel):
    """Descrição pública de uma animação exportada."""

    model_config = ConfigDict(extra="forbid")

    name: AnimationKind
    fps: int
    loops: bool
    directions: list[Direction]
    frames_per_direction: dict[str, int]


# ----------------------------------------------------------------------
# Agregado principal
# ----------------------------------------------------------------------
class CharacterAsset(BaseModel):
    """Um personagem ou criatura completa e exportável."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: "")
    slug: str = Field(default="", max_length=96)
    name: str = Field(min_length=1, max_length=96)
    kind: Literal["character", "creature"] = "character"
    species: str = "human"
    description: str = Field(default="", max_length=1024)
    rarity: Rarity = Rarity.COMMON
    tags: list[str] = Field(default_factory=list)

    origin: Origin = Origin.PROCEDURAL
    seed: int = Field(default=0, ge=0)

    procedural: ProceduralBlueprint | None = None
    image_params: ImageImportParams | None = None
    source_image_ref: str | None = None

    stats: StatBlock = Field(default_factory=StatBlock)
    abilities: list[AbilitySpec] = Field(default_factory=list)

    frame_width: int = Field(default=64, ge=8, le=256)
    frame_height: int = Field(default=64, ge=8, le=256)
    anchor: tuple[float, float] = (0.5, 1.0)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in v if t.strip()})


class ExportOptions(BaseModel):
    """O que incluir no pacote de entrega."""

    model_config = ConfigDict(extra="forbid")

    formats: list[ExportFormat] = Field(default_factory=lambda: [ExportFormat.PHASER_HASH, ExportFormat.UNIFORM_GRID])
    include_sparrow_xml: bool = False
    include_gif_preview: bool = True
    include_individual_frames: bool = False
    include_manifest: bool = True
    include_stats: bool = True
    include_vandoria_card: bool = True
    scale: int = Field(default=1, ge=1, le=8, description="Escala inteira do PNG (1 = nativo, 4 = preview)")
    transparent_background: bool = True

    @field_validator("formats")
    @classmethod
    def _unique(cls, v: list[ExportFormat]) -> list[ExportFormat]:
        seen: list[ExportFormat] = []
        for item in v:
            if item not in seen:
                seen.append(item)
        return seen


class ExportBundle(BaseModel):
    """Resultado de uma exportação."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str
    filename: str
    size_bytes: int
    files: list[str]
    sprite_width: int
    sprite_height: int
    atlas_width: int
    atlas_height: int
    frame_count: int
    color_count: int
    animations: list[AnimationSpec]
    download_url: str
    created_at: datetime = Field(default_factory=utcnow)
