// ============================================================================
// Pixel Master — modelos pré-prontos (templates 16×16 escaláveis)
// ============================================================================
window.PM = window.PM || {};

// charmap: '.' = transparente, '0'-'9' = paleta[0..9], 'A'-'F' = paleta[10..15]
PM.TEMPLATES = [
  {
    name: "Slime",
    kind: "creature",
    category: "slime",
    rarity: "common",
    stats: { hp: 60, attack: 5, defense: 3, speed: 2, magic: 0 },
    description: "Uma gosma verde e saltitante, criatura comum das masmorras de Vandoria.",
    palette: ["#0d2b14", "#37a04b", "#6fd06f", "#b8f0a0", "#206b33", "#000000", "#ffffff"],
    rows: [
      "................",
      "....00000000....",
      "...0111111110...",
      "..011111111110..",
      ".01111111111110.",
      ".01112111112110.",
      "0111211111121110",
      "0112651111562110",
      "0112651111562110",
      "0111111111111110",
      "0111111111111110",
      "0111441111441110",
      "0114441114444110",
      "0111111111111110",
      ".00000000000000.",
      "................"
    ]
  },
  {
    name: "Fantasma",
    kind: "creature",
    category: "espírito",
    rarity: "uncommon",
    stats: { hp: 40, attack: 8, defense: 2, speed: 8, magic: 12 },
    description: "Espírito etéreo que atravessa paredes e assombra ruínas antigas.",
    palette: ["#1a1f2e", "#dce6f5", "#9fb2d0", "#0a0a0a", "#ffffff"],
    rows: [
      "................",
      "....00000000....",
      "..001111111100..",
      ".01111111111110.",
      ".01111111111110.",
      "0111111111111110",
      "0113111111113110",
      "0113111111113110",
      "0111111111111110",
      "0111111111111110",
      "0111111111111110",
      "0111111111111110",
      "0112211111221110",
      "0122221122222110",
      "0122222222222210",
      "0122012201220120"
    ]
  },
  {
    name: "Cavaleiro",
    kind: "character",
    category: "humanoid",
    rarity: "rare",
    stats: { hp: 150, attack: 18, defense: 20, speed: 4, magic: 0 },
    description: "Guerreiro de armadura azul, guardião dos reinos de Vandoria.",
    palette: ["#1a1a24", "#f0c090", "#5a6bd8", "#2e3f8a", "#8fa4f0", "#c8d0e0", "#14141a", "#e8b840"],
    rows: [
      "....00000000....",
      "...0222222220...",
      "..024444444420..",
      "..024444444420..",
      "..026444444620..",
      "...011111110...",
      "...011111110...",
      "....0111110....",
      "..03333333330...",
      ".03377333337730.",
      ".03377333337730.",
      ".03333333333330.",
      ".03333333333330.",
      ".03333333333330.",
      ".0..0333330..0..",
      ".00..0..0..0.00."
    ]
  },
  {
    name: "Esqueleto",
    kind: "creature",
    category: "morto-vivo",
    rarity: "uncommon",
    stats: { hp: 45, attack: 14, defense: 4, speed: 6, magic: 0 },
    description: "Guerreiro morto-vivo reanimado por necromancia.",
    palette: ["#1a1a1a", "#e8e0d0", "#b8ae9c", "#0a0a0a"],
    rows: [
      "....00000000....",
      "..001111111100..",
      ".01111111111110.",
      ".01111111111110.",
      ".01311111111310.",
      ".01111111111110.",
      "..011111111110..",
      "..011111111110..",
      "...011111110....",
      "..01111111110...",
      ".01121111112110.",
      ".01111111111110.",
      ".01111111111110.",
      ".0..0111110..0..",
      ".0...01110...0..",
      ".00..0.0..0.00.."
    ]
  },
  {
    name: "Dragão",
    kind: "creature",
    category: "dragão",
    rarity: "legendary",
    stats: { hp: 300, attack: 30, defense: 22, speed: 10, magic: 25 },
    description: "Dragão alado de escamas violetas, temido em toda Vandoria.",
    palette: ["#1a1220", "#6a4a9c", "#c8a0e0", "#3a2a6a", "#f0d040", "#e0e0e0", "#14141a"],
    rows: [
      "..00........00..",
      ".0330.......0330.",
      ".03330.....03330.",
      ".033330000033330.",
      "..03331111113330.",
      "...033111111330..",
      "....0111111110...",
      "...011111111110..",
      "..01111111111110.",
      "..01121111112110.",
      ".011211111112110.",
      ".011111111111110.",
      ".011111111111110.",
      ".011122111122110.",
      ".011122111122110.",
      ".00..0..0..0..00."
    ]
  },
  {
    name: "Goblin",
    kind: "creature",
    category: "humanoid",
    rarity: "common",
    stats: { hp: 35, attack: 9, defense: 3, speed: 9, magic: 0 },
    description: "Pequeno e ágil saqueador de cavernas, ataca em bandos.",
    palette: ["#1a1a14", "#7fb03a", "#4a8a1a", "#e8d060", "#14141a", "#c8a020", "#e0e0a0"],
    rows: [
      "....00000000....",
      "...0111111110...",
      "..011111111110..",
      "..011111111110..",
      "..014111111410..",
      "...011111110...",
      "...011111110...",
      "....0111110....",
      "..01111111110...",
      ".0111111111110..",
      ".0112111112110..",
      ".0111111111110..",
      ".0111111111110..",
      ".0..0111110..0..",
      ".0...01110...0..",
      ".00..0.0..0.00.."
    ]
  }
];

// ----------------------------------------------------------------------------
// Conversão de um template (16×16) para um frame na grade atual
// ----------------------------------------------------------------------------
PM.templateCharToIndex = function (ch) {
  if (ch === ".") return -1;
  const code = ch.charCodeAt(0);
  if (code >= 48 && code <= 57) return code - 48;
  if (code >= 65 && code <= 70) return code - 65 + 10;
  if (code >= 97 && code <= 102) return code - 97 + 10;
  return -1;
};

PM.templateToFrame = function (template, gridSize) {
  const scale = gridSize / 16;
  const base = new Array(16 * 16).fill(-1);
  for (let y = 0; y < 16; y++) {
    const row = template.rows[y] || "";
    for (let x = 0; x < 16; x++) {
      const ch = x < row.length ? row[x] : ".";
      base[y * 16 + x] = PM.templateCharToIndex(ch);
    }
  }
  // escala por vizinho mais próximo
  const frame = PM.createEmptyFrame(gridSize);
  for (let y = 0; y < gridSize; y++) {
    const sy = Math.floor(y / scale);
    for (let x = 0; x < gridSize; x++) {
      const sx = Math.floor(x / scale);
      frame.pixels[y * gridSize + x] = base[sy * 16 + sx];
    }
  }
  return frame;
};

PM.applyTemplate = function (template) {
  const gridSize = PM.state.project.gridSize;
  PM.state.undoStack.push(PM.clone(PM.state.project));
  PM.state.redoStack = [];

  const p = PM.createProject(gridSize, template.palette);
  p.name = template.name;
  p.kind = template.kind;
  p.category = template.category;
  p.rarity = template.rarity;
  p.stats = Object.assign({}, template.stats);
  p.description = template.description;
  p.animations = [PM.createAnimation("idle", 1, gridSize)];
  p.animations[0].frames[0] = PM.templateToFrame(template, gridSize);

  PM.state.project = p;
  PM.state.animIndex = 0;
  PM.state.frameIndex = 0;
  PM.state.colorIndex = 0;
  PM.refresh();
  PM.toast("Modelo \"" + template.name + "\" carregado!");
};

// ----------------------------------------------------------------------------
// Renderização da grade de templates
// ----------------------------------------------------------------------------
PM.refreshTemplates = function () {
  const grid = document.getElementById("template-grid");
  grid.innerHTML = "";
  PM.TEMPLATES.forEach(function (t) {
    const card = document.createElement("button");
    card.className = "template-card";

    // desenha o template numa thumbnail 16×16
    const frame = PM.templateToFrame(t, 16);
    const c = PM.renderFrameToCanvas(frame, t.palette, 16);
    card.appendChild(c);

    const label = document.createElement("span");
    label.textContent = t.name;
    card.appendChild(label);

    card.addEventListener("click", function () { PM.applyTemplate(t); });
    grid.appendChild(card);
  });
};
