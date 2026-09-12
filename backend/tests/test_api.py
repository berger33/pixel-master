"""Testes de integração da API HTTP (FastAPI TestClient)."""

from __future__ import annotations

import io
import json
import zipfile

import pytest


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_meta_catalog(client):
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert len(data["species"]) >= 20
    assert "walk" in data["animations"]
    assert data["directions"] == ["down", "left", "right", "up"]
    assert len(data["abilities"]) >= 20


def test_generate_returns_asset_and_preview(client):
    res = client.post(
        "/api/characters/generate",
        json={
            "name": "Mago de Teste",
            "rarity": "epic",
            "level": 10,
            "seed": 31337,
            "blueprint": {"seed": 31337, "species": "elf", "outfit": "mage_robe", "weapon": "staff"},
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    asset = body["asset"]
    assert asset["origin"] == "procedural"
    assert asset["seed"] == 31337
    assert asset["stats"]["level"] == 10
    assert asset["stats"]["health"] > 0
    assert body["frame_count"] > 0
    assert set(body["preview"]["pose"]) == {"down", "left", "right", "up"}


def test_generate_validation_errors(client):
    res = client.post(
        "/api/characters/generate",
        json={"name": "x", "blueprint": {"seed": -5, "species": "human"}},
    )
    assert res.status_code == 422


def test_crud_roundtrip(client, procedural_asset):
    asset_id = procedural_asset["id"]

    got = client.get(f"/api/characters/{asset_id}")
    assert got.status_code == 200
    assert got.json()["id"] == asset_id

    listing = client.get("/api/characters").json()
    assert any(a["id"] == asset_id for a in listing)

    deleted = client.delete(f"/api/characters/{asset_id}")
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/characters/{asset_id}").status_code == 404


def test_unknown_asset_404(client):
    assert client.get("/api/characters/nao-existe").status_code == 404
    assert client.get("/api/characters/nao-existe/pose.png").status_code == 404


@pytest.mark.parametrize(
    "path,media",
    [
        ("/pose.png?direction=down&scale=4", "image/png"),
        ("/strip.png?animation=walk&direction=left&scale=3", "image/png"),
        ("/sheet.png?scale=2", "image/png"),
        ("/preview.gif", "image/gif"),
    ],
)
def test_preview_endpoints(client, procedural_asset, path, media):
    res = client.get(f"/api/characters/{procedural_asset['id']}{path}")
    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith(media)
    assert len(res.content) > 500


def test_manifest_and_card(client, procedural_asset):
    base = f"/api/characters/{procedural_asset['id']}"
    manifest = client.get(f"{base}/manifest.json").json()
    assert manifest["frameWidth"] == 64
    cols = manifest["columns"]
    idx = manifest["animationStartIndex"]
    # idle ocupa as 4 primeiras linhas (uma por direção)
    assert idx["idle"]["down"] == 0
    assert idx["walk"]["down"] == 4 * cols
    assert idx["death"]["down"] == 8 * cols

    card = client.get(f"{base}/card.json").json()
    assert card["format"] == "vandoria/character-card"
    assert card["stats"]["health"] > 0
    assert isinstance(card["abilities"], list)


def test_export_zip_contents(client, procedural_asset):
    res = client.post(
        f"/api/characters/{procedural_asset['id']}/export",
        json={"include_individual_frames": True, "include_sparrow_xml": True},
    )
    assert res.status_code == 200, res.text
    bundle = res.json()
    assert bundle["frame_count"] > 0

    dl = client.get(bundle["download_url"])
    assert dl.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(dl.content))
    names = set(zf.namelist())
    assert {"spritesheet.png", "manifest.json", "card.json", "preview.gif", "README.txt", "atlas_sparrow.xml"} <= names
    assert any(n.startswith("frames/") for n in names)

    manifest = json.loads(zf.read("manifest.json"))
    assert manifest["frameWidth"] == bundle["sprite_width"]
    card = json.loads(zf.read("card.json"))
    assert card["id"] == procedural_asset["id"]


def test_export_rejects_path_traversal(client):
    res = client.get("/api/exports/..%2F..%2Fetc%2Fpasswd")
    assert res.status_code in (400, 404)


def test_import_endpoint_end_to_end(client, fixture_image_bytes):
    res = client.post(
        "/api/characters/import",
        files={"file": ("render.png", fixture_image_bytes, "image/png")},
        data={
            "name": "Caçadora Importada",
            "kind": "character",
            "rarity": "rare",
            "level": 8,
            "species": "elf",
            "params": json.dumps({"target_size": 44, "palette_size": 14}),
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["asset"]["origin"] == "image"
    assert body["import_info"]["backgroundRemoved"] is True
    assert set(body["import_info"]["directions"]) == {"down", "left", "right", "up"}

    asset_id = body["asset"]["id"]
    pose = client.get(f"/api/characters/{asset_id}/pose.png?direction=left&scale=4")
    assert pose.status_code == 200

    export = client.post(f"/api/characters/{asset_id}/export", json={})
    assert export.status_code == 200
    assert export.json()["frame_count"] > 0


def test_import_rejects_bad_extension(client):
    res = client.post(
        "/api/characters/import",
        files={"file": ("nota.txt", b"hello", "text/plain")},
        data={"name": "x"},
    )
    assert res.status_code == 415


def test_import_rejects_bad_params(client, fixture_image_bytes):
    res = client.post(
        "/api/characters/import",
        files={"file": ("render.png", fixture_image_bytes, "image/png")},
        data={"name": "x", "params": "{\"target_size\": 9999}"},
    )
    assert res.status_code == 422
