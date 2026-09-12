// ============================================================================
// Pixel Master — persistência local (salvar/abrir projetos no navegador)
// ============================================================================
window.PM = window.PM || {};

PM.STORAGE_KEY = "pixel-master-projects";
PM.AUTOSAVE_KEY = "pixel-master-autosave";

PM.loadProjects = function () {
  try {
    return JSON.parse(localStorage.getItem(PM.STORAGE_KEY)) || {};
  } catch (e) {
    return {};
  }
};

PM.saveProjects = function (map) {
  localStorage.setItem(PM.STORAGE_KEY, JSON.stringify(map));
};

// Salva o projeto atual com um nome
PM.saveProject = function () {
  const p = PM.state.project;
  let name = prompt("Nome do projeto:", p.name);
  if (name == null) return;
  name = name.trim() || p.name;
  p.name = name;
  const map = PM.loadProjects();
  map[name] = PM.clone(p);
  PM.saveProjects(map);
  PM.refreshStats();
  PM.toast("Projeto \"" + name + "\" salvo no navegador.");
};

// Abre um projeto salvo
PM.openProject = function () {
  const map = PM.loadProjects();
  const names = Object.keys(map);
  if (!names.length) {
    PM.toast("Nenhum projeto salvo ainda.");
    return;
  }
  const name = prompt("Projetos salvos:\n" + names.join("\n") + "\n\nDigite o nome para abrir:", names[0]);
  if (name == null) return;
  const data = map[name];
  if (!data) {
    PM.toast("Projeto não encontrado.");
    return;
  }
  PM.loadProjectData(data);
  PM.toast("Projeto \"" + name + "\" carregado.");
};

// Carrega um objeto de projeto (valida estrutura mínima)
PM.loadProjectData = function (data) {
  if (!data || !data.animations || !data.gridSize || !data.palette) {
    PM.toast("Arquivo de projeto inválido.");
    return;
  }
  data.gridSize = Math.max(8, Math.min(128, data.gridSize));
  PM.state.project = data;
  PM.state.animIndex = 0;
  PM.state.frameIndex = 0;
  PM.state.colorIndex = 0;
  PM.state.undoStack = [];
  PM.state.redoStack = [];
  PM.normalizeIndices();
  PM.refresh();
};

// Importa um projeto a partir de arquivo JSON (do export)
PM.importProject = function (file) {
  const reader = new FileReader();
  reader.onload = function () {
    try {
      const data = JSON.parse(reader.result);
      PM.loadProjectData(data);
      PM.toast("Projeto importado com sucesso.");
    } catch (e) {
      PM.toast("Erro ao importar: arquivo JSON inválido.");
    }
  };
  reader.readAsText(file);
};

// Autosave / autorestore
PM.autosave = function () {
  try {
    localStorage.setItem(PM.AUTOSAVE_KEY, JSON.stringify(PM.state.project));
  } catch (e) { /* quota cheia — ignora */ }
};

PM.restoreAutosave = function () {
  try {
    const raw = localStorage.getItem(PM.AUTOSAVE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data && data.animations) return data;
  } catch (e) { /* ignora */ }
  return null;
};
