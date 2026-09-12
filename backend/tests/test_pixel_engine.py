"""Testes do motor de pixel art (canvas, paletas, atlas)."""

from __future__ import annotations

import numpy as np

from app.pixel.canvas import PixelCanvas
from app.pixel.palette import (
    PALETTES,
    build_palette_from_canvas,
    nearest_color,
    outline_color_for,
    quantize_median_cut,
    ramp_from_color,
    snap_canvas_to_palette,
)
from app.pixel.spritesheet import (
    AnimationClip,
    pack_animation_set,
    phaser_hash_atlas,
    sparrow_xml_atlas,
    uniform_grid_manifest,
)


def test_set_get_and_bounds():
    c = PixelCanvas(8, 8)
    c.set(3, 4, (255, 0, 0))
    assert c.get(3, 4) == (255, 0, 0, 255)
    c.set(-1, 0, (1, 2, 3))  # fora dos limites: ignorado silenciosamente
    c.set(99, 99, (1, 2, 3))
    assert c.bbox() == (3, 4, 4, 5)


def test_alpha_blend_source_over():
    c = PixelCanvas(4, 4)
    c.set(0, 0, (255, 0, 0))
    c.blend_pixel(0, 0, (0, 0, 255, 128))
    r, g, b, a = c.get(0, 0)
    assert a == 255
    assert 100 < r < 160 and 100 < b < 160 and g == 0


def test_outline_adds_silhouette_ring():
    c = PixelCanvas(10, 10)
    c.rect(4, 4, 2, 2, (200, 200, 200))
    outlined = c.outline((0, 0, 0))
    assert outlined.get(3, 4)[3] == 255  # anel à esquerda
    assert outlined.get(4, 4)[:3] == (200, 200, 200)  # interior preservado


def test_rotation_preserves_grid_and_pixel_count():
    c = PixelCanvas(16, 16)
    c.rect(6, 6, 4, 4, (10, 200, 30))
    rotated = c.rotated(90, pivot=(8, 8))
    before = int((c.data[..., 3] > 0).sum())
    after = int((rotated.data[..., 3] > 0).sum())
    assert before == after
    assert rotated.width == 16 and rotated.height == 16


def test_scale_nearest_is_blocky():
    c = PixelCanvas(4, 4)
    c.set(0, 0, (255, 255, 255))
    big = c.scaled(8, 8)
    assert big.get(0, 0)[:3] == (255, 255, 255)
    assert big.get(1, 1)[:3] == (255, 255, 255)
    assert big.get(2, 2)[3] == 0


def test_erase_ellipse_cuts_hole():
    c = PixelCanvas(10, 10)
    c.rect(0, 0, 10, 10, (100, 100, 100))
    c.erase_ellipse(5, 5, 2, 2)
    assert c.get(5, 5)[3] == 0
    assert c.get(0, 0)[3] == 255


def test_ramp_is_ordered_light_to_dark():
    ramp = ramp_from_color((200, 60, 60), steps=5)
    # "claro -> escuro" medido pelo canal mais intenso (imune ao deslocamento
    # de matiz que a rampa aplica de propósito)
    peaks = [max(c) for c in ramp.colors]
    assert peaks == sorted(peaks, reverse=True)
    assert peaks[0] > peaks[-1]


def test_quantize_respects_max_colors():
    rng = np.random.default_rng(0)
    pixels = rng.integers(0, 255, size=(500, 3))
    colors = quantize_median_cut(pixels, 8)
    assert 1 <= len(colors) <= 8


def test_snap_reduces_color_count():
    c = PixelCanvas(8, 8)
    for y in range(8):
        for x in range(8):
            c.set(x, y, (x * 30, y * 30, 128))
    palette = [(0, 0, 128), (255, 255, 128)]
    snapped = snap_canvas_to_palette(c, palette)
    assert snapped.color_count() <= 2


def test_nearest_color_and_outline_derivation():
    assert nearest_color((10, 10, 200), [(0, 0, 255), (255, 0, 0)]) == (0, 0, 255)
    oc = outline_color_for([(200, 180, 160), (120, 90, 60)])
    assert sum(oc) < sum((200, 180, 160))  # contorno mais escuro que a base


def test_build_palette_from_canvas_groups_by_hue():
    c = PixelCanvas(6, 6)
    c.rect(0, 0, 3, 6, (200, 40, 40))
    c.rect(3, 0, 3, 6, (40, 40, 200))
    palette = build_palette_from_canvas(c, 8)
    all_colors = [col for ramp in palette.ramps.values() for col in ramp.colors]
    assert (200, 40, 40) in all_colors
    assert (40, 40, 200) in all_colors
    assert len(palette.ramps) >= 2  # vermelho e azul em rampas distintas


def test_spritesheet_grid_and_manifest_indices():
    def frame(i: int, h: int) -> PixelCanvas:
        c = PixelCanvas(16, 20)
        c.rect(2, 20 - h, 12, h, (i * 40, 60, 200))
        return c

    idle = AnimationClip(name="idle", frames_by_direction={"down": [frame(1, 10), frame(2, 11)]}, fps=6)
    walk = AnimationClip(
        name="walk",
        frames_by_direction={
            "down": [frame(1, 10), frame(2, 11), frame(3, 10), frame(1, 11)],
            "left": [frame(2, 10), frame(1, 11), frame(3, 10), frame(2, 11)],
        },
        fps=8,
    )
    sheet = pack_animation_set([idle, walk], frame_width=16, frame_height=20)
    assert sheet.columns == 4
    assert sheet.rows == 3  # idle/down, walk/down, walk/left
    assert sheet.frame_count == 2 + 4 + 4

    manifest = uniform_grid_manifest(sheet)
    idx = manifest["animationStartIndex"]
    assert idx["idle"]["down"] == 0
    assert idx["walk"]["down"] == 4
    assert idx["walk"]["left"] == 8

    atlas = phaser_hash_atlas(sheet)
    assert len(atlas["frames"]) == sheet.frame_count
    first = atlas["frames"]["idle_down_00"]["frame"]
    assert first == {"x": 0, "y": 0, "w": 16, "h": 20}

    xml = sparrow_xml_atlas(sheet)
    assert xml.count("<SubTexture") == sheet.frame_count


def test_pack_aligns_frames_to_ground():
    short = PixelCanvas(10, 10)
    short.rect(0, 6, 10, 4, (200, 0, 0))  # conteúdo no fundo
    clip = AnimationClip(name="idle", frames_by_direction={"down": [short]}, fps=4)
    sheet = pack_animation_set([clip], frame_width=16, frame_height=16)
    cell = sheet.image.crop(0, 0, 16, 16)
    bbox = cell.bbox()
    assert bbox is not None
    assert bbox[3] == 16  # encostado no chão da célula


def test_palettes_have_consistent_ramps():
    for name, palette in PALETTES.items():
        for key, ramp in palette.ramps.items():
            assert len(ramp) >= 2, f"{name}.{key}"
            assert ramp.at(-10) == ramp.colors[0]
            assert ramp.at(999) == ramp.colors[-1]
