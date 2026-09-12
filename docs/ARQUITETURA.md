# Arquitetura do Pixel Master

## Visão geral

```
┌────────────────────────────  frontend (React + Vite)  ────────────────────────────┐
│  ControlPanel (procedural) │ ImportPanel (foto de IA) │ SpritePreview (canvas)    │
│  SidePanel: ficha · exportação · biblioteca                                      │
└───────────────────────────────────┬──────────────────────────────────────────────┘
                                    │  HTTP /api (proxy do Vite)
┌───────────────────────────────────▼──────────────────────────────────────────────┐
│                          backend (FastAPI)                                        │
│  api/routes.py  →  services/character_service.py  →  db/repository.py (SQLite)    │
└───────┬───────────────────────────┬───────────────────────────┬──────────────────┘
        │                           │                           │
┌───────▼────────┐        ┌─────────▼─────────┐        ┌────────▼─────────┐
│ generator/     │        │ animation/        │        │ export/          │
│  procedural/   │        │  animator.py      │        │  bundle.py       │
│  from_image/   │        │  (idle/walk/death)│        │  (atlas/zip/gif) │
└───────┬────────┘        └─────────▲─────────┘        └────────▲─────────┘
        │                           │                           │
        └───────────┬───────────────┘                           │
        ┌───────────▼───────────┐                               │
        │ generator/rig.py      │  camadas + pivôs + tags       │
        │ pixel/canvas,palette, │  primitivas, paletas, atlas   │
        │ pixel/spritesheet     │                               │
        └───────────────────────┴───────────────────────────────┘
```

## Decisões principais

### 1. O `Rig` de camadas é o contrato central
Um sprite não é uma imagem: é um conjunto de **camadas** (cabeça, tronco,
braços, pernas, arma, asas...) cada uma com um **pivô** de articulação, uma
ordem `z` e **tags** semânticas (`leg`, `gait`, `wing`, `tail`, `segment`).

Consequência: o **mesmo animador** move um cavaleiro procedural, um lobo, uma
aranha *e* um sprite recortado de uma foto de IA — porque todos viram rigs com
as mesmas tags. Isso elimina duplicação de lógica de animação e garante
consistência de movimento entre origens diferentes.

### 2. Determinismo por construção
Toda variação estética passa por `core/rng.SeedRandom` (xorshift32 isolado) e
por `zlib.crc32` para hashes de strings — nunca pelo `random` global nem pelo
`hash()` builtin (que tem salt por processo). Dois builds com o mesmo `seed`
produzem bytes idênticos (coberto por teste), o que permite regenerar qualquer
personagem salvo a partir do seu blueprint.

### 3. Pixel art de verdade
* todas as primitivas trabalham na grade inteira (sem coordenadas fracionárias);
* rotações/escalas são reamostradas por **vizinho mais próximo** (nunca bilinear);
* sombreamento em **3 tons** derivados de rampas com deslocamento de matiz;
* contorno de 1 px derivado da própria paleta (não preto chapado);
* sombra de contato sob os pés para ancorar o sprite ao chão;
* contagem de cores contida (monitorada nos testes e no manifesto).

### 4. Dois modos de criação, uma única saída
* **Procedural**: espécies (28 no catálogo) × arquétipos anatômicos (biped,
  brute, quadruped, arachnid, serpent, flyer, blob) × equipamento × paletas.
* **Foto de IA**: remoção de fundo (incluindo regiões *encerradas*),
  pixelização por **cobertura/dominância** (não um downscale borrado),
  quantização de paleta, detecção de vista, síntese das 4 direções e
  segmentação em rig animável.

Ambos terminam no mesmo pipeline: rig → animação → atlas → pacote.

### 5. Exportação orientada ao motor do jogo
O atlas é uma **grade uniforme** (compatível com `load.spritesheet` do Phaser)
acompanhada de um manifesto com `animationStartIndex` em **índice linear da
grade** (contando células vazias) — o detalhe que faz a integração funcionar de
primeira. Formatos alternativos (TexturePacker Hash/Array, Sparrow XML, tags
Aseprite) são gerados pelo mesmo empacotador.

## Mapa de módulos

| Módulo | Responsabilidade |
|---|---|
| `app/pixel/canvas.py` | Superfície RGBA, primitivas, transforms nearest, contorno, blend |
| `app/pixel/palette.py` | Rampas, paletas nomeadas, median-cut, snap, cor de contorno |
| `app/pixel/spritesheet.py` | Empacotamento em grade + atlas JSON/XML + manifesto |
| `app/generator/rig.py` | Camadas, pivôs, tags, composição |
| `app/generator/procedural/*` | Desenho de humanoides e criaturas por espécie/arquétipo |
| `app/generator/from_image/pipeline.py` | Foto → recorte → pixel art → 4 direções → rig |
| `app/animation/animator.py` | idle / walk(4 dir) / death por tags e pivôs |
| `app/export/bundle.py` | Pacote .zip (atlas, manifestos, gif, card, frames, README) |
| `app/domain/*` | Modelos pydantic, catálogo de espécies, habilidades, stats |
| `app/services/character_service.py` | Orquestração + persistência + previews |
| `app/api/routes.py` | HTTP (geração, importação, previews, exportação, CRUD) |
| `app/db/*` | SQLAlchemy Core, SQLite (Postgres via `DATABASE_URL`) |

## Limitações conhecidas (declaradas, não simuladas)

* A síntese de direções a partir de uma foto usa compressão 3/4 para as laterais
  e remoção de rosto para as costas — é uma aproximação de sprite top-down, não
  um re-render 3D. Renders frontais com fundo simples dão o melhor resultado.
* Rotações de camadas em ângulos altos podem produzir serrilhado visível em
  zoom extremo; é o comportamento esperado de rotação nearest em pixel art.
* O editor web não edita pixels individuais (o foco é geração/parametrização);
  edição fina deve ser feita no Aseprite reimportando `atlas_aseprite.json`.
