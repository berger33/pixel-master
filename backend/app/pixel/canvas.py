"""Superfície de desenho em pixels com composição RGBA.

``PixelCanvas`` é um wrapper fino sobre um array ``numpy`` uint8 de forma
``(altura, largura, 4)``. Todas as primitivas trabalham na grade inteira de
pixels — nunca em coordenadas fracionárias — porque arredondamento sub-pixel é
a principal causa de pixel art "borrada".

Convenções
----------
* origem ``(0, 0)`` no canto superior esquerdo;
* cores são tuplas ``(r, g, b)`` ou ``(r, g, b, a)`` com valores 0..255;
* desenho fora dos limites é silenciosamente ignorado (clip), o que simplifica
  muito os geradores que trabalham com formas parciais.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from PIL import Image

Color = Sequence[int]

__all__ = ["PixelCanvas", "Color", "to_rgba"]


def to_rgba(color: Color) -> tuple[int, int, int, int]:
    """Versão pública de :func:`_rgba`."""
    return _rgba(color)


def _rgba(color: Color) -> tuple[int, int, int, int]:
    """Normaliza ``color`` para uma tupla RGBA de 4 inteiros."""
    values = tuple(int(v) for v in color)
    if len(values) == 3:
        return (values[0], values[1], values[2], 255)
    if len(values) == 4:
        return values  # type: ignore[return-value]
    raise ValueError(f"cor precisa ter 3 ou 4 canais, recebeu {len(values)}: {color!r}")


class PixelCanvas:
    """Grade RGBA com primitivas de desenho e composição alfa."""

    __slots__ = ("width", "height", "data")

    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"dimensões precisam ser positivas: {width}x{height}")
        self.width = int(width)
        self.height = int(height)
        self.data = np.zeros((self.height, self.width, 4), dtype=np.uint8)

    # ------------------------------------------------------------------
    # Construtores alternativos
    # ------------------------------------------------------------------
    @classmethod
    def from_pil(cls, image: Image.Image) -> PixelCanvas:
        rgba = image.convert("RGBA")
        canvas = cls(rgba.width, rgba.height)
        canvas.data = np.asarray(rgba, dtype=np.uint8).copy()
        return canvas

    @classmethod
    def from_array(cls, array: np.ndarray) -> PixelCanvas:
        arr = np.asarray(array, dtype=np.uint8)
        if arr.ndim != 3 or arr.shape[2] != 4:
            raise ValueError("array precisa ter forma (H, W, 4)")
        canvas = cls(arr.shape[1], arr.shape[0])
        canvas.data = arr.copy()
        return canvas

    def copy(self) -> PixelCanvas:
        clone = PixelCanvas(self.width, self.height)
        clone.data = self.data.copy()
        return clone

    # ------------------------------------------------------------------
    # Acesso básico
    # ------------------------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> tuple[int, int, int, int]:
        if not self.in_bounds(x, y):
            return (0, 0, 0, 0)
        return tuple(int(v) for v in self.data[y, x])  # type: ignore[return-value]

    def set(self, x: int, y: int, color: Color) -> None:
        """Escreve um pixel substituindo o conteúdo anterior (sem blend)."""
        x, y = int(x), int(y)
        if not self.in_bounds(x, y):
            return
        r, g, b, a = _rgba(color)
        self.data[y, x] = (r, g, b, a)

    def clear(self) -> None:
        self.data[...] = 0

    # ------------------------------------------------------------------
    # Composição alfa (source-over)
    # ------------------------------------------------------------------
    def blend_pixel(self, x: int, y: int, color: Color) -> None:
        """Compõe ``color`` sobre o pixel existente usando source-over."""
        x, y = int(x), int(y)
        if not self.in_bounds(x, y):
            return
        sr, sg, sb, sa = _rgba(color)
        if sa == 255:
            self.data[y, x] = (sr, sg, sb, 255)
            return
        if sa == 0:
            return
        dr, dg, db, da = (int(v) for v in self.data[y, x])
        a = sa / 255.0
        inv = 1.0 - a
        out_a = sa + da * inv
        if out_a <= 0:
            return
        out_r = (sr * sa + dr * da * inv) / out_a
        out_g = (sg * sa + dg * da * inv) / out_a
        out_b = (sb * sa + db * da * inv) / out_a
        self.data[y, x] = (
            int(round(out_r)),
            int(round(out_g)),
            int(round(out_b)),
            int(round(out_a)),
        )

    def blend_region(self, x0: int, y0: int, patch: np.ndarray) -> None:
        """Compõe um bloco RGBA ``(h, w, 4)`` vetorialmente (source-over)."""
        ph, pw = patch.shape[0], patch.shape[1]
        # interseção com a tela
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(self.width, x0 + pw), min(self.height, y0 + ph)
        if dx0 >= dx1 or dy0 >= dy1:
            return
        sx0, sy0 = dx0 - x0, dy0 - y0
        sx1, sy1 = sx0 + (dx1 - dx0), sy0 + (dy1 - dy0)

        src = patch[sy0:sy1, sx0:sx1].astype(np.float32)
        dst = self.data[dy0:dy1, dx0:dx1].astype(np.float32)

        sa = src[..., 3:4] / 255.0
        da = dst[..., 3:4] / 255.0
        out_a = sa + da * (1.0 - sa)
        safe = np.where(out_a > 0, out_a, 1.0)
        out_rgb = (src[..., :3] * sa + dst[..., :3] * da * (1.0 - sa)) / safe

        result = np.empty_like(dst)
        result[..., :3] = np.clip(out_rgb, 0, 255)
        result[..., 3:4] = np.clip(out_a * 255.0, 0, 255)
        # onde a origem é totalmente transparente, preserva o destino
        zero_alpha = (src[..., 3] == 0)
        result[zero_alpha] = dst[zero_alpha]
        self.data[dy0:dy1, dx0:dx1] = np.round(result).astype(np.uint8)

    # ------------------------------------------------------------------
    # Primitivas
    # ------------------------------------------------------------------
    def rect(self, x: int, y: int, w: int, h: int, color: Color, *, fill: bool = True) -> None:
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        if fill:
            patch = np.empty((h, w, 4), dtype=np.uint8)
            patch[..., :] = np.array(_rgba(color), dtype=np.uint8)
            self.blend_region(x, y, patch)
        else:
            self.hline(x, y, w, color)
            self.hline(x, y + h - 1, w, color)
            self.vline(x, y, h, color)
            self.vline(x + w - 1, y, h, color)

    def hline(self, x: int, y: int, length: int, color: Color) -> None:
        for i in range(int(length)):
            self.blend_pixel(x + i, y, color)

    def vline(self, x: int, y: int, length: int, color: Color) -> None:
        for i in range(int(length)):
            self.blend_pixel(x, y + i, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        """Bresenham inteiro — traços nítidos sem anti-aliasing."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.blend_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        color: Color,
        *,
        fill: bool = True,
    ) -> None:
        """Elipse por teste de inclusão normalizado (bom para cabeças/torsos)."""
        if rx <= 0 or ry <= 0:
            return
        rx, ry = float(rx), float(ry)
        cx, cy = float(cx), float(cy)
        x_min = max(0, int(np.floor(cx - rx)))
        x_max = min(self.width - 1, int(np.ceil(cx + rx)))
        y_min = max(0, int(np.floor(cy - ry)))
        y_max = min(self.height - 1, int(np.ceil(cy + ry)))
        if x_min > x_max or y_min > y_max:
            return

        xs = np.arange(x_min, x_max + 1, dtype=np.float32)
        ys = np.arange(y_min, y_max + 1, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)
        norm = ((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2

        if fill:
            mask = norm <= 1.0
        else:
            mask = (norm <= 1.0) & (norm >= 0.55)

        if not mask.any():
            return
        patch = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        patch[mask] = np.array(_rgba(color), dtype=np.uint8)
        self.blend_region(x_min, y_min, patch)

    def circle(self, cx: float, cy: float, r: float, color: Color, *, fill: bool = True) -> None:
        self.ellipse(cx, cy, r, r, color, fill=fill)

    def polygon(self, points: Iterable[Sequence[float]], color: Color) -> None:
        """Preenchimento por scanline de um polígono simples."""
        pts = [(float(p[0]), float(p[1])) for p in points]
        if len(pts) < 3:
            return
        y_min = max(0, int(np.floor(min(p[1] for p in pts))))
        y_max = min(self.height - 1, int(np.ceil(max(p[1] for p in pts))))
        n = len(pts)
        for y in range(y_min, y_max + 1):
            yc = y + 0.5
            crossings: list[float] = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    t = (yc - y1) / (y2 - y1)
                    crossings.append(x1 + t * (x2 - x1))
            if not crossings:
                continue
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                xa = int(np.ceil(crossings[i] - 0.5))
                xb = int(np.floor(crossings[i + 1] - 0.5))
                self.hline(xa, y, max(0, xb - xa + 1), color)

    # ------------------------------------------------------------------
    # Composição entre telas
    # ------------------------------------------------------------------
    def blit(
        self,
        other: PixelCanvas,
        x: int,
        y: int,
        *,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        src = other.data
        if flip_x:
            src = src[:, ::-1]
        if flip_y:
            src = src[::-1, :]
        self.blend_region(int(x), int(y), np.ascontiguousarray(src))

    # ------------------------------------------------------------------
    # Apagamento (necessário para recortes de máscara, ex.: abertura de capuz)
    # ------------------------------------------------------------------
    def erase_rect(self, x: int, y: int, w: int, h: int) -> None:
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.width, int(x) + int(w)), min(self.height, int(y) + int(h))
        if x0 < x1 and y0 < y1:
            self.data[y0:y1, x0:x1] = 0

    def erase_ellipse(self, cx: float, cy: float, rx: float, ry: float) -> None:
        if rx <= 0 or ry <= 0:
            return
        x_min = max(0, int(np.floor(cx - rx)))
        x_max = min(self.width - 1, int(np.ceil(cx + rx)))
        y_min = max(0, int(np.floor(cy - ry)))
        y_max = min(self.height - 1, int(np.ceil(cy + ry)))
        if x_min > x_max or y_min > y_max:
            return
        xs = np.arange(x_min, x_max + 1, dtype=np.float32)
        ys = np.arange(y_min, y_max + 1, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)
        mask = ((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2 <= 1.0
        if mask.any():
            self.data[y_min : y_max + 1, x_min : x_max + 1][mask] = 0

    def alpha_mask(self) -> np.ndarray:
        """Máscara booleana dos pixels visíveis (alfa > 0)."""
        return self.data[..., 3] > 0

    def bbox(self, *, threshold: int = 0) -> tuple[int, int, int, int] | None:
        """Caixa mínima ``(x0, y0, x1, y1)`` do conteúdo visível."""
        mask = self.data[..., 3] > threshold
        if not mask.any():
            return None
        ys, xs = np.nonzero(mask)
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

    def crop(self, x0: int, y0: int, x1: int, y1: int) -> PixelCanvas:
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(self.width, int(x1)), min(self.height, int(y1))
        if x0 >= x1 or y0 >= y1:
            return PixelCanvas(1, 1)
        out = PixelCanvas(x1 - x0, y1 - y0)
        out.data = self.data[y0:y1, x0:x1].copy()
        return out

    def sub(self, x0: int, y0: int, w: int, h: int) -> PixelCanvas:
        """Recorta uma região de tamanho fixo com padding transparente."""
        out = PixelCanvas(int(w), int(h))
        out.blit(self.crop(x0, y0, x0 + int(w), y0 + int(h)), 0, 0)
        return out

    # ------------------------------------------------------------------
    # Transformações geométricas (nearest — preserva a grade)
    # ------------------------------------------------------------------
    def flipped_x(self) -> PixelCanvas:
        out = PixelCanvas(self.width, self.height)
        out.data = np.ascontiguousarray(self.data[:, ::-1])
        return out

    def flipped_y(self) -> PixelCanvas:
        out = PixelCanvas(self.width, self.height)
        out.data = np.ascontiguousarray(self.data[::-1, :])
        return out

    def translated(self, dx: int, dy: int) -> PixelCanvas:
        """Translação inteira sem reamostragem — mantém nitidez absoluta."""
        out = PixelCanvas(self.width, self.height)
        out.blit(self, int(dx), int(dy))
        return out

    def rotated(
        self,
        degrees: float,
        *,
        pivot: Sequence[float] | None = None,
        expand: bool = False,
    ) -> PixelCanvas:
        """Rotação por reamostragem nearest em torno de ``pivot``.

        A saída permanece alinhada à grade de pixels, o que evita serrilhado
        suave incompatível com pixel art.
        """
        angle = float(np.deg2rad(degrees))
        cos_a, sin_a = float(np.cos(angle)), float(np.sin(angle))
        px, py = (
            (float(pivot[0]), float(pivot[1]))
            if pivot is not None
            else ((self.width - 1) / 2.0, (self.height - 1) / 2.0)
        )

        if expand:
            corners = [
                (0, 0),
                (self.width, 0),
                (0, self.height),
                (self.width, self.height),
            ]
            rot = [
                (
                    px + (cx - px) * cos_a - (cy - py) * sin_a,
                    py + (cx - px) * sin_a + (cy - py) * cos_a,
                )
                for cx, cy in corners
            ]
            min_x = min(p[0] for p in rot)
            min_y = min(p[1] for p in rot)
            out_w = int(np.ceil(max(p[0] for p in rot) - min_x))
            out_h = int(np.ceil(max(p[1] for p in rot) - min_y))
            out_px, out_py = px - min_x, py - min_y
        else:
            out_w, out_h = self.width, self.height
            out_px, out_py = px, py

        out = PixelCanvas(max(1, out_w), max(1, out_h))
        ys, xs = np.mgrid[0 : out.height, 0 : out.width]
        # coordenadas de destino -> origem (rotação inversa)
        ox = out_px + (xs - out_px) * cos_a + (ys - out_py) * sin_a
        oy = out_py - (xs - out_px) * sin_a + (ys - out_py) * cos_a
        sxs = np.round(ox).astype(np.int32)
        sys = np.round(oy).astype(np.int32)
        valid = (sxs >= 0) & (sxs < self.width) & (sys >= 0) & (sys < self.height)
        sampled = self.data[np.clip(sys, 0, self.height - 1), np.clip(sxs, 0, self.width - 1)]
        out.data = np.where(valid[..., None], sampled, 0).astype(np.uint8)
        return out

    def scaled(self, new_w: int, new_h: int) -> PixelCanvas:
        """Escala nearest-neighbour (blocos de pixels, sem interpolação)."""
        new_w, new_h = max(1, int(new_w)), max(1, int(new_h))
        out = PixelCanvas(new_w, new_h)
        ys = (np.arange(new_h) * self.height / new_h).astype(np.int32)
        xs = (np.arange(new_w) * self.width / new_w).astype(np.int32)
        out.data = self.data[np.clip(ys, 0, self.height - 1)][:, np.clip(xs, 0, self.width - 1)]
        return out

    # ------------------------------------------------------------------
    # Pós-processamento de pixel art
    # ------------------------------------------------------------------
    def outline(self, color: Color, *, diagonals: bool = True, inside: bool = False) -> PixelCanvas:
        """Retorna uma cópia com contorno de 1px ao redor da silhueta.

        ``inside=True`` desenha o contorno *por dentro* da silhueta (útil para
        separar partes sobrepostas sem alterar a caixa do sprite).
        """
        mask = self.data[..., 3] > 0
        padded = np.pad(mask, 1, mode="constant", constant_values=False)
        neigh = np.zeros_like(padded)
        offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if diagonals:
            offsets += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dy, dx in offsets:
            neigh |= np.roll(np.roll(padded, dy, axis=0), dx, axis=1)
        neigh = neigh[1:-1, 1:-1]

        out = self.copy()
        rgb = _rgba(color)
        if inside:
            target = mask & neigh
            if target.any():
                out.data[target] = np.array(rgb, dtype=np.uint8)
        else:
            target = (~mask) & neigh
            if target.any():
                layer = np.zeros_like(out.data)
                layer[target] = np.array(rgb, dtype=np.uint8)
                out.blend_region(0, 0, layer)
        return out

    def multiply_alpha(self, factor: float) -> PixelCanvas:
        out = self.copy()
        out.data[..., 3] = np.clip(out.data[..., 3].astype(np.float32) * float(factor), 0, 255).astype(
            np.uint8
        )
        return out

    def shade(self, factor: float) -> PixelCanvas:
        """Clareia (``> 1``) ou escurece (``< 1``) os canais RGB preservando alfa."""
        out = self.copy()
        alpha = out.data[..., 3].copy()
        rgb = out.data[..., :3].astype(np.float32) * float(factor)
        out.data[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out.data[..., 3] = alpha
        return out

    def desaturate(self, amount: float) -> PixelCanvas:
        out = self.copy()
        alpha = out.data[..., 3].copy()
        rgb = out.data[..., :3].astype(np.float32)
        gray = rgb.mean(axis=2, keepdims=True)
        blended = rgb * (1.0 - float(amount)) + gray * float(amount)
        out.data[..., :3] = np.clip(blended, 0, 255).astype(np.uint8)
        out.data[..., 3] = alpha
        return out

    def tint(self, color: Color, amount: float) -> PixelCanvas:
        out = self.copy()
        alpha = out.data[..., 3].copy()
        rgb = out.data[..., :3].astype(np.float32)
        target = np.array(_rgba(color)[:3], dtype=np.float32)
        out.data[..., :3] = np.clip(rgb * (1 - amount) + target * amount, 0, 255).astype(np.uint8)
        out.data[..., 3] = alpha
        return out

    # ------------------------------------------------------------------
    # Conversão
    # ------------------------------------------------------------------
    def to_pil(self) -> Image.Image:
        return Image.fromarray(self.data, mode="RGBA")

    def to_bytes(self, fmt: str = "PNG") -> bytes:
        import io

        buffer = io.BytesIO()
        self.to_pil().save(buffer, format=fmt)
        return buffer.getvalue()

    def unique_colors(self, *, ignore_transparent: bool = True) -> list[tuple[int, int, int, int]]:
        flat = self.data.reshape(-1, 4)
        if ignore_transparent:
            flat = flat[flat[:, 3] > 0]
        if flat.size == 0:
            return []
        uniq = np.unique(flat, axis=0)
        return [tuple(int(c) for c in row) for row in uniq]

    def color_count(self, *, ignore_transparent: bool = True) -> int:
        return len(self.unique_colors(ignore_transparent=ignore_transparent))

    def is_empty(self) -> bool:
        return not bool((self.data[..., 3] > 0).any())

    def __repr__(self) -> str:  # pragma: no cover - depuração
        return f"<PixelCanvas {self.width}x{self.height} colors={self.color_count()}>"
