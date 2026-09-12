# 🎮 Pixel Master

**Forjador de personagens e criaturas em pixel art para o jogo Vandoria.**

O Pixel Master cria sprites jogáveis de duas formas — **geração procedural
determinística** e **conversão de renders de IA** — e os entrega prontos para o
motor do jogo: atlas de animação (idle / walk em 4 direções / death), manifesto
de integração e **ficha funcional** (stats, habilidades, recompensas) para o
backend de combate.

```
   foto de IA (alta res.)          seed + parâmetros
          │                              │
          ▼                              ▼
  ┌────────────────┐            ┌────────────────┐
  │ recorte +      │            │ espécies ×     │
  │ pixelização +  │            │ arquétipos ×   │
  │ 4 direções     │            │ equipamento    │
  └───────┬────────┘            └───────┬────────┘
          └──────────┬──────────────────┘
                     ▼
              rig de camadas (pivôs + tags)
                     ▼
        animação: idle · walk(4 dir) · death
                     ▼
   atlas PNG + manifesto JSON + atlas TexturePacker/Sparrow
   + preview.gif + card.json  →  pacote .zip por personagem
```

---

## ✨ O que ele faz

### 1. Geração procedural determinística
* **28 espécies** (humanos, elfos, anões, orcs, demônios, dragões, lobos,
  aranhas, serpentes, slimes, golens, fantasmas...) em **7 arquétipos
  anatômicos** (biped, brute, quadruped, arachnid, serpent, flyer, blob);
* equipamentos: 14 armas, escudos/tochas/livros, capacetes/capuzes/coroas,
  chifres, caudas, asas, capas, barba, 8 penteados;
* paletas em rampas com sombreamento de 3 tons, contorno derivado da própria
  paleta e sombra de contato;
* **mesmo seed ⇒ mesmo sprite, byte a byte** (testado).

### 2. Conversão de foto de IA → personagem jogável
* remoção de fundo automática (inclusive regiões *encerradas*, como o vão de um
  arco), limpeza de specks e fechamento de buracos;
* **pixelização por cobertura/dominância** (pixel art nítido, não downscale
  borrado) + quantização de paleta por median-cut + contorno coeso;
* detecção da vista de origem (frente / lado / costas);
* síntese das **4 direções** (laterais em 3/4 comprimido, costas sem rosto);
* segmentação em **rig animável** (cabeça, tronco, braços, pernas) — o mesmo
  animador dos personagens procedurais.

### 3. Animação
`idle`, `walk` nas 4 direções (`down/left/right/up`) e `death` (colapso estilo
Tibia: cambaleia → cai → assenta → dessatura), todas por pivôs e tags.

### 4. Exportação pronta para o Vandoria
`spritesheet.png` (grade uniforme) · `manifest.json` (índices de animação) ·
`atlas_phaser.json` / `atlas_phaser_array.json` (TexturePacker) ·
`atlas_sparrow.xml` · `atlas_aseprite.json` · `preview.gif` · `frames/*.png` ·
`card.json` (ficha funcional) · `README.txt` — tudo num `.zip`.

### 5. Editor web
Pré-visualização animada em canvas (pixel-perfect), controles de espécie /
seed / proporções / equipamento / paleta, importação por arrastar-e-soltar,
ficha de stats ao vivo, biblioteca de personagens e exportação em 1 clique.

---

## 🚀 Rodando localmente

Requisitos: Python 3.11+, Node 20+.

```bash
make install          # venv + deps backend + npm install frontend

# terminal 1 — API
make run-api          # http://localhost:8000  (Swagger em /docs)

# terminal 2 — editor web
make run-web          # http://localhost:5173
```

Ou com Docker:

```bash
docker compose up --build
# editor em http://localhost:5173 · api em http://localhost:8000/docs
```

### Testes e lint

```bash
make test             # 87 testes (motor, geradores, animador, pipeline de IA, API)
make lint             # ruff (backend) + tsc (frontend)
```

---

## 🔌 Integrando no Vandoria (Phaser 3)

```js
import { loadPixelMasterCharacter, spawnCharacter, loadCharacterCard }
  from './integration/vandoria/pixelmaster-loader.js';

await loadPixelMasterCharacter(scene, 'hero', '/api/characters/<id>');
const hero = spawnCharacter(scene, 'hero', 400, 300);
hero.walk('left');
hero.die();

const card = await loadCharacterCard('/api/characters/<id>');
// card.stats / card.abilities alimentam o sistema de combate
```

Detalhes do contrato de exportação e da grade: [`integration/vandoria/README.md`](integration/vandoria/README.md).

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/LEVANTAMENTO.md`](docs/LEVANTAMENTO.md) | Levantamento de estado: o que foi encontrado, o que foi entregue e o que resta |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | Decisões de arquitetura, mapa de módulos, limitações conhecidas |
| [`docs/API.md`](docs/API.md) | Referência completa da API HTTP |
| [`integration/vandoria/README.md`](integration/vandoria/README.md) | Contrato de exportação + guia de integração |

---

## 🗂️ Estrutura

```
backend/
  app/
    pixel/        canvas RGBA, paletas/rampas, empacotador de atlas
    generator/
      procedural/   humanoides + criaturas (7 arquétipos)
      from_image/   pipeline foto-de-IA → rig
      rig.py        camadas + pivôs + tags (contrato de animação)
    animation/    animador idle/walk/death
    export/       montagem do pacote .zip
    domain/       modelos, espécies, habilidades, stats
    services/     orquestração + persistência
    api/          rotas FastAPI
    db/           SQLAlchemy Core (SQLite; Postgres via DATABASE_URL)
  tests/          87 testes (inclui fixture de render de IA)
frontend/         editor React + Vite (TS)
integration/      helper Phaser 3 para o Vandoria
docs/             levantamento, arquitetura, API
```

## ⚙️ Configuração (variáveis de ambiente)

Prefixo `PIXELMASTER_`: `DATABASE_URL`, `STORAGE_DIR`, `UPLOAD_DIR`,
`SPRITE_WIDTH/HEIGHT`, `MAX_UPLOAD_BYTES`, `CORS_ORIGINS`, `DEBUG`.

## 📝 Licença

Uso interno do projeto Vandoria.
