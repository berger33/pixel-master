"""Catálogo de habilidades e gerador determinístico de fichas de gameplay.

O Pixel Master não entrega só a arte: entrega o personagem **funcional**, o que
significa uma ficha de atributos coerente com a espécie, o equipamento e a
raridade. Tudo aqui é derivado deterministicamente do ``seed``, então o mesmo
personagem sempre recebe os mesmos números.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

from app.domain.models import AbilitySpec, Rarity, StatBlock
from app.domain.species import Species

__all__ = ["Ability", "ABILITIES", "ABILITY_BY_KEY", "AbilityLibrary", "derive_stats", "derive_abilities"]


@dataclass(frozen=True)
class Ability:
    key: str
    name: str
    description: str
    kind: str
    power: int
    cooldown: float
    cost: int
    tags: tuple[str, ...] = ()


_ABILITY_DEFS: list[tuple[str, str, str, str, int, float, int, tuple[str, ...]]] = [
    ("mordida", "Mordida", "Ataque corpo a corpo básico com os dentes.", "attack", 8, 3.0, 0, ("beast",)),
    ("investida", "Investida", "Avança em linha reta causando dano e empurrando o alvo.", "attack", 14, 6.0, 4, ("beast", "brute")),
    ("uivo", "Uivo", "Aumenta o ataque dos aliados próximos por alguns segundos.", "buff", 0, 12.0, 6, ("beast", "pack")),
    ("patada", "Patada", "Golpe pesado que pode atordoar.", "attack", 18, 5.0, 5, ("beast",)),
    ("rugido", "Rugido", "Reduz a defesa dos inimigos próximos.", "debuff", 0, 14.0, 8, ("beast", "fear")),
    ("machado_pesado", "Machado Pesado", "Golpe amplo que atinge vários inimigos adjacentes.", "attack", 20, 7.0, 6, ("brute", "weapon")),
    ("porrada", "Porrada", "Soco brutal com grande recuo.", "attack", 16, 4.0, 3, ("brute",)),
    ("regeneracao", "Regeneração", "Recupera vida continuamente fora de combate.", "passive", 0, 0.0, 0, ("regeneration",)),
    ("pele_de_pedra", "Pele de Pedra", "Reduz o dano físico recebido.", "passive", 0, 0.0, 0, ("defense",)),
    ("pisao_terremoto", "Pisão Terremoto", "Atordoa todos os inimigos adjacentes.", "attack", 22, 10.0, 12, ("construct", "aoe")),
    ("mordida_venenosa", "Mordida Venenosa", "Causa dano e aplica veneno por 6 segundos.", "attack", 12, 6.0, 4, ("poison",)),
    ("teia", "Teia", "Prende o alvo, reduzindo muito a velocidade.", "debuff", 0, 9.0, 6, ("control",)),
    ("pinca", "Pinça", "Agarra e causa dano contínuo enquanto o alvo não escapa.", "attack", 13, 5.0, 3, ("arachnid",)),
    ("ferrao", "Ferrão", "Aplica veneno acumulativo.", "attack", 10, 6.0, 4, ("poison",)),
    ("carapaca", "Carapaça", "Bloqueia dano frontal; vulnerável pelos flancos.", "passive", 0, 0.0, 0, ("defense",)),
    ("bote", "Bote", "Ataque rápido de curta distância com chance de crítico.", "attack", 15, 4.0, 3, ("ambush",)),
    ("veneno", "Veneno", "Dano por segundo após o contato.", "debuff", 6, 8.0, 5, ("poison",)),
    ("sopro_de_fogo", "Sopro de Fogo", "Cone de fogo que causa dano alto em área.", "attack", 34, 12.0, 20, ("fire", "aoe", "dragon")),
    ("voo_rasante", "Voo Rasante", "Mergulha sobre o alvo causando dano e recuo.", "attack", 26, 9.0, 14, ("flying", "dragon")),
    ("cauda_chicote", "Cauda Chicote", "Varredura que atinge inimigos atrás do usuário.", "attack", 18, 6.0, 6, ("aoe", "dragon")),
    ("mordida_flamejante", "Mordida Flamejante", "Mordida que aplica queimadura.", "attack", 20, 5.0, 6, ("fire", "beast")),
    ("ecolocalizacao", "Ecolocalização", "Revela inimigos invisíveis próximos.", "passive", 0, 0.0, 0, ("flying",)),
    ("absorver", "Absorver", "Converte parte do dano recebido em vida.", "passive", 0, 0.0, 0, ("ooze",)),
    ("dividir", "Dividir", "Ao morrer, gera dois slimes menores.", "passive", 0, 0.0, 0, ("ooze",)),
    ("esporos", "Esporos", "Nuvem que causa confusão no alvo.", "debuff", 4, 10.0, 7, ("poison", "plant")),
    ("corte_osseo", "Corte Ósseo", "Golpe com arma improvisada de osso.", "attack", 9, 3.0, 0, ("undead",)),
    ("reanimar", "Reanimar", "Retorna um aliado morto-vivo caído.", "summon", 0, 20.0, 25, ("undead",)),
    ("toque_gelado", "Toque Gélido", "Dano de gelo que reduz a velocidade do alvo.", "attack", 14, 6.0, 8, ("undead", "ice")),
    ("atravessar", "Atravessar", "Ignora obstáculos físicos por alguns segundos.", "buff", 0, 15.0, 12, ("incorporeal",)),
    ("golpe_decisivo", "Golpe Decisivo", "Ataque com bônus de crítico aumentado.", "attack", 16, 5.0, 4, ("humanoid", "weapon")),
    ("flecha_arcana", "Flecha Arcana", "Disparo mágico à distância que nunca erra.", "attack", 18, 7.0, 10, ("arcane", "ranged")),
    ("passo_silvestre", "Passo Silvestre", "Aumenta velocidade e evasão em terreno natural.", "buff", 0, 12.0, 8, ("forest",)),
    ("investida_de_ferro", "Investida de Ferro", "Avança causando dano e ganhando defesa.", "attack", 17, 8.0, 6, ("brute", "defense")),
    ("furia_sangrenta", "Fúria Sangrenta", "Troca defesa por ataque por alguns segundos.", "buff", 0, 14.0, 10, ("brute",)),
    ("grito_de_guerra", "Grito de Guerra", "Aumenta o ataque dos aliados e causa medo.", "buff", 0, 16.0, 12, ("brute", "fear")),
    ("esquiva_sortuda", "Esquiva Sortuda", "Chance elevada de evitar ataques.", "passive", 0, 0.0, 0, ("rogue",)),
    ("ataque_furtivo", "Ataque Furtivo", "Dano dobrado contra alvos que não o veem.", "attack", 22, 8.0, 6, ("rogue",)),
    ("furto", "Furto", "Rouba ouro ou item do alvo.", "attack", 6, 6.0, 2, ("thief",)),
    ("punhalada", "Punhalada", "Ataque rápido de baixo custo.", "attack", 10, 3.0, 1, ("rogue", "weapon")),
    ("chuva_de_brasas", "Chuva de Brasas", "Área de fogo que persiste no chão.", "attack", 30, 14.0, 22, ("fire", "aoe", "infernal")),
    ("asas_infernais", "Asas Infernais", "Permite sobrevoar obstáculos.", "buff", 0, 20.0, 18, ("flying", "infernal")),
    ("julgamento", "Julgamento", "Dano sagrado massivo em um único alvo.", "attack", 38, 16.0, 28, ("holy",)),
    ("aura_sagrada", "Aura Sagrada", "Cura aliados próximos continuamente.", "heal", 8, 18.0, 20, ("holy",)),
]

ABILITIES: tuple[Ability, ...] = tuple(
    Ability(key=k, name=n, description=d, kind=kd, power=p, cooldown=c, cost=co, tags=t)
    for (k, n, d, kd, p, c, co, t) in _ABILITY_DEFS
)
ABILITY_BY_KEY: dict[str, Ability] = {a.key: a for a in ABILITIES}


class AbilityLibrary:
    """Consulta de habilidades por tag — usada pela UI para montar a ficha."""

    @staticmethod
    def all() -> list[Ability]:
        return list(ABILITIES)

    @staticmethod
    def by_tag(tag: str) -> list[Ability]:
        return [a for a in ABILITIES if tag in a.tags]

    @staticmethod
    def get(key: str) -> Ability | None:
        return ABILITY_BY_KEY.get(key)


# ----------------------------------------------------------------------
# Derivação determinística
# ----------------------------------------------------------------------
_RARITY_SCALE: dict[Rarity, dict[str, float]] = {
    Rarity.COMMON: {"health": 1.00, "attack": 1.00, "defense": 1.00, "xp": 1.00, "gold": 1.00},
    Rarity.UNCOMMON: {"health": 1.15, "attack": 1.12, "defense": 1.12, "xp": 1.4, "gold": 1.5},
    Rarity.RARE: {"health": 1.35, "attack": 1.3, "defense": 1.3, "xp": 2.2, "gold": 2.6},
    Rarity.EPIC: {"health": 1.65, "attack": 1.55, "defense": 1.55, "xp": 4.0, "gold": 5.0},
    Rarity.LEGENDARY: {"health": 2.1, "attack": 1.95, "defense": 1.95, "xp": 8.0, "gold": 11.0},
}

_BASE_STATS = {
    "health": 52, "mana": 12, "attack": 9, "defense": 6, "magic_attack": 4,
    "magic_defense": 3, "speed": 7, "stamina": 14, "accuracy": 74, "evasion": 7,
}


def _small(seed: int, salt: int) -> float:
    """Pseudo-aleatório determinístico em ``[0, 1)`` sem depender de ``random``."""
    x = (seed * 374761393 + salt * 668265263) & 0xFFFFFFFF
    x = (x ^ (x >> 13)) * 1274126177 & 0xFFFFFFFF
    return (x & 0xFFFF) / 65536.0


def derive_stats(
    *,
    species: Species,
    rarity: Rarity,
    level: int = 1,
    seed: int = 0,
    armor_level: int = 1,
    arcane: bool = False,
) -> StatBlock:
    """Calcula atributos coerentes com espécie, raridade, nível e equipamento."""
    level = max(1, min(255, int(level)))
    rarity_scale = _RARITY_SCALE[rarity]

    growth = 1.0 + 0.16 * (level - 1)
    variance = lambda salt: 0.92 + 0.16 * _small(seed, salt)  # noqa: E731

    armor_bonus = max(0, min(4, int(armor_level)))

    health = _BASE_STATS["health"] * species.stat_multiplier("health") * rarity_scale["health"] * growth * variance(1)
    attack = _BASE_STATS["attack"] * species.stat_multiplier("attack") * rarity_scale["attack"] * growth * variance(2)
    defense = (
        _BASE_STATS["defense"]
        * species.stat_multiplier("defense")
        * rarity_scale["defense"]
        * growth
        * variance(3)
        * (1.0 + 0.22 * armor_bonus)
    )
    speed = _BASE_STATS["speed"] * species.stat_multiplier("speed") * (1.0 + 0.03 * (level - 1)) * variance(4)
    magic_attack = _BASE_STATS["magic_attack"] * (1.9 if arcane else 1.0) * growth * variance(5)
    magic_defense = _BASE_STATS["magic_defense"] * (1.6 if arcane else 1.0) * growth * variance(6)

    return StatBlock(
        level=level,
        health=max(1, int(round(health))),
        mana=max(0, int(round(_BASE_STATS["mana"] * (2.2 if arcane else 1.0) * growth))),
        attack=max(0, int(round(attack))),
        defense=max(0, int(round(defense))),
        magic_attack=max(0, int(round(magic_attack))),
        magic_defense=max(0, int(round(magic_defense))),
        speed=max(0, int(round(speed))),
        stamina=max(0, int(round(_BASE_STATS["stamina"] * growth))),
        accuracy=max(0, min(100, int(round(_BASE_STATS["accuracy"] + 0.6 * (level - 1) + 6 * variance(7))))),
        evasion=max(0, min(100, int(round(_BASE_STATS["evasion"] * species.stat_multiplier("speed") + 0.4 * (level - 1))))),
        experience_reward=max(0, int(round(8 * rarity_scale["xp"] * growth * species.stat_multiplier("health")))),
        gold_reward=max(0, int(round(5 * rarity_scale["gold"] * growth))),
    )


def derive_abilities(species: Species, *, seed: int = 0, max_count: int = 3) -> list[AbilitySpec]:
    """Monta a lista de habilidades a partir do catálogo da espécie."""
    keys: list[str] = []
    for key in species.abilities:
        if key in ABILITY_BY_KEY and key not in keys:
            keys.append(key)

    # complementa com habilidades coerentes com as tags da espécie
    if len(keys) < max_count:
        pool = [
            a.key
            for a in ABILITIES
            if a.key not in keys and any(tag in species.tags for tag in a.tags)
        ]
        # zlib.crc32 em vez de hash(): este é estável entre processos, o que é
        # requisito para a geração determinística.
        ordered = sorted(pool, key=lambda k: (_small(seed, 100 + (zlib.crc32(k.encode()) % 997)), k))
        for key in ordered:
            if len(keys) >= max_count:
                break
            keys.append(key)

    out: list[AbilitySpec] = []
    for key in keys[:max_count]:
        ability = ABILITY_BY_KEY[key]
        out.append(
            AbilitySpec(
                key=ability.key,
                name=ability.name,
                description=ability.description,
                kind=ability.kind,  # type: ignore[arg-type]
                power=ability.power,
                cooldown=ability.cooldown,
                cost=ability.cost,
            )
        )
    return out
