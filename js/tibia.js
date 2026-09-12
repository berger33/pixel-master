// ============================================================================
// Pixel Master — Motor de criação de personagens no estilo Tibia
// ----------------------------------------------------------------------------
// Gera um personagem humanóide em projeção OBLÍQUA TOP-DOWN (~135°), com:
//   • 4 direções (Norte, Leste, Sul, Oeste)
//   • 4 frames de caminhada por direção (parado → passo → parado → passo)
//   • contorno escuro (silhueta)
//   • sistema de cor por partes (cabeça / corpo / pernas / pés)
//   • máscara de tint (template) para recolorir sem redesenhar
//
// Puro (sem DOM): funciona no Node (geração) e no navegador (editor).
// ============================================================================
(function (root) {
  "use strict";

  // ---- Direções (convenção Tibia) -----------------------------------------
  const DIR = { NORTH: 1, EAST: 2, SOUTH: 3, WEST: 4 };

  // ---- Índices de cor (paleta interna) ------------------------------------
  const C = {
    OUTLINE: 0,
    SKIN: 1,
    HAIR: 2,
    BODY: 3,
    BODY_DARK: 4,
    LEGS: 5,
    LEGS_DARK: 6,
    FEET: 7,
    FEET_DARK: 8
  };

  // ---- Regiões tintáveis (máscara de cor) ---------------------------------
  // Índices >= 10 para não colidir com C.OUTLINE (0) e os índices de cor (1..8).
  const REGION = { HEAD: 10, BODY: 11, LEGS: 12, FEET: 13 };

  // Cores da máscara (padrão Tibia): vermelho/amarelo/verde/azul
  const MASK_RGB = {
    10: [255, 0, 0],    // cabeça
    11: [255, 255, 0],  // corpo
    12: [0, 255, 0],    // pernas
    13: [0, 0, 255]     // pés
  };

  // Paleta padrão de um "Guerreiro" agradável
  const DEFAULT_PALETTE = {
    [C.OUTLINE]: [26, 22, 22],
    [C.SKIN]: [242, 200, 154],
    [C.HAIR]: [74, 42, 20],
    [C.BODY]: [176, 48, 48],
    [C.BODY_DARK]: [128, 30, 30],
    [C.LEGS]: [58, 90, 160],
    [C.LEGS_DARK]: [38, 60, 110],
    [C.FEET]: [106, 74, 42],
    [C.FEET_DARK]: [70, 48, 26]
  };

  // ---- Mapeamento kind -> índice de cor -----------------------------------
  const KIND_COLOR = {
    hair: C.HAIR,
    skin: C.SKIN,
    torso: C.BODY,
    torsoDark: C.BODY_DARK,
    arm: C.BODY,
    hand: C.SKIN,
    leg: C.LEGS,
    legDark: C.LEGS_DARK,
    foot: C.FEET,
    footDark: C.FEET_DARK
  };

  // ---- Mapeamento kind -> região tintável ---------------------------------
  const KIND_REGION = {
    hair: REGION.HEAD,
    skin: REGION.HEAD,
    torso: REGION.BODY,
    torsoDark: REGION.BODY,
    arm: REGION.BODY,
    hand: REGION.BODY,
    leg: REGION.LEGS,
    legDark: REGION.LEGS,
    foot: REGION.FEET,
    footDark: REGION.FEET
  };

  // -------------------------------------------------------------------------
  // Primitivas
  // -------------------------------------------------------------------------
  function makeP(kind, cx, cy, rx, ry) { return { kind, cx, cy, rx, ry }; }

  function ellipse(px, W, H, cx, cy, rx, ry, color) {
    const x0 = Math.max(0, Math.floor(cx - rx)), x1 = Math.min(W - 1, Math.ceil(cx + rx));
    const y0 = Math.max(0, Math.floor(cy - ry)), y1 = Math.min(H - 1, Math.ceil(cy + ry));
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const dx = (x - cx) / rx, dy = (y - cy) / ry;
        if (dx * dx + dy * dy <= 1) px[y * W + x] = color;
      }
    }
  }

  function setPx(px, W, H, x, y, color) {
    x = Math.round(x); y = Math.round(y);
    if (x < 0 || y < 0 || x >= W || y >= H) return;
    px[y * W + x] = color;
  }

  // Contorno de silhueta: pixel preenchido adjacente a transparente -> contorno
  function applyOutline(px, W, H, outlineColor) {
    const out = new Int32Array(px.length);
    out.set(px);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        if (px[y * W + x] < 0) continue;
        let edge = false;
        edge = edge || (x === 0 || px[y * W + (x - 1)] < 0);
        edge = edge || (x === W - 1 || px[y * W + (x + 1)] < 0);
        edge = edge || (y === 0 || px[(y - 1) * W + x] < 0);
        edge = edge || (y === H - 1 || px[(y + 1) * W + x] < 0);
        if (edge) out[y * W + x] = outlineColor;
      }
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // Geometria das partes por direção + passo
  // step: 0 = parado, -1 = passo esquerdo, +1 = passo direito
  // Proporções "encorpadas" (cabeça grande, corpo achatado = assinatura Tibia).
  // -------------------------------------------------------------------------
  function partsFor(direction, step) {
    const P = [];

    // pé que avança desce (projeção oblíqua: "para frente" = para baixo no tile)
    const adv = step < 0 ? "L" : step > 0 ? "R" : null;

    if (direction === DIR.SOUTH) {
      // ---- FRENTE (de frente para o espectador) ----
      P.push(makeP("hair", 15.5, 11.2, 4.4, 3.0));
      P.push(makeP("skin", 15.5, 13.3, 3.6, 3.3));
      P.push(makeP("torso", 15.5, 17.6, 5.2, 2.4));
      P.push(makeP("torsoDark", 15.5, 18.5, 4.2, 1.2));

      // braços colados ao torso (sem vão)
      const alx = step < 0 ? 9.1 : 9.6, arx = step > 0 ? 21.9 : 21.4;
      const aly = step < 0 ? 18.6 : 17.9, ary = step > 0 ? 18.6 : 17.9;
      P.push(makeP("arm", alx, aly, 1.4, 2.6));
      P.push(makeP("arm", arx, ary, 1.4, 2.6));
      P.push(makeP("hand", alx, aly + 2.5, 1.0, 1.0));
      P.push(makeP("hand", arx, ary + 2.5, 1.0, 1.0));

      const llx = step < 0 ? 12.9 : 13.5, lrx = step > 0 ? 18.1 : 17.5;
      P.push(makeP("leg", llx, 20.3, 1.6, 1.8));
      P.push(makeP("leg", lrx, 20.3, 1.6, 1.8));
      P.push(makeP("legDark", llx, 21.3, 1.3, 0.9));
      P.push(makeP("legDark", lrx, 21.3, 1.3, 0.9));

      const fly = adv === "L" ? 23.6 : 22.3, fry = adv === "R" ? 23.6 : 22.3;
      const flx = adv === "L" ? 12.3 : 13.0, frx = adv === "R" ? 18.7 : 18.0;
      P.push(makeP("foot", flx, fly, 2.0, 1.0));
      P.push(makeP("foot", frx, fry, 2.0, 1.0));
      P.push(makeP("footDark", flx, fly + 0.5, 1.5, 0.5));
      P.push(makeP("footDark", frx, fry + 0.5, 1.5, 0.5));
    }
    else if (direction === DIR.NORTH) {
      // ---- COSTAS (de costas para o espectador) ----
      P.push(makeP("hair", 15.5, 12.5, 4.5, 3.9));   // cabelo cobre a cabeça toda
      P.push(makeP("torso", 15.5, 17.6, 5.2, 2.4));
      P.push(makeP("torsoDark", 15.5, 18.5, 4.2, 1.2));

      const alx = step < 0 ? 9.1 : 9.6, arx = step > 0 ? 21.9 : 21.4;
      P.push(makeP("arm", alx, 17.9, 1.4, 2.6));
      P.push(makeP("arm", arx, 17.9, 1.4, 2.6));
      P.push(makeP("hand", alx, 20.4, 1.0, 1.0));
      P.push(makeP("hand", arx, 20.4, 1.0, 1.0));

      const llx = step < 0 ? 12.9 : 13.5, lrx = step > 0 ? 18.1 : 17.5;
      P.push(makeP("leg", llx, 20.3, 1.6, 1.8));
      P.push(makeP("leg", lrx, 20.3, 1.6, 1.8));
      P.push(makeP("legDark", llx, 21.3, 1.3, 0.9));
      P.push(makeP("legDark", lrx, 21.3, 1.3, 0.9));

      const fly = adv === "L" ? 23.6 : 22.3, fry = adv === "R" ? 23.6 : 22.3;
      P.push(makeP("foot", adv === "L" ? 12.3 : 13.0, fly, 2.0, 1.0));
      P.push(makeP("foot", adv === "R" ? 18.7 : 18.0, fry, 2.0, 1.0));
    }
    else if (direction === DIR.EAST) {
      // ---- PERFIL, olhando para a direita ----
      P.push(makeP("hair", 14.2, 12.6, 2.9, 3.2));   // nuca (esquerda)
      P.push(makeP("skin", 16.2, 13.4, 2.7, 3.0));   // rosto (direita)
      P.push(makeP("torso", 15.2, 17.7, 3.4, 2.2));
      P.push(makeP("torsoDark", 15.2, 18.5, 2.9, 1.1));

      // braço da frente: pende na borda dianteira (direita) e desce até a mão
      const armX = 18.0, armY = step < 0 ? 18.4 : 17.9;
      P.push(makeP("arm", armX, armY, 1.2, 2.5));
      P.push(makeP("hand", armX, armY + 2.6, 1.0, 1.0));

      // duas pernas (perfil: quase sobrepostas)
      const l1x = step < 0 ? 13.9 : 14.5, l2x = step > 0 ? 16.7 : 16.1;
      P.push(makeP("leg", l1x, 20.3, 1.5, 1.7));
      P.push(makeP("leg", l2x, 20.3, 1.5, 1.7));
      P.push(makeP("legDark", l1x, 21.3, 1.2, 0.8));
      P.push(makeP("legDark", l2x, 21.3, 1.2, 0.8));

      const f1y = adv === "L" ? 23.4 : 22.2, f2y = adv === "R" ? 23.4 : 22.2;
      P.push(makeP("foot", adv === "L" ? 13.6 : 14.3, f1y, 1.8, 1.0));
      P.push(makeP("foot", adv === "R" ? 17.5 : 16.9, f2y, 1.8, 1.0));
    }
    else { // DIR.WEST
      // ---- PERFIL, olhando para a esquerda ----
      P.push(makeP("hair", 16.8, 12.6, 2.9, 3.2));   // nuca (direita)
      P.push(makeP("skin", 14.8, 13.4, 2.7, 3.0));   // rosto (esquerda)
      P.push(makeP("torso", 15.8, 17.7, 3.4, 2.2));
      P.push(makeP("torsoDark", 15.8, 18.5, 2.9, 1.1));

      const armX = 13.0, armY = step > 0 ? 18.4 : 17.9;
      P.push(makeP("arm", armX, armY, 1.2, 2.5));
      P.push(makeP("hand", armX, armY + 2.6, 1.0, 1.0));

      const l1x = step > 0 ? 17.1 : 16.5, l2x = step < 0 ? 14.3 : 14.9;
      P.push(makeP("leg", l1x, 20.3, 1.5, 1.7));
      P.push(makeP("leg", l2x, 20.3, 1.5, 1.7));
      P.push(makeP("legDark", l1x, 21.3, 1.2, 0.8));
      P.push(makeP("legDark", l2x, 21.3, 1.2, 0.8));

      const f1y = adv === "R" ? 23.4 : 22.2, f2y = adv === "L" ? 23.4 : 22.2;
      P.push(makeP("foot", adv === "R" ? 17.7 : 17.0, f1y, 1.8, 1.0));
      P.push(makeP("foot", adv === "L" ? 13.5 : 14.2, f2y, 1.8, 1.0));
    }

    return P;
  }

  // Features faciais (apenas na vista de frente/perfil)
  function faceFeatures(px, W, H, direction) {
    if (direction === DIR.SOUTH) {
      setPx(px, W, H, 14, 13.4, C.OUTLINE); // olho esquerdo
      setPx(px, W, H, 17, 13.4, C.OUTLINE); // olho direito
      setPx(px, W, H, 15, 15.2, C.OUTLINE); // boca
      setPx(px, W, H, 16, 15.2, C.OUTLINE);
    } else if (direction === DIR.EAST) {
      setPx(px, W, H, 17, 12.9, C.OUTLINE); // olho (perfil)
    } else if (direction === DIR.WEST) {
      setPx(px, W, H, 14, 12.9, C.OUTLINE);
    }
  }

  // -------------------------------------------------------------------------
  // Renderização
  // -------------------------------------------------------------------------
  function renderIndexes(direction, frame, W, H) {
    W = W || 32; H = H || 32;
    const step = frame % 2 === 0 ? (frame === 2 ? -1 : 1) : 0; // frames 1,3 parado; 2/4 passo
    const px = new Int32Array(W * H).fill(-1);
    const parts = partsFor(direction, step);
    for (const p of parts) ellipse(px, W, H, p.cx, p.cy, p.rx, p.ry, KIND_COLOR[p.kind]);
    const outlined = applyOutline(px, W, H, C.OUTLINE);
    faceFeatures(outlined, W, H, direction);
    return outlined;
  }

  function renderMaskIndexes(direction, frame, W, H) {
    W = W || 32; H = H || 32;
    const step = frame % 2 === 0 ? (frame === 2 ? -1 : 1) : 0;
    const px = new Int32Array(W * H).fill(-1);
    const parts = partsFor(direction, step);
    for (const p of parts) ellipse(px, W, H, p.cx, p.cy, p.rx, p.ry, KIND_REGION[p.kind]);
    // contorno escuro (mantém silhueta); regiões viram índices de máscara
    return applyOutline(px, W, H, C.OUTLINE);
  }

  // índices -> RGBA
  function toRGBA(indexes, W, H, colorForIndex, alphaOf) {
    const out = Buffer.alloc(W * H * 4);
    for (let i = 0; i < indexes.length; i++) {
      const idx = indexes[i];
      let r = 0, g = 0, b = 0, a = 0;
      if (idx >= 0) {
        const c = colorForIndex(idx);
        r = c[0]; g = c[1]; b = c[2]; a = alphaOf ? alphaOf(idx) : 255;
      }
      const o = i * 4;
      out[o] = r; out[o + 1] = g; out[o + 2] = b; out[o + 3] = a;
    }
    return out;
  }

  function renderRGBA(direction, frame, palette, W, H) {
    W = W || 32; H = H || 32;
    palette = palette || DEFAULT_PALETTE;
    const idx = renderIndexes(direction, frame, W, H);
    return { w: W, h: H, data: toRGBA(idx, W, H, function (i) { return palette[i] || [0, 0, 0]; }) };
  }

  function renderMaskRGBA(direction, frame, W, H) {
    W = W || 32; H = H || 32;
    const idx = renderMaskIndexes(direction, frame, W, H);
    return {
      w: W, h: H,
      data: toRGBA(idx, W, H, function (i) {
        if (i === C.OUTLINE) return [17, 17, 17]; // contorno da máscara
        return MASK_RGB[i] || [0, 0, 0];
      })
    };
  }

  // Recolore uma máscara (RGBA) usando uma paleta: troca vermelho/amarelo/verde/azul
  function tintMask(maskRGBA, palette) {
    palette = palette || DEFAULT_PALETTE;
    const data = Buffer.from(maskRGBA.data);
    const w = maskRGBA.w, h = maskRGBA.h;
    const map = {
      "255,0,0": palette[C.SKIN],     // cabeça -> cor de pele (ou cabeça)
      "255,255,0": palette[C.BODY],   // corpo
      "0,255,0": palette[C.LEGS],     // pernas
      "0,0,255": palette[C.FEET]      // pés
    };
    for (let i = 0; i < w * h; i++) {
      const o = i * 4;
      const r = data[o], g = data[o + 1], b = data[o + 2];
      if (data[o + 3] === 0) continue;
      const key = r + "," + g + "," + b;
      if (map[key]) {
        data[o] = map[key][0]; data[o + 1] = map[key][1]; data[o + 2] = map[key][2];
      }
    }
    return { w, h, data };
  }

  // Escala por vizinho mais próximo (RGBA)
  function scaleRGBA(src, factor) {
    const w = src.w * factor, h = src.h * factor;
    const out = Buffer.alloc(w * h * 4);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const sx = Math.floor(x / factor), sy = Math.floor(y / factor);
        src.data.copy(out, (y * w + x) * 4, (sy * src.w + sx) * 4, (sy * src.w + sx) * 4 + 4);
      }
    }
    return { w, h, data: out };
  }

  // ---- Export --------------------------------------------------------------
  const Tibia = {
    DIR,
    C,
    REGION,
    DEFAULT_PALETTE,
    renderIndexes,
    renderMaskIndexes,
    renderRGBA,
    renderMaskRGBA,
    tintMask,
    scaleRGBA
  };

  root.Tibia = Tibia;
  if (typeof module !== "undefined" && module.exports) module.exports = Tibia;
})(typeof window !== "undefined" ? window : globalThis);
