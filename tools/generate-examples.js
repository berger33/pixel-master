#!/usr/bin/env node
// ============================================================================
// Pixel Master — gerador de sprites (PNG) e JSON de exemplo
// Uso: node tools/generate-examples.js
// ============================================================================
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

global.window = globalThis;

// carrega a lógica compartilhada (sem tocar no DOM)
require("../js/state.js");
require("../js/palette.js");
require("../js/exporter.js");
require("../js/templates.js");

// ----------------------------------------------------------------------------
// Encoder PNG mínimo (RGBA 8 bits)
// ----------------------------------------------------------------------------
const CRC_TABLE = (function () {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, "ascii");
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crc]);
}

function encodePNG(width, height, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;  // bit depth
  ihdr[9] = 6;  // color type: RGBA
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0; // filtro "None"
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  }
  const idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([sig, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0))]);
}

// ----------------------------------------------------------------------------
// Renderização de grids para RGBA (escala por vizinho mais próximo)
// ----------------------------------------------------------------------------
function gridScaledRGBA(grid, palette, scale) {
  const w = 16 * scale, h = 16 * scale;
  const out = Buffer.alloc(w * h * 4);
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      const c = grid[y * 16 + x];
      if (c < 0) continue;
      const rgb = PM.hexToRgb(palette[c]);
      if (!rgb) continue;
      for (let dy = 0; dy < scale; dy++) {
        for (let dx = 0; dx < scale; dx++) {
          const o = ((y * scale + dy) * w + (x * scale + dx)) * 4;
          out[o] = rgb[0]; out[o + 1] = rgb[1]; out[o + 2] = rgb[2]; out[o + 3] = 255;
        }
      }
    }
  }
  return { w, h, data: out };
}

// Monta uma sprite sheet (frames lado a lado) em RGBA escalado
function sheetRGBA(frames, palette, scale) {
  const fw = 16 * scale, fh = 16 * scale;
  const w = frames.length * fw, h = fh;
  const out = Buffer.alloc(w * h * 4);
  frames.forEach(function (fr, i) {
    const s = gridScaledRGBA(fr.pixels, palette, scale);
    for (let y = 0; y < fh; y++) {
      s.data.copy(out, (y * w + i * fw) * 4, y * fw * 4, y * fw * 4 + fw * 4);
    }
  });
  return { w, h, data: out };
}

function writePNG(file, width, height, rgba) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, encodePNG(width, height, rgba));
}

// ----------------------------------------------------------------------------
// Geração
// ----------------------------------------------------------------------------
const ROOT = path.join(__dirname, "..", "examples");
const SCALE = 4;

function main() {
  const count = PM.TEMPLATES.length;
  console.log("Gerando exemplos para " + count + " modelos...\n");

  // limpa o diretório de exemplos (mantém-se versionável, sem lixo antigo)
  fs.rmSync(ROOT, { recursive: true, force: true });

  const overview = []; // sprites idle para a imagem-resumo

  PM.TEMPLATES.forEach(function (t) {
    const slug = PM.slugify(t.name);
    const anims = PM.buildTemplateAnimations(t, 16);
    const base64 = {};

    anims.forEach(function (anim) {
      const sheet = sheetRGBA(anim.frames, t.palette, SCALE);
      const file = path.join(ROOT, "sprites", slug + "-" + anim.name + ".png");
      writePNG(file, sheet.w, sheet.h, sheet.data);
      base64[anim.name] = "data:image/png;base64," + encodePNG(sheet.w, sheet.h, sheet.data).toString("base64");
    });

    // JSON no mesmo formato exportado pelo app
    const json = {
      format: "pixel-master/v1",
      exportedAt: new Date().toISOString(),
      name: t.name,
      kind: t.kind,
      category: t.category,
      rarity: t.rarity,
      gridSize: 16,
      palette: t.palette.slice(),
      stats: Object.assign({}, t.stats),
      description: t.description,
      animations: anims.map(function (anim) {
        return {
          name: anim.name,
          fps: anim.fps,
          frameCount: anim.frames.length,
          spriteSheet: base64[anim.name],
          frames: anim.frames.map(function (f) { return { pixels: f.pixels.slice() }; })
        };
      })
    };
    fs.mkdirSync(path.join(ROOT, "json"), { recursive: true });
    fs.writeFileSync(path.join(ROOT, "json", slug + ".json"), JSON.stringify(json, null, 2));
    overview.push({ name: t.name, grid: PM.templateBaseGrid(t), palette: t.palette });

    console.log("✓ " + t.name + "  → " + anims.length + " animações (" +
      anims.map(a => a.name + "×" + a.frames.length).join(", ") + ")");
  });

  // imagem-resumo com todos os modelos (idle)
  const fw = 16 * SCALE, fh = 16 * SCALE;
  const ow = overview.length * fw;
  const ors = Buffer.alloc(ow * fh * 4);
  overview.forEach(function (o, i) {
    const s = gridScaledRGBA(o.grid, o.palette, SCALE);
    for (let y = 0; y < fh; y++) {
      s.data.copy(ors, (y * ow + i * fw) * 4, y * fw * 4, y * fw * 4 + fw * 4);
    }
  });
  writePNG(path.join(ROOT, "overview.png"), ow, fh, ors);

  console.log("\nExemplos gerados em examples/ (sprites/, json/, overview.png)");
}

main();
