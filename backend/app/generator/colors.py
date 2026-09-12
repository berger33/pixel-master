"""Resolução de rampas de cor a partir do blueprint.

Centraliza a regra "paleta nomeada OU cor customizada OU padrão da espécie",
usada tanto pelo gerador procedural quanto pelo pipeline de importação de foto.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import PaletteChoice
from app.domain.species import Species
from app.pixel.palette import PALETTES, Ramp, ramp_from_color

__all__ = ["SpriteColors", "resolve_colors", "resolve_single", "DEFAULT_OUTFIT_COLOR"]

DEFAULT_OUTFIT_COLOR: dict[str, tuple[int, int, int]] = {
    "adventurer": (122, 92, 62),
    "peasant": (150, 128, 96),
    "noble": (126, 58, 92),
    "mage_robe": (72, 62, 140),
    "ranger": (74, 108, 62),
    "rogue": (66, 62, 74),
    "knight": (126, 132, 146),
    "monk": (176, 148, 96),
}


@dataclass
class SpriteColors:
    """Conjunto de rampas resolvidas para um sprite."""

    skin: Ramp
    hair: Ramp
    cloth: Ramp
    metal: Ramp
    leather: Ramp
    accent: Ramp
    eyes: Ramp
    creature: Ramp
    outline: tuple[int, int, int] = (24, 22, 32)
    extras: dict[str, Ramp] = field(default_factory=dict)

    def all_colors(self) -> list[tuple[int, int, int]]:
        out: list[tuple[int, int, int]] = []
        ramps = [self.skin, self.hair, self.cloth, self.metal, self.leather, self.accent, self.eyes, self.creature]
        ramps += list(self.extras.values())
        for ramp in ramps:
            for c in ramp.colors:
                if c not in out:
                    out.append(c)
        return out


def resolve_single(
    family: str,
    key: str | None,
    custom: tuple[int, int, int] | None,
    fallback_key: str,
    *,
    steps: int = 5,
) -> Ramp:
    """Resolve uma rampa: cor customizada > chave nomeada > chave de fallback."""
    if custom is not None:
        return ramp_from_color(tuple(int(c) for c in custom), steps=steps, name=family)
    if key:
        ramp = PALETTES.get(family, PALETTES["cloth"]).ramps.get(key)
        if ramp is not None:
            return ramp
    return PALETTES.get(family, PALETTES["cloth"]).ramps[fallback_key]


def resolve_colors(
    choice: PaletteChoice,
    species: Species,
    custom_colors: dict[str, tuple[int, int, int]] | None = None,
) -> SpriteColors:
    """Monta as rampas de um sprite a partir do blueprint + espécie."""
    custom = custom_colors or {}

    def c(family: str, key: str | None, species_default: str) -> tuple[int, int, int] | None:
        return custom.get(family)

    cloth_key = choice.cloth
    cloth_custom = custom.get("cloth") or custom.get("outfit")
    if cloth_custom is not None:
        cloth_ramp = ramp_from_color(tuple(int(v) for v in cloth_custom), name="cloth")
    elif cloth_key in PALETTES["cloth"].ramps:
        cloth_ramp = PALETTES["cloth"].ramps[cloth_key]
    else:
        cloth_ramp = ramp_from_color(DEFAULT_OUTFIT_COLOR.get("adventurer"), name="cloth")

    return SpriteColors(
        skin=resolve_single("skin", choice.skin or species.skin, custom.get("skin"), species.skin or "fair"),
        hair=resolve_single("hair", choice.hair or species.hair, custom.get("hair"), species.hair or "brown"),
        cloth=cloth_ramp,
        metal=resolve_single("metal", choice.metal, custom.get("metal"), "steel"),
        leather=resolve_single("leather", choice.leather, custom.get("leather"), "tan"),
        accent=resolve_single("metal", choice.accent, custom.get("accent"), "gold"),
        eyes=resolve_single("eye", custom.get("eyes") and None or (choice.eyes or species.eyes), custom.get("eyes"), species.eyes or "black"),
        creature=resolve_single("monster", choice.creature or species.creature, custom.get("creature"), species.creature or "scale"),
        outline=tuple(int(v) for v in choice.outline),  # type: ignore[assignment]
        extras={
            "wood": resolve_single("nature", "wood", custom.get("wood"), "wood"),
            "bone": resolve_single("monster", "bone", custom.get("bone"), "bone"),
            "shadow": resolve_single("monster", "shadow", custom.get("shadow"), "shadow"),
        },
    )
