"""Empacotamento de frames em atlas e geração de metadados de animação.

O sprite final de um personagem é uma grade uniforme de quadros de
``frame_width x frame_height``. Cada linha corresponde a um par
*(animação, direção)* e cada coluna a um quadro da sequência. Essa disposição
permite duas integrações simultâneas:

1. ``load.spritesheet(...)`` em Phaser (grade uniforme + índice de quadros);
2. atlas JSON Hash / Array compatível com TexturePacker e PixiJS.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

import numpy as np

from app.pixel.canvas import PixelCanvas

__all__ = [
    "DIRECTIONS",
    "Direction",
    "AnimationClip",
    "FrameRef",
    "SpriteSheet",
    "pack_animation_set",
    "phaser_hash_atlas",
    "phaser_array_atlas",
    "sparrow_xml_atlas",
    "uniform_grid_manifest",
]

Direction = str
DIRECTIONS: tuple[Direction, ...] = ("down", "left", "right", "up")


@dataclass
class AnimationClip:
    """Uma animação completa com suas variações direcionais."""

    name: str
    frames_by_direction: dict[Direction, list[PixelCanvas]]
    fps: int = 8
    loops: bool = True
    ping_pong: bool = False

    def directions(self) -> list[Direction]:
        return [d for d in DIRECTIONS if d in self.frames_by_direction]

    def frame_count(self, direction: Direction) -> int:
        return len(self.frames_by_direction.get(direction, []))

    @property
    def max_frames(self) -> int:
        return max((len(f) for f in self.frames_by_direction.values()), default=0)

    def playback_order(self, count: int) -> list[int]:
        """Ordem de reprodução, incluindo vai-e-volta quando configurado."""
        base = list(range(count))
        if self.ping_pong and count > 2:
            base = base + list(reversed(base[1:-1]))
        return base


@dataclass
class FrameRef:
    """Posição de um quadro dentro do atlas."""

    name: str
    animation: str
    direction: Direction
    index: int
    row: int
    x: int
    y: int
    w: int
    h: int

    columns: int = 0

    @property
    def grid_index(self) -> int:
        """Índice do quadro numa leitura linear da grade uniforme.

        É este número que um motor usa com ``load.spritesheet`` (frameWidth /
        frameHeight), pois células vazias no fim de uma linha também contam.
        """
        return self.row * self.columns + self.index

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "animation": self.animation,
            "direction": self.direction,
            "index": self.index,
            "frame": {"x": self.x, "y": self.y, "w": self.w, "h": self.h},
            "sourceSize": {"w": self.w, "h": self.h},
            "spriteSourceSize": {"x": 0, "y": 0, "w": self.w, "h": self.h},
            "rotated": False,
            "trimmed": False,
        }


@dataclass
class SpriteSheet:
    """Atlas empacotado + índice de quadros e mapa de animações."""

    image: PixelCanvas
    frames: list[FrameRef]
    frame_width: int
    frame_height: int
    columns: int
    rows: int
    animations: dict[str, dict[str, object]] = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def by_name(self, name: str) -> FrameRef:
        for f in self.frames:
            if f.name == name:
                return f
        raise KeyError(name)


def _row_keys(clips: Iterable[AnimationClip]) -> list[tuple[str, Direction]]:
    """Ordem determinística das linhas: animação na ordem dada, direção canônica."""
    rows: list[tuple[str, Direction]] = []
    for clip in clips:
        for direction in clip.directions():
            rows.append((clip.name, direction))
    return rows


def pack_animation_set(
    clips: Sequence[AnimationClip],
    *,
    frame_width: int = 64,
    frame_height: int = 64,
    name_template: str = "{animation}_{direction}_{index:02d}",
) -> SpriteSheet:
    """Monta todos os clipes em uma única grade uniforme.

    Quadros menores que a célula são centralizados horizontalmente e alinhados
    pela base (pés no chão), que é a convenção de sprites top-down de RPG.
    """
    if not clips:
        raise ValueError("nenhum clipe de animação para empacotar")

    rows = _row_keys(clips)
    columns = max(
        (len(c.frames_by_direction[d]) for c in clips for d in c.directions()),
        default=1,
    )
    columns = max(1, columns)

    atlas = PixelCanvas(columns * frame_width, max(1, len(rows)) * frame_height)
    frames: list[FrameRef] = []

    for row_index, (anim_name, direction) in enumerate(rows):
        clip = next(c for c in clips if c.name == anim_name)
        clip_frames = clip.frames_by_direction[direction]
        for col_index, src in enumerate(clip_frames):
            cell = PixelCanvas(frame_width, frame_height)
            # alinhamento: base do conteúdo encosta no fundo da célula
            bbox = src.bbox()
            offset_x = (frame_width - src.width) // 2
            offset_y = frame_height - src.height
            if bbox is not None:
                offset_x = max(0, min(frame_width - src.width, offset_x))
                offset_y = max(0, min(frame_height - src.height, offset_y))
            cell.blit(src, offset_x, offset_y)

            x = col_index * frame_width
            y = row_index * frame_height
            atlas.data[y : y + frame_height, x : x + frame_width] = cell.data
            frames.append(
                FrameRef(
                    name=name_template.format(animation=anim_name, direction=direction, index=col_index),
                    animation=anim_name,
                    direction=direction,
                    index=col_index,
                    row=row_index,
                    columns=columns,
                    x=x,
                    y=y,
                    w=frame_width,
                    h=frame_height,
                )
            )

    animations: dict[str, dict[str, object]] = {}
    for clip in clips:
        entry: dict[str, object] = {
            "fps": clip.fps,
            "loops": clip.loops,
            "pingPong": clip.ping_pong,
            "directions": {},
        }
        per_direction: dict[str, object] = {}
        for direction in clip.directions():
            count = len(clip.frames_by_direction[direction])
            per_direction[direction] = {
                "frames": [
                    name_template.format(animation=clip.name, direction=direction, index=i)
                    for i in range(count)
                ],
                "order": clip.playback_order(count),
                "count": count,
            }
        entry["directions"] = per_direction
        animations[clip.name] = entry

    sheet = SpriteSheet(
        image=atlas,
        frames=frames,
        frame_width=frame_width,
        frame_height=frame_height,
        columns=columns,
        rows=len(rows),
        animations=animations,
    )
    return sheet


# ----------------------------------------------------------------------
# Formatos de metadados
# ----------------------------------------------------------------------
def _meta(sheet: SpriteSheet, image_name: str) -> dict[str, object]:
    return {
        "app": "Pixel Master",
        "version": "1.0.0",
        "image": image_name,
        "format": "RGBA8888",
        "size": {"w": sheet.image.width, "h": sheet.image.height},
        "scale": "1",
        "frameWidth": sheet.frame_width,
        "frameHeight": sheet.frame_height,
        "columns": sheet.columns,
        "rows": sheet.rows,
        "frameCount": sheet.frame_count,
    }


def phaser_hash_atlas(sheet: SpriteSheet, image_name: str = "spritesheet.png") -> dict[str, object]:
    """Atlas **JSON Hash** — formato TexturePacker aceito por Phaser 3 e PixiJS."""
    return {
        "frames": {f.name: _phaser_frame_body(f) for f in sheet.frames},
        "animations": {
            name: [f.name for f in sheet.frames if f.animation == name]
            for name in {f.animation for f in sheet.frames}
        },
        "meta": _meta(sheet, image_name),
    }


def _phaser_frame_body(f: FrameRef) -> dict[str, object]:
    return {
        "frame": {"x": f.x, "y": f.y, "w": f.w, "h": f.h},
        "rotated": False,
        "trimmed": False,
        "spriteSourceSize": {"x": 0, "y": 0, "w": f.w, "h": f.h},
        "sourceSize": {"w": f.w, "h": f.h},
    }


def phaser_array_atlas(sheet: SpriteSheet, image_name: str = "spritesheet.png") -> dict[str, object]:
    """Atlas **JSON Array** — variante alternativa do formato TexturePacker."""
    return {
        "frames": [{"filename": f.name, **_phaser_frame_body(f)} for f in sheet.frames],
        "meta": _meta(sheet, image_name),
    }


def sparrow_xml_atlas(sheet: SpriteSheet, image_name: str = "spritesheet.png") -> str:
    """Atlas **Sparrow/Starling XML**, aceito por diversos motores 2D."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<TextureAtlas imagePath="{image_name}" width="{sheet.image.width}" height="{sheet.image.height}">',
    ]
    for f in sheet.frames:
        lines.append(
            f'    <SubTexture name="{f.name}" x="{f.x}" y="{f.y}" width="{f.w}" height="{f.h}" />'
        )
    lines.append("</TextureAtlas>")
    return "\n".join(lines)


def uniform_grid_manifest(
    sheet: SpriteSheet,
    image_name: str = "spritesheet.png",
    *,
    anchor: tuple[float, float] = (0.5, 1.0),
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Manifesto de grade uniforme — o formato mais simples de consumir.

    Compatível com ``this.load.spritesheet(key, url, {frameWidth, frameHeight})``
    no Phaser: ``animationStartIndex[anim][dir]`` é o **índice linear da grade**
    do primeiro quadro, pronto para ``generateFrameNumbers(start, end)``.
    """
    starts: dict[tuple[str, str], int] = {}
    counts: dict[tuple[str, str], int] = {}
    for f in sheet.frames:
        key = (f.animation, f.direction)
        if f.index == 0:
            starts[key] = f.grid_index
        counts[key] = f.index + 1

    animation_index: dict[str, dict[str, int]] = {}
    for (anim, direction), start in starts.items():
        animation_index.setdefault(anim, {})[direction] = start

    manifest: dict[str, object] = {
        "format": "pixel-master/uniform-grid",
        "version": 1,
        "image": image_name,
        "frameWidth": sheet.frame_width,
        "frameHeight": sheet.frame_height,
        "columns": sheet.columns,
        "rows": sheet.rows,
        "frameCount": sheet.frame_count,
        "anchor": {"x": anchor[0], "y": anchor[1]},
        "animations": sheet.animations,
        "animationStartIndex": animation_index,
        "animationFrameCounts": {
            anim: {d: counts[(anim, d)] for d in per} for anim, per in animation_index.items()
        },
    }
    if extra:
        manifest.update(extra)
    return manifest


def estimate_atlas_size(clips: Iterable[AnimationClip], frame_width: int, frame_height: int) -> tuple[int, int]:
    """Prevê o tamanho do atlas antes de empacotar (útil para limites de texture)."""
    rows = _row_keys(clips)
    columns = max((c.max_frames for c in clips), default=1)
    return (columns * frame_width, max(1, len(rows)) * frame_height)


def is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def next_power_of_two(value: int) -> int:
    return 1 if value <= 1 else 2 ** int(math.ceil(math.log2(value)))


def unique_colors_in(sheet: SpriteSheet) -> int:
    """Quantidade de cores distintas do atlas — métrica de qualidade de pixel art."""
    data = sheet.image.data
    visible = data[..., 3] > 0
    if not visible.any():
        return 0
    return int(len(np.unique(data[..., :3][visible], axis=0)))
