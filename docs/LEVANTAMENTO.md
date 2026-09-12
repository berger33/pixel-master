# Pixel Master — Levantamento de Estado do Projeto

**Levantamento inicial:** 2026-09-12 (repo vazio)
**Entrega concluída:** 2026-09-12 (branch `arena/01a09333-pixel-master`)
**Repositório:** https://github.com/berger33/pixel-master
**Objetivo do cliente:** entregar o projeto 100% funcional para criar
personagens e criaturas utilizáveis no jogo **Vandoria**.

---

## 1. Ponto de partida (o que foi encontrado)

Inspeção de árvore de arquivos, histórico Git completo, branches, issues, PRs,
releases e busca por "vandoria" na conta:

| Fonte | Resultado no levantamento inicial |
|---|---|
| Arquivos no repo | **1** — `README.md` com apenas o título |
| Commits (todas as branches) | **1** — `b6db192 Initial commit` |
| Issues / PRs / Releases | 0 / 0 / 0 |
| Data de criação do repo | mesmo dia do levantamento |
| Spec / arquitetura / testes / CI | inexistentes |
| Menção a "Vandoria" no GitHub do dono | nenhuma |

**Conclusão do levantamento:** projeto *greenfield* absoluto — **0% entregue**.
Não havia dívida técnica nem contrato pré-existente; todo o escopo precisava
ser construído do zero.

---

## 2. Requisitos fechados com o cliente

| # | Decisão | Escolha |
|---|---|---|
| D1 | Motor do Vandoria | Web (Phaser / PixiJS / JS) → atlas PNG + JSON TexturePacker/Phaser |
| D2 | Estilo/perspectiva | 64×64, 4 direções, RPG clássico (Tibia / PokexGames); idle + walk 4 dir |
| D3 | Geração | **dois modos**: procedural determinístico **e** conversão de foto de IA pronta (o programa recebe o render e o transforma em personagem com idle/walk 4 dir/death) |
| D4 | Stack | Python/FastAPI + React |

---

## 3. O que foi entregue (100% do escopo fechado)

### 3.1 Motor de pixel art (`backend/app/pixel/`)
- [x] `PixelCanvas` RGBA com primitivas (rect, ellipse, line, polygon, cápsulas),
      blend source-over vetorial, recorte de máscara, transforms *nearest*;
- [x] contorno de silhueta, sombra de contato, shade/desaturate/tint;
- [x] rampas e paletas nomeadas (pele, cabelo, tecido, metal, couro, monstro...),
      quantização median-cut, snap de paleta, cor de contorno derivada;
- [x] empacotador de atlas em grade uniforme + formatos TexturePacker
      Hash/Array, Sparrow XML, tags Aseprite e **manifesto com índice linear da
      grade** (o detalhe que faz `load.spritesheet` funcionar de primeira).

### 3.2 Geração procedural (`backend/app/generator/procedural/`)
- [x] 28 espécies em 7 arquétipos (biped, brute, quadruped, arachnid, serpent,
      flyer, blob), cada uma com paletas, equipamentos e balanceamento próprios;
- [x] humanoides com cabelo (8 estilos), barba, 9 coberturas de cabeça,
      14 armas, 5 secundárias, capas, asas, chifres, caudas;
- [x] criaturas: quadrúpedes, aracnídeos de 8 pernas, serpentes, voadores, slimes;
- [x] 4 direções nativas (a direita é espelho exato da esquerda — testado);
- [x] determinismo por seed (xorshift32 isolado + crc32) — bytes idênticos.

### 3.3 Pipeline foto-de-IA → personagem (`backend/app/generator/from_image/`)
- [x] remoção de fundo (alfa, cor sólida ou auto com flood-fill **e** regiões
      encerradas), limpeza de specks/buracos;
- [x] pixelização por cobertura/dominância + quantização + contorno;
- [x] detecção de vista (frente/lado/costas) por simetria da cabeça + contraste
      de olhos;
- [x] síntese das 4 direções (3/4 comprimido nas laterais, costas sem rosto);
- [x] segmentação em **rig animável** com pivôs e tags (o mesmo animador).

### 3.4 Animação (`backend/app/animation/`)
- [x] `idle`, `walk` (4 direções) e `death` por pivôs/tags, compartilhado entre
      procedurais e importados;
- [x] marchas por arquétipo (passo bípede, galga diagonal de quadrúpede,
      ondulação de serpente, batida de asas, squash de slime);
- [x] death com colapso + dessaturação (cadáver), estilo Tibia.

### 3.5 Exportação (`backend/app/export/` + `integration/vandoria/`)
- [x] pacote `.zip`: spritesheet, manifestos, atlas alternativos, preview.gif,
      frames individuais, `card.json` (ficha funcional), README de integração;
- [x] helper Phaser 3 (`pixelmaster-loader.js`) com `loadPixelMasterCharacter`,
      `spawnCharacter` e `loadCharacterCard`;
- [x] **exportação em lote do bestiário** (`POST /api/characters/export-batch`):
      zip único com índice `bestiary.json` (stats + habilidades + caminhos),
      `contact_sheet.png` (grade de poses frontais) e uma pasta por personagem.

### 3.6 API + persistência (`backend/app/api|services|db`)
- [x] FastAPI com geração, importação multipart, CRUD, previews sob demanda
      (pose/strip/sheet/gif/manifest/card), download do zip e export do
      bestiário completo em lote;
- [x] persistência SQLAlchemy Core (SQLite; Postgres via `DATABASE_URL`);
- [x] ficha de stats/habilidades derivada deterministicamente de espécie +
      raridade + nível + seed.

### 3.7 Editor web (`frontend/`)
- [x] React + Vite + TS; preview animado em canvas pixel-perfect lendo o
      manifesto exatamente como o jogo leria;
- [x] painéis procedural / importação de IA / ficha / exportação / biblioteca.

### 3.8 Engenharia
- [x] **90 testes** passando (motor, geradores, animador, pipeline de IA, API);
- [x] **ruff limpo** + **tsc limpo**;
- [x] CI GitHub Actions (backend: pytest+ruff; frontend: typecheck+build);
- [x] Dockerfile + docker-compose + Makefile;
- [x] documentação: levantamento, arquitetura, API, integração.

---

## 4. Métricas da entrega

| Métrica | Valor |
|---|---|
| Testes automatizados | 90 (todos verdes) |
| Espécies no catálogo | 28 |
| Arquétipos anatômicos | 7 |
| Armas / secundárias / coberturas | 14 / 5 / 9 |
| Habilidades no catálogo | 43 |
| Endpoints HTTP | ~20 |
| Formatos de atlas exportados | 5 |
| Direções por personagem | 4 |
| Animações por personagem | 3 (idle, walk, death) |

---

## 5. O que resta (fora do escopo fechado — backlog opcional)

Nada do escopo pedido ficou pendente. Itens que **poderiam** evoluir o produto
depois, registrados por transparência:

1. Editor de pixels individuais no web (hoje a edição fina é no Aseprite via
   `atlas_aseprite.json`);
2. Re-render 3D/IA das vistas laterais a partir da foto (hoje: síntese 3/4 —
   limitação documentada em `docs/ARQUITETURA.md`);
3. Autenticação/multi-usuário na API (hoje é ferramenta de estúdio single-user);
4. Migrações Alembic (o esquema é criado idempotentemente no boot).

---

## 6. Como verificar a entrega

```bash
make test        # 90 testes
make lint        # ruff + tsc
make run-api     # Swagger em http://localhost:8000/docs
make run-web     # editor em http://localhost:5173
```

Fluxo de aceitação sugerido:
1. gerar um cavaleiro (seed fixo) e conferir que regenera idêntico;
2. importar `backend/tests/fixtures/ai_character_render.png` e conferir as
   4 direções + animações;
3. exportar o `.zip` e abrir `preview.gif` + `manifest.json`;
4. carregar o pacote numa cena Phaser usando
   `integration/vandoria/pixelmaster-loader.js`.
