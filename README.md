# Pixel Master 🎨

**Criador de Personagens & Criaturas para o jogo Vandoria.**

Uma aplicação web de arte em pixel art que permite desenhar personagens e criaturas em uma grade de pixels, criar animações (frames), definir atributos de jogo e exportar tudo em formatos prontos para usar no Vandoria.

## ✨ Funcionalidades

- 🖌️ **Editor de pixels** — lápis, borracha, balde (preenchimento), conta-gotas e ferramenta de mover.
- 🎞️ **Animações** — múltiplas animações (idle, andar, atacar…) com frames e FPS configuráveis.
- 🎨 **Paletas** — paletas prontas (Fantasia, Floresta, Fogo, Gelo, Metal, Neon) + cores personalizadas.
- 🧩 **Modelos pré-prontos** — Slime, Fantasma, Cavaleiro, Esqueleto, Dragão, Goblin, Golem de Pedra, Zumbi e Aranha — cada um já com **animações consistentes** de idle, andar e atacar (derivadas do sprite base).
- 📊 **Atributos** — nome, tipo, categoria, raridade, HP, ataque, defesa, velocidade, magia e descrição.
- 🖼️ **Exportação** — PNG (sprite sheet), sprite sheet completo e JSON (com sprites embutidos).
- 💾 **Salvar/Abrir** — projetos salvos no navegador + importação/exportação de arquivo JSON.
- ⏪ Undo/redo, zoom, espelhamento (simetria), onion skin e pré-visualização animada.

## 🚀 Como usar

Abra o `index.html` em um navegador moderno, ou sirva a pasta com um servidor local:

```bash
python3 -m http.server 8000
# e acesse http://localhost:8000
```

## 🕹️ Atalhos

| Tecla | Ação |
|-------|------|
| `B` / `E` / `F` / `I` / `M` | Lápis / Borracha / Balde / Conta-gotas / Mover |
| `Ctrl+Z` / `Ctrl+Y` | Desfazer / Refazer |
| `Ctrl+S` | Salvar (autosave) |

## 📦 Formatos de exportação

- **PNG**: sprite sheet horizontal da animação atual (ampliado 4× para nitidez).
- **Sprite Sheet**: todas as animações em uma única imagem (uma linha por animação).
- **JSON**: projeto completo com paleta, stats, frames e sprites em base64.

## 🧩 Animações consistentes dos modelos

Ao carregar um modelo, o Pixel Master gera automaticamente as animações **a partir do próprio sprite base**, garantindo que todas as poses mantenham a identidade visual do personagem:

| Animação | Frames | Como é gerada |
|----------|--------|---------------|
| `idle` | 2 | respiração (corpo desce 1px) ou flutuação (fantasmas sobem 1px) |
| `walk` | 4 | alternância dos pés (modelos bípedes) ou ondulação/pulo (slime, fantasma) |
| `attack` | 3 | agacha → golpeia (sobe 1px) → recupera |

## 🏛️ Motor de personagens estilo Tibia (novo)

Além do editor de pixel art, o projeto agora inclui um **motor de criação no estilo Tibia** (`js/tibia.js`), baseado na análise empírica dos outfits reais (ver `docs/analise-outfits-reais.md`):

- **Projeção oblíqua top-down (~135°)** — a "inclinação" característica do Tibia.
- **4 direções** (norte/east/south/west) × **4 frames de caminhada** (parado → passo → parado → passo) = 16 sprites por personagem.
- **Contorno escuro** na silhueta (auto-calculado).
- **Sistema de cor por partes**: cabeça / corpo / pernas / pés, com **máscara de tint** — troca de cor sem redesenhar.
- Canvas nativo **32×32** + export **64×64** (upscale 2×), como os outfits modernos do Tibia.

### Gerar um personagem

```bash
node tools/generate-tibia-character.js                         # guerreiro (padrão)
node tools/generate-tibia-character.js --name Mage \
  --body "#2a6ad0" --legs "#c8a02a" --hair "#3a2a50"            # recolorir
node tools/generate-tibia-character.js --ascii                 # visualizar 1 frame em texto
```

A saída vai para `examples/tibia/<nome>/`:

- `32/` e `64/` — sprites nomeados `{direção}_{montaria}_{addon}_{frame}.png` (padrão Tibia).
- `mask/` — máscaras de cor (🔴 cabeça · 🟡 corpo · 🟢 pernas · 🔵 pés).
- `overview.png` — grade 4 direções × 4 frames.
- `recolor-demo.png` — prova do sistema de tint (recolorido sem redesenhar).
- `index.html` — galeria para visualizar tudo no navegador.

Exemplos já gerados: `examples/tibia/warrior/` (vermelho) e `examples/tibia/mage/` (azul/dourado).

## 📁 Exemplos prontos (`examples/`)

Sprites e JSON já gerados para os 9 modelos, prontos para usar no Vandoria:

- `examples/sprites/<modelo>-idle.png`, `-walk.png`, `-attack.png` — sprite sheets animadas.
- `examples/json/<modelo>.json` — dados completos (stats, paleta, frames + sprites em base64).
- `examples/overview.png` — imagem-resumo com todos os modelos.

Para regenerar (após editar os templates em `js/templates.js`):

```bash
node tools/generate-examples.js
```

## 📅 Painel de commits

| Commit | Descrição |
|--------|-----------|
| `b6db192` | Initial commit |
| `d69eb3c` | feat: estrutura da interface do Pixel Master (HTML/CSS) |
| `95ef115` | feat: núcleo do editor (estado, undo/redo, ferramentas de desenho, paleta) |
| `67b2442` | feat: animações/frames, atributos, templates prontos e preview |
| `93f4182` | feat: exportação (PNG/sheet/JSON), persistência local e orquestração |
| `bea6f3c` | docs: painel de commits no README |
| `dd18c59` | docs: corrige hash no painel de commits |
| `456a40b` | feat: animações consistentes (idle/walk/attack) + 3 novos modelos (Golem, Zumbi, Aranha) |
| `e1ab18f` | feat: gerador de sprites/JSON de exemplo + slugify com acentos |
| `cd8c6c7` | assets: sprites PNG e JSON de exemplo para os 9 modelos |
| `2f38c9d` | docs: atualiza painel de commits e documenta exemplos |
| `a9dcaf8` | docs: análise comparativa do estilo Tibia vs Pixel Master |
| `bdf1225` | docs: análise empírica dos outfits reais do Tibia (dimensões, direções, ciclo de caminhada, tint por partes) |
| `8585d55` | docs: registra análise empírica no painel de commits |
| `63cd7dd` | feat: motor de personagens estilo Tibia (4 direções × 4 frames, contorno, cor por partes) |
| `770fe31` | feat: gerador CLI de personagem Tibia (PNG 32/64, máscara de cor, recolor) |
| `992adad` | assets: personagens de exemplo estilo Tibia (Warrior e Mage, 4 direções × 4 frames) |
