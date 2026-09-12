// ============================================================================
// Pixel Master — exportação (PNG, sprite sheet e JSON)
// ============================================================================
window.PM = window.PM || {};

PM.EXPORT_SCALE = 4; // multiplicador para manter nitidez dos pixels

// Constrói um canvas com os frames de uma animação lado a lado (resolução nativa)
PM.buildAnimSheet = function (anim, gridSize, palette) {
  const n = anim.frames.length;
  const c = document.createElement("canvas");
  c.width = gridSize * n;
  c.height = gridSize;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  anim.frames.forEach(function (frame, i) {
    const f = PM.renderFrameToCanvas(frame, palette, gridSize);
    ctx.drawImage(f, i * gridSize, 0);
  });
  return c;
};

// Constrói um canvas com todas as animações (uma linha por animação)
PM.buildFullSheet = function (project) {
  const gs = project.gridSize;
  const maxFrames = Math.max.apply(null, project.animations.map(function (a) { return a.frames.length; }));
  const c = document.createElement("canvas");
  c.width = gs * maxFrames;
  c.height = gs * project.animations.length;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  project.animations.forEach(function (anim, row) {
    anim.frames.forEach(function (frame, col) {
      const f = PM.renderFrameToCanvas(frame, project.palette, gs);
      ctx.drawImage(f, col * gs, row * gs);
    });
  });
  return c;
};

// Amplia um canvas por vizinho mais próximo
PM.scaleCanvas = function (canvas, factor) {
  const c = document.createElement("canvas");
  c.width = canvas.width * factor;
  c.height = canvas.height * factor;
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(canvas, 0, 0, c.width, c.height);
  return c;
};

PM.canvasToPngUrl = function (canvas) {
  return canvas.toDataURL("image/png");
};

PM.slugify = function (str) {
  return (str || "personagem")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "personagem";
};

PM.downloadBlob = function (blob, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function () { URL.revokeObjectURL(a.href); }, 1500);
};

PM.canvasToBlob = function (canvas) {
  return new Promise(function (resolve) {
    canvas.toBlob(function (blob) { resolve(blob); }, "image/png");
  });
};

// ----------------------------------------------------------------------------
// Exportações
// ----------------------------------------------------------------------------

// Exporta a animação atual como PNG (sprite sheet horizontal)
PM.exportCurrentPng = function () {
  const p = PM.state.project;
  const anim = PM.currentAnim();
  const native = PM.buildAnimSheet(anim, p.gridSize, p.palette);
  const scaled = PM.scaleCanvas(native, PM.EXPORT_SCALE);
  PM.canvasToBlob(scaled).then(function (blob) {
    PM.downloadBlob(blob, PM.slugify(p.name) + "-" + PM.slugify(anim.name) + ".png");
    PM.toast("PNG de \"" + anim.name + "\" exportado!");
  });
};

// Exporta todas as animações numa única sprite sheet PNG
PM.exportFullSheet = function () {
  const p = PM.state.project;
  const native = PM.buildFullSheet(p);
  const scaled = PM.scaleCanvas(native, PM.EXPORT_SCALE);
  PM.canvasToBlob(scaled).then(function (blob) {
    PM.downloadBlob(blob, PM.slugify(p.name) + "-sheet.png");
    PM.toast("Sprite sheet completo exportado!");
  });
};

// Exporta o projeto inteiro como JSON (com sprites embutidos em base64)
PM.exportJson = function () {
  const p = PM.state.project;

  const payload = {
    format: "pixel-master/v1",
    exportedAt: new Date().toISOString(),
    name: p.name,
    kind: p.kind,
    category: p.category,
    rarity: p.rarity,
    gridSize: p.gridSize,
    palette: p.palette.slice(),
    stats: Object.assign({}, p.stats),
    description: p.description,
    animations: p.animations.map(function (anim) {
      const sheet = PM.scaleCanvas(PM.buildAnimSheet(anim, p.gridSize, p.palette), PM.EXPORT_SCALE);
      return {
        name: anim.name,
        fps: anim.fps,
        frameCount: anim.frames.length,
        spriteSheet: PM.canvasToPngUrl(sheet),
        frames: anim.frames.map(function (f) { return { pixels: f.pixels.slice() }; })
      };
    })
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  PM.downloadBlob(blob, PM.slugify(p.name) + ".json");
  PM.toast("JSON de \"" + p.name + "\" exportado!");
};
