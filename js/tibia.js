// ============================================================================
// Pixel Master — Motor de criação de personagens no estilo Tibia
// ----------------------------------------------------------------------------
// Pipeline de arte (não é "8-bit chapado"):
//   • projeção oblíqua top-down (~135°)
//   • 4 direções × 4 frames de caminhada
//   • iluminação direcional (luz de cima/esquerda)
//   • rampa de 4 tons por material + DITHERING (Bayer 2×2)
//   • contorno com SELOUT (mais claro em cima, mais escuro embaixo)
//   • sistema de cor por partes (cabeça/corpo/pernas/pés) via máscara
//
// Puro (sem DOM): funciona no Node (geração) e no navegador (editor).
// ============================================================================
(function (root) {
  "use strict";

  const DIR = { NORTH: 1, EAST: 2, SOUTH: 3, WEST: 4 };

  // ---- IDs de material -----------------------------------------------------
  const C = { SKIN: 0, HAIR: 1, BODY: 2, LEGS: 3, FEET: 4 };

  // ---- Paleta base (cores "Tibia": levemente dessaturadas/terrosas) --------
  const OUTLINE_DARK = [30, 24, 20];   // contorno inferior (sombra)
  const OUTLINE_LIGHT = [78, 62, 50];  // contorno superior (iluminado)

  const DEFAULT_PALETTE = {
    [C.SKIN]: [238, 196, 150],   // pele
    [C.HAIR]: [96, 60, 32],      // cabelo
    [C.BODY]: [168, 58, 48],     // túnica (vermelho terroso)
    [C.LEGS]: [72, 92, 150],     // calça (azul acinzentado)
    [C.FEET]: [104, 78, 46]      // botas (marrom)
  };

  // ---- Regiões de tint (máscara) ------------------------------------------
  const REGION = { HEAD: 0, BODY: 1, LEGS: 2, FEET: 3, SKIN: 4 };
  const MASK_RGB = {
    [REGION.HEAD]: [255, 0, 0],      // cabeça/cabelo
    [REGION.BODY]: [255, 255, 0],    // corpo
    [REGION.LEGS]: [0, 255, 0],      // pernas
    [REGION.FEET]: [0, 0, 255],      // pés
    [REGION.SKIN]: [150, 150, 150]   // pele (fixo, não tintável)
  };

  // ---- kind (parte) -> material -------------------------------------------
  const KIND_MAT = {
    hair: C.HAIR, skin: C.SKIN, torso: C.BODY, torsoDark: C.BODY,
    arm: C.BODY, hand: C.SKIN, leg: C.LEGS, legDark: C.LEGS,
    foot: C.FEET, footDark: C.FEET
  };
  const KIND_REGION = {
    hair: REGION.HEAD, skin: REGION.SKIN, torso: REGION.BODY, torsoDark: REGION.BODY,
    arm: REGION.BODY, hand: REGION.SKIN, leg: REGION.LEGS, legDark: REGION.LEGS,
    foot: REGION.FEET, footDark: REGION.FEET
  };

  // -------------------------------------------------------------------------
  // Cores: rampa de 4 tons por material
  // -------------------------------------------------------------------------
  function ramp(base) {
    return [
      scale(base, 1.30),  // luz
      base,               // base
      scale(base, 0.66),  // sombra
      scale(base, 0.40)   // escuro
    ];
  }
  function scale(rgb, f) {
    return rgb.map(function (c) { return Math.max(0, Math.min(255, Math.round(c * f))); });
  }
  // rampas pré-computadas
  const RAMPS = {
    [C.SKIN]: ramp(DEFAULT_PALETTE[C.SKIN]),
    [C.HAIR]: ramp(DEFAULT_PALETTE[C.HAIR]),
    [C.BODY]: ramp(DEFAULT_PALETTE[C.BODY]),
    [C.LEGS]: ramp(DEFAULT_PALETTE[C.LEGS]),
    [C.FEET]: ramp(DEFAULT_PALETTE[C.FEET])
  };

  // -------------------------------------------------------------------------
  // Primitivas
  // -------------------------------------------------------------------------
  function makeP(kind, cx, cy, rx, ry) { return { kind, cx, cy, rx, ry }; }

  // Preenche uma elipse em dois grids: material (int) e luz (float 0..1).
  function fillEllipse(mat, light, W, H, p, matId, lightFn) {
    const x0 = Math.max(0, Math.floor(p.cx - p.rx)), x1 = Math.min(W - 1, Math.ceil(p.cx + p.rx));
    const y0 = Math.max(0, Math.floor(p.cy - p.ry)), y1 = Math.min(H - 1, Math.ceil(p.cy + p.ry));
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const dx = (x - p.cx) / p.rx, dy = (y - p.cy) / p.ry;
        if (dx * dx + dy * dy <= 1) {
          const i = y * W + x;
          mat[i] = matId;
          light[i] = lightFn(x, y, p);
        }
      }
    }
  }

  // Luz direcional (cima/esquerda): valor 1 = claro, 0 = escuro
  function partLight(x, y, p) {
    const nx = (x - p.cx) / p.rx;
    const ny = (y - p.cy) / p.ry;
    let L = 0.55 - 0.38 * nx - 0.30 * ny;
    return Math.max(0, Math.min(1, L));
  }

  // Dithering Bayer 2×2 para transições suaves entre tons
  const BAYER = [[0, 2], [3, 1]]; // valores /4
  function shadeFromLight(L, x, y) {
    const scaled = (1 - L) * 3; // 0 (claro) .. 3 (escuro)
    const base = Math.floor(scaled);
    const frac = scaled - base;
    const thr = BAYER[y & 1][x & 1] / 4;
    let s = frac > thr ? base + 1 : base;
    return Math.max(0, Math.min(3, s));
  }

  // -------------------------------------------------------------------------
  // Geometria das partes por direção + passo
  // -------------------------------------------------------------------------
  function partsFor(direction, step) {
    const P = [];
    const adv = step < 0 ? "L" : step > 0 ? "R" : null;

    if (direction === DIR.SOUTH) {
      // FRENTE
      P.push(makeP("hair", 15.5, 11.1, 4.7, 3.0));
      P.push(makeP("skin", 15.5, 13.2, 3.8, 3.3));
      P.push(makeP("torso", 15.5, 17.6, 4.7, 2.4));
      P.push(makeP("torsoDark", 15.5, 18.4, 3.9, 1.1));

      const alx = step < 0 ? 9.4 : 9.9, arx = step > 0 ? 21.6 : 21.1;
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
      P.push(makeP("foot", flx, fly, 2.2, 1.0));
      P.push(makeP("foot", frx, fry, 2.2, 1.0));
      P.push(makeP("footDark", flx, fly + 0.5, 1.6, 0.5));
      P.push(makeP("footDark", frx, fry + 0.5, 1.6, 0.5));
    }
    else if (direction === DIR.NORTH) {
      // COSTAS
      P.push(makeP("hair", 15.5, 12.4, 4.8, 3.9));
      P.push(makeP("torso", 15.5, 17.6, 4.7, 2.4));
      P.push(makeP("torsoDark", 15.5, 18.4, 3.9, 1.1));

      const alx = step < 0 ? 9.4 : 9.9, arx = step > 0 ? 21.6 : 21.1;
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
      P.push(makeP("foot", adv === "L" ? 12.3 : 13.0, fly, 2.2, 1.0));
      P.push(makeP("foot", adv === "R" ? 18.7 : 18.0, fry, 2.2, 1.0));
    }
    else if (direction === DIR.EAST) {
      // PERFIL → direita
      P.push(makeP("hair", 14.2, 12.5, 2.9, 3.2));
      P.push(makeP("skin", 16.2, 13.4, 2.7, 3.0));
      P.push(makeP("torso", 15.2, 17.7, 3.4, 2.2));
      P.push(makeP("torsoDark", 15.2, 18.5, 2.9, 1.1));

      const armX = 18.0, armY = step < 0 ? 18.4 : 17.9;
      P.push(makeP("arm", armX, armY, 1.2, 2.5));
      P.push(makeP("hand", armX, armY + 2.6, 1.0, 1.0));

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
      P.push(makeP("hair", 16.8, 12.5, 2.9, 3.2));
      P.push(makeP("skin", 14.8, 13.4, 2.7, 3.0));
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

  // Features faciais (pixels individuais)
  function faceFeatures(mat, W, H, direction) {
    const set = function (x, y, v) {
      x = Math.round(x); y = Math.round(y);
      if (x < 0 || y < 0 || x >= W || y >= H) return;
      mat[y * W + x] = v;
    };
    if (direction === DIR.SOUTH) {
      set(14, 13.3, 200); set(17, 13.3, 200);   // olhos (marcador -> cor escura)
      set(15, 15.1, 201); set(16, 15.1, 201);   // boca
    } else if (direction === DIR.EAST) {
      set(17, 12.9, 200);
    } else if (direction === DIR.WEST) {
      set(14, 12.9, 200);
    }
  }

  // -------------------------------------------------------------------------
  // Renderização: material+light -> RGBA com sombreamento e selout
  // -------------------------------------------------------------------------
  function renderMaterialLight(direction, frame, W, H) {
    W = W || 32; H = H || 32;
    const step = frame % 2 === 0 ? (frame === 2 ? -1 : 1) : 0;
    const mat = new Int32Array(W * H).fill(-1);
    const light = new Float32Array(W * H);
    const parts = partsFor(direction, step);
    for (const p of parts) {
      fillEllipse(mat, light, W, H, p, KIND_MAT[p.kind], partLight);
    }
    // características faciais: marcadores especiais (200/201) resolvidos depois
    faceFeatures(mat, W, H, direction);
    return { mat, light };
  }

  // Resolve marcadores faciais -> índice de "escuro" do material apropriado
  function resolveFace(mat, W, H, faceColorIdx) {
    for (let i = 0; i < mat.length; i++) {
      if (mat[i] >= 200) mat[i] = faceColorIdx;
    }
  }

  function buildRGBA(mat, light, W, H, ramps) {
    // 1) bbox para o selout
    let minY = H, maxY = 0;
    for (let i = 0; i < mat.length; i++) {
      if (mat[i] >= 0) { const y = (i / W) | 0; if (y < minY) minY = y; if (y > maxY) maxY = y; }
    }

    // 2) sombra por pixel (dithering)
    const shade = new Int32Array(W * H).fill(-1);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const m = mat[y * W + x];
        if (m < 0) continue;
        if (m >= 200) { shade[y * W + x] = 3; continue; } // face = escuro
        shade[y * W + x] = shadeFromLight(light[y * W + x], x, y);
      }
    }

    // 3) contorno (selout): pixel preenchido adjacente a vazio
    const out = Buffer.alloc(W * H * 4);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const m = mat[y * W + x];
        if (m < 0) continue;
        const mm = m >= 200 ? C.SKIN : m; // marcadores de face -> pele escura
        let edge = false;
        edge = edge || (x === 0 || mat[y * W + (x - 1)] < 0);
        edge = edge || (x === W - 1 || mat[y * W + (x + 1)] < 0);
        edge = edge || (y === 0 || mat[(y - 1) * W + x] < 0);
        edge = edge || (y === H - 1 || mat[(y + 1) * W + x] < 0);

        let r, g, b;
        if (edge) {
          // selout: contorno mais claro em cima, mais escuro embaixo
          const t = maxY > minY ? (y - minY) / (maxY - minY) : 0.5;
          r = Math.round(OUTLINE_LIGHT[0] * (1 - t) + OUTLINE_DARK[0] * t);
          g = Math.round(OUTLINE_LIGHT[1] * (1 - t) + OUTLINE_DARK[1] * t);
          b = Math.round(OUTLINE_LIGHT[2] * (1 - t) + OUTLINE_DARK[2] * t);
        } else {
          const rampArr = ramps[mm];
          const col = rampArr[shade[y * W + x]];
          r = col[0]; g = col[1]; b = col[2];
        }
        const o = (y * W + x) * 4;
        out[o] = r; out[o + 1] = g; out[o + 2] = b; out[o + 3] = 255;
      }
    }
    return out;
  }

  function renderRGBA(direction, frame, palette, W, H) {
    W = W || 32; H = H || 32;
    palette = palette || DEFAULT_PALETTE;
    const ramps = {
      [C.SKIN]: ramp(palette[C.SKIN]),
      [C.HAIR]: ramp(palette[C.HAIR]),
      [C.BODY]: ramp(palette[C.BODY]),
      [C.LEGS]: ramp(palette[C.LEGS]),
      [C.FEET]: ramp(palette[C.FEET])
    };
    const { mat, light } = renderMaterialLight(direction, frame, W, H);
    return { w: W, h: H, data: buildRGBA(mat, light, W, H, ramps) };
  }

  // -------------------------------------------------------------------------
  // Máscara de cor (regiões tintáveis)
  // -------------------------------------------------------------------------
  function renderMaskRGBA(direction, frame, W, H) {
    W = W || 32; H = H || 32;
    const { mat } = renderMaterialLight(direction, frame, W, H);
    const out = Buffer.alloc(W * H * 4);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const m = mat[y * W + x];
        if (m < 0) continue;
        let edge = false;
        edge = edge || (x === 0 || mat[y * W + (x - 1)] < 0);
        edge = edge || (x === W - 1 || mat[y * W + (x + 1)] < 0);
        edge = edge || (y === 0 || mat[(y - 1) * W + x] < 0);
        edge = edge || (y === H - 1 || mat[(y + 1) * W + x] < 0);
        const o = (y * W + x) * 4;
        let col;
        if (edge) col = [17, 17, 17];
        else if (m >= 200) col = [17, 17, 17]; // face
        else {
          const region = KIND_REGION[matKindName(m)];
          col = MASK_RGB[region];
        }
        out[o] = col[0]; out[o + 1] = col[1]; out[o + 2] = col[2]; out[o + 3] = 255;
      }
    }
    return { w: W, h: H, data: out };
  }

  // (helper) id material -> nome do kind, para a máscara
  function matKindName(m) {
    if (m === C.SKIN) return "skin";
    if (m === C.HAIR) return "hair";
    if (m === C.BODY) return "torso";
    if (m === C.LEGS) return "leg";
    if (m === C.FEET) return "foot";
    return "skin";
  }

  // -------------------------------------------------------------------------
  // Recolorir via máscara (troca as 4 regiões + pele, mantém contorno)
  // -------------------------------------------------------------------------
  function tintMask(maskRGBA, palette) {
    palette = palette || DEFAULT_PALETTE;
    const data = Buffer.from(maskRGBA.data);
    const w = maskRGBA.w, h = maskRGBA.h;
    const map = {
      "255,0,0": palette[C.HAIR],
      "255,255,0": palette[C.BODY],
      "0,255,0": palette[C.LEGS],
      "0,0,255": palette[C.FEET],
      "150,150,150": palette[C.SKIN]
    };
    for (let i = 0; i < w * h; i++) {
      const o = i * 4;
      if (data[o + 3] === 0) continue;
      const key = data[o] + "," + data[o + 1] + "," + data[o + 2];
      if (map[key]) {
        data[o] = map[key][0]; data[o + 1] = map[key][1]; data[o + 2] = map[key][2];
      }
    }
    return { w, h, data };
  }

  // Escala por vizinho mais próximo
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
    DIR, C, REGION,
    DEFAULT_PALETTE, OUTLINE_DARK, OUTLINE_LIGHT,
    renderRGBA, renderMaskRGBA, tintMask, scaleRGBA,
    // expostos para testes/depuração
    partsFor, renderMaterialLight, buildRGBA, ramp
  };

  root.Tibia = Tibia;
  if (typeof module !== "undefined" && module.exports) module.exports = Tibia;
})(typeof window !== "undefined" ? window : globalThis);
