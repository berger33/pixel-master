// ============================================================================
// Pixel Master — paleta de cores
// ============================================================================
window.PM = window.PM || {};

PM.PALETTE_PRESETS = {
  "Fantasia (padrão)": [
    "#000000", "#ffffff", "#8b8b8b", "#d9d9d9",
    "#7a3b2e", "#c0392b", "#e67e22", "#f1c40f",
    "#27ae60", "#2ecc71", "#16a085", "#2980b9",
    "#3498db", "#8e44ad", "#9b59b6", "#ecf0f1"
  ],
  "Floresta": [
    "#0b1f12", "#1d3b26", "#2e5c38", "#4a7c4f",
    "#6a9e5f", "#8fbf6b", "#c4e08a", "#6b4a2b",
    "#8a5a33", "#3b2a1a", "#d9b380", "#f1e0c6",
    "#7a8b3a", "#a3b84f", "#ffffff", "#000000"
  ],
  "Fogo & Lava": [
    "#1a0a0a", "#3a1212", "#6b1a1a", "#9c2a1a",
    "#c93c1a", "#e8541a", "#f47a2a", "#f7a53a",
    "#fbd45a", "#fff3a0", "#7a2a0a", "#2a0a0a",
    "#ffffff", "#000000", "#4a0f0f", "#a34a1a"
  ],
  "Gelo & Água": [
    "#0a1420", "#12283a", "#1c3d5c", "#2a5f8a",
    "#3f86b8", "#6fb8e0", "#a8dcf0", "#e0f6ff",
    "#ffffff", "#8aa8c8", "#4a6a8a", "#0a0a18",
    "#12204a", "#1a2f6b", "#b8d4e8", "#d8e8f0"
  ],
  "Metal & Robô": [
    "#0a0a0c", "#1c1c22", "#2e2e38", "#4a4a58",
    "#6b6b7a", "#8a8a9c", "#b8b8c8", "#e0e0ec",
    "#8a5a1a", "#c8a23a", "#3a6bd8", "#5a9cf0",
    "#ffffff", "#000000", "#7a1a1a", "#2ae8b8"
  ],
  "Neon": [
    "#05030a", "#120a2a", "#2a0a5a", "#4a1a9c",
    "#7a2ae8", "#b84af0", "#f05af0", "#ff7ae0",
    "#2af0e0", "#3af0a0", "#a0f040", "#f0f040",
    "#f0a020", "#f04040", "#ffffff", "#000000"
  ]
};

// Conversão hex -> rgba string para desenho
PM.hexToRgb = function (hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

PM.colorAt = function (index) {
  const p = PM.state.project;
  return p.palette[index] || "#000000";
};

PM.setColor = function (index) {
  PM.state.colorIndex = index;
  PM.refreshPalette();
};

PM.addColor = function (hex) {
  const p = PM.state.project;
  if (p.palette.includes(hex.toLowerCase())) {
    PM.setColor(p.palette.indexOf(hex.toLowerCase()));
    return;
  }
  PM.commit(function () {
    p.palette.push(hex.toLowerCase());
    PM.state.colorIndex = p.palette.length - 1;
  });
};

PM.removeColor = function (index) {
  const p = PM.state.project;
  if (p.palette.length <= 1) {
    PM.toast("A paleta precisa de pelo menos 1 cor.");
    return;
  }
  PM.commit(function () {
    // remove a cor e reindexa os pixels que a usavam para transparente (-1)
    const removed = index;
    p.palette.splice(removed, 1);
    p.animations.forEach(function (anim) {
      anim.frames.forEach(function (frame) {
        for (let i = 0; i < frame.pixels.length; i++) {
          if (frame.pixels[i] === removed) frame.pixels[i] = -1;
          else if (frame.pixels[i] > removed) frame.pixels[i] -= 1;
        }
      });
    });
    if (PM.state.colorIndex >= p.palette.length) PM.state.colorIndex = p.palette.length - 1;
    if (PM.state.colorIndex === removed) PM.state.colorIndex = Math.max(0, removed - 1);
  });
};

// ----------------------------------------------------------------------------
// Renderização da UI de paleta
// ----------------------------------------------------------------------------
PM.refreshPalette = function () {
  const preset = document.getElementById("preset-palette");
  const swatches = document.getElementById("swatches");
  const activeSwatch = document.getElementById("active-swatch");
  const activeHex = document.getElementById("active-color-hex");
  const p = PM.state.project;

  // preenche o seletor de paletas prontas (apenas 1ª vez)
  if (!preset.options.length) {
    Object.keys(PM.PALETTE_PRESETS).forEach(function (name) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      preset.appendChild(opt);
    });
  }

  swatches.innerHTML = "";
  p.palette.forEach(function (hex, i) {
    const b = document.createElement("button");
    b.className = "swatch" + (i === PM.state.colorIndex ? " active" : "");
    b.style.background = hex;
    b.title = hex;
    b.addEventListener("click", function () { PM.setColor(i); });
    swatches.appendChild(b);
  });

  activeSwatch.style.background = PM.colorAt(PM.state.colorIndex);
  activeHex.textContent = PM.colorAt(PM.state.colorIndex).toUpperCase();
};
