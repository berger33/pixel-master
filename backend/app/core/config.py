"""Configuração central da aplicação.

Todos os parâmetros podem ser sobrescritos por variáveis de ambiente com o
prefixo ``PIXELMASTER_``, o que permite apontar a persistência para PostgreSQL
em produção mantendo SQLite no desenvolvimento local.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Parâmetros de runtime do Pixel Master."""

    model_config = SettingsConfigDict(
        env_prefix="PIXELMASTER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pixel Master"
    version: str = "1.0.0"
    debug: bool = False

    # --- Persistência -----------------------------------------------------
    database_url: str = f"sqlite:///{(_BACKEND_DIR / 'pixelmaster.db').as_posix()}"

    # --- Armazenamento de artefatos --------------------------------------
    storage_dir: Path = _BACKEND_DIR / "var" / "exports"
    upload_dir: Path = _BACKEND_DIR / "var" / "uploads"

    # --- Padrões de arte --------------------------------------------------
    sprite_width: int = 64
    sprite_height: int = 64
    max_palette_colors: int = 32
    max_upload_bytes: int = 25 * 1024 * 1024
    allowed_upload_extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

    # --- CORS -------------------------------------------------------------
    cors_origins: tuple[str, ...] = ("*",)

    def ensure_dirs(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
