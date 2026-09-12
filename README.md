# Pixel Master 🎨

**Criador de Personagens & Criaturas para o jogo Vandoria.**

Uma aplicação web de arte em pixel art que permite desenhar personagens e criaturas em uma grade de pixels, criar animações (frames), definir atributos de jogo e exportar tudo em formatos prontos para usar no Vandoria.

## ✨ Funcionalidades

- 🖌️ **Editor de pixels** — lápis, borracha, balde (preenchimento), conta-gotas e ferramenta de mover.
- 🎞️ **Animações** — múltiplas animações (idle, andar, atacar…) com frames e FPS configuráveis.
- 🎨 **Paletas** — paletas prontas (Fantasia, Floresta, Fogo, Gelo, Metal, Neon) + cores personalizadas.
- 🧩 **Modelos pré-prontos** — Slime, Fantasma, Cavaleiro, Esqueleto, Dragão e Goblin.
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

## 📅 Painel de commits

| Commit | Descrição |
|--------|-----------|
| `b6db192` | Initial commit |
| `d69eb3c` | feat: estrutura da interface do Pixel Master (HTML/CSS) |
| `95ef115` | feat: núcleo do editor (estado, undo/redo, ferramentas de desenho, paleta) |
| `67b2442` | feat: animações/frames, atributos, templates prontos e preview |
| `93f4182` | feat: exportação (PNG/sheet/JSON), persistência local e orquestração |
| `bea6f3c` | docs: painel de commits no README |
