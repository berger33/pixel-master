#!/usr/bin/env node
// ============================================================================
// Gera uma galeria HTML autocontida (imagens em base64) de todos os
// personagens estilo Tibia em examples/tibia/*.
// Uso: node tools/generate-tibia-gallery.js
// ============================================================================
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const TIBIA = path.join(ROOT, "examples", "tibia");
const OUT = path.join(TIBIA, "galeria.html");

const DIRS = [
  { id: 1, label: "Norte (costas)" },
  { id: 2, label: "Leste" },
  { id: 3, label: "Sul (frente)" },
  { id: 4, label: "Oeste" }
];
const FRAME_LABEL = { 1: "parado", 2: "passo", 3: "parado", 4: "passo" };

function b64(file) {
  const abs = path.join(TIBIA, file);
  if (!fs.existsSync(abs)) return "";
  return "data:image/png;base64," + fs.readFileSync(abs).toString("base64");
}

function findChars() {
  return fs.readdirSync(TIBIA, { withFileTypes: true })
    .filter((e) => e.isDirectory() && e.name !== "." && e.name !== "..")
    .map((e) => e.name);
}

function charSection(name) {
  const title = name.charAt(0).toUpperCase() + name.slice(1);

  let overviewHtml = "";
  const ov = b64(name + "/overview.png");
  if (ov) overviewHtml = "<div class='ov'><img src='" + ov + "'><p>overview.png (4 direções × 4 frames)</p></div>";

  let recolorHtml = "";
  const rc = b64(name + "/recolor-demo.png");
  if (rc) recolorHtml = "<div class='ov'><img src='" + rc + "'><p>recolor-demo.png (recolorido via tint)</p></div>";

  let rows = "";
  for (const d of DIRS) {
    let cells = "";
    for (let f = 1; f <= 4; f++) {
      const rel = name + "/64/" + d.id + "_1_1_" + f + ".png";
      const maskRel = name + "/mask/64/" + d.id + "_1_1_" + f + ".png";
      const img = b64(rel), mask = b64(maskRel);
      if (!img) continue;
      cells +=
        "<td><img src='" + img + "'><div class='fl'>" + FRAME_LABEL[f] + "</div>" +
        "<img class='mask' src='" + mask + "'></td>";
    }
    rows += "<tr><th>" + d.label + "</th>" + cells + "</tr>";
  }

  return "<section><h2>" + title + "</h2>" +
    "<div class='side'>" + overviewHtml + recolorHtml + "</div>" +
    "<table><tr><th>Direção</th><th colspan='4'>Frames (acima) + máscara de cor (abaixo)</th></tr>" +
    rows + "</table></section>";
}

const sections = findChars().map(charSection).join("\n");

const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Galeria — Personagens estilo Tibia</title>
<style>
  :root { --bg:#12141a; --panel:#171a22; --border:#2c3140; --text:#e6e9f0; --muted:#9aa1b5; --accent:#7c5cff; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family:system-ui,sans-serif; padding:28px; }
  h1 { font-size:24px; margin:0 0 4px; }
  .sub { color:var(--muted); margin:0 0 24px; font-size:14px; }
  section { background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:20px; margin-bottom:28px; }
  h2 { margin:0 0 12px; font-size:18px; color:var(--accent); }
  .side { display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px; }
  .ov { text-align:center; }
  .ov img { image-rendering:pixelated; border:1px solid var(--border); border-radius:8px; }
  .ov p { margin:6px 0 0; font-size:12px; color:var(--muted); }
  table { border-collapse:collapse; }
  th, td { border:1px solid var(--border); padding:10px; text-align:center; vertical-align:top; }
  th { color:var(--muted); font-weight:600; font-size:13px; }
  td img { image-rendering:pixelated; display:block; margin:0 auto; }
  td img.mask { margin-top:8px; opacity:0.95; }
  .fl { font-size:11px; color:var(--muted); margin:6px 0; }
  .legend { color:var(--muted); font-size:13px; margin-top:20px; }
  .legend b { color:var(--text); }
</style>
</head>
<body>
<h1>🏛️ Personagens estilo Tibia</h1>
<p class="sub">Validação do motor de criação — 4 direções × 4 frames (parado → passo → parado → passo), contorno escuro e sistema de cor por partes.</p>
${sections}
<p class="legend"><b>Legenda da máscara de cor:</b> <span style="color:#ff5555">■</span> cabeça · <span style="color:#ffee55">■</span> corpo · <span style="color:#55ff55">■</span> pernas · <span style="color:#5555ff">■</span> pés · <span style="color:#444">■</span> contorno. Essa máscara permite trocar a cor do outfit sem redesenhar.</p>
</body>
</html>`;

fs.writeFileSync(OUT, html);
console.log("Galeria gerada em examples/tibia/galeria.html (" +
  Math.round(fs.statSync(OUT).size / 1024) + " KB, imagens embutidas)");
