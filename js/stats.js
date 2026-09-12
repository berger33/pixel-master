// ============================================================================
// Pixel Master — atributos do personagem/criatura
// ============================================================================
window.PM = window.PM || {};

PM.refreshStats = function () {
  const p = PM.state.project;
  document.getElementById("stat-name").value = p.name;
  document.getElementById("stat-kind").value = p.kind;
  document.getElementById("stat-category").value = p.category;
  document.getElementById("stat-rarity").value = p.rarity;
  document.getElementById("stat-hp").value = p.stats.hp;
  document.getElementById("stat-atk").value = p.stats.attack;
  document.getElementById("stat-def").value = p.stats.defense;
  document.getElementById("stat-spd").value = p.stats.speed;
  document.getElementById("stat-mag").value = p.stats.magic;
  document.getElementById("stat-desc").value = p.description;
};

// Associa um campo de texto a um mutador (commit ao sair do campo)
PM.bindStat = function (id, getter, setter) {
  const el = document.getElementById(id);
  el.addEventListener("change", function () {
    PM.commit(function () { setter(getter()); });
  });
};

PM.initStatsBindings = function () {
  PM.bindStat("stat-name",
    function () { return document.getElementById("stat-name").value.trim() || "Sem nome"; },
    function (v) { PM.state.project.name = v; });

  PM.bindStat("stat-kind",
    function () { return document.getElementById("stat-kind").value; },
    function (v) { PM.state.project.kind = v; });

  PM.bindStat("stat-category",
    function () { return document.getElementById("stat-category").value.trim(); },
    function (v) { PM.state.project.category = v; });

  PM.bindStat("stat-rarity",
    function () { return document.getElementById("stat-rarity").value; },
    function (v) { PM.state.project.rarity = v; });

  PM.bindStat("stat-hp",
    function () { return parseInt(document.getElementById("stat-hp").value, 10) || 0; },
    function (v) { PM.state.project.stats.hp = v; });

  PM.bindStat("stat-atk",
    function () { return parseInt(document.getElementById("stat-atk").value, 10) || 0; },
    function (v) { PM.state.project.stats.attack = v; });

  PM.bindStat("stat-def",
    function () { return parseInt(document.getElementById("stat-def").value, 10) || 0; },
    function (v) { PM.state.project.stats.defense = v; });

  PM.bindStat("stat-spd",
    function () { return parseInt(document.getElementById("stat-spd").value, 10) || 0; },
    function (v) { PM.state.project.stats.speed = v; });

  PM.bindStat("stat-mag",
    function () { return parseInt(document.getElementById("stat-mag").value, 10) || 0; },
    function (v) { PM.state.project.stats.magic = v; });

  PM.bindStat("stat-desc",
    function () { return document.getElementById("stat-desc").value; },
    function (v) { PM.state.project.description = v; });
};
