#!/usr/bin/env python3
# ============================================================================
# Compõe uma prévia grande, nítida e legendada dos personagens estilo Tibia,
# para visualização/validação humana (fundo quadriculado + labels + máscara).
# ============================================================================
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(ROOT, "..", "examples", "tibia")

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DIRS = [
    (1, "NORTE (costas)"),
    (2, "LESTE"),
    (3, "SUL (frente)"),
    (4, "OESTE"),
]
FRAMES = [("1", "parado"), ("2", "passo"), ("3", "parado"), ("4", "passo")]

SCALE = 6           # fator de ampliação do sprite 32px -> 192px por célula
SPRITE = 32 * SCALE # 192
MASK = 32 * SCALE   # máscara na mesma escala (fica claro para ver)
LABEL_W = 210
CELL_W = SPRITE + 24
HEADER_H = 64


def load_rgba(path):
    im = Image.open(path).convert("RGBA")
    return im


def checker(size, cell=16, a=(235, 238, 242), b=(205, 210, 218)):
    im = Image.new("RGBA", size, a)
    d = ImageDraw.Draw(im)
    w, h = size
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=b)
    return im


def make_preview(char_name):
    base = os.path.join(EXAMPLES, char_name)
    if not os.path.isdir(base):
        print("pasta não encontrada:", base)
        return None

    n_rows = len(DIRS)
    n_cols = len(FRAMES)

    # layout: coluna de labels à esquerda + coluna de sprites (com máscara embaixo)
    total_w = LABEL_W + n_cols * CELL_W
    total_h = HEADER_H + n_rows * (SPRITE + MASK + 28)

    canvas = Image.new("RGB", (total_w, total_h), (240, 242, 246))
    d = ImageDraw.Draw(canvas)
    f_small = ImageFont.truetype(FONT_PATH, 18)
    f_med = ImageFont.truetype(FONT_PATH, 22)
    f_title = ImageFont.truetype(FONT_BOLD, 30)

    # título
    title = "Personagem estilo Tibia — " + char_name.capitalize()
    d.text((LABEL_W + 8, 14), title, fill=(20, 24, 34), font=f_title)

    # cabeçalho de frames
    for c, (fnum, flabel) in enumerate(FRAMES):
        cx = LABEL_W + c * CELL_W + CELL_W // 2
        d.text((cx, 40), "frame " + fnum + "  (" + flabel + ")", fill=(60, 66, 82), font=f_small, anchor="ma")

    # célula de cada sprite
    for r, (did, dlabel) in enumerate(DIRS):
        y0 = HEADER_H + r * (SPRITE + MASK + 28)
        # label de direção
        d.text((LABEL_W - 14, y0 + SPRITE // 2), dlabel, fill=(30, 34, 48), font=f_med, anchor="rm")
        for c, (fnum, flabel) in enumerate(FRAMES):
            x0 = LABEL_W + c * CELL_W
            # fundo quadriculado do sprite
            chk = checker((SPRITE, SPRITE))
            canvas.paste(chk, (x0 + 8, y0))
            # sprite 32px ampliado
            p = os.path.join(base, "32", f"{did}_1_1_{fnum}.png")
            if os.path.exists(p):
                spr = load_rgba(p).resize((SPRITE, SPRITE), Image.NEAREST)
                canvas.paste(spr, (x0 + 8, y0), spr)
            # máscara de cor embaixo
            m = os.path.join(base, "mask", "32", f"{did}_1_1_{fnum}.png")
            my = y0 + SPRITE + 8
            chk2 = checker((MASK, MASK), cell=12)
            canvas.paste(chk2, (x0 + 8, my))
            if os.path.exists(m):
                mask = load_rgba(m).resize((MASK, MASK), Image.NEAREST)
                canvas.paste(mask, (x0 + 8, my), mask)
            d.text((x0 + CELL_W // 2, my + MASK + 2), "máscara", fill=(110, 116, 130), font=f_small, anchor="ma")

    # legenda inferior
    leg_y = total_h - 4
    legend = "Máscara:  vermelho=cabeça  ·  amarelo=corpo  ·  verde=pernas  ·  azul=pés  ·  cinza=pele  ·  preto=contorno"
    d.text((LABEL_W + 8, leg_y), legend, fill=(110, 116, 130), font=f_small)

    out = os.path.join(EXAMPLES, "preview-" + char_name + ".png")
    canvas.save(out)
    print("OK ->", out, canvas.size)
    return out


if __name__ == "__main__":
    for name in ("warrior", "mage"):
        make_preview(name)
