// ============================================================================
// Pixel Master — inicialização e eventos da interface
// ============================================================================
window.PM = window.PM || {};

// ----------------------------------------------------------------------------
// Toast
// ----------------------------------------------------------------------------
PM.toast = function (msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(PM._toastTimer);
  PM._toastTimer = setTimeout(function () { el.hidden = true; }, 2200);
};

// ----------------------------------------------------------------------------
// Redimensionamento da grade (escala por vizinho mais próximo)
// ----------------------------------------------------------------------------
PM.resizeGrid = function (newSize) {
  const p = PM.state.project;
  const oldSize = p.gridSize;
  if (oldSize === newSize) return;

  if (!confirm("Alterar a grade de " + oldSize + "×" + oldSize + " para " + newSize +
      "×" + newSize + "? O desenho será redimensionado.")) {
    document.getElementById("grid-size").value = String(oldSize);
    return;
  }

  PM.commit(function () {
    p.gridSize = newSize;
    p.animations.forEach(function (anim) {
      anim.frames.forEach(function (frame) {
        const old = frame.pixels.slice();
        const out = new Array(newSize * newSize).fill(-1);
        const scale = newSize / oldSize;
        for (let y = 0; y < newSize; y++) {
          const sy = Math.floor(y / scale);
          for (let x = 0; x < newSize; x++) {
            const sx = Math.floor(x / scale);
            out[y * newSize + x] = old[sy * oldSize + sx];
          }
        }
        frame.pixels = out;
      });
    });
  });
  PM.setZoom(PM.state.zoom);
};

// ----------------------------------------------------------------------------
// Atalhos de teclado
// ----------------------------------------------------------------------------
PM.handleKeydown = function (e) {
  if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT")) {
    return;
  }
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && e.key.toLowerCase() === "z") {
    e.preventDefault();
    if (e.shiftKey) PM.redo(); else PM.undo();
    return;
  }
  if (ctrl && e.key.toLowerCase() === "y") {
    e.preventDefault();
    PM.redo();
    return;
  }
  if (ctrl && e.key.toLowerCase() === "s") {
    e.preventDefault();
    PM.autosave();
    PM.toast("Projeto salvo (autosave).");
    return;
  }
  const k = e.key.toLowerCase();
  const toolMap = { b: "pencil", e: "eraser", f: "fill", i: "eyedropper", m: "move" };
  if (toolMap[k]) {
    PM.state.tool = toolMap[k];
    PM.refreshTools();
  }
};

// ----------------------------------------------------------------------------
// Inicialização
// ----------------------------------------------------------------------------
PM.init = function () {
  PM.editor.canvas = document.getElementById("editor-canvas");
  PM.editor.ctx = PM.editor.canvas.getContext("2d");
  PM.preview.canvas = document.getElementById("preview-canvas");
  PM.preview.ctx = PM.preview.canvas.getContext("2d");

  // restaura autosave ou cria projeto novo
  const saved = PM.restoreAutosave();
  if (saved) {
    PM.state.project = saved;
    PM.state.animIndex = 0;
    PM.state.frameIndex = 0;
    PM.normalizeIndices();
  } else {
    PM.resetState(32, PM.DEFAULT_PALETTE);
  }

  // ---- ferramentas ----
  document.querySelectorAll(".tool").forEach(function (b) {
    b.addEventListener("click", function () {
      PM.state.tool = b.dataset.tool;
      PM.refreshTools();
    });
  });

  // ---- canvas ----
  PM.editor.canvas.addEventListener("pointerdown", PM.editor.onPointerDown);
  PM.editor.canvas.addEventListener("pointermove", PM.editor.onPointerMove);
  PM.editor.canvas.addEventListener("pointerup", PM.editor.onPointerUp);
  PM.editor.canvas.addEventListener("pointerleave", PM.editor.onPointerUp);
  PM.editor.canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });

  document.getElementById("canvas-wrap").addEventListener("wheel", function (e) {
    e.preventDefault();
    if (e.deltaY < 0) PM.zoomIn(); else PM.zoomOut();
  }, { passive: false });

  // ---- botões gerais ----
  document.getElementById("btn-undo").addEventListener("click", PM.undo);
  document.getElementById("btn-redo").addEventListener("click", PM.redo);
  document.getElementById("btn-zoom-in").addEventListener("click", PM.zoomIn);
  document.getElementById("btn-zoom-out").addEventListener("click", PM.zoomOut);
  document.getElementById("btn-new").addEventListener("click", function () {
    if (confirm("Criar um novo projeto? O trabalho atual será perdido (salve antes).")) {
      PM.resetState(32, PM.DEFAULT_PALETTE);
      PM.setZoom(10);
      PM.refresh();
    }
  });
  document.getElementById("btn-save").addEventListener("click", PM.saveProject);
  document.getElementById("btn-load").addEventListener("click", PM.openProject);

  // ---- exportações ----
  document.getElementById("btn-export-png").addEventListener("click", PM.exportCurrentPng);
  document.getElementById("btn-export-sheet").addEventListener("click", PM.exportFullSheet);
  document.getElementById("btn-export-json").addEventListener("click", PM.exportJson);

  // ---- frame ----
  document.getElementById("btn-clear-frame").addEventListener("click", PM.clearFrame);
  document.getElementById("btn-flip-h").addEventListener("click", function () { PM.flipFrame(true); });
  document.getElementById("btn-flip-v").addEventListener("click", function () { PM.flipFrame(false); });
  document.getElementById("btn-add-frame").addEventListener("click", PM.addFrame);
  document.getElementById("btn-dup-frame").addEventListener("click", PM.duplicateFrame);
  document.getElementById("btn-del-frame").addEventListener("click", PM.deleteFrame);

  // ---- animações ----
  document.getElementById("btn-add-anim").addEventListener("click", function () { PM.addAnimation(); });
  document.getElementById("btn-rename-anim").addEventListener("click", PM.renameAnimation);
  document.getElementById("btn-del-anim").addEventListener("click", PM.deleteAnimation);
  document.getElementById("anim-select").addEventListener("change", function () {
    PM.selectAnimation(parseInt(this.value, 10));
  });
  document.getElementById("anim-fps").addEventListener("change", function () {
    PM.setAnimFps(parseInt(this.value, 10));
  });

  // ---- grade ----
  document.getElementById("grid-size").addEventListener("change", function () {
    PM.resizeGrid(parseInt(this.value, 10));
  });

  // ---- paleta ----
  document.getElementById("preset-palette").addEventListener("change", function () {
    const preset = PM.PALETTE_PRESETS[this.value];
    if (preset) {
      PM.commit(function () {
        PM.state.project.palette = preset.slice();
        PM.state.colorIndex = 0;
      });
    }
  });
  document.getElementById("btn-add-color").addEventListener("click", function () {
    PM.addColor(document.getElementById("custom-color").value);
  });
  document.getElementById("btn-del-color").addEventListener("click", function () {
    PM.removeColor(PM.state.colorIndex);
  });
  document.getElementById("custom-color").addEventListener("input", function () {
    const swatch = document.getElementById("active-swatch");
    swatch.style.background = this.value;
    document.getElementById("active-color-hex").textContent = this.value.toUpperCase();
  });

  // ---- opções ----
  document.getElementById("mirror-x").addEventListener("change", function () {
    PM.state.mirrorX = this.checked;
  });
  document.getElementById("onion-skin").addEventListener("change", function () {
    PM.state.onionSkin = this.checked;
    PM.refreshEditor();
  });

  // ---- abas ----
  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("active"); });
      document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("active"); });
      tab.classList.add("active");
      document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
    });
  });

  // ---- preview ----
  document.getElementById("btn-play").addEventListener("click", PM.playPreview);
  document.getElementById("btn-stop").addEventListener("click", PM.stopPreview);

  // ---- importação de arquivo ----
  const fileInput = document.getElementById("file-input");
  document.getElementById("btn-import").addEventListener("click", function () {
    fileInput.click();
  });
  fileInput.addEventListener("change", function () {
    if (fileInput.files.length) PM.importProject(fileInput.files[0]);
    fileInput.value = "";
  });

  // ---- global ----
  document.addEventListener("keydown", PM.handleKeydown);
  window.addEventListener("beforeunload", function () { PM.autosave(); });

  PM.initStatsBindings();
  PM.refreshTemplates();
  PM.setZoom(10);
  PM.refresh();
};

// autosave periódico
setInterval(PM.autosave, 15000);

document.addEventListener("DOMContentLoaded", PM.init);
