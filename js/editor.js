// ============================================================================
// Pixel Master — editor de pixels (canvas, ferramentas, zoom)
// ============================================================================
window.PM = window.PM || {};

PM.editor = {
  canvas: null,
  ctx: null,
  drawing: false,
  lastX: -1,
  lastY: -1,
  moveStart: null,
  moveSnapshot: null
};

// ----------------------------------------------------------------------------
// Desenho de um frame num contexto (em escala de células)
// ----------------------------------------------------------------------------
PM.drawFrameToContext = function (ctx, frame, palette, gridSize, cell, alpha, mirror) {
  ctx.save();
  if (alpha != null) ctx.globalAlpha = alpha;
  for (let i = 0; i < frame.pixels.length; i++) {
    const c = frame.pixels[i];
    if (c < 0) continue;
    const x = (i % gridSize) * cell;
    const y = Math.floor(i / gridSize) * cell;
    ctx.fillStyle = palette[c];
    ctx.fillRect(x, y, cell, cell);
    if (mirror) {
      const mx = (gridSize - 1 - (i % gridSize)) * cell;
      ctx.fillRect(mx, y, cell, cell);
    }
  }
  ctx.restore();
};

// Renderiza um frame em um canvas isolado (sem zoom, 1px por célula)
PM.renderFrameToCanvas = function (frame, palette, gridSize) {
  const c = document.createElement("canvas");
  c.width = gridSize;
  c.height = gridSize;
  const ctx = c.getContext("2d");
  for (let i = 0; i < frame.pixels.length; i++) {
    const col = frame.pixels[i];
    if (col < 0) continue;
    ctx.fillStyle = palette[col];
    ctx.fillRect(i % gridSize, Math.floor(i / gridSize), 1, 1);
  }
  return c;
};

// ----------------------------------------------------------------------------
// Renderização do editor
// ----------------------------------------------------------------------------
PM.refreshEditor = function () {
  const canvas = PM.editor.canvas;
  const ctx = PM.editor.ctx;
  const p = PM.state.project;
  const gs = p.gridSize;
  const z = PM.state.zoom;
  const frame = PM.currentFrame();

  canvas.width = gs * z;
  canvas.height = gs * z;
  canvas.style.width = gs * z + "px";
  canvas.style.height = gs * z + "px";
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.imageSmoothingEnabled = false;

  // onion skin — frame anterior
  if (PM.state.onionSkin && frame) {
    const anim = PM.currentAnim();
    const prev = anim.frames[PM.state.frameIndex - 1];
    if (prev) PM.drawFrameToContext(ctx, prev, p.palette, gs, z, 0.25, PM.state.mirrorX);
  }

  // frame atual
  if (frame) {
    PM.drawFrameToContext(ctx, frame, p.palette, gs, z, 1, PM.state.mirrorX);
  }

  // linhas da grade
  if (z >= 6) {
    ctx.strokeStyle = "rgba(0,0,0,0.14)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= gs; i++) {
      ctx.moveTo(i * z + 0.5, 0);
      ctx.lineTo(i * z + 0.5, gs * z);
      ctx.moveTo(0, i * z + 0.5);
      ctx.lineTo(gs * z, i * z + 0.5);
    }
    ctx.stroke();
  }

  // contorno
  ctx.strokeStyle = "rgba(255,255,255,0.25)";
  ctx.strokeRect(0.5, 0.5, gs * z - 1, gs * z - 1);
};

// ----------------------------------------------------------------------------
// Coordenadas do ponteiro -> célula
// ----------------------------------------------------------------------------
PM.cellFromEvent = function (e) {
  const rect = PM.editor.canvas.getBoundingClientRect();
  const x = Math.floor((e.clientX - rect.left) / PM.state.zoom);
  const y = Math.floor((e.clientY - rect.top) / PM.state.zoom);
  return { x, y };
};

PM.inBounds = function (x, y) {
  const gs = PM.state.project.gridSize;
  return x >= 0 && y >= 0 && x < gs && y < gs;
};

// ----------------------------------------------------------------------------
// Operações de célula
// ----------------------------------------------------------------------------
PM.setPixel = function (x, y, color) {
  const p = PM.state.project;
  const gs = p.gridSize;
  const frame = PM.currentFrame();
  const idx = y * gs + x;
  frame.pixels[idx] = color;
  if (PM.state.mirrorX) {
    const mx = gs - 1 - x;
    frame.pixels[y * gs + mx] = color;
  }
};

PM.getPixel = function (x, y) {
  const gs = PM.state.project.gridSize;
  return PM.currentFrame().pixels[y * gs + x];
};

// ----------------------------------------------------------------------------
// Flood fill
// ----------------------------------------------------------------------------
PM.floodFill = function (x, y, newColor) {
  const p = PM.state.project;
  const gs = p.gridSize;
  const frame = PM.currentFrame();
  const target = frame.pixels[y * gs + x];
  if (target === newColor) return;

  const stack = [[x, y]];
  while (stack.length) {
    const [cx, cy] = stack.pop();
    const idx = cy * gs + cx;
    if (cx < 0 || cy < 0 || cx >= gs || cy >= gs) continue;
    if (frame.pixels[idx] !== target) continue;
    frame.pixels[idx] = newColor;
    if (PM.state.mirrorX) frame.pixels[cy * gs + (gs - 1 - cx)] = newColor;
    stack.push([cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]);
  }
};

// ----------------------------------------------------------------------------
// Bresenham (para traços contínuos)
// ----------------------------------------------------------------------------
PM.lineCells = function (x0, y0, x1, y1, fn) {
  let dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  let x = x0, y = y0;
  for (;;) {
    fn(x, y);
    if (x === x1 && y === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x += sx; }
    if (e2 < dx) { err += dx; y += sy; }
  }
};

// ----------------------------------------------------------------------------
// Aplicação de uma ferramenta num ponto
// ----------------------------------------------------------------------------
PM.applyTool = function (x, y) {
  if (!PM.inBounds(x, y)) return;
  const tool = PM.state.tool;
  const frame = PM.currentFrame();

  if (tool === "pencil") PM.setPixel(x, y, PM.state.colorIndex);
  else if (tool === "eraser") PM.setPixel(x, y, -1);
  else if (tool === "eyedropper") {
    const c = PM.getPixel(x, y);
    if (c >= 0) PM.setColor(c);
  }
};

// ----------------------------------------------------------------------------
// Eventos de ponteiro
// ----------------------------------------------------------------------------
PM.editor.onPointerDown = function (e) {
  e.preventDefault();
  const { x, y } = PM.cellFromEvent(e);
  PM.editor.drawing = true;
  PM.editor.lastX = x;
  PM.editor.lastY = y;

  if (PM.state.tool === "fill") {
    if (PM.inBounds(x, y)) {
      PM.commit(function () { PM.floodFill(x, y, PM.state.colorIndex); });
    }
    return;
  }

  if (PM.state.tool === "move") {
    PM.editor.moveStart = { x, y };
    PM.editor.moveSnapshot = PM.currentFrame().pixels.slice();
    PM.pushUndo();
    return;
  }

  // pencil / eraser / eyedropper
  PM.pushUndo();
  PM.applyTool(x, y);
  PM.refreshEditor();
  PM.refreshFrames();
  PM.editor.canvas.setPointerCapture(e.pointerId);
};

PM.editor.onPointerMove = function (e) {
  if (!PM.editor.drawing) return;
  const { x, y } = PM.cellFromEvent(e);

  if (PM.state.tool === "move" && PM.editor.moveStart) {
    const dx = x - PM.editor.moveStart.x;
    const dy = y - PM.editor.moveStart.y;
    const gs = PM.state.project.gridSize;
    const frame = PM.currentFrame();
    const snap = PM.editor.moveSnapshot;
    const out = new Array(gs * gs).fill(-1);
    for (let i = 0; i < snap.length; i++) {
      if (snap[i] < 0) continue;
      const sx = i % gs, sy = Math.floor(i / gs);
      const nx = sx + dx, ny = sy + dy;
      if (nx < 0 || ny < 0 || nx >= gs || ny >= gs) continue;
      out[ny * gs + nx] = snap[i];
    }
    frame.pixels = out;
    PM.refreshEditor();
    PM.refreshFrames();
    return;
  }

  if (x === PM.editor.lastX && y === PM.editor.lastY) return;
  PM.lineCells(PM.editor.lastX, PM.editor.lastY, x, y, function (cx, cy) {
    PM.applyTool(cx, cy);
  });
  PM.editor.lastX = x;
  PM.editor.lastY = y;
  PM.refreshEditor();
  PM.refreshFrames();
};

PM.editor.onPointerUp = function () {
  if (!PM.editor.drawing) return;
  PM.editor.drawing = false;
  PM.editor.lastX = -1;
  PM.editor.lastY = -1;
  PM.editor.moveStart = null;
  PM.editor.moveSnapshot = null;
};

// ----------------------------------------------------------------------------
// Ações utilitárias do frame
// ----------------------------------------------------------------------------
PM.clearFrame = function () {
  const frame = PM.currentFrame();
  PM.commit(function () {
    frame.pixels = new Array(frame.pixels.length).fill(-1);
  });
};

PM.flipFrame = function (horizontal) {
  const p = PM.state.project;
  const gs = p.gridSize;
  const frame = PM.currentFrame();
  PM.commit(function () {
    const src = frame.pixels.slice();
    const out = new Array(gs * gs).fill(-1);
    for (let i = 0; i < src.length; i++) {
      if (src[i] < 0) continue;
      const x = i % gs, y = Math.floor(i / gs);
      const nx = horizontal ? gs - 1 - x : x;
      const ny = horizontal ? y : gs - 1 - y;
      out[ny * gs + nx] = src[i];
    }
    frame.pixels = out;
  });
};

// ----------------------------------------------------------------------------
// Zoom
// ----------------------------------------------------------------------------
PM.setZoom = function (z) {
  PM.state.zoom = Math.max(4, Math.min(64, z));
  const label = document.getElementById("zoom-label");
  if (label) label.textContent = Math.round((PM.state.zoom / PM.state.project.gridSize) * 100) + "%";
  PM.refreshEditor();
};

PM.zoomIn = function () { PM.setZoom(PM.state.zoom + 2); };
PM.zoomOut = function () { PM.setZoom(PM.state.zoom - 2); };

// ----------------------------------------------------------------------------
// Estado visual das ferramentas
// ----------------------------------------------------------------------------
PM.refreshTools = function () {
  document.querySelectorAll(".tool").forEach(function (b) {
    b.classList.toggle("active", b.dataset.tool === PM.state.tool);
  });
  document.getElementById("mirror-x").checked = PM.state.mirrorX;
  document.getElementById("onion-skin").checked = PM.state.onionSkin;
};
