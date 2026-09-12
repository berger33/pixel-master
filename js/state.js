// ============================================================================
// Pixel Master — estado global, modelo de dados e undo/redo
// ============================================================================
window.PM = window.PM || {};

PM.GRID_SIZES = [16, 32, 48, 64];
PM.MAX_UNDO = 60;

PM.DEFAULT_PALETTE = [
  "#000000", "#ffffff", "#8b8b8b", "#d9d9d9",
  "#7a3b2e", "#c0392b", "#e67e22", "#f1c40f",
  "#27ae60", "#2ecc71", "#16a085", "#2980b9",
  "#3498db", "#8e44ad", "#9b59b6", "#ecf0f1"
];

// ----------------------------------------------------------------------------
// Fábricas de dados
// ----------------------------------------------------------------------------
PM.createEmptyFrame = function (gridSize) {
  return { pixels: new Array(gridSize * gridSize).fill(-1) };
};

PM.createAnimation = function (name, frameCount, gridSize, fps) {
  const frames = [];
  for (let i = 0; i < frameCount; i++) frames.push(PM.createEmptyFrame(gridSize));
  return { name, fps: fps || 4, frames };
};

PM.createProject = function (gridSize, palette) {
  gridSize = gridSize || 32;
  palette = palette ? palette.slice() : PM.DEFAULT_PALETTE.slice();
  return {
    name: "Novo Personagem",
    kind: "character",
    category: "humanoid",
    rarity: "common",
    gridSize: gridSize,
    palette: palette,
    animations: [PM.createAnimation("idle", 1, gridSize)],
    stats: { hp: 100, attack: 10, defense: 5, speed: 5, magic: 0 },
    description: ""
  };
};

PM.clone = function (obj) {
  return JSON.parse(JSON.stringify(obj));
};

// ----------------------------------------------------------------------------
// Estado da sessão de edição
// ----------------------------------------------------------------------------
PM.state = {
  project: null,
  animIndex: 0,
  frameIndex: 0,
  tool: "pencil",
  colorIndex: 0,
  mirrorX: false,
  onionSkin: false,
  zoom: 10,
  undoStack: [],
  redoStack: []
};

PM.resetState = function (gridSize, palette) {
  PM.state.project = PM.createProject(gridSize, palette);
  PM.state.animIndex = 0;
  PM.state.frameIndex = 0;
  PM.state.undoStack = [];
  PM.state.redoStack = [];
};

PM.currentAnim = function () {
  return PM.state.project.animations[PM.state.animIndex];
};

PM.currentFrame = function () {
  const anim = PM.currentAnim();
  if (!anim || !anim.frames.length) return null;
  return anim.frames[PM.state.frameIndex] || anim.frames[0];
};

PM.normalizeIndices = function () {
  const p = PM.state.project;
  if (!p.animations.length) {
    p.animations = [PM.createAnimation("idle", 1, p.gridSize)];
  }
  if (PM.state.animIndex >= p.animations.length) PM.state.animIndex = p.animations.length - 1;
  const anim = PM.currentAnim();
  if (!anim.frames.length) anim.frames = [PM.createEmptyFrame(p.gridSize)];
  if (PM.state.frameIndex >= anim.frames.length) PM.state.frameIndex = anim.frames.length - 1;
};

// ----------------------------------------------------------------------------
// Undo / redo — snapshots do projeto inteiro
// ----------------------------------------------------------------------------
PM.pushUndo = function () {
  PM.state.undoStack.push(PM.clone(PM.state.project));
  if (PM.state.undoStack.length > PM.MAX_UNDO) PM.state.undoStack.shift();
  PM.state.redoStack = [];
};

PM.commit = function (mutator) {
  PM.pushUndo();
  mutator();
  PM.refresh();
};

PM.undo = function () {
  if (!PM.state.undoStack.length) return;
  PM.state.redoStack.push(PM.clone(PM.state.project));
  PM.state.project = PM.state.undoStack.pop();
  PM.normalizeIndices();
  PM.refresh();
};

PM.redo = function () {
  if (!PM.state.redoStack.length) return;
  PM.state.undoStack.push(PM.clone(PM.state.project));
  PM.state.project = PM.state.redoStack.pop();
  PM.normalizeIndices();
  PM.refresh();
};

// ----------------------------------------------------------------------------
// Refresh — chamado após qualquer mudança para redesenhar a UI
// ----------------------------------------------------------------------------
PM.refresh = function () {
  PM.refreshEditor();
  PM.refreshPalette();
  PM.refreshFrames();
  PM.refreshStats();
  PM.refreshPreview();
  PM.refreshTools();
};
