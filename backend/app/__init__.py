"""Pixel Master — engine de pixel art e gerador de personagens/criaturas.

Módulos principais
------------------
``app.pixel``       primitivos de desenho, paletas e empacotamento de spritesheet
``app.generator``   geração procedural determinística e pipeline foto -> sprite
``app.animation``   keyframes de idle / walk (4 direções) / death
``app.export``      atlas PNG + JSON (Phaser 3, TexturePacker, Sparrow) e bundle .zip
``app.domain``      modelos de domínio (personagem, criatura, stats, paleta)
``app.api``         camada HTTP FastAPI
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
