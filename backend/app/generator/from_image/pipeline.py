"""Pipeline *foto de IA -> personagem jogável*.

Fluxo completo:

1. **carregar** a imagem enviada (render de IA em alta resolução);
2. **remover o fundo** (alfa existente, cor sólida informada ou flood-fill
   automático a partir das bordas);
3. **limpar** a máscara (remove specks e fecha pequenos buracos);
4. **pixelizar** por amostragem de cobertura: cada pixel de saída herda a cor
   *dominante* dos pixels de primeiro plano da sua célula — o resultado é
   pixel art nítido, não um downscale borrado;
5. **quantizar** a paleta (median cut) e aplicar contorno coeso;
6. **detectar a vista** de origem (frente / lado / costas) por simetria e
   proporção;
7. **sintetizar as 4 direções** (a vista de costas remove o rosto; as vistas
   laterais aplicam compressão horizontal 3/4);
8. **segmentar em camadas** (cabeça, tronco, braços, pernas) com pivôs e tags,
   produzindo um :class:`Rig` que o animador compartilhado consegue mover —
   exatamente como um personagem procedural.
"""

from __future__ import annotations

import io
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from app.domain.models import ImageImportParams
from app.generator.rig import Layer, PartKind, Rig
from app.pixel.canvas import PixelCanvas
from app.pixel.palette import outline_color_for, quantize_median_cut, snap_canvas_to_palette

__all__ = [
    "ImportMeta",
    "ImportResult",
    "load_image",
    "remove_background",
    "clean_mask",
    "pixelize",
    "detect_view",
    "segment_rig",
    "synthesize_directions",
    "import_image",
]


@dataclass
class ImportMeta:
    detected_view: str
    source_size: tuple[int, int]
    cropped_size: tuple[int, int]
    target_size: tuple[int, int]
    palette_size: int
    palette: list[tuple[int, int, int]]
    outline_color: tuple[int, int, int]
    background_removed: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportResult:
    rigs: dict[str, Rig]
    sprites: dict[str, PixelCanvas]
    meta: ImportMeta


# ----------------------------------------------------------------------
# 1-2. carga e remoção de fundo
# ----------------------------------------------------------------------
def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img.convert("RGBA")


def _has_alpha(img: Image.Image) -> bool:
    alpha = np.asarray(img)[:, :, 3]
    return bool(alpha.min() < 250)


def remove_background(img: Image.Image, params: ImageImportParams) -> tuple[Image.Image, bool]:
    """Retorna ``(imagem com alfa de recorte, fundo_removido)``."""
    arr = np.asarray(img).astype(np.int16)
    h, w = arr.shape[:2]

    if params.background == "keep":
        return img, False
    if params.background == "alpha" or (params.background == "auto" and _has_alpha(img)):
        return img, _has_alpha(img)

    # Cor de referência do fundo: informada ou mediana das bordas.
    if params.background == "solid" and params.background_color is not None:
        target = np.array(params.background_color, dtype=np.int16)
    else:
        border = np.concatenate(
            [arr[0, :, :3], arr[-1, :, :3], arr[:, 0, :3], arr[:, -1, :3]]
        )
        target = np.median(border, axis=0).astype(np.int16)

    # Todo pixel próximo da cor de fundo vira transparente — inclusive regiões
    # *encerradas* (o vão dentro de um arco, o espaço entre as pernas), que um
    # flood-fill a partir das bordas não alcançaria.
    dist = np.abs(arr[:, :, :3] - target).sum(axis=2)
    bg = dist <= params.background_tolerance * 3

    out = np.asarray(img).copy()
    out[bg, 3] = 0
    return Image.fromarray(out, "RGBA"), True


# ----------------------------------------------------------------------
# 3. limpeza de máscara
# ----------------------------------------------------------------------
def _components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Rotula componentes 4-conexos; retorna (labels, count)."""
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    current = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and labels[y, x] == 0:
                current += 1
                dq = deque([(y, x)])
                labels[y, x] = current
                while dq:
                    cy, cx = dq.popleft()
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                            labels[ny, nx] = current
                            dq.append((ny, nx))
    return labels, current


def clean_mask(alpha: np.ndarray, despeckle: int) -> np.ndarray:
    mask = alpha > 8
    if despeckle <= 0:
        return mask
    labels, count = _components(mask)
    if count <= 1:
        return mask
    sizes = np.bincount(labels.ravel())
    keep_min = max(despeckle, int(mask.sum() * 0.02))
    out = np.zeros_like(mask)
    for lab in range(1, count + 1):
        if sizes[lab] >= keep_min:
            out |= labels == lab
    # fecha buracos pequenos (olhos claros recortados por engano, etc.)
    inv_labels, inv_count = _components(~out)
    inv_sizes = np.bincount(inv_labels.ravel())
    border_label = inv_labels[0, 0]
    for lab in range(1, inv_count + 1):
        if lab != border_label and inv_sizes[lab] <= max(4, despeckle * 2):
            out |= inv_labels == lab
    return out


# ----------------------------------------------------------------------
# 4-5. pixelização + paleta
# ----------------------------------------------------------------------
def pixelize(img: Image.Image, params: ImageImportParams, frame: tuple[int, int]) -> PixelCanvas:
    arr = np.asarray(img).astype(np.float32)
    alpha = arr[:, :, 3] / 255.0
    rgb = arr[:, :, :3]

    ys, xs = np.nonzero(alpha > 0.02)
    if ys.size == 0:
        return PixelCanvas(frame[0], frame[1])
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cropped_rgb = rgb[y0:y1, x0:x1]
    cropped_a = alpha[y0:y1, x0:x1]

    ch, cw = cropped_a.shape
    max_h = int(params.target_size)
    max_w = int(params.target_size)
    scale = min(max_w / cw, max_h / ch)
    tw = max(4, int(round(cw * scale)))
    th = max(4, int(round(ch * scale)))

    # cobertura e cor ponderada por alfa via redimensionamento BOX
    cov_img = Image.fromarray((cropped_a * 255).astype(np.uint8), "L").resize((tw, th), Image.BOX)
    cov = np.asarray(cov_img).astype(np.float32) / 255.0
    prem = cropped_rgb * cropped_a[..., None]
    prem_img = Image.fromarray(np.clip(prem, 0, 255).astype(np.uint8)).resize((tw, th), Image.BOX)
    prem_arr = np.asarray(prem_img).astype(np.float32)

    safe_cov = np.where(cov > 1e-4, cov, 1.0)
    color = prem_arr / safe_cov[..., None]

    threshold = 0.45 if params.pixel_mode == "dominant" else (0.30 if params.pixel_mode == "average" else 0.5)
    keep = cov >= threshold

    canvas = PixelCanvas(frame[0], frame[1])
    # centraliza horizontalmente, alinha a base ao chão
    off_x = (frame[0] - tw) // 2
    off_y = frame[1] - 3 - th
    patch = np.zeros((th, tw, 4), dtype=np.uint8)
    patch[..., :3] = np.clip(color, 0, 255).astype(np.uint8)
    patch[..., 3] = np.where(keep, 255, 0).astype(np.uint8)
    canvas.blend_region(off_x, max(0, off_y), patch)

    if params.cleanup:
        mask = clean_mask(canvas.data[..., 3], params.despeckle)
        canvas.data[..., 3] = np.where(mask, canvas.data[..., 3], 0)

    # quantização de paleta
    visible = canvas.data[..., 3] > 0
    if visible.any():
        colors = quantize_median_cut(canvas.data[..., :3][visible], params.palette_size)
        canvas = snap_canvas_to_palette(canvas, colors)
    else:
        colors = []

    if params.outline and visible.any():
        oc = outline_color_for(colors, strength=params.outline_strength)
        canvas = canvas.outline(oc, diagonals=True)

    return canvas


# ----------------------------------------------------------------------
# 6. detecção de vista
# ----------------------------------------------------------------------
def detect_view(canvas: PixelCanvas) -> str:
    """Classifica a vista de origem como ``front`` / ``side`` / ``back``.

    A proporção largura/altura de um personagem em pé é parecida nas duas
    vistas, então o discriminante principal é a **simetria da região da
    cabeça** (rostos e capuzes frontais são simétricos; perfis não), reforçada
    pela simetria global do corpo.
    """
    mask = canvas.alpha_mask()
    bbox = canvas.bbox()
    if bbox is None:
        return "front"
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    aspect = w / max(1, h)
    sub = mask[y0:y1, x0:x1]
    mirrored = sub[:, ::-1]
    sym = float((sub & mirrored).sum()) / max(1, float((sub | mirrored).sum()))

    head_h = max(3, int(h * 0.35))
    head = sub[:head_h]
    head_m = head[:, ::-1]
    head_sym = float((head & head_m).sum()) / max(1, float((head | head_m).sum()))

    if aspect < 0.30 or head_sym < 0.52:
        return "side"
    if head_sym >= 0.62 or sym >= 0.80:
        pass  # candidato a frente/costas
    else:
        return "side"

    # frente vs costas: um rosto tem pixels *bem mais escuros* que o tom
    # mediano da cabeça (olhos, boca) na faixa central; costas não têm.
    # a faixa dos olhos fica no topo da silhueta (a cabeça de um personagem
    # em pé ocupa roughly os 30% superiores do bounding box)
    y_a = y0 + int(h * 0.05)
    y_b = y0 + int(h * 0.30)
    band = canvas.data[y_a:y_b, x0 + 1 : max(x0 + 2, x1 - 1)]
    vis = band[..., 3] > 0
    if vis.sum() == 0:
        return "front"
    rgb = band[..., :3][vis].astype(np.float32)
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    # olhos/boca são *muito* mais escuros que o ponto mais claro da cabeça;
    # medir contra o máximo (e não contra a mediana) torna o teste estável
    # mesmo quando a cabeça inclui capuz/cabelo escuros.
    peak = float(lum.max())
    dark = int((lum < peak * 0.35).sum())
    return "front" if dark >= 2 else "back"


# ----------------------------------------------------------------------
# 7. síntese de direções
# ----------------------------------------------------------------------
def _fill_face(canvas: PixelCanvas, head_box: tuple[int, int, int, int]) -> PixelCanvas:
    """Preenche o rosto com a cor mediana da cabeça (vista de costas)."""
    x0, y0, x1, y1 = head_box
    region = canvas.data[y0:y1, x0:x1]
    vis = region[..., 3] > 0
    if not vis.any():
        return canvas
    out = canvas.copy()
    med = np.median(region[..., :3][vis], axis=0).astype(np.uint8)
    r = out.data[y0:y1, x0:x1]
    inner = vis.copy()
    # preserva 1px de borda para manter o contorno
    inner[:1, :] = False
    inner[-1:, :] = False
    inner[:, :1] = False
    inner[:, -1:] = False
    r[inner, :3] = med
    out.data[y0:y1, x0:x1] = r
    return out


def synthesize_directions(front: PixelCanvas, params: ImageImportParams) -> dict[str, PixelCanvas]:
    bbox = front.bbox()
    out: dict[str, PixelCanvas] = {}
    if bbox is None:
        return out
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    head_box = (x0, y0, x1, min(y1, y0 + int(h * 0.34)))

    view = detect_view(front)
    if view == "front":
        out["down"] = front
        out["up"] = _fill_face(front, head_box)
    elif view == "back":
        out["up"] = front
        out["down"] = front  # sem rosto para inventar; usa a mesma silhueta
    else:
        out["left"] = front
        out["right"] = front.flipped_x()
        out["down"] = front
        out["up"] = _fill_face(front, head_box)

    if params.synthesize_directions:
        squeeze = float(params.side_squeeze)
        if "left" not in out:
            squeezed = _squeeze(front, squeeze)
            out["left"] = squeezed
            out["right"] = squeezed.flipped_x()
        if "down" not in out:
            out["down"] = _unsqueeze(out.get("left", front), 1.0 / squeeze)
        if "up" not in out:
            bb = out["down"].bbox() or (0, 0, 1, 1)
            out["up"] = _fill_face(out["down"], (bb[0], bb[1], bb[2], min(bb[3], bb[1] + int((bb[3] - bb[1]) * 0.34))))
    return out


def _squeeze(canvas: PixelCanvas, factor: float) -> PixelCanvas:
    bbox = canvas.bbox()
    if bbox is None:
        return canvas
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    new_w = max(4, int(round(w * factor)))
    sub = canvas.crop(x0, y0, x1, y1).scaled(new_w, h)
    out = PixelCanvas(canvas.width, canvas.height)
    off_x = (canvas.width - new_w) // 2
    out.blit(sub, off_x, y0)
    return out


def _unsqueeze(canvas: PixelCanvas, factor: float) -> PixelCanvas:
    return _squeeze(canvas, factor)


# ----------------------------------------------------------------------
# 8. segmentação em rig
# ----------------------------------------------------------------------
def segment_rig(sprite: PixelCanvas, direction: str, *, species: str = "imported") -> Rig:
    mask = sprite.alpha_mask()
    bbox = sprite.bbox()
    rig = Rig(width=sprite.width, height=sprite.height, direction=direction, species=species, archetype="biped")
    if bbox is None:
        return rig
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    cx = (x0 + x1) / 2.0

    widths = mask[y0:y1, x0:x1].sum(axis=1).astype(np.float32)
    # pescoço = mínimo local após o pico da cabeça (primeiros 45%)
    search_end = max(3, int(h * 0.45))
    head_peak = int(np.argmax(widths[:search_end]))
    neck_rel = head_peak + int(np.argmin(widths[head_peak:search_end])) if search_end > head_peak else head_peak
    neck_y = y0 + max(2, neck_rel)
    hip_y = y0 + int(h * 0.60)

    def region(ya: int, yb: int, xa: int, xb: int) -> PixelCanvas:
        layer = PixelCanvas(sprite.width, sprite.height)
        layer.data[ya:yb, xa:xb] = sprite.data[ya:yb, xa:xb]
        return layer

    # cabeça
    head = region(y0, neck_y, x0, x1)
    # núcleo do tronco (largura na linha do quadril)
    row = mask[hip_y - 1, x0:x1]
    cols = np.nonzero(row)[0]
    core_half = max(2, int((cols.max() - cols.min()) / 2 * 0.62)) if cols.size else max(2, int((x1 - x0) * 0.3))
    core_l = int(cx - core_half)
    core_r = int(cx + core_half)

    torso = PixelCanvas(sprite.width, sprite.height)
    torso.data[neck_y:hip_y, core_l:core_r] = sprite.data[neck_y:hip_y, core_l:core_r]
    arm_l = region(neck_y, hip_y, x0, core_l)
    arm_r = region(neck_y, hip_y, core_r, x1)

    # pernas: divide no vão central da faixa inferior
    leg_band = mask[hip_y:y1, x0:x1]
    colsum = leg_band.sum(axis=0)
    mid = (x1 - x0) // 2
    search = colsum[max(0, mid - 4) : mid + 4]
    gap_rel = int(np.argmin(search)) if search.size else mid
    gap = x0 + max(0, mid - 4) + gap_rel
    leg_l = region(hip_y, y1, x0, gap)
    leg_r = region(hip_y, y1, gap, x1)

    rig.add(Layer(name="leg_back", kind=PartKind.LEG_BACK, canvas=leg_r, pivot=(gap + 1, hip_y), tags={"leg": 1, "gait": 1}))
    rig.add(Layer(name="arm_back", kind=PartKind.ARM_BACK, canvas=arm_r, pivot=(core_r - 1, neck_y + 2), tags={"arm": 1, "gait": 1}))
    rig.add(Layer(name="torso", kind=PartKind.TORSO, canvas=torso, pivot=(int(cx), hip_y), tags={"body": 1}))
    rig.add(Layer(name="leg_front", kind=PartKind.LEG_FRONT, canvas=leg_l, pivot=(gap - 1, hip_y), tags={"leg": 1, "gait": 0}))
    rig.add(Layer(name="head", kind=PartKind.HEAD, canvas=head, pivot=(int(cx), neck_y), tags={"head": 1}))
    rig.add(Layer(name="arm_front", kind=PartKind.ARM_FRONT, canvas=arm_l, pivot=(core_l + 1, neck_y + 2), tags={"arm": 1, "gait": 0}))

    rig.joints = {
        "head": (int(cx), int((y0 + neck_y) / 2)),
        "neck": (int(cx), neck_y),
        "hip": (int(cx), hip_y),
        "ground": (int(cx), y1),
        "shoulder_front": (core_l + 1, neck_y + 2),
        "shoulder_back": (core_r - 1, neck_y + 2),
    }
    rig.proportions = {
        "height": float(h),
        "body_width": float(x1 - x0),
        "stride": max(2.0, h * 0.10),
        "leg_length": float(y1 - hip_y),
    }
    rig.palette_colors = [tuple(int(c) for c in c3) for c3 in np.unique(sprite.data[..., :3][sprite.data[..., 3] > 0], axis=0)][:48]
    return rig


# ----------------------------------------------------------------------
# API de alto nível
# ----------------------------------------------------------------------
def import_image(data: bytes, params: ImageImportParams, *, frame: tuple[int, int] = (64, 64)) -> ImportResult:
    warnings: list[str] = []
    img = load_image(data)
    src_size = img.size
    img, removed = remove_background(img, params)

    if params.auto_crop:
        alpha = np.asarray(img)[:, :, 3]
        ys, xs = np.nonzero(alpha > 8)
        if ys.size:
            pad = int(params.padding)
            y0 = max(0, ys.min() - pad)
            y1 = min(img.height, ys.max() + 1 + pad)
            x0 = max(0, xs.min() - pad)
            x1 = min(img.width, xs.max() + 1 + pad)
            img = img.crop((x0, y0, x1, y1))
        else:
            warnings.append("nenhum pixel de primeiro plano encontrado após remoção de fundo")

    sprite = pixelize(img, params, frame)
    if sprite.is_empty():
        warnings.append("sprite vazio: verifique o fundo/tolerância")

    visible = sprite.data[..., 3] > 0
    palette = (
        [tuple(int(c) for c in row) for row in np.unique(sprite.data[..., :3][visible], axis=0)]
        if visible.any()
        else []
    )
    outline_c = outline_color_for(palette, strength=params.outline_strength) if palette else (24, 22, 32)

    sprites = synthesize_directions(sprite, params)
    rigs: dict[str, Rig] = {}
    for direction, spr in sprites.items():
        rig = segment_rig(spr, direction)
        rig.outline_color = outline_c
        rigs[direction] = rig

    meta = ImportMeta(
        detected_view=detect_view(sprite),
        source_size=src_size,
        cropped_size=img.size,
        target_size=(frame[0], frame[1]),
        palette_size=len(palette),
        palette=palette[:64],
        outline_color=outline_c,
        background_removed=removed,
        warnings=warnings,
    )
    return ImportResult(rigs=rigs, sprites=sprites, meta=meta)
