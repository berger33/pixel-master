// ============================================================================
// Pixel Master — animações e frames
// ============================================================================
window.PM = window.PM || {};

PM.selectAnimation = function (i) {
  PM.state.animIndex = i;
  PM.state.frameIndex = 0;
  PM.refresh();
};

PM.selectFrame = function (i) {
  PM.state.frameIndex = i;
  PM.refreshEditor();
  PM.refreshFrames();
  PM.refreshPreview();
};

// ----------------------------------------------------------------------------
// Manipulação de animações
// ----------------------------------------------------------------------------
PM.addAnimation = function (name) {
  const p = PM.state.project;
  PM.commit(function () {
    p.animations.push(PM.createAnimation(name || ("anim" + (p.animations.length + 1)), 1, p.gridSize));
    PM.state.animIndex = p.animations.length - 1;
    PM.state.frameIndex = 0;
  });
};

PM.renameAnimation = function () {
  const anim = PM.currentAnim();
  const name = prompt("Nome da animação:", anim.name);
  if (name == null || !name.trim()) return;
  PM.commit(function () { anim.name = name.trim(); });
};

PM.deleteAnimation = function () {
  const p = PM.state.project;
  if (p.animations.length <= 1) {
    PM.toast("É preciso manter pelo menos 1 animação.");
    return;
  }
  PM.commit(function () {
    p.animations.splice(PM.state.animIndex, 1);
    PM.normalizeIndices();
    PM.state.frameIndex = 0;
  });
};

PM.setAnimFps = function (fps) {
  const anim = PM.currentAnim();
  PM.commit(function () { anim.fps = Math.max(1, Math.min(30, fps)); });
};

// ----------------------------------------------------------------------------
// Manipulação de frames
// ----------------------------------------------------------------------------
PM.addFrame = function () {
  const anim = PM.currentAnim();
  PM.commit(function () {
    anim.frames.push(PM.createEmptyFrame(PM.state.project.gridSize));
    PM.state.frameIndex = anim.frames.length - 1;
  });
};

PM.duplicateFrame = function () {
  const anim = PM.currentAnim();
  const frame = PM.currentFrame();
  PM.commit(function () {
    const copy = PM.clone(frame);
    anim.frames.splice(PM.state.frameIndex + 1, 0, copy);
    PM.state.frameIndex += 1;
  });
};

PM.deleteFrame = function () {
  const anim = PM.currentAnim();
  if (anim.frames.length <= 1) {
    PM.toast("É preciso manter pelo menos 1 frame por animação.");
    return;
  }
  PM.commit(function () {
    anim.frames.splice(PM.state.frameIndex, 1);
    if (PM.state.frameIndex >= anim.frames.length) PM.state.frameIndex = anim.frames.length - 1;
  });
};

// ----------------------------------------------------------------------------
// Renderização da UI de animações/frames
// ----------------------------------------------------------------------------
PM.refreshFrames = function () {
  const p = PM.state.project;
  const animSelect = document.getElementById("anim-select");
  const fpsInput = document.getElementById("anim-fps");
  const strip = document.getElementById("frames-strip");
  const anim = PM.currentAnim();

  // seletor de animações
  animSelect.innerHTML = "";
  p.animations.forEach(function (a, i) {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = a.name + " (" + a.frames.length + "f)";
    animSelect.appendChild(opt);
  });
  animSelect.value = String(PM.state.animIndex);

  fpsInput.value = anim.fps;

  // miniaturas dos frames
  strip.innerHTML = "";
  anim.frames.forEach(function (frame, i) {
    const thumb = document.createElement("button");
    thumb.className = "frame-thumb" + (i === PM.state.frameIndex ? " active" : "");
    const c = PM.renderFrameToCanvas(frame, p.palette, p.gridSize);
    thumb.appendChild(c);
    const idx = document.createElement("span");
    idx.className = "idx";
    idx.textContent = i + 1;
    thumb.appendChild(idx);
    thumb.addEventListener("click", function () { PM.selectFrame(i); });
    strip.appendChild(thumb);
  });
};
