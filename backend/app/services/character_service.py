"""Serviço de personagens: geração, importação, animação, preview e exportação.

É a camada que orquestra os módulos de baixo nível e é a única que conhece
persistência e sistema de arquivos. Toda a arte é *derivada sob demanda* a
partir do blueprint (procedural) ou da imagem-fonte armazenada (importação),
garantindo que um personagem salvo seja sempre regenerável.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from collections.abc import Callable
from pathlib import Path

from app.animation.animator import AnimationParams, build_clips
from app.core.config import get_settings
from app.db.repository import CharacterRepository
from app.domain.abilities import derive_abilities, derive_stats
from app.domain.models import (
    AnimationKind,
    CharacterAsset,
    Direction,
    ExportBundle,
    ExportOptions,
    ImageImportParams,
    Origin,
    ProceduralBlueprint,
    Rarity,
)
from app.domain.species import Species, get_species
from app.export.bundle import ExportArtifacts, build_artifacts, build_bundle_result, build_zip
from app.generator.from_image.pipeline import import_image
from app.generator.procedural.creature import build_creature_rig
from app.generator.rig import Rig, compose_rig
from app.pixel.canvas import PixelCanvas
from app.pixel.spritesheet import AnimationClip, SpriteSheet, pack_animation_set

__all__ = ["CharacterService", "slugify"]

_ALL_DIRECTIONS = [Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.UP]


def slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text)
    ascii_text = norm.encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "personagem"


class CharacterService:
    def __init__(self, repo: type[CharacterRepository] = CharacterRepository) -> None:
        self.repo = repo
        self.settings = get_settings()
        self._import_cache: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Criação
    # ------------------------------------------------------------------
    def create_procedural(
        self,
        blueprint: ProceduralBlueprint,
        *,
        name: str,
        kind: str = "character",
        rarity: Rarity = Rarity.COMMON,
        level: int = 1,
        tags: list[str] | None = None,
        description: str = "",
        seed: int | None = None,
    ) -> CharacterAsset:
        species = get_species(blueprint.species)
        resolved_seed = blueprint.seed if seed is None else seed
        blueprint = blueprint.model_copy(update={"seed": resolved_seed, "species": species.key})
        # a anatomia vem da espécie
        blueprint = blueprint.model_copy(update={"archetype": species.archetype})

        arcane = bool(blueprint.outfit == "mage_robe" or blueprint.weapon in ("staff", "wand"))
        stats = derive_stats(
            species=species, rarity=rarity, level=level, seed=resolved_seed,
            armor_level=blueprint.armor_level, arcane=arcane,
        )
        abilities = derive_abilities(species, seed=resolved_seed)

        asset = CharacterAsset(
            id=uuid.uuid4().hex,
            slug=slugify(name),
            name=name,
            kind=kind,  # type: ignore[arg-type]
            species=species.key,
            description=description,
            rarity=rarity,
            tags=tags or [],
            origin=Origin.PROCEDURAL,
            seed=resolved_seed,
            procedural=blueprint,
            stats=stats,
            abilities=abilities,
        )
        return self.repo.save(asset)

    def create_from_image(
        self,
        image_bytes: bytes,
        params: ImageImportParams,
        *,
        name: str,
        kind: str = "character",
        rarity: Rarity = Rarity.COMMON,
        level: int = 1,
        tags: list[str] | None = None,
        description: str = "",
        extension: str = ".png",
        seed: int = 0,
        species: str = "human",
    ) -> tuple[CharacterAsset, dict]:
        asset_id = uuid.uuid4().hex
        ext = extension if extension.startswith(".") else f".{extension}"
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        src_path = self.settings.upload_dir / f"{asset_id}{ext}"
        src_path.write_bytes(image_bytes)

        sp = get_species(species)
        stats = derive_stats(species=sp, rarity=rarity, level=level, seed=seed)
        abilities = derive_abilities(sp, seed=seed)

        asset = CharacterAsset(
            id=asset_id,
            slug=slugify(name),
            name=name,
            kind=kind,  # type: ignore[arg-type]
            species=sp.key,
            description=description,
            rarity=rarity,
            tags=tags or [],
            origin=Origin.IMAGE,
            seed=seed,
            image_params=params,
            source_image_ref=src_path.name,
            stats=stats,
            abilities=abilities,
        )
        asset = self.repo.save(asset)

        result = self._import_result(asset)
        meta = {
            "detectedView": result.meta.detected_view,
            "sourceSize": list(result.meta.source_size),
            "paletteSize": result.meta.palette_size,
            "backgroundRemoved": result.meta.background_removed,
            "warnings": result.meta.warnings,
            "directions": sorted(result.rigs),
        }
        return asset, meta

    # ------------------------------------------------------------------
    # Rigs / clipes
    # ------------------------------------------------------------------
    def _source_bytes(self, asset: CharacterAsset) -> bytes:
        if not asset.source_image_ref:
            raise ValueError("personagem sem imagem-fonte")
        path = self.settings.upload_dir / asset.source_image_ref
        return path.read_bytes()

    def _cached_import(self, cache_key: str, data: bytes, params_json: str):
        """Cache simples por instância (evita re-processar a mesma foto)."""
        hit = self._import_cache.get(cache_key)
        if hit is not None:
            return hit
        params = ImageImportParams.model_validate_json(params_json)
        result = import_image(data, params)
        if len(self._import_cache) > 8:
            self._import_cache.pop(next(iter(self._import_cache)))
        self._import_cache[cache_key] = result
        return result

    def _import_result(self, asset: CharacterAsset):
        data = self._source_bytes(asset)
        key = f"{asset.id}:{len(data)}"
        return self._cached_import(key, data, (asset.image_params or ImageImportParams()).model_dump_json())

    def rig_factory(self, asset: CharacterAsset) -> Callable[[Direction], Rig]:
        if asset.origin == Origin.IMAGE:
            result = self._import_result(asset)

            def factory_image(direction: Direction) -> Rig:
                rig = result.rigs.get(direction.value)
                if rig is None:
                    rig = next(iter(result.rigs.values()))
                return rig

            return factory_image

        bp = asset.procedural or ProceduralBlueprint(seed=asset.seed, species=asset.species)

        def factory_proc(direction: Direction) -> Rig:
            return build_creature_rig(bp, direction)

        return factory_proc

    def animation_params(self, asset: CharacterAsset) -> AnimationParams:
        p = asset.image_params
        if p is not None:
            return AnimationParams(
                idle_frames=p.idle_frames, walk_frames=p.walk_frames, death_frames=p.death_frames,
                idle_fps=p.idle_fps, walk_fps=p.walk_fps, death_fps=p.death_fps,
            )
        return AnimationParams()

    def kinds(self, asset: CharacterAsset) -> list[AnimationKind]:
        p = asset.image_params
        return list(p.animations) if p else [AnimationKind.IDLE, AnimationKind.WALK, AnimationKind.DEATH]

    def clips(self, asset: CharacterAsset) -> list[AnimationClip]:
        return build_clips(
            self.rig_factory(asset),
            directions=_ALL_DIRECTIONS,
            params=self.animation_params(asset),
            kinds=self.kinds(asset),
        )

    def sheet(self, asset: CharacterAsset) -> SpriteSheet:
        return pack_animation_set(self.clips(asset), frame_width=asset.frame_width, frame_height=asset.frame_height)

    # ------------------------------------------------------------------
    # Previews
    # ------------------------------------------------------------------
    def render_pose(self, asset: CharacterAsset, direction: Direction, scale: int = 6) -> bytes:
        rig = self.rig_factory(asset)(direction)
        canvas = compose_rig(rig)
        return self._scaled_png(canvas, scale)

    def render_strip(self, asset: CharacterAsset, animation: str, direction: Direction, scale: int = 4) -> bytes:
        clip = next((c for c in self.clips(asset) if c.name == animation), None)
        if clip is None:
            raise KeyError(animation)
        frames = clip.frames_by_direction.get(direction.value) or next(iter(clip.frames_by_direction.values()))
        strip = PixelCanvas(len(frames) * asset.frame_width, asset.frame_height)
        for i, f in enumerate(frames):
            strip.blit(f, i * asset.frame_width, 0)
        return self._scaled_png(strip, scale)

    def render_sheet(self, asset: CharacterAsset, scale: int = 3) -> bytes:
        return self._scaled_png(self.sheet(asset).image, scale)

    def render_gif(self, asset: CharacterAsset) -> bytes:
        from app.export.bundle import _gif_bytes

        return _gif_bytes(self.clips(asset), "down")

    @staticmethod
    def _scaled_png(canvas: PixelCanvas, scale: int) -> bytes:
        import io

        from PIL import Image

        img = canvas.to_pil()
        if scale > 1:
            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Exportação
    # ------------------------------------------------------------------
    def export(self, asset: CharacterAsset, options: ExportOptions | None = None) -> tuple[ExportBundle, bytes, Path]:
        options = options or ExportOptions()
        artifacts: ExportArtifacts = build_artifacts(asset, self.clips(asset), options)
        zip_name = f"{asset.slug or asset.id}_pixelmaster.zip"
        zip_bytes = build_zip(artifacts, zip_name)

        self.settings.storage_dir.mkdir(parents=True, exist_ok=True)
        stamp = uuid.uuid4().hex[:8]
        zip_path = self.settings.storage_dir / f"{asset.id}_{stamp}.zip"
        zip_path.write_bytes(zip_bytes)

        bundle = build_bundle_result(
            asset, artifacts,
            download_url=f"/api/exports/{zip_path.name}",
            zip_filename=zip_name,
            zip_size=len(zip_bytes),
        )
        return bundle, zip_bytes, zip_path

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def get(self, asset_id: str) -> CharacterAsset | None:
        return self.repo.get(asset_id)

    def list(self) -> list[CharacterAsset]:
        return self.repo.list_all()

    def delete(self, asset_id: str) -> bool:
        asset = self.repo.get(asset_id)
        if asset is None:
            return False
        if asset.source_image_ref:
            path = self.settings.upload_dir / asset.source_image_ref
            if path.exists():
                path.unlink()
        self._import_cache.clear()
        return self.repo.delete(asset_id)


def species_of(asset: CharacterAsset) -> Species:
    return get_species(asset.species)
