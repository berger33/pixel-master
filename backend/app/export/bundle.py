"""Montagem do pacote de entrega de um personagem.

Produz, a partir dos clipes de animação e da ficha do personagem:

* ``spritesheet.png``  — atlas de grade uniforme (Phaser ``load.spritesheet``);
* ``atlas_phaser.json``/``atlas_phaser_array.json``/``atlas_sparrow.xml``;
* ``manifest.json``    — manifesto de grade + índices de animação;
* ``preview.gif``      — pré-visualização animada (idle -> walk -> death);
* ``frames/…``         — quadros individuais (opcional);
* ``card.json``        — a *ficha funcional* pronta para o backend do Vandoria;
* ``README.txt``       — instruções rápidas de integração.
"""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass

from PIL import Image

from app.domain.models import (
    AnimationSpec,
    CharacterAsset,
    ExportBundle,
    ExportFormat,
    ExportOptions,
)
from app.pixel.spritesheet import (
    AnimationClip,
    SpriteSheet,
    pack_animation_set,
    phaser_array_atlas,
    phaser_hash_atlas,
    sparrow_xml_atlas,
    uniform_grid_manifest,
)

__all__ = ["ExportArtifacts", "build_artifacts", "build_zip", "build_bundle_result"]


@dataclass
class ExportArtifacts:
    files: dict[str, bytes]
    sheet: SpriteSheet

    def names(self) -> list[str]:
        return sorted(self.files)


def _gif_bytes(clips: Iterable[AnimationClip], direction: str = "down") -> bytes:
    segments: list[tuple[Image.Image, int]] = []
    for clip in clips:
        frames = clip.frames_by_direction.get(direction) or next(iter(clip.frames_by_direction.values()))
        dur = max(1, int(round(1000.0 / clip.fps)))
        for f in frames:
            segments.append((f.to_pil(), dur))
    if not segments:
        return b""

    pframes: list[Image.Image] = []
    durations: list[int] = []
    for img, dur in segments:
        p = img.convert("P", palette=Image.ADAPTIVE, colors=255)
        alpha = img.split()[3]
        mask = alpha.point(lambda a: 255 if a <= 8 else 0)
        p.paste(255, mask)
        pframes.append(p)
        durations.append(dur)

    buf = io.BytesIO()
    pframes[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=pframes[1:],
        duration=durations,
        loop=0,
        transparency=255,
        disposal=2,
    )
    return buf.getvalue()


def _png_bytes(sheet: SpriteSheet, scale: int) -> bytes:
    img = sheet.image.to_pil()
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _card_json(asset: CharacterAsset, sheet: SpriteSheet) -> dict:
    return {
        "format": "vandoria/character-card",
        "version": 1,
        "id": asset.id,
        "slug": asset.slug,
        "name": asset.name,
        "kind": asset.kind,
        "species": asset.species,
        "rarity": asset.rarity.value,
        "tags": asset.tags,
        "description": asset.description,
        "origin": asset.origin.value,
        "seed": asset.seed,
        "sprite": {
            "atlas": "spritesheet.png",
            "frameWidth": sheet.frame_width,
            "frameHeight": sheet.frame_height,
            "columns": sheet.columns,
            "rows": sheet.rows,
            "frameCount": sheet.frame_count,
            "anchor": {"x": asset.anchor[0], "y": asset.anchor[1]},
            "colorCount": sheet.image.color_count(),
        },
        "animations": sheet.animations,
        "stats": asset.stats.model_dump(),
        "powerRating": asset.stats.power_rating(),
        "abilities": [a.model_dump() for a in asset.abilities],
    }


def build_artifacts(
    asset: CharacterAsset,
    clips: list[AnimationClip],
    options: ExportOptions | None = None,
) -> ExportArtifacts:
    options = options or ExportOptions()
    sheet = pack_animation_set(clips, frame_width=asset.frame_width, frame_height=asset.frame_height)
    files: dict[str, bytes] = {}

    files["spritesheet.png"] = _png_bytes(sheet, options.scale)

    if ExportFormat.PHASER_HASH in options.formats:
        files["atlas_phaser.json"] = json.dumps(phaser_hash_atlas(sheet), indent=2).encode()
    if ExportFormat.PHASER_ARRAY in options.formats:
        files["atlas_phaser_array.json"] = json.dumps(phaser_array_atlas(sheet), indent=2).encode()
    if ExportFormat.SPARROW_XML in options.formats or options.include_sparrow_xml:
        files["atlas_sparrow.xml"] = sparrow_xml_atlas(sheet).encode()
    if ExportFormat.UNIFORM_GRID in options.formats or options.include_manifest:
        files["manifest.json"] = json.dumps(
            uniform_grid_manifest(sheet, extra={"assetId": asset.id, "assetSlug": asset.slug}),
            indent=2,
        ).encode()
    if ExportFormat.ASEPRITE_SHEET in options.formats:
        # Aseprite importa grades uniformes diretamente; entregamos o JSON de
        # descrição de tags no formato que ele entende ao reimportar.
        files["atlas_aseprite.json"] = json.dumps(_aseprite_tags(sheet), indent=2).encode()

    if options.include_gif_preview:
        files["preview.gif"] = _gif_bytes(clips, "down")

    if options.include_stats or options.include_vandoria_card:
        files["card.json"] = json.dumps(_card_json(asset, sheet), indent=2).encode()

    if options.include_individual_frames:
        for f in sheet.frames:
            cell = sheet.image.crop(f.x, f.y, f.x + f.w, f.y + f.h)
            files[f"frames/{f.name}.png"] = cell.to_bytes("PNG")

    files["README.txt"] = _readme(asset, sheet).encode()
    return ExportArtifacts(files=files, sheet=sheet)


def _aseprite_tags(sheet: SpriteSheet) -> dict:
    tags = []
    for name, payload in sheet.animations.items():
        directions = payload["directions"]
        assert isinstance(directions, dict)
        for direction, info in directions.items():
            assert isinstance(info, dict)
            start = sheet.frames[[i for i, f in enumerate(sheet.frames) if f.animation == name and f.direction == direction][0]].index
            count = int(info["count"])
            tags.append({"name": f"{name}_{direction}", "from": start + 1, "to": start + count})
    return {
        "meta": {"format": "aseprite-tags", "frameTags": tags},
        "frameWidth": sheet.frame_width,
        "frameHeight": sheet.frame_height,
    }


def _readme(asset: CharacterAsset, sheet: SpriteSheet) -> str:
    anims = ", ".join(f"{name}({len(d)} dirs)" for name, d in
                      ((n, p["directions"]) for n, p in sheet.animations.items()))
    return f"""Pixel Master — pacote de personagem
===================================
Personagem : {asset.name} ({asset.species}, {asset.rarity.value})
Origem     : {asset.origin.value} (seed {asset.seed})
Quadro     : {sheet.frame_width}x{sheet.frame_height} px | {sheet.columns} colunas x {sheet.rows} linhas
Animações  : {anims}

Integração rápida (Phaser 3)
----------------------------
this.load.spritesheet('{asset.slug or asset.id}', 'spritesheet.png', {{
  frameWidth: {sheet.frame_width}, frameHeight: {sheet.frame_height}
}});
// depois de carregado:
const idx = manifest.animationStartIndex;              // manifest.json
this.anims.create({{
  key: '{asset.slug or asset.id}_walk_down',
  frames: this.anims.generateFrameNumbers('{asset.slug or asset.id}', {{
    start: idx.walk.down, end: idx.walk.down + {sheet.animations['walk']['directions']['down']['count'] - 1}
  }}),
  frameRate: {sheet.animations['walk']['fps']}, repeat: -1
}});

Outros motores
--------------
- atlas_phaser.json  -> formato TexturePacker JSON Hash (Phaser/PixiJS)
- atlas_sparrow.xml  -> formato Sparrow/Starling (Unity extensions, Cocos)
- card.json          -> ficha funcional (stats + habilidades) para o backend

A ficha funcional (card.json) contém HP/MP/atk/def/spd, recompensas de XP/ouro
e habilidades — pronta para alimentar o sistema de combate do Vandoria.
"""


def build_zip(artifacts: ExportArtifacts, filename: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in artifacts.names():
            zf.writestr(name, artifacts.files[name])
    return buf.getvalue()


def build_bundle_result(
    asset: CharacterAsset,
    artifacts: ExportArtifacts,
    *,
    download_url: str,
    zip_filename: str,
    zip_size: int,
) -> ExportBundle:
    specs = [
        AnimationSpec(
            name=clip_name,  # type: ignore[arg-type]
            fps=int(payload["fps"]),
            loops=bool(payload["loops"]),
            directions=sorted(payload["directions"].keys()),
            frames_per_direction={d: int(i["count"]) for d, i in payload["directions"].items()},
        )
        for clip_name, payload in artifacts.sheet.animations.items()
    ]
    return ExportBundle(
        asset_id=asset.id,
        filename=zip_filename,
        size_bytes=zip_size,
        files=artifacts.names(),
        sprite_width=artifacts.sheet.frame_width,
        sprite_height=artifacts.sheet.frame_height,
        atlas_width=artifacts.sheet.image.width,
        atlas_height=artifacts.sheet.image.height,
        frame_count=artifacts.sheet.frame_count,
        color_count=artifacts.sheet.image.color_count(),
        animations=specs,
        download_url=download_url,
    )
