#!/usr/bin/env node
// ============================================================================
// Pixel Master — gera um personagem de exemplo no estilo Tibia
// Uso:
//   node tools/generate-tibia-character.js                 # guerreiro padrão
//   node tools/generate-tibia-character.js --name Mage     # nome custom
//   node tools/generate-tibia-character.js --ascii         # imprime 1 frame em ASCII
// ============================================================================
const fs = require("fs");
const path = require("path");
const { encodePNG } = require("./lib/png.js");

global.window = globalThis;
const Tibia = require("../js/tibia.js");

// ---------------------------------------------------------------------------
// argumentos
// ---------------------------------------------------------------------------
function parseArgs() {
  const a = process.argv.slice(2);
  const args = { name: "Warrior", ascii: false, out: null, colors: {} };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--name") args.name = a[++i];
    else if (a[i] === "--ascii") args.ascii = true;
    else if (a[i] === "--out") args.out = a[++i];
    else if (a[i] === "--body") args.colors.body = a[++i];
    else if (a[i] === "--legs") args.colors.legs = a[++i];
    else if (a[i] === "--hair") args.colors.hair = a[++i];
    else if (a[i] === "--skin") args.colors.skin = a[++i];
    else if (a[i] === "--feet") args.colors.feet = a[++i];
  }
  return args;
}

// hex "#rrggbb" -> [r,g,b]
function hex2rgb(h) {
  const m = /^#?([0-9a-f]{6})$/i.exec(h || "");
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

// aplica overrides de cor na paleta padrão (gera o tom escuro automaticamente)
function applyColors(overrides) {
  const pal = {};
  const base = Tibia.DEFAULT_PALETTE;
  for (const k in base) pal[k] = base[k].slice();
  const dark = function (rgb) { return rgb.map(function (c) { return Math.round(c * 0.65); }); };
  const C = Tibia.C;
  if (overrides.body) { pal[C.BODY] = hex2rgb(overrides.body); pal[C.BODY_DARK] = dark(pal[C.BODY]); }
  if (overrides.legs) { pal[C.LEGS] = hex2rgb(overrides.legs); pal[C.LEGS_DARK] = dark(pal[C.LEGS]); }
  if (overrides.hair) { pal[C.HAIR] = hex2rgb(overrides.hair); }
  if (overrides.skin) { pal[C.SKIN] = hex2rgb(overrides.skin); }
  if (overrides.feet) { pal[C.FEET] = hex2rgb(overrides.feet); pal[C.FEET_DARK] = dark(pal[C.FEET]); }
  return pal;
}

const args = parseArgs();
const slug = args.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "character";
const OUT = args.out || path.join(__dirname, "..", "examples", "tibia", slug);

const DIRS = [
  { id: Tibia.DIR.NORTH, label: "norte" },
  { id: Tibia.DIR.EAST, label: "leste" },
  { id: Tibia.DIR.SOUTH, label: "sul" },
  { id: Tibia.DIR.WEST, label: "oeste" }
];

function writePNG(file, w, h, rgba) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, encodePNG(w, h, rgba));
}

function tilePath(scale) {
  return path.join(OUT, scale === 1 ? "32" : "64");
}

// ---------------------------------------------------------------------------
// ASCII (depuração / validação visual)
// ---------------------------------------------------------------------------
function asciiDump(direction, frame) {
  const idx = Tibia.renderIndexes(direction, frame, 32, 32);
  const chars = { "-1": " ", "0": "#", "1": "s", "2": "h", "3": "B", "4": "B", "5": "L", "6": "L", "7": "F", "8": "F" };
  const lines = [];
  for (let y = 0; y < 32; y++) {
    let line = "";
    for (let x = 0; x < 32; x++) line += chars[String(idx[y * 32 + x])] || "?";
    lines.push(line);
  }
  return lines.join("\n");
}

if (args.ascii) {
  console.log("=== FRENTE (sul), frame 1 ===");
  console.log(asciiDump(Tibia.DIR.SOUTH, 1));
  console.log("\n=== COSTAS (norte), frame 1 ===");
  console.log(asciiDump(Tibia.DIR.NORTH, 1));
  console.log("\n=== LESTE (perfil), frame 1 ===");
  console.log(asciiDump(Tibia.DIR.EAST, 1));
  console.log("\n=== OESTE (perfil), frame 1 ===");
  console.log(asciiDump(Tibia.DIR.WEST, 1));
  process.exit(0);
}

// ---------------------------------------------------------------------------
// geração
// ---------------------------------------------------------------------------
fs.rmSync(OUT, { recursive: true, force: true });

const manifest = {
  format: "pixel-master/tibia/v1",
  name: args.name,
  kind: "character",
  style: "tibia-oblique",
  gridSize: 32,
  directions: ["north", "east", "south", "west"],
  framesPerDirection: 4,
  palette: {},
  sprites: [],
  masks: []
};

// paleta em hex para o manifesto
const hex = function (rgb) {
  return "#" + rgb.map(function (c) { return ("0" + c.toString(16)).slice(-2); }).join("");
};
const PAL = applyColors(args.colors);
manifest.palette = {
  outline: hex(PAL[Tibia.C.OUTLINE]),
  head: hex(PAL[Tibia.C.SKIN]),
  hair: hex(PAL[Tibia.C.HAIR]),
  body: hex(PAL[Tibia.C.BODY]),
  bodyDark: hex(PAL[Tibia.C.BODY_DARK]),
  legs: hex(PAL[Tibia.C.LEGS]),
  legsDark: hex(PAL[Tibia.C.LEGS_DARK]),
  feet: hex(PAL[Tibia.C.FEET]),
  feetDark: hex(PAL[Tibia.C.FEET_DARK])
};

// monta a grade do overview (4 direções x 4 frames) em 64px
const CELL = 64;
const ow = CELL * 4, oh = CELL * 4;
const overview = Buffer.alloc(ow * oh * 4);

DIRS.forEach(function (d, di) {
  for (let f = 1; f <= 4; f++) {
    const rgba = Tibia.renderRGBA(d.id, f, PAL, 32, 32);
    const up = Tibia.scaleRGBA(rgba, 2); // 64×64

    // sprites 32 e 64
    const rel = d.id + "_1_1_" + f + ".png";
    writePNG(path.join(tilePath(1), rel), rgba.w, rgba.h, rgba.data);
    writePNG(path.join(tilePath(2), rel), up.w, up.h, up.data);
    manifest.sprites.push({ direction: d.label, frame: f, file: "32/" + rel, file64: "64/" + rel });

    // máscara de tint (template)
    const mask = Tibia.renderMaskRGBA(d.id, f, 32, 32);
    const maskUp = Tibia.scaleRGBA(mask, 2);
    writePNG(path.join(OUT, "mask", "32", rel), mask.w, mask.h, mask.data);
    writePNG(path.join(OUT, "mask", "64", rel), maskUp.w, maskUp.h, maskUp.data);
    manifest.masks.push({ direction: d.label, frame: f, file: "mask/32/" + rel });

    // overview (64px, com margem)
    const ox = f - 1, oy = di;
    up.data.copy(overview, (oy * ow + ox * CELL) * 4);
  }
});
writePNG(path.join(OUT, "overview.png"), ow, oh, overview);

// variante recolorida (demonstra o sistema de tint) — outfit azul/verde
const RECOLOR = {
  [Tibia.C.OUTLINE]: [26, 22, 22],
  [Tibia.C.SKIN]: [242, 200, 154],
  [Tibia.C.HAIR]: [40, 30, 60],
  [Tibia.C.BODY]: [40, 120, 200],
  [Tibia.C.BODY_DARK]: [26, 84, 150],
  [Tibia.C.LEGS]: [40, 140, 90],
  [Tibia.C.LEGS_DARK]: [26, 100, 62],
  [Tibia.C.FEET]: [70, 60, 40],
  [Tibia.C.FEET_DARK]: [46, 40, 26]
};
// usa a máscara + tint para provar recolorização sem redesenhar
{
  const mask = Tibia.renderMaskRGBA(Tibia.DIR.SOUTH, 1, 32, 32);
  const tinted = Tibia.tintMask(mask, RECOLOR);
  const up = Tibia.scaleRGBA(tinted, 2);
  writePNG(path.join(OUT, "recolor-demo.png"), up.w, up.h, up.data);
}

fs.writeFileSync(path.join(OUT, "character.json"), JSON.stringify(manifest, null, 2));

// galeria HTML para visualização no navegador
const gallery = buildGallery(args.name, manifest);
fs.writeFileSync(path.join(OUT, "index.html"), gallery);

console.log("Personagem \"" + args.name + "\" gerado em examples/tibia/" + slug + "/");
console.log("  - 16 sprites 32×32  (32/)");
console.log("  - 16 sprites 64×64  (64/)");
console.log("  - 16 máscaras de cor (mask/)");
console.log("  - overview.png (4 direções × 4 frames)");
console.log("  - recolor-demo.png (recolorido via tint, sem redesenhar)");
console.log("  - character.json + index.html (galeria)");

// ---------------------------------------------------------------------------
function buildGallery(name, manifest) {
  const dirLabels = { north: "Norte (costas)", east: "Leste", south: "Sul (frente)", west: "Oeste" };
  let rows = "";
  DIRS.forEach(function (d) {
    let cells = "";
    for (let f = 1; f <= 4; f++) {
      const rel = d.id + "_1_1_" + f + ".png";
      cells += "<td><img src='64/" + rel + "' width='96' height='96'><div>" + frameLabel(f) + "</div>" +
        "<img src='mask/64/" + rel + "' width='64' height='64'></td>";
    }
    rows += "<tr><th>" + dirLabels[d.label] + "</th>" + cells + "</tr>";
  });
  return "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>" +
    "<title>" + name + " — estilo Tibia</title><style>" +
    "body{background:#12141a;color:#e6e9f0;font-family:system-ui,sans-serif;padding:24px;}" +
    "table{border-collapse:collapse;}th,td{border:1px solid #2c3140;padding:10px;text-align:center;vertical-align:top;}" +
    "img{image-rendering:pixelated;}div{font-size:11px;color:#9aa1b5;margin:4px 0;}" +
    "h1{font-size:20px;} .note{color:#9aa1b5;font-size:13px;}" +
    "</style></head><body><h1>" + name + " — estilo Tibia</h1>" +
    "<p class='note'>4 direções × 4 frames (parado → passo → parado → passo). Abaixo de cada sprite está a máscara de cor " +
    "(🔴 cabeça · 🟡 corpo · 🟢 pernas · 🔵 pés).</p>" +
    "<table><tr><th>Direção</th><th colspan='4'>Frames</th></tr>" + rows + "</table>" +
    "<p class='note'>Ver também: <a href='overview.png'>overview.png</a> e <a href='recolor-demo.png'>recolor-demo.png</a>.</p>" +
    "</body></html>";
}

function frameLabel(f) {
  return f === 1 || f === 3 ? "parado" : "passo";
}
