"""Configuração de testes: isola banco e diretórios de artefatos em tmp."""

from __future__ import annotations

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="pixelmaster-test-")
os.environ["PIXELMASTER_DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["PIXELMASTER_STORAGE_DIR"] = f"{_TMP}/exports"
os.environ["PIXELMASTER_UPLOAD_DIR"] = f"{_TMP}/uploads"
os.environ["PIXELMASTER_DEBUG"] = "false"

import pathlib  # noqa: E402

import pytest  # noqa: E402

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_image_bytes() -> bytes:
    return (FIXTURES / "ai_character_render.png").read_bytes()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def procedural_asset(client):
    payload = {
        "name": "Cavaleiro de Teste",
        "kind": "character",
        "rarity": "rare",
        "level": 5,
        "seed": 4242,
        "blueprint": {"seed": 4242, "species": "human", "outfit": "knight", "weapon": "sword"},
    }
    res = client.post("/api/characters/generate", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["asset"]
