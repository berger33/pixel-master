"""Paletas, rampas de sombreamento e quantização de cores.

Pixel art de qualidade depende de **rampas**: sequências curtas de tons da mesma
família que vão do destaque à sombra. Este módulo fornece

* rampas prontas para pele, cabelo, tecido, metal, couro, ossos e couros de
  monstro;
* geração de rampa a partir de uma cor-base qualquer (útil no modo procedural
  e ao extrair paleta de uma foto);
* quantização por *median cut* para reduzir uma imagem importada a ``N`` cores;
* derivação de cor de contorno a partir da cor dominante.
"""

from __future__ import annotations

import colorsys
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from app.pixel.canvas import PixelCanvas

__all__ = [
    "Ramp",
    "Palette",
    "PALETTES",
    "get_palette",
    "list_palettes",
    "ramp_from_color",
    "quantize_median_cut",
    "nearest_color",
    "snap_canvas_to_palette",
    "outline_color_for",
    "shift_hue",
    "luminance",
    "build_palette_from_canvas",
]


@dataclass(frozen=True)
class Ramp:
    """Sequência ordenada de tons, do mais claro ao mais escuro."""

    name: str
    colors: tuple[tuple[int, int, int], ...]

    def __len__(self) -> int:
        return len(self.colors)

    @property
    def light(self) -> tuple[int, int, int]:
        return self.colors[0]

    @property
    def dark(self) -> tuple[int, int, int]:
        return self.colors[-1]

    def at(self, index: int) -> tuple[int, int, int]:
        """Tom seguro por índice (satura nas pontas, nunca estoura)."""
        if not self.colors:
            return (0, 0, 0)
        return self.colors[max(0, min(len(self.colors) - 1, int(index)))]

    def highlight(self) -> tuple[int, int, int]:
        return self.at(0)

    def base(self) -> tuple[int, int, int]:
        return self.at(len(self.colors) // 3)

    def shade(self) -> tuple[int, int, int]:
        return self.at(len(self.colors) * 2 // 3)

    def shadow(self) -> tuple[int, int, int]:
        return self.at(-1)


@dataclass
class Palette:
    """Conjunto nomeado de rampas usado por um sprite."""

    name: str
    ramps: dict[str, Ramp] = field(default_factory=dict)

    def ramp(self, key: str) -> Ramp:
        return self.ramps[key]

    def colors(self) -> list[tuple[int, int, int]]:
        out: list[tuple[int, int, int]] = []
        for ramp in self.ramps.values():
            for c in ramp.colors:
                if c not in out:
                    out.append(c)
        return out

    def color_count(self) -> int:
        return len(self.colors())


# ----------------------------------------------------------------------
# Construção de rampas
# ----------------------------------------------------------------------
def _to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    return colorsys.rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def _from_hsv(hsv: tuple[float, float, float]) -> tuple[int, int, int]:
    h, s, v = hsv
    h = h % 1.0
    s = float(np.clip(s, 0.0, 1.0))
    v = float(np.clip(v, 0.0, 1.0))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def ramp_from_color(
    base: tuple[int, int, int],
    *,
    steps: int = 5,
    name: str = "ramp",
    hue_shift: float = -0.045,
) -> Ramp:
    """Cria uma rampa a partir de uma cor central.

    A rampa desloca levemente o **matiz** em direção ao quente nas sombras e ao
    frio nos brilhos, além de aumentar a saturação nos extremos. Esse é o truque
    que separa pixel art vibrante de cinza "sujo".
    """
    steps = max(2, int(steps))
    h, s, v = _to_hsv(tuple(int(c) for c in base))  # type: ignore[arg-type]
    colors: list[tuple[int, int, int]] = []
    for i in range(steps):
        t = i / (steps - 1)          # 0 = claro, 1 = escuro
        value = float(np.clip(v * (1.42 - 0.92 * t), 0.05, 1.0))
        sat = float(np.clip(s * (1.0 + 0.35 * abs(t - 0.45) * 2), 0.0, 1.0))
        hue = h + hue_shift * (1.0 - 2.0 * t)
        colors.append(_from_hsv((hue, sat, value)))
    return Ramp(name=name, colors=tuple(colors))


def shift_hue(color: tuple[int, int, int], delta: float) -> tuple[int, int, int]:
    h, s, v = _to_hsv(color)
    return _from_hsv((h + delta, s, v))


# ----------------------------------------------------------------------
# Paletas prontas
# ----------------------------------------------------------------------
def _r(name: str, *colors: tuple[int, int, int]) -> Ramp:
    return Ramp(name=name, colors=colors)


PALETTES: dict[str, Palette] = {
    "skin": Palette(
        name="skin",
        ramps={
            "pale": _r("pale", (255, 236, 214), (247, 212, 176), (224, 172, 130), (183, 130, 95), (133, 88, 62)),
            "fair": _r("fair", (252, 214, 176), (240, 187, 140), (212, 148, 103), (166, 106, 68), (117, 71, 44)),
            "tan": _r("tan", (238, 186, 133), (214, 152, 96), (176, 113, 64), (132, 79, 41), (90, 52, 27)),
            "brown": _r("brown", (196, 138, 92), (163, 104, 62), (124, 72, 39), (88, 48, 25), (57, 30, 16)),
            "dark": _r("dark", (141, 92, 60), (110, 65, 38), (81, 44, 24), (55, 29, 15), (35, 18, 10)),
            "ashen": _r("ashen", (206, 214, 205), (170, 181, 168), (129, 141, 128), (92, 103, 92), (59, 68, 60)),
        },
    ),
    "hair": Palette(
        name="hair",
        ramps={
            "black": _r("black", (86, 84, 100), (58, 56, 70), (38, 36, 48), (24, 23, 32), (14, 13, 20)),
            "brown": _r("brown", (166, 112, 66), (131, 82, 43), (96, 56, 27), (64, 36, 17), (40, 22, 11)),
            "blond": _r("blond", (247, 226, 158), (226, 193, 110), (192, 152, 71), (145, 108, 44), (99, 73, 29)),
            "red": _r("red", (219, 128, 84), (186, 91, 51), (146, 62, 31), (103, 39, 19), (66, 24, 12)),
            "white": _r("white", (255, 255, 255), (232, 234, 240), (198, 202, 214), (156, 161, 176), (112, 117, 133)),
            "green": _r("green", (150, 214, 132), (105, 176, 92), (69, 133, 62), (44, 92, 41), (27, 58, 26)),
            "blue": _r("blue", (130, 176, 232), (86, 133, 201), (53, 94, 161), (33, 62, 116), (20, 39, 76)),
        },
    ),
    "cloth": Palette(
        name="cloth",
        ramps={
            "white": _r("white", (245, 245, 245), (214, 214, 220), (172, 173, 184), (128, 130, 143), (86, 88, 100)),
            "red": _r("red", (226, 108, 96), (191, 70, 61), (148, 44, 40), (104, 28, 27), (66, 18, 18)),
            "blue": _r("blue", (116, 158, 214), (78, 118, 179), (49, 84, 141), (32, 57, 100), (20, 36, 64)),
            "green": _r("green", (126, 190, 116), (88, 155, 82), (57, 116, 55), (37, 80, 37), (23, 51, 24)),
            "yellow": _r("yellow", (240, 214, 122), (214, 179, 79), (173, 137, 47), (126, 96, 30), (83, 63, 20)),
            "purple": _r("purple", (176, 128, 214), (140, 90, 184), (104, 60, 145), (71, 39, 104), (45, 24, 67)),
            "brown": _r("brown", (176, 130, 86), (141, 96, 55), (104, 66, 34), (70, 43, 21), (44, 27, 13)),
            "black": _r("black", (96, 96, 108), (66, 66, 76), (44, 44, 53), (28, 28, 35), (16, 16, 21)),
            "teal": _r("teal", (112, 200, 190), (74, 163, 156), (45, 122, 118), (29, 84, 82), (18, 54, 53)),
        },
    ),
    "metal": Palette(
        name="metal",
        ramps={
            "steel": _r("steel", (226, 232, 240), (178, 188, 201), (132, 143, 158), (89, 98, 112), (56, 62, 73)),
            "iron": _r("iron", (176, 172, 168), (134, 130, 127), (96, 93, 91), (63, 61, 60), (39, 38, 37)),
            "gold": _r("gold", (255, 232, 145), (238, 196, 88), (200, 152, 47), (148, 105, 26), (97, 68, 16)),
            "copper": _r("copper", (232, 168, 122), (199, 124, 79), (157, 88, 50), (112, 58, 31), (72, 37, 20)),
            "mithril": _r("mithril", (214, 247, 255), (160, 216, 235), (112, 172, 196), (72, 126, 150), (45, 85, 104)),
        },
    ),
    "leather": Palette(
        name="leather",
        ramps={
            "tan": _r("tan", (201, 158, 106), (166, 121, 70), (126, 87, 45), (87, 58, 28), (55, 36, 17)),
            "dark": _r("dark", (126, 96, 70), (98, 71, 49), (71, 50, 33), (48, 33, 21), (30, 20, 13)),
            "fur": _r("fur", (196, 176, 152), (163, 141, 116), (124, 104, 83), (87, 72, 56), (55, 45, 35)),
        },
    ),
    "monster": Palette(
        name="monster",
        ramps={
            "slime": _r("slime", (176, 235, 141), (128, 204, 96), (86, 163, 62), (55, 122, 41), (33, 81, 26)),
            "scale": _r("scale", (122, 186, 148), (84, 152, 112), (54, 116, 82), (34, 82, 57), (20, 53, 36)),
            "chitin": _r("chitin", (166, 122, 92), (131, 88, 60), (96, 60, 38), (64, 39, 24), (40, 24, 15)),
            "bone": _r("bone", (242, 238, 219), (214, 207, 181), (176, 167, 141), (133, 124, 101), (92, 85, 68)),
            "flesh": _r("flesh", (214, 122, 132), (181, 84, 99), (140, 53, 68), (99, 34, 46), (63, 21, 30)),
            "demon": _r("demon", (232, 106, 84), (196, 66, 51), (152, 38, 30), (107, 23, 19), (68, 14, 12)),
            "shadow": _r("shadow", (116, 106, 158), (86, 76, 126), (59, 51, 94), (38, 32, 64), (22, 19, 38)),
            "undead": _r("undead", (196, 214, 186), (158, 179, 145), (117, 138, 104), (81, 99, 70), (52, 64, 44)),
            "arcane": _r("arcane", (196, 148, 240), (158, 105, 214), (119, 71, 173), (83, 46, 129), (52, 28, 85)),
        },
    ),
    "nature": Palette(
        name="nature",
        ramps={
            "wood": _r("wood", (176, 128, 82), (141, 96, 55), (104, 68, 36), (72, 45, 22), (45, 28, 14)),
            "leaf": _r("leaf", (150, 204, 106), (110, 168, 74), (76, 130, 49), (49, 92, 32), (30, 60, 20)),
            "stone": _r("stone", (176, 172, 168), (140, 137, 133), (104, 101, 99), (72, 70, 68), (46, 45, 44)),
        },
    ),
    "eye": Palette(
        name="eye",
        ramps={
            "white": _r("white", (255, 255, 255), (232, 232, 236), (200, 200, 208), (158, 158, 168), (112, 112, 122)),
            "black": _r("black", (70, 70, 82), (46, 46, 56), (30, 30, 38), (19, 19, 25), (11, 11, 15)),
            "red": _r("red", (242, 122, 106), (214, 79, 65), (173, 47, 38), (126, 29, 24), (81, 18, 15)),
            "blue": _r("blue", (148, 196, 242), (102, 158, 219), (63, 117, 179), (40, 80, 132), (24, 51, 87)),
            "green": _r("green", (158, 224, 138), (114, 190, 96), (76, 148, 59), (49, 104, 38), (30, 66, 23)),
            "amber": _r("amber", (250, 214, 122), (229, 178, 74), (190, 137, 42), (141, 96, 25), (94, 63, 15)),
        },
    ),
}


def get_palette(name: str) -> Palette:
    if name not in PALETTES:
        raise KeyError(f"paleta desconhecida: {name!r} (disponíveis: {sorted(PALETTES)})")
    return PALETTES[name]


def list_palettes() -> list[str]:
    return sorted(PALETTES)


# ----------------------------------------------------------------------
# Quantização / matching
# ----------------------------------------------------------------------
def luminance(color: tuple[int, int, int]) -> float:
    """Luminância perceptual (Rec. 601) de uma cor RGB."""
    r, g, b = color[:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


def quantize_median_cut(pixels: np.ndarray, max_colors: int) -> list[tuple[int, int, int]]:
    """Reduz ``pixels`` (N, 3) a no máximo ``max_colors`` cores representativas."""
    if pixels.size == 0:
        return []
    pts = np.asarray(pixels, dtype=np.int32).reshape(-1, 3)
    max_colors = max(1, int(max_colors))
    if max_colors >= len(np.unique(pts, axis=0)):
        uniq = np.unique(pts, axis=0)
        return [(int(r[0]), int(r[1]), int(r[2])) for r in uniq]

    buckets: list[np.ndarray] = [pts]
    while len(buckets) < max_colors:
        # escolhe o bucket com maior extensão de cor e volume
        scored = []
        for i, b in enumerate(buckets):
            if len(b) < 2:
                continue
            extent = (b.max(axis=0) - b.min(axis=0)).max()
            scored.append((int(extent), len(b), i))
        if not scored:
            break
        scored.sort(reverse=True)
        extent, _, idx = scored[0]
        if extent <= 1:
            break
        target = buckets.pop(idx)
        channel = int(np.argmax(target.max(axis=0) - target.min(axis=0)))
        order = target[np.argsort(target[:, channel], kind="stable")]
        half = len(order) // 2
        buckets.append(order[:half])
        buckets.append(order[half:])

    colors: list[tuple[int, int, int]] = []
    for b in buckets:
        if len(b) == 0:
            continue
        mean = b.mean(axis=0)
        colors.append((int(round(mean[0])), int(round(mean[1])), int(round(mean[2]))))
    # remove duplicatas preservando ordem
    seen: set[tuple[int, int, int]] = set()
    out: list[tuple[int, int, int]] = []
    for c in colors:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:max_colors]


def nearest_color(color: tuple[int, int, int], candidates: Sequence[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Cor de ``candidates`` mais próxima no espaço RGB (distância euclidiana)."""
    if not candidates:
        return tuple(int(c) for c in color)  # type: ignore[return-value]
    arr = np.asarray(candidates, dtype=np.int32)
    target = np.asarray(color[:3], dtype=np.int32)
    dist = ((arr - target) ** 2).sum(axis=1)
    return tuple(int(v) for v in arr[int(np.argmin(dist))])  # type: ignore[return-value]


def snap_canvas_to_palette(canvas: PixelCanvas, colors: Sequence[tuple[int, int, int]]) -> PixelCanvas:
    """Reescreve todos os pixels visíveis de ``canvas`` para a cor mais próxima.

    A busca é vetorizada: distância de cada pixel único contra a paleta.
    """
    if not colors:
        return canvas.copy()
    out = canvas.copy()
    data = out.data
    alpha = data[..., 3]
    visible = alpha > 0
    if not visible.any():
        return out
    rgb = data[..., :3][visible].astype(np.int32)
    uniq, inverse = np.unique(rgb, axis=0, return_inverse=True)
    palette = np.asarray(colors, dtype=np.int32)
    # (n_unique, n_palette)
    diff = uniq[:, None, :] - palette[None, :, :]
    dist = (diff**2).sum(axis=2)
    best = palette[np.argmin(dist, axis=1)]
    mapped = best[inverse.reshape(-1)]
    data[..., :3][visible] = mapped.astype(np.uint8)
    return out


def outline_color_for(colors: Sequence[tuple[int, int, int]], *, strength: float = 0.42) -> tuple[int, int, int]:
    """Deriva uma cor de contorno coesa a partir das cores do sprite.

    Usa a cor dominante escurecida e levemente dessaturada, o que mantém o
    contorno "dentro" da paleta em vez de preto puro chapado.
    """
    if not colors:
        return (16, 16, 22)
    arr = np.asarray(colors, dtype=np.float32)
    # dominante ponderada pela luminosidade inversa (tons médios/escuros)
    lum = arr.mean(axis=1)
    weights = 1.0 / (1.0 + lum / 60.0)
    mixed = (arr * weights[:, None]).sum(axis=0) / weights.sum()
    h, s, v = colorsys.rgb_to_hsv(mixed[0] / 255, mixed[1] / 255, mixed[2] / 255)
    return _from_hsv((h, min(1.0, s * 1.05), max(0.08, v * strength)))


def build_palette_from_canvas(canvas: PixelCanvas, max_colors: int = 16) -> Palette:
    """Extrai uma ``Palette`` a partir de um canvas arbitrário.

    Agrupa as cores quantizadas em rampas por matiz, o que permite reusar o
    resultado no sombreamento procedural.
    """
    rgb = canvas.data[..., :3][canvas.data[..., 3] > 0]
    colors = quantize_median_cut(rgb, max_colors)
    if not colors:
        return Palette(name="extracted", ramps={"base": Ramp("base", ((0, 0, 0),))})

    grouped: dict[int, list[tuple[int, int, int]]] = {}
    for c in colors:
        h, s, v = _to_hsv(c)
        key = int(round(h * 12)) % 12 if s > 0.15 else 12  # 12 = neutros
        grouped.setdefault(key, []).append(c)

    ramps: dict[str, Ramp] = {}
    names = [
        "red", "orange", "yellow", "lime", "green", "teal",
        "cyan", "blue", "indigo", "purple", "magenta", "pink", "neutral",
    ]
    for key, group in sorted(grouped.items()):
        # do mais claro ao mais escuro, para formar uma rampa utilizável
        group.sort(key=lambda c: -luminance(c))
        ramps[names[key]] = Ramp(name=names[key], colors=tuple(group))
    return Palette(name="extracted", ramps=ramps)
