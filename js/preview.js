// ============================================================================
// Pixel Master — pré-visualização animada
// ============================================================================
window.PM = window.PM || {};

PM.preview = {
  canvas: null,
  ctx: null,
  timer: null,
  frame: 0
};

PM.refreshPreview = function () {
  const canvas = PM.preview.canvas;
  const ctx = PM.preview.ctx;
  const p = PM.state.project;
  const anim = PM.currentAnim();
  const gs = p.gridSize;

  const SCALE = 5;
  canvas.width = gs * SCALE;
  canvas.height = gs * SCALE;
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (anim.frames.length) {
    PM.drawFrameToContext(ctx, anim.frames[PM.preview.frame % anim.frames.length], p.palette, gs, SCALE);
  }
};

PM.previewTick = function () {
  const anim = PM.currentAnim();
  if (anim && anim.frames.length) {
    PM.preview.frame = (PM.preview.frame + 1) % anim.frames.length;
  }
  PM.refreshPreview();
};

PM.playPreview = function () {
  if (PM.preview.timer) return;
  const anim = PM.currentAnim();
  const fps = anim ? anim.fps : 4;
  PM.preview.timer = setInterval(PM.previewTick, Math.max(60, Math.round(1000 / fps)));
};

PM.stopPreview = function () {
  if (PM.preview.timer) {
    clearInterval(PM.preview.timer);
    PM.preview.timer = null;
  }
};
