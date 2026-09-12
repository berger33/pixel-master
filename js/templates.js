// ============================================================================
// Pixel Master — modelos pré-prontos (templates 16×16 escaláveis)
// + gerador de animações consistentes (idle / walk / attack)
// ============================================================================
window.PM = window.PM || {};

// charmap: '.' = transparente, '0'-'9' = paleta[0..9], 'A'-'F' = paleta[10..15]
// Flags por template:
//   walk:  "steps" (alterna os pés) | "bounce" (pulo/ondulação)
//   float: idle com flutuação para cima (fantasmas etc.)
//   attack: gera animação de ataque
PM.TEMPLATES = [
  {
    name: "Slime",
    kind: "creature",
    category: "slime",
    rarity: "common",
    walk: "bounce",
    attack: true,
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
    walk: "bounce",
    float: true,
    attack: false,
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
    walk: "steps",
    attack: true,
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
    walk: "steps",
    attack: true,
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
    walk: "steps",
    attack: true,
    stats: { hp: 300, attack: 30, defense: 22, speed: 10, magic: 25 },
    description: "Dragão alado de escamas violetas, temido em toda Vandoria.",
    palette: ["#1a1220", "#6a4a9c", "#c8a0e0", "#3a2a6a", "#f0d040", "#e0e0e0", "#14141a"],
    rows: [
      "..00........00..",
      ".0330......0330.",
      ".03330....03330.",
      ".03333000033330.",
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
    walk: "steps",
    attack: true,
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
  },
  {
    name: "Golem de Pedra",
    kind: "creature",
    category: "construto",
    rarity: "epic",
    walk: "steps",
    attack: true,
    stats: { hp: 260, attack: 24, defense: 30, speed: 1, magic: 0 },
    description: "Colosso de pedra animado por runas ancestrais, quase impenetrável.",
    palette: ["#1a1a1a", "#8a8a92", "#5a5a62", "#4a8a3a", "#b0b0b8", "#3af0e0"],
    rows: [
      "....00000000....",
      "...0111111110...",
      "..011111111110..",
      "..011411114110..",
      "..011411114110..",
      "..011111111110..",
      "..011111111110..",
      "..011111111110..",
      "..011111111110..",
      "..011311111110..",
      ".01131111113110.",
      ".01121111112110.",
      ".01121111112110.",
      ".01111111111110.",
      ".0..0111110..0..",
      ".00..0..0..00..."
    ]
  },
  {
    name: "Zumbi",
    kind: "creature",
    category: "morto-vivo",
    rarity: "uncommon",
    walk: "steps",
    attack: true,
    stats: { hp: 70, attack: 11, defense: 6, speed: 3, magic: 0 },
    description: "Cadáver reanimado e faminto, lento mas incansável.",
    palette: ["#141a10", "#7aa03a", "#4a7020", "#0a0a0a", "#8a1a1a"],
    rows: [
      "....00000000....",
      "..001111111100..",
      ".01111111111110.",
      ".01111111111110.",
      ".01311111113110.",
      ".01111111111110.",
      "..011111111110..",
      "..011111111110..",
      "...011111110....",
      "..01111111110...",
      ".0111111111110..",
      ".0124111114210..",
      ".0111111111110..",
      ".0..0111110..0..",
      ".0...01110...0..",
      ".00..0.0..0.00.."
    ]
  },
  {
    name: "Aranha",
    kind: "creature",
    category: "inseto",
    rarity: "uncommon",
    walk: "steps",
    attack: true,
    stats: { hp: 30, attack: 12, defense: 3, speed: 12, magic: 0 },
    description: "Aracnídeo venenoso que espreita nas teias das cavernas.",
    palette: ["#1a1010", "#2a1a1a", "#4a2a2a", "#f05050", "#1a0a0a"],
    rows: [
      ".0...0....0...0.",
      "..0..0....0..0..",
      "...0.0....0.0...",
      "....0.0..0.0....",
      ".....0.00.0.....",
      "......0000......",
      "......0000......",
      ".....011110.....",
      "....01111110....",
      "....01131110....",
      "....01111110....",
      ".....011110.....",
      "......0000......",
      "......0000......",
      ".....0.00.0.....",
      "....0.0..0.0...."
    ]
  }
];

// ----------------------------------------------------------------------------
// Helpers de grid (16×16) para gerar animações CONSISTENTES com o sprite base
// ----------------------------------------------------------------------------
PM.templateCharToIndex = function (ch) {
  if (ch === ".") return -1;
  const code = ch.charCodeAt(0);
  if (code >= 48 && code <= 57) return code - 48;
  if (code >= 65 && code <= 70) return code - 65 + 10;
  if (code >= 97 && code <= 102) return code - 97 + 10;
  return -1;
};

// Converte o template para um grid 16×16 (array de índices, -1 = transparente)
PM.templateBaseGrid = function (template) {
  const g = new Array(256).fill(-1);
  for (let y = 0; y < 16; y++) {
    const row = template.rows[y] || "";
    for (let x = 0; x < 16; x++) {
      const ch = x < row.length ? row[x] : ".";
      g[y * 16 + x] = PM.templateCharToIndex(ch);
    }
  }
  return g;
};

// Desloca todos os pixels (dx, dy). Pixels que saem da grade são descartados.
PM.gridShift = function (grid, dx, dy) {
  const out = new Array(256).fill(-1);
  for (let i = 0; i < 256; i++) {
    const c = grid[i];
    if (c < 0) continue;
    const x = i % 16, y = (i / 16) | 0;
    const nx = x + dx, ny = y + dy;
    if (nx < 0 || nx >= 16 || ny < 0 || ny >= 16) continue;
    out[ny * 16 + nx] = c;
  }
  return out;
};

// Levanta o "pé" de um lado: remove a fileira inferior do lado indicado,
// criando a alternância de passos sem alterar o restante do corpo.
PM.gridLiftFoot = function (grid, side) {
  let bottom = -1;
  for (let y = 15; y >= 0; y--) {
    let any = false;
    for (let x = 0; x < 16; x++) { if (grid[y * 16 + x] >= 0) { any = true; break; } }
    if (any) { bottom = y; break; }
  }
  if (bottom < 0) return grid.slice();
  const out = grid.slice();
  for (let x = 0; x < 16; x++) {
    const inSide = side === "left" ? x < 8 : x >= 8;
    if (inSide) out[bottom * 16 + x] = -1;
  }
  return out;
};

// Escala um grid 16×16 para o gridSize atual (vizinho mais próximo)
PM.gridToFrame = function (grid, gridSize) {
  const scale = gridSize / 16;
  const frame = PM.createEmptyFrame(gridSize);
  for (let y = 0; y < gridSize; y++) {
    const sy = Math.floor(y / scale);
    for (let x = 0; x < gridSize; x++) {
      const sx = Math.floor(x / scale);
      frame.pixels[y * gridSize + x] = grid[sy * 16 + sx];
    }
  }
  return frame;
};

PM.templateToFrame = function (template, gridSize) {
  return PM.gridToFrame(PM.templateBaseGrid(template), gridSize);
};

// ----------------------------------------------------------------------------
// Geração de animações (idle, walk, attack) derivadas do sprite base
// Todas as poses partem do MESMO grid base → consistência garantida.
// ----------------------------------------------------------------------------
PM.buildTemplateAnimations = function (template, gridSize) {
  const base = PM.templateBaseGrid(template);
  const toFrame = function (g) { return PM.gridToFrame(g, gridSize); };
  const anims = [];

  // idle — 2 frames (respiração/flutuação sutil)
  const idleFrames = [toFrame(base)];
  if (template.float) idleFrames.push(toFrame(PM.gridShift(base, 0, -1)));
  else idleFrames.push(toFrame(PM.gridShift(base, 0, 1)));
  anims.push({ name: "idle", fps: 2, frames: idleFrames });

  // walk — 4 frames
  const walkFrames = [];
  if (template.walk === "steps") {
    // alterna os pés + leve deslocamento de peso para baixo
    walkFrames.push(toFrame(base));
    walkFrames.push(toFrame(PM.gridLiftFoot(PM.gridShift(base, 0, 1), "left")));
    walkFrames.push(toFrame(base));
    walkFrames.push(toFrame(PM.gridLiftFoot(PM.gridShift(base, 0, 1), "right")));
  } else {
    // ondulação/pulo (slime, fantasma…)
    walkFrames.push(toFrame(base));
    walkFrames.push(toFrame(PM.gridShift(base, 0, -1)));
    walkFrames.push(toFrame(base));
    walkFrames.push(toFrame(PM.gridShift(base, 0, -1)));
  }
  anims.push({ name: "walk", fps: 6, frames: walkFrames });

  // attack — 3 frames (agachar, golpear, recuperar)
  if (template.attack) {
    anims.push({
      name: "attack",
      fps: 8,
      frames: [
        toFrame(PM.gridShift(base, 0, 1)),
        toFrame(PM.gridShift(base, 0, -1)),
        toFrame(base)
      ]
    });
  }

  return anims;
};

// ----------------------------------------------------------------------------
// Aplicação de um template ao projeto
// ----------------------------------------------------------------------------
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
  p.animations = PM.buildTemplateAnimations(template, gridSize);

  PM.state.project = p;
  PM.state.animIndex = 0;
  PM.state.frameIndex = 0;
  PM.state.colorIndex = 0;
  PM.refresh();
  PM.toast("Modelo \"" + template.name + "\" carregado (" + p.animations.length + " animações)!");
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
