"""Primitivas de desenho de partes anatômicas e de equipamento.

Todas as funções desenham em coordenadas **absolutas do quadro** (o rig usa
camadas de tamanho completo), o que simplifica pivôs e composição.

Convenção de luz: a iluminação vem do canto superior esquerdo. Cada parte é
pintada em três tons derivados da rampa (claro / base / sombra), que é o padrão
consagrado de pixel art e mantém a contagem de cores baixa.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from app.pixel.canvas import Color, PixelCanvas, to_rgba
from app.pixel.palette import Ramp, ramp_from_color

__all__ = [
    "PartStyle",
    "tone3",
    "shade_by_light",
    "capsule",
    "blob",
    "draw_head",
    "draw_eyes",
    "draw_hair",
    "draw_hair_back",
    "draw_headgear",
    "draw_torso",
    "draw_limb",
    "draw_foot",
    "draw_hand",
    "draw_weapon",
    "draw_offhand",
    "draw_horns",
    "draw_tail",
    "draw_wings",
    "draw_shadow",
    "outline_layer",
    "WEAPONS",
    "HEADGEAR",
    "HAIR_STYLES",
    "OFFHANDS",
    "TAILS",
    "HORNS",
]

HAIR_STYLES: tuple[str, ...] = (
    "bald", "short", "medium", "long", "ponytail", "braid", "mohawk", "curly",
)
HEADGEAR: tuple[str | None, ...] = (
    None, "hood", "cap", "bandana", "crown", "helm", "wizard_hat", "circlet", "antlers",
)
WEAPONS: tuple[str, ...] = (
    "sword", "greatsword", "axe", "mace", "hammer", "dagger", "staff", "wand",
    "bow", "spear", "scythe", "whip", "sling", "claws",
)
OFFHANDS: tuple[str | None, ...] = (None, "shield", "buckler", "torch", "book", "orb")
HORNS: tuple[str, ...] = ("small", "large", "curved", "tusks", "antlers")
TAILS: tuple[str, ...] = ("short", "rat", "bushy", "snake", "spiked", "barbed", "flame")


@dataclass
class PartStyle:
    """Configuração estética compartilhada entre as partes."""

    outline: bool = True
    shading: bool = True
    outline_color: Color = (24, 22, 32)
    dither: bool = False


def tone3(ramp: Ramp) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """Extrai (claro, base, sombra) de uma rampa."""
    n = len(ramp)
    if n >= 5:
        return ramp.colors[1], ramp.colors[2], ramp.colors[3]
    if n >= 3:
        return ramp.colors[0], ramp.colors[n // 2], ramp.colors[-1]
    if n == 2:
        return ramp.colors[0], ramp.colors[0], ramp.colors[1]
    return ramp.colors[0], ramp.colors[0], ramp.colors[0]


def ramp_from(base: Color, steps: int = 5, name: str = "part") -> Ramp:
    return ramp_from_color(tuple(int(c) for c in base[:3]), steps=steps, name=name)  # type: ignore[arg-type]


def shade_by_light(
    canvas: PixelCanvas,
    ramp: Ramp,
    *,
    bbox: tuple[int, int, int, int] | None = None,
    light_x: float = 0.22,
    light_y: float = 0.18,
    style: PartStyle | None = None,
) -> PixelCanvas:
    """Repinta **em lugar** os pixels visíveis em 3 tons conforme a luz.

    ``light_x``/``light_y`` são posições normalizadas (0..1) da fonte de luz
    dentro da caixa delimitadora da parte. Retorna o próprio ``canvas`` para
    permitir encadeamento.
    """
    style = style or PartStyle()
    if not style.shading:
        return canvas
    region = bbox or canvas.bbox()
    if region is None:
        return canvas
    x0, y0, x1, y1 = region
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    light, base, shadow = tone3(ramp)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    dx = (xs - x0) / w - light_x
    dy = (ys - y0) / h - light_y
    dist = np.sqrt(dx * dx + dy * dy)
    max_dist = math.hypot(max(light_x, 1 - light_x), max(light_y, 1 - light_y)) or 1.0
    t = dist / max_dist

    sub = canvas.data[y0:y1, x0:x1]
    visible = sub[..., 3] > 0

    band_light = visible & (t <= 0.42)
    band_shadow = visible & (t >= 0.78)
    band_base = visible & ~band_light & ~band_shadow

    if style.dither:
        checker = ((xs + ys) % 2) == 0
        band_base = band_base & ~(checker & (t > 0.66))
        band_shadow = band_shadow | (visible & checker & (t > 0.66) & (t < 0.78))

    sub[band_light, :3] = np.array(light, dtype=np.uint8)
    sub[band_base, :3] = np.array(base, dtype=np.uint8)
    sub[band_shadow, :3] = np.array(shadow, dtype=np.uint8)
    canvas.data[y0:y1, x0:x1] = sub
    return canvas


def capsule(
    canvas: PixelCanvas,
    a: Sequence[float],
    b: Sequence[float],
    radius: float,
    color: Color,
) -> None:
    """Preenche uma cápsula (segmento engrossado) — ideal para braços e pernas.

    ``a`` e ``b`` são pontos ``(x, y)``.
    """
    radius = max(0.6, float(radius))
    xa, ya, xb, yb = float(a[0]), float(a[1]), float(b[0]), float(b[1])
    min_x = max(0, int(math.floor(min(xa, xb) - radius)))
    max_x = min(canvas.width - 1, int(math.ceil(max(xa, xb) + radius)))
    min_y = max(0, int(math.floor(min(ya, yb) - radius)))
    max_y = min(canvas.height - 1, int(math.ceil(max(ya, yb) + radius)))
    if min_x > max_x or min_y > max_y:
        return

    ys, xs = np.mgrid[min_y : max_y + 1, min_x : max_x + 1].astype(np.float32)
    px, py = xs + 0.5, ys + 0.5

    seg_dx, seg_dy = xb - xa, yb - ya
    seg_len2 = seg_dx * seg_dx + seg_dy * seg_dy
    if seg_len2 <= 1e-6:
        t = np.zeros_like(px)
    else:
        t = np.clip(((px - xa) * seg_dx + (py - ya) * seg_dy) / seg_len2, 0.0, 1.0)
    cx = xa + t * seg_dx
    cy = ya + t * seg_dy
    inside = ((px - cx) ** 2 + (py - cy) ** 2) <= radius * radius

    if not inside.any():
        return
    patch = np.zeros(inside.shape + (4,), dtype=np.uint8)
    patch[inside] = np.array(to_rgba(color), dtype=np.uint8)
    canvas.blend_region(min_x, min_y, patch)


def blob(
    canvas: PixelCanvas,
    points: Sequence[Sequence[float]],
    radius: float,
    color: Color,
) -> None:
    """Cápsula por múltiplos pontos (polilinha engrossada) — caudas, chifres."""
    pts = list(points)
    for i in range(len(pts) - 1):
        capsule(canvas, pts[i], pts[i + 1], radius, color)
    if len(pts) == 1:
        canvas.circle(pts[0][0], pts[0][1], radius, color)


def outline_layer(canvas: PixelCanvas, color: Color, *, inside: bool = False) -> PixelCanvas:
    return canvas.outline(color, diagonals=True, inside=inside)


# ----------------------------------------------------------------------
# Cabeça
# ----------------------------------------------------------------------
def draw_head(
    canvas: PixelCanvas,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    ramp: Ramp,
    *,
    shape: str = "round",
    style: PartStyle | None = None,
) -> tuple[int, int, int, int]:
    """Desenha a cabeça e retorna a bbox desenhada."""
    style = style or PartStyle()
    if shape == "square":
        canvas.rect(int(cx - rx), int(cy - ry), int(rx * 2), int(ry * 2), (0, 0, 0, 255))
        canvas.ellipse(cx, cy - ry * 0.35, rx, ry * 0.7, (0, 0, 0, 255))
        canvas.ellipse(cx, cy + ry * 0.4, rx * 0.86, ry * 0.62, (0, 0, 0, 255))
    elif shape == "pointy":
        canvas.ellipse(cx, cy, rx, ry, (0, 0, 0, 255))
        canvas.polygon(
            [(cx - rx * 0.5, cy + ry * 0.6), (cx + rx * 0.5, cy + ry * 0.6), (cx, cy + ry * 1.35)],
            (0, 0, 0, 255),
        )
    elif shape == "profile":
        # vista lateral: mais estreita, com sugestão de nariz na frente
        canvas.ellipse(cx, cy, rx, ry, (0, 0, 0, 255))
        canvas.ellipse(cx - rx * 0.25, cy + ry * 0.25, rx * 0.8, ry * 0.7, (0, 0, 0, 255))
    else:
        canvas.ellipse(cx, cy, rx, ry, (0, 0, 0, 255))
        canvas.ellipse(cx, cy + ry * 0.35, rx * 0.82, ry * 0.68, (0, 0, 0, 255))

    box = canvas.bbox()
    if box is not None:
        shade_by_light(canvas, ramp, bbox=box, style=style)
        return box
    return (int(cx - rx), int(cy - ry), int(cx + rx) + 1, int(cy + ry) + 1)


def draw_eyes(
    canvas: PixelCanvas,
    cx: float,
    cy: float,
    spacing: float,
    eye_ramp: Ramp,
    *,
    style: str = "normal",
    blink: bool = False,
    direction: str = "down",
    scale: float = 1.0,
) -> None:
    """Desenha os olhos conforme a direção e o estilo da espécie."""
    white = eye_ramp.at(0)
    dark = eye_ramp.at(-1)
    mid = eye_ramp.at(2) if len(eye_ramp) > 2 else dark

    if blink:
        canvas.set(int(cx - spacing), int(cy), dark)
        canvas.set(int(cx - spacing) + 1, int(cy), dark)
        if direction != "profile":
            canvas.set(int(cx + spacing), int(cy), dark)
            canvas.set(int(cx + spacing) - 1, int(cy), dark)
        return

    if direction == "up":
        return  # de costas não há rosto

    if style in ("glow", "demon", "arcane"):
        for sign in (-1, 1) if direction != "profile" else (-1,):
            ex = int(cx + sign * spacing)
            canvas.rect(ex - 1, int(cy) - 1, 3, 2, mid)
            canvas.set(ex, int(cy) - 1, white)
        return

    if style == "beast":
        signs = (-1, 1) if direction != "profile" else (-1,)
        for i, sign in enumerate(signs):
            ex = int(cx + sign * spacing)
            canvas.set(ex - 1, int(cy), mid)
            canvas.set(ex, int(cy), dark)
            canvas.set(ex + 1, int(cy) - 1 if i == 0 else int(cy) + 1, mid)
        return

    if style == "closed":
        for sign in (-1, 1) if direction != "profile" else (-1,):
            ex = int(cx + sign * spacing)
            canvas.hline(ex - 1, int(cy), 3, dark)
        return

    # normal / dot
    if direction == "profile":
        ex = int(cx - spacing * 0.9)
        w = max(1, int(round(1.4 * scale)))
        canvas.rect(ex, int(cy) - 1, w, 3, white)
        canvas.rect(ex, int(cy), w, 2, dark)
        return

    w = max(1, int(round(2 * scale)))
    h = max(2, int(round(3 * scale)))
    for sign in (-1, 1):
        ex = int(cx + sign * spacing) - (w // 2)
        if style == "small":
            canvas.rect(ex + (w // 2), int(cy), 1, 2, dark)
            continue
        canvas.rect(ex, int(cy) - 1, w, h, white)
        canvas.rect(ex, int(cy), w, h - 1, dark)
        canvas.set(ex, int(cy) - 1, white)


def draw_mouth(canvas: PixelCanvas, cx: float, cy: float, width: int, color: Color, *, fangs: bool = False) -> None:
    if width <= 0:
        return
    canvas.hline(int(cx - width // 2), int(cy), width, color)
    if fangs:
        canvas.set(int(cx - width // 2), int(cy) + 1, (245, 245, 245))
        canvas.set(int(cx + width // 2), int(cy) + 1, (245, 245, 245))


# ----------------------------------------------------------------------
# Cabelo
# ----------------------------------------------------------------------
def draw_hair(
    canvas: PixelCanvas,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    ramp: Ramp,
    *,
    style: str = "short",
    direction: str = "down",
    length: float = 0.5,
    facial_hair: bool = False,
    back_canvas: PixelCanvas | None = None,
) -> None:
    """Desenha o cabelo na camada frontal (e opcionalmente na camada traseira)."""
    if style == "bald":
        if facial_hair:
            _draw_beard(canvas, cx, cy, rx, ry, ramp, direction)
        return

    light, base, shadow = tone3(ramp)
    top = cy - ry

    if direction == "up":
        # de costas: cobre quase toda a cabeça
        canvas.ellipse(cx, cy - ry * 0.12, rx * 1.04, ry * 1.02, base)
        canvas.ellipse(cx - rx * 0.3, cy - ry * 0.45, rx * 0.55, ry * 0.42, light)
        if style in ("long", "ponytail", "braid") and back_canvas is not None:
            drop = ry * (1.1 + length * 1.6)
            back_canvas.ellipse(cx, cy + drop * 0.45, rx * 0.92, drop * 0.62, base)
            back_canvas.ellipse(cx + rx * 0.3, cy + drop * 0.5, rx * 0.4, drop * 0.4, shadow)
        return

    if direction == "profile":
        canvas.ellipse(cx + rx * 0.12, cy - ry * 0.22, rx * 1.02, ry * 0.86, base)
        canvas.ellipse(cx - rx * 0.25, cy - ry * 0.5, rx * 0.5, ry * 0.34, light)
        if style in ("long", "ponytail", "braid") and back_canvas is not None:
            back_canvas.ellipse(cx + rx * 0.55, cy + ry * (0.4 + length), rx * 0.5, ry * (0.5 + length * 0.9), base)
        if style == "mohawk":
            for i in range(4):
                canvas.rect(int(cx - rx * 0.2 + i), int(top - 3 - i % 2), 1, 4 + i % 2, shadow)
        if facial_hair:
            _draw_beard(canvas, cx, cy, rx, ry, ramp, direction)
        return

    # --- vista frontal ---
    if style == "short":
        canvas.ellipse(cx, cy - ry * 0.56, rx * 1.04, ry * 0.50, base)
        canvas.ellipse(cx - rx * 0.34, cy - ry * 0.78, rx * 0.44, ry * 0.26, light)
        canvas.rect(int(cx - rx), int(cy - ry * 0.40), 2, int(ry * 0.62), shadow)
        canvas.rect(int(cx + rx - 2), int(cy - ry * 0.40), 2, int(ry * 0.62), shadow)
    elif style == "medium":
        canvas.ellipse(cx, cy - ry * 0.52, rx * 1.06, ry * 0.56, base)
        canvas.rect(int(cx - rx * 1.05), int(cy - ry * 0.30), int(rx * 0.40), int(ry * 1.05), base)
        canvas.rect(int(cx + rx * 0.65), int(cy - ry * 0.30), int(rx * 0.40), int(ry * 1.05), base)
        canvas.ellipse(cx - rx * 0.3, cy - ry * 0.74, rx * 0.48, ry * 0.26, light)
    elif style == "long":
        canvas.ellipse(cx, cy - ry * 0.48, rx * 1.08, ry * 0.60, base)
        canvas.rect(int(cx - rx * 1.08), int(cy - ry * 0.30), int(rx * 0.44), int(ry * (1.4 + length)), base)
        canvas.rect(int(cx + rx * 0.64), int(cy - ry * 0.30), int(rx * 0.44), int(ry * (1.4 + length)), base)
        canvas.ellipse(cx - rx * 0.32, cy - ry * 0.72, rx * 0.48, ry * 0.26, light)
        if back_canvas is not None:
            back_canvas.ellipse(cx, cy + ry * (0.55 + length * 0.9), rx * 1.0, ry * (0.75 + length * 0.8), base)
            back_canvas.ellipse(cx + rx * 0.45, cy + ry * (0.6 + length), rx * 0.4, ry * 0.6, shadow)
    elif style == "ponytail":
        canvas.ellipse(cx, cy - ry * 0.52, rx * 1.04, ry * 0.54, base)
        canvas.ellipse(cx - rx * 0.3, cy - ry * 0.76, rx * 0.46, ry * 0.26, light)
        if back_canvas is not None:
            drop = ry * (0.9 + length * 1.3)
            blob(back_canvas, [(cx, top + ry * 0.3), (cx + rx * 0.5, top + drop * 0.5), (cx + rx * 0.3, top + drop)], max(1.6, rx * 0.28), base)
    elif style == "braid":
        canvas.ellipse(cx, cy - ry * 0.52, rx * 1.04, ry * 0.54, base)
        if back_canvas is not None:
            drop = ry * (0.9 + length * 1.4)
            steps = 5
            for i in range(steps):
                t = i / (steps - 1)
                bx = cx + rx * 0.45 + math.sin(t * math.pi * 1.4) * rx * 0.16
                by = top + ry * 0.3 + drop * t
                back_canvas.ellipse(bx, by, rx * (0.34 - 0.12 * t), ry * 0.28, base if i % 2 == 0 else shadow)
    elif style == "mohawk":
        canvas.rect(int(cx - rx * 0.95), int(cy - ry * 0.1), 2, int(ry * 0.4), shadow)
        canvas.rect(int(cx + rx * 0.95 - 2), int(cy - ry * 0.1), 2, int(ry * 0.4), shadow)
        for i in range(5):
            hgt = 3 + int(2.5 * math.sin(math.pi * i / 4))
            canvas.rect(int(cx - rx * 0.55) + i * max(1, int(rx * 0.28)), int(top - hgt + 2), 2, hgt + 2, base)
        canvas.rect(int(cx - rx * 0.5), int(top - 2), max(2, int(rx)), 2, light)
    elif style == "curly":
        canvas.ellipse(cx, cy - ry * 0.46, rx * 1.08, ry * 0.62, base)
        for i in range(9):
            ang = math.pi * (0.15 + 0.7 * i / 8)
            bx = cx + math.cos(ang) * rx * 1.02
            by = cy - ry * 0.35 - math.sin(ang) * ry * 0.8
            canvas.circle(bx, by, max(1.4, rx * 0.24), light if i % 3 == 0 else base)
        canvas.rect(int(cx - rx * 1.06), int(cy - ry * 0.15), int(rx * 0.4), int(ry * 0.7), base)
        canvas.rect(int(cx + rx * 0.66), int(cy - ry * 0.15), int(rx * 0.4), int(ry * 0.7), base)

    if facial_hair:
        _draw_beard(canvas, cx, cy, rx, ry, ramp, direction)


def draw_hair_back(
    canvas: PixelCanvas,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    ramp: Ramp,
    *,
    style: str = "short",
    direction: str = "down",
    length: float = 0.5,
) -> None:
    """Desenha apenas a porção de cabelo que fica **atrás** do corpo.

    Usada para montar a camada ``hair_back`` do rig sem duplicar o desenho da
    franja (que pertence à camada frontal).
    """
    if style not in ("long", "ponytail", "braid"):
        return
    _, base, shadow = tone3(ramp)
    top = cy - ry

    if direction == "profile":
        drop = ry * (0.55 + length * 1.5)
        blob(canvas, [(cx + rx * 0.5, top + ry * 0.55), (cx + rx * 0.85, top + drop * 0.6), (cx + rx * 0.6, top + drop)], max(1.8, rx * 0.42), base)
        blob(canvas, [(cx + rx * 0.85, top + drop * 0.6), (cx + rx * 0.95, top + drop)], max(1.2, rx * 0.24), shadow)
        return

    if style == "long":
        drop = ry * (1.15 + length * 1.9)
        canvas.ellipse(cx, cy + drop * 0.42, rx * 1.02, drop * 0.58, base)
        canvas.ellipse(cx + rx * 0.42, cy + drop * 0.46, rx * 0.42, drop * 0.4, shadow)
        canvas.ellipse(cx - rx * 0.45, cy + drop * 0.34, rx * 0.34, drop * 0.3, tone3(ramp)[0])
    elif style == "ponytail":
        drop = ry * (1.0 + length * 1.5)
        blob(canvas, [(cx + rx * 0.2, top + ry * 0.5), (cx + rx * 0.75, top + drop * 0.55), (cx + rx * 0.55, top + drop)], max(1.8, rx * 0.34), base)
        blob(canvas, [(cx + rx * 0.75, top + drop * 0.55), (cx + rx * 0.6, top + drop)], max(1.3, rx * 0.24), shadow)
    elif style == "braid":
        drop = ry * (1.0 + length * 1.6)
        steps = 6
        for i in range(steps):
            t = i / (steps - 1)
            bx = cx + rx * 0.5 + math.sin(t * math.pi * 1.5) * rx * 0.2
            by = top + ry * 0.45 + drop * t
            canvas.ellipse(bx, by, rx * (0.38 - 0.16 * t), ry * 0.3, base if i % 2 == 0 else shadow)


def _draw_beard(canvas: PixelCanvas, cx: float, cy: float, rx: float, ry: float, ramp: Ramp, direction: str) -> None:
    _, base, shadow = tone3(ramp)
    if direction == "up":
        return
    if direction == "profile":
        canvas.ellipse(cx - rx * 0.35, cy + ry * 0.55, rx * 0.62, ry * 0.55, base)
        canvas.ellipse(cx - rx * 0.1, cy + ry * 0.8, rx * 0.4, ry * 0.35, shadow)
        return
    canvas.ellipse(cx, cy + ry * 0.52, rx * 0.86, ry * 0.56, base)
    canvas.ellipse(cx, cy + ry * 0.78, rx * 0.58, ry * 0.34, shadow)
    canvas.hline(int(cx - rx * 0.85), int(cy + ry * 0.05), int(rx * 0.4), base)
    canvas.hline(int(cx + rx * 0.45), int(cy + ry * 0.05), int(rx * 0.4), base)


# ----------------------------------------------------------------------
# Torso e membros
# ----------------------------------------------------------------------
def draw_torso(
    canvas: PixelCanvas,
    cx: float,
    top: float,
    width: float,
    height: float,
    ramp: Ramp,
    *,
    style: PartStyle | None = None,
    outfit: str = "adventurer",
    accent: Ramp | None = None,
    bulky: bool = False,
    direction: str = "down",
) -> None:
    """Desenha o tronco com roupa/armadura e detalhes do vestuário."""
    style = style or PartStyle()
    light, base, shadow = tone3(ramp)

    shoulder_w = width * (1.18 if bulky else 1.0)
    waist_w = width * (0.78 if not bulky else 0.92)
    if direction == "profile":
        shoulder_w *= 0.62
        waist_w *= 0.62

    canvas.polygon(
        [
            (cx - shoulder_w / 2, top + height * 0.16),
            (cx + shoulder_w / 2, top + height * 0.16),
            (cx + waist_w / 2, top + height),
            (cx - waist_w / 2, top + height),
        ],
        (0, 0, 0, 255),
    )
    canvas.ellipse(cx, top + height * 0.18, shoulder_w / 2, height * 0.2, (0, 0, 0, 255))

    box = canvas.bbox()
    shade_by_light(canvas, ramp, bbox=box, style=style)

    # detalhes do vestuário
    if accent is not None:
        acc_light, acc_base, acc_shadow = tone3(accent)
        if outfit in ("knight", "mage_robe", "noble"):
            canvas.rect(int(cx - 1), int(top + height * 0.2), 2, int(height * 0.72), acc_base)
            canvas.rect(int(cx - 1), int(top + height * 0.2), 1, int(height * 0.72), acc_light)
        if outfit in ("adventurer", "rogue", "ranger", "knight"):
            belt_y = int(top + height * 0.74)
            canvas.rect(int(cx - waist_w / 2), belt_y, int(waist_w), 2, acc_shadow)
            canvas.rect(int(cx - 1), belt_y, 2, 2, acc_base)
        if outfit == "mage_robe":
            canvas.polygon(
                [(cx, top + height * 0.2), (cx - width * 0.42, top + height), (cx + width * 0.42, top + height)],
                acc_shadow,
            )
    if outfit in ("knight", "adventurer") and bulky:
        # placas de ombro
        canvas.ellipse(cx - shoulder_w / 2 + 1, top + height * 0.2, 3, 2.4, light)
        canvas.ellipse(cx + shoulder_w / 2 - 1, top + height * 0.2, 3, 2.4, light)


def draw_limb(
    canvas: PixelCanvas,
    joint_a: tuple[float, float],
    joint_b: tuple[float, float],
    joint_c: tuple[float, float] | None,
    thickness: float,
    ramp: Ramp,
    *,
    style: PartStyle | None = None,
    hand: bool = False,
    foot: bool = False,
    hand_ramp: Ramp | None = None,
) -> None:
    """Desenha um membro articulado (ombro -> cotovelo -> mão / quadril -> joelho -> pé)."""
    style = style or PartStyle()
    _, base, shadow = tone3(ramp)
    radius = max(1.0, thickness / 2.0)

    points = [joint_a, joint_b] + ([joint_c] if joint_c is not None else [])
    for i in range(len(points) - 1):
        r = radius if i == 0 else radius * 0.88
        capsule(canvas, points[i], points[i + 1], r, base)
    # leve sombra na metade inferior do membro
    if style.shading:
        end = points[-1]
        capsule(canvas, (end[0], end[1] - 1), end, radius * 0.8, shadow)

    tip = points[-1]
    if hand:
        draw_hand(canvas, tip[0], tip[1], radius * 1.15, hand_ramp or ramp)
    if foot:
        draw_foot(canvas, tip[0], tip[1], radius * 1.5, radius * 0.9, hand_ramp or ramp)


def draw_hand(canvas: PixelCanvas, x: float, y: float, r: float, ramp: Ramp) -> None:
    _, base, _ = tone3(ramp)
    canvas.circle(x, y, max(1.0, r), base)


def draw_foot(canvas: PixelCanvas, x: float, y: float, w: float, h: float, ramp: Ramp) -> None:
    light, base, shadow = tone3(ramp)
    canvas.ellipse(x, y, max(1.2, w), max(0.9, h), base)
    canvas.hline(int(x - w * 0.7), int(y + h * 0.5), int(w * 1.4), shadow)
    canvas.set(int(x - w * 0.4), int(y - h * 0.4), light)


# ----------------------------------------------------------------------
# Equipamento
# ----------------------------------------------------------------------
def draw_headgear(
    canvas: PixelCanvas,
    kind: str | None,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    ramp: Ramp,
    *,
    accent: Ramp | None = None,
    direction: str = "down",
    style: PartStyle | None = None,
) -> None:
    if kind is None:
        return
    style = style or PartStyle()
    light, base, shadow = tone3(ramp)
    acc = tone3(accent) if accent else (light, base, shadow)

    if kind == "hood":
        canvas.ellipse(cx, cy - ry * 0.1, rx * 1.24, ry * 1.16, base)
        if direction != "up":
            # recorta a abertura do capuz para revelar o rosto
            face_rx, face_ry = rx * 0.74, ry * 0.80
            canvas.erase_ellipse(cx, cy + ry * 0.14, face_rx, face_ry)
            canvas.ellipse(cx, cy + ry * 0.10, face_rx * 1.06, face_ry * 1.02, shadow, fill=False)
        canvas.ellipse(cx - rx * 0.4, cy - ry * 0.55, rx * 0.5, ry * 0.4, light)
    elif kind == "cap":
        canvas.ellipse(cx, cy - ry * 0.5, rx * 1.06, ry * 0.52, base)
        canvas.rect(int(cx - rx * 1.1), int(cy - ry * 0.45), int(rx * 2.2), 2, shadow)
        canvas.ellipse(cx - rx * 0.3, cy - ry * 0.68, rx * 0.4, ry * 0.22, light)
    elif kind == "bandana":
        canvas.rect(int(cx - rx * 1.02), int(cy - ry * 0.52), int(rx * 2.04), 3, base)
        canvas.rect(int(cx - rx * 1.02), int(cy - ry * 0.52), int(rx * 2.04), 1, light)
        if direction != "profile":
            canvas.polygon([(cx + rx * 0.9, cy - ry * 0.4), (cx + rx * 1.6, cy - ry * 0.05), (cx + rx * 0.95, cy - ry * 0.05)], shadow)
    elif kind == "crown":
        canvas.rect(int(cx - rx * 0.85), int(cy - ry * 0.82), int(rx * 1.7), 3, acc[1])
        for i in range(4):
            px = int(cx - rx * 0.85) + 1 + i * max(1, int(rx * 1.7 / 4))
            canvas.polygon([(px, cy - ry * 0.82), (px + 2, cy - ry * 0.82), (px + 1, cy - ry * 1.25)], acc[0])
        canvas.set(int(cx), int(cy - ry * 0.8), (220, 60, 70))
    elif kind == "helm":
        canvas.ellipse(cx, cy - ry * 0.08, rx * 1.12, ry * 1.06, base)
        canvas.rect(int(cx - rx * 1.05), int(cy - ry * 0.1), int(rx * 2.1), int(ry * 0.9), base)
        canvas.ellipse(cx - rx * 0.4, cy - ry * 0.5, rx * 0.5, ry * 0.38, light)
        if direction == "up":
            canvas.ellipse(cx, cy, rx * 0.8, ry * 0.7, shadow)
        elif direction == "profile":
            canvas.rect(int(cx - rx * 1.0), int(cy - ry * 0.05), int(rx * 1.5), 2, (18, 18, 26))
            canvas.polygon([(cx - rx * 1.05, cy + ry * 0.1), (cx - rx * 1.5, cy + ry * 0.45), (cx - rx * 1.0, cy + ry * 0.5)], shadow)
        else:
            canvas.rect(int(cx - rx * 0.82), int(cy - ry * 0.05), int(rx * 1.64), 2, (18, 18, 26))
            canvas.rect(int(cx - 1), int(cy - ry * 0.9), 2, int(ry * 1.1), shadow)
    elif kind == "wizard_hat":
        canvas.ellipse(cx, cy - ry * 0.72, rx * 1.5, ry * 0.28, shadow)
        canvas.ellipse(cx, cy - ry * 0.78, rx * 1.4, ry * 0.24, base)
        canvas.polygon(
            [
                (cx - rx * 0.86, cy - ry * 0.78),
                (cx + rx * 0.86, cy - ry * 0.78),
                (cx + rx * 0.18, cy - ry * 2.35),
                (cx - rx * 0.42, cy - ry * 1.9),
            ],
            base,
        )
        canvas.polygon(
            [
                (cx - rx * 0.8, cy - ry * 0.78),
                (cx - rx * 0.2, cy - ry * 0.78),
                (cx - rx * 0.4, cy - ry * 1.9),
            ],
            light,
        )
        canvas.rect(int(cx - rx * 0.86), int(cy - ry * 0.92), int(rx * 1.72), 2, acc[1])
    elif kind == "circlet":
        canvas.rect(int(cx - rx * 0.95), int(cy - ry * 0.62), int(rx * 1.9), 2, acc[1])
        canvas.set(int(cx), int(cy - ry * 0.62), acc[0])
        canvas.set(int(cx), int(cy - ry * 0.5), (120, 200, 240))
    elif kind == "antlers":
        for sign in (-1, 1):
            bx = cx + sign * rx * 0.72
            blob(
                canvas,
                [(bx, cy - ry * 0.7), (bx + sign * rx * 0.4, cy - ry * 1.3), (bx + sign * rx * 0.7, cy - ry * 1.7)],
                1.1,
                acc[2],
            )
            blob(canvas, [(bx + sign * rx * 0.35, cy - ry * 1.2), (bx + sign * rx * 0.05, cy - ry * 1.75)], 0.9, acc[1])


def _facing_sign(direction: str) -> int:
    return -1 if direction in ("left", "profile") else 1


def profile_side(direction: str) -> bool:
    return direction in ("left", "right", "profile")


def draw_weapon(
    canvas: PixelCanvas,
    kind: str,
    hand: tuple[float, float],
    ramp: Ramp,
    metal: Ramp,
    *,
    direction: str = "down",
    angle: float = 0.0,
    outward: int = 1,
) -> None:
    """Desenha a arma ancorada na mão, já rotacionada para a pose.

    ``outward`` desloca a arma para longe do centro do corpo (-1 = braço
    esquerdo, +1 = braço direito), evitando que a lâmina cubra o tronco.
    """
    wood_light, wood_base, wood_shadow = tone3(ramp)
    steel_light, steel_base, steel_shadow = tone3(metal)

    tmp = PixelCanvas(canvas.width, canvas.height)
    hx, hy = hand
    facing = -1 if direction in ("left", "profile") else 1

    if kind in ("sword", "greatsword"):
        long = kind == "greatsword"
        blade_len = 16 if long else 12
        blade_w = 3 if long else 2
        hx = hx + (3 * outward if not profile_side(direction) else 0)
        capsule(tmp, (hx, hy + 3), (hx, hy - blade_len), blade_w / 2 + 0.4, steel_base)
        tmp.rect(int(hx - blade_w / 2), int(hy - blade_len), blade_w, blade_len, steel_base)
        tmp.vline(int(hx - blade_w / 2), int(hy - blade_len + 1), blade_len - 2, steel_light)
        tmp.vline(int(hx + blade_w / 2 - 1), int(hy - blade_len + 1), blade_len - 2, steel_shadow)
        tmp.polygon([(hx - blade_w / 2, hy - blade_len), (hx + blade_w / 2, hy - blade_len), (hx, hy - blade_len - 3)], steel_light)
        tmp.rect(int(hx - (5 if long else 4)), int(hy + 2), (10 if long else 8), 2, steel_shadow)
        tmp.rect(int(hx - 1), int(hy + 4), 2, 5, wood_base)
        tmp.set(int(hx - 1), int(hy + 8), steel_light)
    elif kind in ("axe", "hammer"):
        shaft_len = 18 if kind == "axe" else 16
        capsule(tmp, (hx, hy + 6), (hx, hy - shaft_len), 1.3, wood_base)
        tmp.vline(int(hx - 1), int(hy - shaft_len + 2), shaft_len, wood_shadow)
        if kind == "axe":
            tmp.polygon(
                [
                    (hx + 1, hy - shaft_len + 1),
                    (hx + 9 * facing, hy - shaft_len + 3),
                    (hx + 10 * facing, hy - shaft_len + 9),
                    (hx + 1, hy - shaft_len + 8),
                ],
                steel_base,
            )
            tmp.polygon(
                [
                    (hx + 6 * facing, hy - shaft_len + 3),
                    (hx + 9 * facing, hy - shaft_len + 3),
                    (hx + 10 * facing, hy - shaft_len + 9),
                    (hx + 7 * facing, hy - shaft_len + 8),
                ],
                steel_light,
            )
        else:
            tmp.rect(int(hx - 5), int(hy - shaft_len - 2), 10, 8, steel_base)
            tmp.rect(int(hx - 5), int(hy - shaft_len - 2), 10, 2, steel_light)
            tmp.rect(int(hx - 5), int(hy - shaft_len + 4), 10, 2, steel_shadow)
    elif kind in ("mace",):
        capsule(tmp, (hx, hy + 5), (hx, hy - 12), 1.3, wood_base)
        tmp.circle(hx, hy - 14, 3.4, steel_base)
        tmp.circle(hx - 1, hy - 15, 1.6, steel_light)
        for dx, dy in ((0, -4), (3, -1), (-3, -1), (0, 3)):
            tmp.set(int(hx + dx), int(hy - 14 + dy), steel_shadow)
    elif kind == "dagger":
        capsule(tmp, (hx, hy + 3), (hx, hy - 6), 1.1, wood_base)
        tmp.rect(int(hx - 1), int(hy - 12), 2, 7, steel_base)
        tmp.vline(int(hx - 1), int(hy - 11), 5, steel_light)
        tmp.rect(int(hx - 3), int(hy - 6), 6, 1, steel_shadow)
    elif kind in ("staff", "wand"):
        length = 26 if kind == "staff" else 13
        capsule(tmp, (hx, hy + 6), (hx, hy - length), 1.2, wood_base)
        tmp.vline(int(hx - 1), int(hy - length + 2), length + 4, wood_shadow)
        tmp.circle(hx, hy - length - 1, 2.6 if kind == "staff" else 1.8, (150, 210, 255))
        tmp.set(int(hx - 1), int(hy - length - 2), (235, 250, 255))
    elif kind == "bow":
        points = []
        for i in range(13):
            t = i / 12.0
            ang = math.pi * (0.15 + 0.7 * t)
            points.append((hx + math.cos(ang) * 7 * facing, hy - 12 + math.sin(ang) * 13))
        blob(tmp, points, 1.2, wood_base)
        tmp.line(int(hx + 7 * facing), int(hy - 12 + 13 * math.sin(math.pi * 0.15)), int(hx + 7 * facing), int(hy - 12 + 13 * math.sin(math.pi * 0.85)), (230, 230, 220))
    elif kind == "spear":
        capsule(tmp, (hx, hy + 8), (hx, hy - 20), 1.1, wood_base)
        tmp.polygon([(hx - 2, hy - 20), (hx + 2, hy - 20), (hx, hy - 27)], steel_base)
        tmp.vline(int(hx), int(hy - 25), 5, steel_light)
    elif kind == "scythe":
        capsule(tmp, (hx, hy + 6), (hx, hy - 22), 1.2, wood_base)
        points = [(hx, hy - 22)]
        for i in range(9):
            t = i / 8.0
            points.append((hx + math.sin(t * math.pi * 0.6) * 11 * facing, hy - 22 + t * 9 - math.cos(t * 2) * 2))
        blob(tmp, points, 1.4, steel_base)
        tmp.set(int(hx + 4 * facing), int(hy - 22), steel_light)
    elif kind == "whip":
        points = [(hx, hy + 2)]
        for i in range(1, 10):
            t = i / 9.0
            points.append((hx + math.sin(t * math.pi * 1.6) * 8 * facing, hy + 2 + t * 14))
        blob(tmp, points, 0.8, (90, 62, 44))
    elif kind == "sling":
        tmp.line(int(hx - 4), int(hy - 2), int(hx + 4), int(hy - 2), (150, 130, 100))
        tmp.ellipse(hx, hy + 2, 3, 2.4, (120, 90, 60))
    elif kind == "claws":
        for i in range(3):
            capsule(tmp, (hx - 2 + i * 2, hy), (hx - 3 + i * 2, hy + 6), 0.8, (235, 235, 240))

    if abs(angle) > 1e-6:
        tmp = tmp.rotated(angle, pivot=(hx, hy))

    canvas.blend_region(0, 0, tmp.data)


def draw_offhand(
    canvas: PixelCanvas,
    kind: str | None,
    hand: tuple[float, float],
    ramp: Ramp,
    metal: Ramp,
    *,
    direction: str = "down",
) -> None:
    if kind is None:
        return
    wood_light, wood_base, wood_shadow = tone3(ramp)
    steel_light, steel_base, steel_shadow = tone3(metal)
    hx, hy = hand

    if kind in ("shield", "buckler"):
        small = kind == "buckler"
        w = 7 if small else 10
        h = 8 if small else 12
        hx = hx + 1
        hy = hy + 1
        canvas.ellipse(hx, hy, w / 2, h / 2, wood_base)
        canvas.ellipse(hx - w * 0.16, hy - h * 0.18, w * 0.3, h * 0.28, wood_light)
        canvas.circle(hx, hy, 2 if small else 3, steel_base)
        canvas.set(int(hx - 1), int(hy - 1), steel_light)
        if not small:
            canvas.polygon([(hx - w / 2 + 1, hy + h * 0.3), (hx + w / 2 - 1, hy + h * 0.3), (hx, hy + h / 2 + 2)], wood_shadow)
    elif kind == "torch":
        capsule(canvas, (hx, hy + 5), (hx, hy - 4), 1.2, wood_base)
        canvas.ellipse(hx, hy - 6, 2.6, 3.4, (255, 150, 40))
        canvas.ellipse(hx, hy - 7, 1.6, 2.2, (255, 225, 130))
    elif kind == "book":
        canvas.rect(int(hx - 4), int(hy - 5), 8, 10, (120, 50, 50))
        canvas.rect(int(hx - 3), int(hy - 4), 6, 8, (235, 225, 200))
        canvas.vline(int(hx - 4), int(hy - 5), 10, (80, 30, 30))
    elif kind == "orb":
        canvas.circle(hx, hy - 3, 4, (140, 110, 220))
        canvas.set(int(hx - 1), int(hy - 5), (220, 200, 255))
        canvas.circle(hx, hy - 3, 4, (90, 60, 160), fill=False)


def draw_horns(
    canvas: PixelCanvas,
    kind: str | None,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    ramp: Ramp,
    *,
    direction: str = "down",
) -> None:
    if kind is None:
        return
    light, base, shadow = tone3(ramp)
    if kind == "tusks":
        for sign in (-1, 1) if direction != "profile" else (-1,):
            bx = cx + sign * rx * 0.55
            blob(canvas, [(bx, cy + ry * 0.55), (bx + sign * rx * 0.18, cy + ry * 0.15), (bx + sign * rx * 0.1, cy - ry * 0.1)], 1.2, (240, 236, 214))
    elif kind == "small":
        for sign in (-1, 1) if direction != "profile" else (-1,):
            bx = cx + sign * rx * 0.7
            blob(canvas, [(bx, cy - ry * 0.6), (bx + sign * rx * 0.25, cy - ry * 1.05)], 1.4, base)
    elif kind == "large":
        for sign in (-1, 1) if direction != "profile" else (-1,):
            bx = cx + sign * rx * 0.68
            blob(
                canvas,
                [
                    (bx, cy - ry * 0.55),
                    (bx + sign * rx * 0.45, cy - ry * 1.15),
                    (bx + sign * rx * 0.3, cy - ry * 1.75),
                ],
                1.7,
                base,
            )
            blob(canvas, [(bx + sign * rx * 0.42, cy - ry * 1.1), (bx + sign * rx * 0.15, cy - ry * 1.4)], 1.0, light)
    elif kind == "curved":
        for sign in (-1, 1) if direction != "profile" else (-1,):
            pts = []
            for i in range(7):
                t = i / 6.0
                ang = math.pi * (0.5 + 0.9 * t)
                pts.append((cx + sign * rx * (0.7 + 0.55 * math.cos(ang) * sign * -1), cy - ry * (0.5 + 0.75 * math.sin(ang))))
            blob(canvas, pts, 1.5, base)
    elif kind == "antlers":
        draw_headgear(canvas, "antlers", cx, cy, rx, ry, ramp, direction=direction)


def draw_tail(
    canvas: PixelCanvas,
    kind: str | None,
    hip: tuple[float, float],
    ramp: Ramp,
    *,
    direction: str = "down",
    phase: float = 0.0,
    length: float = 1.0,
) -> None:
    if kind is None:
        return
    light, base, shadow = tone3(ramp)
    hx, hy = hip
    sway = math.sin(phase) * 2.5

    if kind == "short":
        blob(canvas, [(hx, hy), (hx + 3, hy + 2 + sway * 0.3)], 1.8, base)
    elif kind == "rat":
        pts = [(hx, hy)]
        for i in range(1, 9):
            t = i / 8.0
            pts.append((hx + math.sin(t * 3 + phase) * 4, hy + t * 14 * length))
        blob(canvas, pts, 0.9, shadow)
    elif kind == "bushy":
        pts = [(hx, hy), (hx - 4 + sway * 0.4, hy + 4), (hx - 6 + sway * 0.6, hy - 2)]
        blob(canvas, pts, 3.0, base)
        blob(canvas, [(hx - 6 + sway * 0.6, hy - 2), (hx - 8 + sway, hy - 8)], 2.4, light)
    elif kind == "snake":
        pts = [(hx, hy)]
        for i in range(1, 11):
            t = i / 10.0
            pts.append((hx + math.sin(t * 4 + phase) * 6, hy + t * 16 * length))
        blob(canvas, pts, 1.4, base)
    elif kind == "spiked":
        pts = [(hx, hy)]
        for i in range(1, 10):
            t = i / 9.0
            pts.append((hx + math.sin(t * 3.2 + phase) * 5, hy + t * 15 * length))
        blob(canvas, pts, 1.8, base)
        for i in range(2, 9, 2):
            t = i / 9.0
            canvas.polygon(
                [
                    (hx + math.sin(t * 3.2 + phase) * 5 - 1, hy + t * 15 * length),
                    (hx + math.sin(t * 3.2 + phase) * 5 + 1, hy + t * 15 * length),
                    (hx + math.sin(t * 3.2 + phase) * 5, hy + t * 15 * length - 3),
                ],
                shadow,
            )
    elif kind == "barbed":
        pts = [(hx, hy)]
        for i in range(1, 9):
            t = i / 8.0
            pts.append((hx + math.sin(t * 3 + phase) * 5, hy + t * 13 * length))
        blob(canvas, pts, 1.1, shadow)
        end = pts[-1]
        canvas.polygon([(end[0] - 2, end[1]), (end[0] + 2, end[1]), (end[0], end[1] + 4)], (200, 60, 60))
    elif kind == "flame":
        pts = [(hx, hy)]
        for i in range(1, 8):
            t = i / 7.0
            pts.append((hx + math.sin(t * 3.5 + phase) * 4, hy + t * 11 * length))
        blob(canvas, pts, 1.6, (120, 40, 20))
        for p in pts[2:]:
            canvas.circle(p[0], p[1], 1.2, (255, 140 + int(40 * math.sin(phase + p[0])), 40))


def draw_wings(
    canvas: PixelCanvas,
    cx: float,
    cy: float,
    span: float,
    ramp: Ramp,
    *,
    style: str = "bat",
    flap: float = 0.0,
    direction: str = "down",
) -> None:
    """Desenha asas. ``flap`` em [0,1] controla a abertura."""
    light, base, shadow = tone3(ramp)
    lift = math.sin(flap * math.pi * 2) * span * 0.18
    if direction == "profile":
        span *= 0.55

    for sign in (-1, 1):
        if style == "feather":
            for i in range(5):
                t = i / 4.0
                w = span * (0.35 + 0.65 * t)
                y = cy - span * 0.25 + t * span * 0.28 - lift * (1 - t * 0.4)
                canvas.ellipse(cx + sign * w * 0.62, y, w * 0.42, 2.2, base if i % 2 else light)
        elif style == "demon":
            pts = [(cx, cy)]
            for i in range(1, 7):
                t = i / 6.0
                pts.append((cx + sign * span * t, cy - span * 0.55 * math.sin(t * math.pi) - lift * t))
            pts.append((cx + sign * span * 0.55, cy + span * 0.28 - lift * 0.3))
            pts.append((cx + sign * span * 0.25, cy + span * 0.05))
            canvas.polygon(pts, base)
            canvas.polygon(pts[:4] + [(cx + sign * span * 0.4, cy - span * 0.1)], shadow)
            for i in range(1, 6):
                t = i / 6.0
                canvas.line(int(cx), int(cy), int(cx + sign * span * t), int(cy - span * 0.55 * math.sin(t * math.pi) - lift * t), shadow)
        else:  # bat
            pts = [(cx, cy - span * 0.15)]
            for i in range(1, 8):
                t = i / 7.0
                pts.append((cx + sign * span * t, cy - span * 0.5 * math.sin(t * math.pi) - lift * t))
            for i in range(7, 0, -1):
                t = i / 7.0
                scallop = 0.30 + 0.18 * math.sin(t * math.pi * 3)
                pts.append((cx + sign * span * t, cy + span * scallop - lift * t * 0.4))
            canvas.polygon(pts, base)
            for i in range(1, 7):
                t = i / 7.0
                canvas.line(
                    int(cx), int(cy - span * 0.15),
                    int(cx + sign * span * t), int(cy - span * 0.5 * math.sin(t * math.pi) - lift * t),
                    shadow,
                )
            canvas.ellipse(cx + sign * span * 0.18, cy - span * 0.28 - lift * 0.3, span * 0.14, span * 0.1, light)


def draw_shadow(canvas: PixelCanvas, cx: float, ground_y: float, width: float, *, alpha: int = 70) -> None:
    """Sombra de contato — ancora o sprite ao chão e melhora muito a leitura."""
    canvas.ellipse(cx, ground_y, width * 0.55, max(1.4, width * 0.14), (18, 16, 28, alpha))
    canvas.ellipse(cx, ground_y, width * 0.36, max(1.0, width * 0.09), (12, 10, 20, alpha + 30))
