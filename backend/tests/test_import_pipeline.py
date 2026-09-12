"""Testes do pipeline foto-de-IA -> personagem jogável."""

from __future__ import annotations

import numpy as np
from PIL import Image

from app.animation.animator import AnimationParams, build_clips
from app.domain.models import ImageImportParams
from app.generator.from_image.pipeline import (
    clean_mask,
    detect_view,
    import_image,
    load_image,
    pixelize,
    remove_background,
    synthesize_directions,
)
from app.generator.rig import compose_rig
from app.pixel.canvas import PixelCanvas


def _synthetic_front_png() -> bytes:
    """Render sintético: fundo cinza sólido + silhueta frontal simétrica."""
    img = Image.new("RGBA", (120, 200), (216, 216, 216, 255))
    px = img.load()
    # cabeça
    for y in range(20, 60):
        for x in range(45, 75):
            if ((x - 60) / 15) ** 2 + ((y - 40) / 20) ** 2 <= 1:
                px[x, y] = (240, 200, 170, 255)
    # olhos grandes o bastante para sobreviver à pixelização
    for x in range(50, 56):
        for y in range(37, 44):
            px[x, y] = (30, 30, 40, 255)
    for x in range(64, 70):
        for y in range(37, 44):
            px[x, y] = (30, 30, 40, 255)
    # boca
    for x in range(55, 65):
        for y in range(50, 53):
            px[x, y] = (120, 60, 60, 255)
    # braços (alargam a silhueta, como num render real)
    for y in range(62, 120):
        for x in list(range(30, 40)) + list(range(80, 90)):
            px[x, y] = (60, 120, 70, 255)
    # tronco
    for y in range(60, 130):
        for x in range(40, 80):
            px[x, y] = (60, 120, 70, 255)
    # pernas
    for y in range(130, 190):
        for x in list(range(44, 58)) + list(range(62, 76)):
            px[x, y] = (70, 60, 50, 255)
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_load_and_background_removal(fixture_image_bytes):
    img = load_image(fixture_image_bytes)
    assert img.mode == "RGBA"
    out, removed = remove_background(img, ImageImportParams())
    assert removed is True
    alpha = np.asarray(out)[:, :, 3]
    # cantos (fundo) transparentes, centro (personagem) opaco
    assert alpha[0, 0] == 0
    assert alpha[alpha.shape[0] // 2, alpha.shape[1] // 2] > 0


def test_background_removal_clears_enclosed_holes():
    # um "aro" com fundo preso no meio deve ficar transparente no centro
    img = Image.new("RGBA", (60, 60), (200, 200, 200, 255))
    px = img.load()
    for y in range(10, 50):
        for x in range(10, 50):
            if 15 <= x <= 45 and 15 <= y <= 45 and not (20 <= x <= 40 and 20 <= y <= 40):
                px[x, y] = (40, 40, 200, 255)
    out, _ = remove_background(img, ImageImportParams(background_tolerance=30))
    alpha = np.asarray(out)[:, :, 3]
    assert alpha[30, 30] == 0  # miolo do aro virou transparente


def test_clean_mask_removes_specks():
    mask = np.zeros((40, 40), dtype=bool)
    mask[5:20, 5:20] = True
    mask[35, 35] = True  # speck
    cleaned = clean_mask(mask.astype(np.uint8) * 255, despeckle=3)
    assert cleaned[5, 5]
    assert not cleaned[35, 35]


def test_pixelize_produces_crisp_low_palette_sprite(fixture_image_bytes):
    img = load_image(fixture_image_bytes)
    img, _ = remove_background(img, ImageImportParams())
    sprite = pixelize(img, ImageImportParams(target_size=48, palette_size=12), (64, 64))
    assert not sprite.is_empty()
    assert sprite.color_count() <= 12 + 1  # paleta + contorno
    bbox = sprite.bbox()
    assert bbox is not None and bbox[3] <= 64


def _hand_sprite(with_face: bool) -> PixelCanvas:
    """Sprite 64x64 montado à mão para exercitar o classificador de vista."""
    c = PixelCanvas(64, 64)
    c.ellipse(32, 16, 8, 8, (240, 200, 170))          # cabeça
    if with_face:
        c.rect(28, 15, 3, 3, (25, 25, 35))           # olho esq
        c.rect(34, 15, 3, 3, (25, 25, 35))           # olho dir
        c.rect(30, 21, 5, 1, (140, 70, 70))          # boca
    c.rect(26, 25, 13, 18, (60, 120, 70))            # tronco
    c.rect(27, 43, 5, 16, (70, 60, 50))              # perna esq
    c.rect(33, 43, 5, 16, (70, 60, 50))              # perna dir
    return c


def test_detect_view_front_for_symmetric_render():
    assert detect_view(_hand_sprite(with_face=True)) == "front"


def test_detect_view_back_when_no_face():
    assert detect_view(_hand_sprite(with_face=False)) == "back"


def test_detect_view_side_for_asymmetric_sprite():
    c = _hand_sprite(with_face=True)
    # desloca todo o conteúdo para um lado e remove a simetria
    asym = PixelCanvas(64, 64)
    asym.blit(c, 6, 0)
    asym.rect(46, 30, 8, 3, (200, 200, 60))  # braço estendido p/ frente
    assert detect_view(asym) == "side"


def test_synthesize_produces_four_directions(fixture_image_bytes):
    img, _ = remove_background(load_image(fixture_image_bytes), ImageImportParams())
    sprite = pixelize(img, ImageImportParams(target_size=48), (64, 64))
    dirs = synthesize_directions(sprite, ImageImportParams())
    assert set(dirs) == {"down", "left", "right", "up"}
    # laterais comprimidas em relação à frontal
    fw = sprite.bbox()
    lw = dirs["left"].bbox()
    assert (lw[2] - lw[0]) < (fw[2] - fw[0])
    # costas sem rosto != frente
    assert dirs["up"].to_bytes() != dirs["down"].to_bytes()


def test_segment_rig_has_animatable_layers(fixture_image_bytes):
    result = import_image(fixture_image_bytes, ImageImportParams(target_size=48))
    rig = result.rigs["down"]
    kinds = {layer.kind for layer in rig.layers}
    assert {"head", "torso", "leg_front", "leg_back"} <= kinds
    legs = [lay for lay in rig.layers if lay.tags.get("leg")]
    assert len(legs) >= 2
    assert {int(lay.tags["gait"]) for lay in legs} == {0, 1}


def test_import_end_to_end_animates(fixture_image_bytes):
    result = import_image(fixture_image_bytes, ImageImportParams(target_size=48, palette_size=16))
    assert result.meta.background_removed
    assert result.meta.detected_view in ("front", "side", "back")
    clips = build_clips(lambda d: result.rigs[d.value], params=AnimationParams())
    walk = next(c for c in clips if c.name == "walk")
    assert set(walk.frames_by_direction) == {"down", "left", "right", "up"}
    distinct = {f.to_bytes() for f in walk.frames_by_direction["down"]}
    assert len(distinct) >= 3
    for direction in ("down", "left", "right", "up"):
        assert not compose_rig(result.rigs[direction]).is_empty()


def test_import_empty_image_warns():
    import io

    buf = io.BytesIO()
    Image.new("RGBA", (40, 40), (200, 200, 200, 255)).save(buf, format="PNG")
    result = import_image(buf.getvalue(), ImageImportParams())
    assert result.meta.warnings, "imagem só-fundo deve gerar aviso"
