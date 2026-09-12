# Referência da API HTTP

Base: `http://localhost:8000` · Swagger interativo em `/docs`.

## Sistema

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Banner da aplicação |
| GET | `/health` | Healthcheck |
| GET | `/api/meta` | Catálogos: espécies, arquétipos, armas, vestuários, paletas, habilidades |

## Personagens

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/characters/generate` | Gera um personagem procedural (body: `GenerateRequest`) |
| POST | `/api/characters/import` | Converte uma foto de IA em personagem (multipart) |
| GET | `/api/characters` | Lista personagens salvos |
| GET | `/api/characters/{id}` | Documento completo do personagem |
| DELETE | `/api/characters/{id}` | Remove personagem + imagem-fonte |

### `POST /api/characters/generate`

```jsonc
{
  "name": "Cavaleiro de Vandoria",
  "kind": "character",            // character | creature
  "rarity": "rare",               // common..legendary (afeta stats)
  "level": 7,
  "tags": ["guild", "tank"],
  "seed": 1234,                   // opcional; sem ele usa blueprint.seed
  "blueprint": {
    "seed": 1234,
    "species": "human",
    "outfit": "knight",
    "weapon": "sword",
    "offhand": "shield",
    "hair_style": "short",
    "body_size": 1.0, "head_size": 1.0, "limb_thickness": 1.0,
    "armor_level": 2,
    "cape": false, "wings": false,
    "outline": true, "shading": true
  }
}
```

Resposta: `{ asset, preview: {pose, strip, sheet, gif, manifest}, frame_count, color_count }`.

### `POST /api/characters/import` (multipart/form-data)

| Campo | Tipo | Descrição |
|---|---|---|
| `file` | binário | PNG/JPG/WebP/BMP do render de IA |
| `name` | texto | nome do personagem |
| `kind`, `rarity`, `level`, `species`, `tags`, `description` | texto | metadados da ficha |
| `params` | JSON | `ImageImportParams` (ver abaixo) |

`ImageImportParams` (principais): `background` (`auto|alpha|solid|keep`),
`background_color`, `background_tolerance`, `auto_crop`, `padding`,
`target_size` (16–64), `palette_size` (2–32), `pixel_mode`
(`dominant|average|box`), `outline`, `outline_strength`, `cleanup`,
`despeckle`, `source_view` (`auto|front|side|back`), `synthesize_directions`,
`side_squeeze`, `idle_frames`, `walk_frames`, `death_frames`, `*_fps`.

## Previews (imagens sob demanda)

| Rota | Parâmetros | Saída |
|---|---|---|
| GET `/api/characters/{id}/pose.png` | `direction`, `scale` | PNG do quadro neutro |
| GET `/api/characters/{id}/strip.png` | `animation`, `direction`, `scale` | PNG com a sequência de quadros lado a lado |
| GET `/api/characters/{id}/sheet.png` | `scale` | PNG do atlas completo |
| GET `/api/characters/{id}/preview.gif` | — | GIF animado (idle→walk→death) |
| GET `/api/characters/{id}/manifest.json` | — | Manifesto de grade uniforme |
| GET `/api/characters/{id}/card.json` | — | Ficha funcional (stats/habilidades) |

## Exportação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/characters/{id}/export` | Monta o pacote; body `ExportOptions` (opcional) |
| POST | `/api/characters/export-batch` | **Bestiário completo** num único `.zip`; body `{ "ids": [...]?, "options": {...}? }` (`ids` omitido/null = todos os salvos) |
| GET | `/api/exports/{filename}` | Baixa o `.zip` gerado |

`ExportOptions`: `formats` (`phaser_hash`, `phaser_array`, `sparrow_xml`,
`uniform_grid`, `aseprite_sheet`), `include_sparrow_xml`, `include_gif_preview`,
`include_individual_frames`, `include_manifest`, `include_stats`,
`include_vandoria_card`, `scale` (1–8), `transparent_background`.

### Exportação em lote (`export-batch`)

Resposta `BatchExportResult`: `filename`, `size_bytes`, `download_url`
(`/api/exports/...`), `character_count` e `files`. Layout do zip:

```
bestiary.json          # índice: id, slug, name, species, rarity, origin, seed,
                       #         stats, abilities, power_rating, sprite size e
                       #         caminhos (dir/) de cada personagem
contact_sheet.png      # poses frontais em grade de 8 colunas (overview)
<slug>__<id8>/         # pasta por personagem — mesmo conteúdo do export individual
```

Erros: `404` se algum id não existe ou se a seleção é vazia.

## Códigos de erro

| Código | Quando |
|---|---|
| 404 | personagem/arquivo inexistente |
| 413 | upload acima de `PIXELMASTER_MAX_UPLOAD_BYTES` |
| 415 | extensão de imagem não suportada |
| 422 | payload/parâmetros inválidos (validação pydantic) |
