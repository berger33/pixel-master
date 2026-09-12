"""Rotas HTTP do Pixel Master."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.api.schemas import (
    BatchExportRequest,
    BatchExportResult,
    GenerateRequest,
    GenerateResponse,
    MetaResponse,
    PreviewUrls,
)
from app.core.config import Settings, get_settings
from app.domain.abilities import ABILITIES
from app.domain.models import (
    CharacterAsset,
    Direction,
    ExportBundle,
    ExportOptions,
    ImageImportParams,
    Rarity,
)
from app.domain.species import SPECIES, archetypes, list_species
from app.generator.procedural import parts as P
from app.pixel.palette import PALETTES
from app.services.character_service import CharacterService

router = APIRouter()

_service = CharacterService()


def get_service() -> CharacterService:
    return _service


ServiceDep = Annotated[CharacterService, Depends(get_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _preview_urls(asset_id: str) -> PreviewUrls:
    base = f"/api/characters/{asset_id}"
    return PreviewUrls(
        pose={d.value: f"{base}/pose.png?direction={d.value}" for d in Direction},
        strip={
            "idle": f"{base}/strip.png?animation=idle",
            "walk": f"{base}/strip.png?animation=walk",
            "death": f"{base}/strip.png?animation=death",
        },
        sheet=f"{base}/sheet.png",
        gif=f"{base}/preview.gif",
        manifest=f"{base}/manifest.json",
    )


# ----------------------------------------------------------------------
# health / meta
# ----------------------------------------------------------------------
@router.get("/health", tags=["system"])
def health() -> dict[str, object]:
    from app import __version__

    return {"status": "ok", "app": "Pixel Master", "version": __version__}


@router.get("/api/meta", response_model=MetaResponse, tags=["meta"])
def meta() -> MetaResponse:
    species = [
        {
            "key": s.key,
            "name": s.name,
            "kind": s.kind,
            "archetype": s.archetype.value,
            "rarity": s.rarity.value,
            "tags": list(s.tags),
            "hairStyles": list(s.hair_styles),
            "outfits": list(s.outfits),
            "weapons": list(s.weapons),
            "headgear": [h for h in s.headgear if h],
            "horns": list(s.horns),
            "tails": list(s.tails),
            "wings": s.wings,
        }
        for s in list_species()
    ]
    return MetaResponse(
        species=species,
        archetypes=archetypes(),
        hair_styles=[h for h in P.HAIR_STYLES],
        headgear=[h for h in P.HEADGEAR if h],
        weapons=list(P.WEAPONS),
        offhands=[o for o in P.OFFHANDS if o],
        outfits=sorted({o for s in SPECIES.values() for o in s.outfits}),
        horns=list(P.HORNS),
        tails=list(P.TAILS),
        palettes={name: sorted(p.ramps) for name, p in PALETTES.items()},
        rarities=[r.value for r in Rarity],
        directions=[d.value for d in Direction],
        animations=["idle", "walk", "death"],
        abilities=[
            {"key": a.key, "name": a.name, "kind": a.kind, "description": a.description}
            for a in ABILITIES
        ],
    )


# ----------------------------------------------------------------------
# geração procedural
# ----------------------------------------------------------------------
@router.post("/api/characters/generate", response_model=GenerateResponse, tags=["characters"])
def generate(body: GenerateRequest, service: ServiceDep) -> GenerateResponse:
    asset = service.create_procedural(
        body.blueprint,
        name=body.name,
        kind=body.kind,
        rarity=body.rarity,
        level=body.level,
        tags=body.tags,
        description=body.description,
        seed=body.seed,
    )
    sheet = service.sheet(asset)
    return GenerateResponse(
        asset=asset,
        preview=_preview_urls(asset.id),
        frame_count=sheet.frame_count,
        color_count=sheet.image.color_count(),
    )


# ----------------------------------------------------------------------
# importação de imagem de IA
# ----------------------------------------------------------------------
class ImportMetaResponse(BaseModel):
    asset: CharacterAsset
    preview: PreviewUrls
    import_info: dict


@router.post("/api/characters/import", response_model=ImportMetaResponse, tags=["characters"])
async def import_character(
    service: ServiceDep,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form()],
    kind: Annotated[str, Form()] = "character",
    rarity: Annotated[str, Form()] = "common",
    level: Annotated[int, Form()] = 1,
    species: Annotated[str, Form()] = "human",
    tags: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    params: Annotated[str, Form()] = "{}",
) -> ImportMetaResponse:
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "imagem excede o tamanho máximo permitido")
    ext = f".{(file.filename or 'img').rsplit('.', 1)[-1].lower()}"
    if ext not in settings.allowed_upload_extensions:
        raise HTTPException(415, f"extensão não suportada: {ext}")

    try:
        import_params = ImageImportParams.model_validate(json.loads(params or "{}"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, f"parâmetros de importação inválidos: {exc}") from exc

    asset, info = service.create_from_image(
        data,
        import_params,
        name=name,
        kind=kind,
        rarity=Rarity(rarity),
        level=level,
        tags=[t for t in tags.split(",") if t.strip()],
        description=description,
        extension=ext,
        species=species,
    )
    return ImportMetaResponse(asset=asset, preview=_preview_urls(asset.id), import_info=info)


# ----------------------------------------------------------------------
# listagem / leitura / exclusão
# ----------------------------------------------------------------------
@router.get("/api/characters", response_model=list[CharacterAsset], tags=["characters"])
def list_characters(service: ServiceDep) -> list[CharacterAsset]:
    return service.list()


@router.get("/api/characters/{asset_id}", response_model=CharacterAsset, tags=["characters"])
def get_character(asset_id: str, service: ServiceDep) -> CharacterAsset:
    asset = service.get(asset_id)
    if asset is None:
        raise HTTPException(404, "personagem não encontrado")
    return asset


@router.delete("/api/characters/{asset_id}", tags=["characters"])
def delete_character(asset_id: str, service: ServiceDep) -> dict[str, bool]:
    return {"deleted": service.delete(asset_id)}


# ----------------------------------------------------------------------
# previews (imagens sob demanda)
# ----------------------------------------------------------------------
def _png(data: bytes) -> Response:
    return Response(content=data, media_type="image/png")


@router.get("/api/characters/{asset_id}/pose.png", tags=["preview"])
def pose(
    asset_id: str,
    service: ServiceDep,
    direction: Direction = Query(Direction.DOWN),
    scale: int = Query(6, ge=1, le=12),
) -> Response:
    asset = _require(service, asset_id)
    return _png(service.render_pose(asset, direction, scale))


@router.get("/api/characters/{asset_id}/strip.png", tags=["preview"])
def strip(
    asset_id: str,
    service: ServiceDep,
    animation: str = Query("walk"),
    direction: Direction = Query(Direction.DOWN),
    scale: int = Query(4, ge=1, le=12),
) -> Response:
    asset = _require(service, asset_id)
    try:
        return _png(service.render_strip(asset, animation, direction, scale))
    except KeyError as exc:
        raise HTTPException(404, f"animação desconhecida: {animation}") from exc


@router.get("/api/characters/{asset_id}/sheet.png", tags=["preview"])
def sheet_png(asset_id: str, service: ServiceDep, scale: int = Query(3, ge=1, le=8)) -> Response:
    asset = _require(service, asset_id)
    return _png(service.render_sheet(asset, scale))


@router.get("/api/characters/{asset_id}/preview.gif", tags=["preview"])
def preview_gif(asset_id: str, service: ServiceDep) -> Response:
    asset = _require(service, asset_id)
    return Response(content=service.render_gif(asset), media_type="image/gif")


@router.get("/api/characters/{asset_id}/manifest.json", tags=["preview"])
def manifest(asset_id: str, service: ServiceDep) -> Response:
    from app.pixel.spritesheet import uniform_grid_manifest

    asset = _require(service, asset_id)
    sheet = service.sheet(asset)
    payload = uniform_grid_manifest(sheet, extra={"assetId": asset.id, "assetSlug": asset.slug})
    return Response(content=json.dumps(payload, indent=2), media_type="application/json")


@router.get("/api/characters/{asset_id}/card.json", tags=["preview"])
def card(asset_id: str, service: ServiceDep) -> Response:
    from app.export.bundle import _card_json

    asset = _require(service, asset_id)
    return Response(content=json.dumps(_card_json(asset, service.sheet(asset)), indent=2), media_type="application/json")


# ----------------------------------------------------------------------
# exportação
# ----------------------------------------------------------------------
@router.post("/api/characters/{asset_id}/export", response_model=ExportBundle, tags=["export"])
def export_character(
    asset_id: str,
    service: ServiceDep,
    options: ExportOptions | None = None,
) -> ExportBundle:
    asset = _require(service, asset_id)
    bundle, _zip, _path = service.export(asset, options or ExportOptions())
    return bundle


@router.post("/api/characters/export-batch", response_model=BatchExportResult, tags=["export"])
def export_batch(body: BatchExportRequest, service: ServiceDep) -> BatchExportResult:
    """Exporta o bestiário completo (ou um subconjunto) em um único .zip."""
    try:
        return service.export_batch(body.ids, body.options)
    except KeyError as exc:
        raise HTTPException(404, f"personagem não encontrado: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/api/exports/{filename}", tags=["export"])
def download_export(filename: str, settings: SettingsDep) -> FileResponse:
    path = (settings.storage_dir / filename).resolve()
    if not str(path).startswith(str(settings.storage_dir.resolve())):
        raise HTTPException(400, "caminho inválido")
    if not path.exists():
        raise HTTPException(404, "arquivo não encontrado")
    return FileResponse(path, media_type="application/zip", filename=filename)


def _require(service: CharacterService, asset_id: str) -> CharacterAsset:
    asset = service.get(asset_id)
    if asset is None:
        raise HTTPException(404, "personagem não encontrado")
    return asset
