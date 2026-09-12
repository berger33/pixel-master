"""Catálogo de espécies do universo Vandoria.

Cada espécie declara o arquétipo anatômico, restrições de equipamento, rampas
de cor padrão e multiplicadores de atributos. O gerador procedural usa essas
informações para produzir sprites coerentes sem intervenção manual, e o
balanceamento de stats deriva delas — o que mantém a ficha do personagem
consistente com a sua aparência.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.domain.models import BodyArchetype, Rarity

__all__ = ["Species", "SPECIES", "get_species", "list_species", "species_for_kind"]

Kind = Literal["character", "creature"]


@dataclass(frozen=True)
class Species:
    key: str
    name: str
    kind: Kind
    archetype: BodyArchetype
    description: str
    rarity: Rarity = Rarity.COMMON
    tags: tuple[str, ...] = ()
    # aparência padrão
    skin: str = "fair"
    hair: str = "brown"
    cloth: str = "brown"
    accent: str = "gold"
    creature: str = "scale"
    eyes: str = "black"
    hair_styles: tuple[str, ...] = ("short", "medium", "long")
    outfits: tuple[str, ...] = ("adventurer",)
    weapons: tuple[str, ...] = ("sword",)
    headgear: tuple[str | None, ...] = (None,)
    horns: tuple[str, ...] = ()
    tails: tuple[str, ...] = ()
    wings: bool = False
    extra_limbs: int = 0
    spikes: int = 0
    body_size: float = 1.0
    head_size: float = 1.0
    limb_thickness: float = 1.0
    # balanceamento
    stat_scale: dict[str, float] = field(default_factory=lambda: {"health": 1.0, "attack": 1.0, "defense": 1.0, "speed": 1.0})
    abilities: tuple[str, ...] = ()

    def stat_multiplier(self, stat: str) -> float:
        return self.stat_scale.get(stat, 1.0)


def _s(**kwargs: object) -> Species:
    return Species(**kwargs)  # type: ignore[arg-type]


SPECIES: dict[str, Species] = {
    # ------------------------------------------------------------------
    # Personagens jogáveis / NPCs humanoides
    # ------------------------------------------------------------------
    "human": _s(
        key="human", name="Humano", kind="character", archetype=BodyArchetype.BIPED,
        description="Versátil e numeroso, o humano é a base das guildas de Vandoria.",
        tags=("playable", "humanoid", "guild"),
        hair_styles=("short", "medium", "long", "ponytail", "bald", "braid", "mohawk", "curly"),
        outfits=("adventurer", "peasant", "noble", "mage_robe", "ranger", "rogue", "knight", "monk"),
        weapons=("sword", "axe", "mace", "dagger", "staff", "bow", "spear", "greatsword", "wand"),
        headgear=(None, "hood", "cap", "bandana", "crown", "helm", "wizard_hat", "circlet"),
        stat_scale={"health": 1.0, "attack": 1.0, "defense": 1.0, "speed": 1.0},
        abilities=("golpe_decisivo",),
    ),
    "elf": _s(
        key="elf", name="Elfo", kind="character", archetype=BodyArchetype.BIPED,
        description="Longevos arqueiros e magos das florestas de Vandoria.",
        rarity=Rarity.UNCOMMON, tags=("playable", "humanoid", "arcane", "forest"),
        skin="pale", hair="blond", eyes="green", body_size=0.95, head_size=0.94,
        hair_styles=("long", "ponytail", "braid", "medium"),
        outfits=("mage_robe", "ranger", "rogue", "noble", "adventurer"),
        weapons=("bow", "staff", "wand", "dagger", "sword"),
        headgear=(None, "hood", "circlet", "wizard_hat", "bandana"),
        stat_scale={"health": 0.88, "attack": 0.95, "defense": 0.82, "speed": 1.18},
        abilities=("flecha_arcana", "passo_silvestre"),
    ),
    "dwarf": _s(
        key="dwarf", name="Anão", kind="character", archetype=BodyArchetype.BIPED,
        description="Ferreiros e guerreiros das montanhas, resistentes e teimosos.",
        rarity=Rarity.UNCOMMON, tags=("playable", "humanoid", "forge", "mountain"),
        skin="tan", hair="red", cloth="brown", accent="copper",
        body_size=1.0, head_size=1.1, limb_thickness=1.25,
        hair_styles=("bald", "long", "braid"),
        outfits=("knight", "peasant", "adventurer", "rogue"),
        weapons=("axe", "mace", "greatsword", "hammer", "sword"),
        headgear=(None, "helm", "cap", "hood"), horns=(),
        stat_scale={"health": 1.22, "attack": 1.12, "defense": 1.25, "speed": 0.82},
        abilities=("investida_de_ferro", "pele_de_pedra"),
    ),
    "orc": _s(
        key="orc", name="Orc", kind="character", archetype=BodyArchetype.HUMANOID_BRUTE,
        description="Guerrero das estepes, forte e intimidador.",
        rarity=Rarity.UNCOMMON, tags=("playable", "humanoid", "brute", "horde"),
        skin="tan", creature="slime", hair="black", cloth="red", accent="iron",
        body_size=1.15, head_size=1.05, limb_thickness=1.3,
        hair_styles=("bald", "mohawk", "short"),
        outfits=("adventurer", "knight", "rogue", "peasant"),
        weapons=("axe", "greatsword", "mace", "spear", "sword"),
        headgear=(None, "helm", "bandana", "hood"), horns=("small", "tusks"),
        stat_scale={"health": 1.3, "attack": 1.28, "defense": 1.05, "speed": 0.85},
        abilities=("furia_sangrenta", "grito_de_guerra"),
    ),
    "halfling": _s(
        key="halfling", name="Halfling", kind="character", archetype=BodyArchetype.BIPED,
        description="Pequeno, ágil e surpreendentemente sortudo.",
        rarity=Rarity.UNCOMMON, tags=("playable", "humanoid", "rogue", "lucky"),
        skin="fair", hair="brown", body_size=0.78, head_size=1.15, limb_thickness=0.9,
        hair_styles=("curly", "short", "medium"),
        outfits=("peasant", "rogue", "adventurer", "ranger"),
        weapons=("dagger", "bow", "sling", "sword"),
        headgear=(None, "cap", "hood", "bandana"),
        stat_scale={"health": 0.72, "attack": 0.85, "defense": 0.75, "speed": 1.32},
        abilities=("esquiva_sortuda", "ataque_furtivo"),
    ),
    "undead": _s(
        key="undead", name="Morto-vivo", kind="character", archetype=BodyArchetype.BIPED,
        description="Retornado por magia profana; não respira, não cansa, não perdoa.",
        rarity=Rarity.RARE, tags=("playable", "humanoid", "undead", "dark"),
        skin="ashen", hair="white", cloth="black", accent="arcane", eyes="red",
        creature="undead",
        hair_styles=("bald", "long", "short"),
        outfits=("rogue", "mage_robe", "knight", "adventurer"),
        weapons=("dagger", "sword", "staff", "wand", "scythe"),
        headgear=(None, "hood", "circlet", "helm"),
        stat_scale={"health": 1.05, "attack": 1.0, "defense": 0.95, "speed": 0.9},
        abilities=("toque_gelado", "reanimar"),
    ),
    "demon": _s(
        key="demon", name="Demônio", kind="character", archetype=BodyArchetype.HUMANOID_BRUTE,
        description="Invocado das profundezas, movido por fogo e contrato.",
        rarity=Rarity.EPIC, tags=("playable", "humanoid", "infernal", "fire"),
        creature="demon", skin="dark", hair="black", cloth="black", accent="gold", eyes="red",
        body_size=1.12, head_size=1.02, limb_thickness=1.18, wings=True,
        hair_styles=("bald", "mohawk"),
        outfits=("mage_robe", "knight", "adventurer"),
        weapons=("greatsword", "scythe", "staff", "whip"),
        headgear=(None, "crown", "hood"), horns=("large", "curved", "small"), tails=("barbed",),
        stat_scale={"health": 1.35, "attack": 1.4, "defense": 1.15, "speed": 1.0},
        abilities=("chuva_de_brasas", "asas_infernais"),
    ),
    "celestial": _s(
        key="celestial", name="Celestial", kind="character", archetype=BodyArchetype.BIPED,
        description="Guardião alado da Ordem de Vandoria.",
        rarity=Rarity.LEGENDARY, tags=("npc", "humanoid", "holy", "winged"),
        skin="pale", hair="white", cloth="white", accent="gold", eyes="amber",
        wings=True, body_size=1.05,
        hair_styles=("long", "medium"),
        outfits=("mage_robe", "knight", "noble"),
        weapons=("spear", "sword", "staff", "greatsword"),
        headgear=(None, "crown", "circlet"),
        stat_scale={"health": 1.25, "attack": 1.2, "defense": 1.3, "speed": 1.15},
        abilities=("julgamento", "aura_sagrada"),
    ),

    # ------------------------------------------------------------------
    # Criaturas / monstros
    # ------------------------------------------------------------------
    "rat": _s(
        key="rat", name="Rato Gigante", kind="creature", archetype=BodyArchetype.QUADRUPED,
        description="Praga dos esgotos; fraco sozinho, perigoso em horda.",
        creature="chitin", eyes="red", body_size=0.6,
        tags=("monster", "beast", "swarm", "early-game"), tails=("rat",),
        stat_scale={"health": 0.4, "attack": 0.35, "defense": 0.3, "speed": 1.1},
        abilities=("mordida",),
    ),
    "wolf": _s(
        key="wolf", name="Lobo", kind="creature", archetype=BodyArchetype.QUADRUPED,
        description="Caçador em matilha das florestas do norte.",
        creature="chitin", hair="brown", eyes="amber", body_size=0.9,
        tags=("monster", "beast", "pack"), tails=("bushy",),
        stat_scale={"health": 0.8, "attack": 0.9, "defense": 0.6, "speed": 1.35},
        abilities=("investida", "uivo"),
    ),
    "bear": _s(
        key="bear", name="Urso", kind="creature", archetype=BodyArchetype.QUADRUPED,
        description="Bruto territorial; derruba aventureiros desprevenidos.",
        creature="chitin", hair="brown", body_size=1.35, limb_thickness=1.4,
        tags=("monster", "beast", "elite"),
        stat_scale={"health": 1.9, "attack": 1.5, "defense": 1.2, "speed": 0.85},
        abilities=("patada", "rugido"),
    ),
    "boar": _s(
        key="boar", name="Javali", kind="creature", archetype=BodyArchetype.QUADRUPED,
        description="Investe em linha reta e não desiste fácil.",
        creature="chitin", hair="brown", body_size=1.0, horns=("tusks",),
        tags=("monster", "beast"), tails=("short",),
        stat_scale={"health": 1.2, "attack": 1.1, "defense": 1.0, "speed": 1.0},
        abilities=("investida",),
    ),
    "spider": _s(
        key="spider", name="Aranha Gigante", kind="creature", archetype=BodyArchetype.ARACHNID,
        description="Oito pernas, presas venenosas, paciência infinita.",
        creature="chitin", eyes="red", extra_limbs=6, body_size=1.0,
        tags=("monster", "arachnid", "poison"),
        stat_scale={"health": 0.9, "attack": 1.05, "defense": 0.7, "speed": 1.25},
        abilities=("mordida_venenosa", "teia"),
    ),
    "scorpion": _s(
        key="scorpion", name="Escorpião", kind="creature", archetype=BodyArchetype.ARACHNID,
        description="Carapaça dura e um ferrão que atravessa couro.",
        creature="chitin", extra_limbs=6, spikes=2, body_size=0.95, tails=("stinger",),
        tags=("monster", "arachnid", "desert", "poison"),
        stat_scale={"health": 1.1, "attack": 1.15, "defense": 1.4, "speed": 0.8},
        abilities=("ferrao", "pinca"),
    ),
    "serpent": _s(
        key="serpent", name="Serpente", kind="creature", archetype=BodyArchetype.SERPENT,
        description="Desliza silenciosa entre as ruínas e ataca de bote.",
        creature="scale", eyes="amber", body_size=1.0,
        tags=("monster", "reptile", "ambush"), tails=("snake",),
        stat_scale={"health": 0.85, "attack": 1.1, "defense": 0.65, "speed": 1.3},
        abilities=("bote", "veneno"),
    ),
    "dragon": _s(
        key="dragon", name="Dragão", kind="creature", archetype=BodyArchetype.FLYER,
        description="Chefão dos céus de Vandoria. Escamas, fogo e tesouro.",
        rarity=Rarity.LEGENDARY, creature="scale", eyes="amber", wings=True,
        body_size=1.45, head_size=1.1, limb_thickness=1.3, spikes=6, horns=("large",), tails=("spiked",),
        tags=("boss", "dragon", "fire", "flying"),
        stat_scale={"health": 3.2, "attack": 2.8, "defense": 2.4, "speed": 1.0},
        abilities=("sopro_de_fogo", "voo_rasante", "cauda_chicote"),
    ),
    "wyvern": _s(
        key="wyvern", name="Wyvern", kind="creature", archetype=BodyArchetype.FLYER,
        description="Primo menor do dragão, igualmente mal-humorado.",
        rarity=Rarity.EPIC, creature="scale", wings=True, body_size=1.2, tails=("spiked",), horns=("curved",),
        tags=("monster", "flying", "dragonkin"),
        stat_scale={"health": 1.9, "attack": 1.8, "defense": 1.4, "speed": 1.4},
        abilities=("voo_rasante", "mordida"),
    ),
    "bat": _s(
        key="bat", name="Morcego", kind="creature", archetype=BodyArchetype.FLYER,
        description="Enxame noturno das cavernas.",
        creature="shadow", wings=True, body_size=0.55,
        tags=("monster", "flying", "cave", "swarm"),
        stat_scale={"health": 0.35, "attack": 0.4, "defense": 0.3, "speed": 1.5},
        abilities=("mordida", "ecolocalizacao"),
    ),
    "slime": _s(
        key="slime", name="Slime", kind="creature", archetype=BodyArchetype.BLOB,
        description="Gelatina ácida que absorve o que toca.",
        creature="slime", eyes="black", body_size=0.85,
        tags=("monster", "ooze", "early-game", "acid"),
        stat_scale={"health": 0.7, "attack": 0.55, "defense": 0.9, "speed": 0.5},
        abilities=("absorver", "dividir"),
    ),
    "golem": _s(
        key="golem", name="Golem de Pedra", kind="creature", archetype=BodyArchetype.HUMANOID_BRUTE,
        description="Construto animado por runas; lento, porém quase indestrutível.",
        rarity=Rarity.EPIC, creature="bone", skin="ashen", body_size=1.3, limb_thickness=1.5,
        tags=("monster", "construct", "guardian"),
        stat_scale={"health": 2.4, "attack": 1.6, "defense": 2.6, "speed": 0.45},
        abilities=("pisao_terremoto", "pele_de_pedra"),
    ),
    "skeleton": _s(
        key="skeleton", name="Esqueleto", kind="creature", archetype=BodyArchetype.BIPED,
        description="Ossos reanimados; quebra fácil, mas volta em horda.",
        creature="bone", eyes="black", body_size=1.0, limb_thickness=0.85,
        weapons=("sword", "dagger", "bow", "axe", "scythe"),
        tags=("monster", "undead", "swarm"),
        stat_scale={"health": 0.6, "attack": 0.75, "defense": 0.5, "speed": 0.9},
        abilities=("corte_osseo", "reanimar"),
    ),
    "ghost": _s(
        key="ghost", name="Fantasma", kind="creature", archetype=BodyArchetype.FLYER,
        description="Eco incorpóreo de quem morreu com pendências.",
        rarity=Rarity.RARE, creature="shadow", eyes="white", body_size=1.0,
        tags=("monster", "undead", "incorporeal", "spirit"),
        stat_scale={"health": 0.75, "attack": 0.95, "defense": 1.3, "speed": 1.2},
        abilities=("toque_gelado", "atravessar"),
    ),
    "minotaur": _s(
        key="minotaur", name="Minotauro", kind="creature", archetype=BodyArchetype.HUMANOID_BRUTE,
        description="Guardião de labirintos, armado com machado pesado.",
        rarity=Rarity.RARE, creature="chitin", hair="brown", body_size=1.25, limb_thickness=1.35,
        horns=("large",), tails=("short",), weapons=("axe", "greatsword", "mace"),
        outfits=("peasant", "knight"),
        tags=("monster", "beast", "labyrinth", "elite"),
        stat_scale={"health": 2.0, "attack": 1.9, "defense": 1.5, "speed": 0.9},
        abilities=("investida", "machado_pesado"),
    ),
    "troll": _s(
        key="troll", name="Troll", kind="creature", archetype=BodyArchetype.HUMANOID_BRUTE,
        description="Regenera ferimentos; fogo e ácido são o contragolpe.",
        rarity=Rarity.RARE, creature="slime", body_size=1.3, limb_thickness=1.45,
        tags=("monster", "brute", "regeneration"),
        stat_scale={"health": 2.2, "attack": 1.7, "defense": 1.3, "speed": 0.7},
        abilities=("regeneracao", "porrada"),
    ),
    "goblin": _s(
        key="goblin", name="Goblin", kind="creature", archetype=BodyArchetype.BIPED,
        description="Pequeno, covarde e numeroso; rouba tudo que brilha.",
        creature="slime", eyes="amber", body_size=0.72, head_size=1.2,
        weapons=("dagger", "spear", "bow", "mace"),
        tags=("monster", "humanoid", "swarm", "thief"),
        stat_scale={"health": 0.5, "attack": 0.6, "defense": 0.45, "speed": 1.2},
        abilities=("furto", "punhalada"),
    ),
    "crab": _s(
        key="crab", name="Caranguejo Blindado", kind="creature", archetype=BodyArchetype.ARACHNID,
        description="Carapaça impenetrável pelas costas.",
        creature="chitin", extra_limbs=4, body_size=0.85, spikes=3,
        tags=("monster", "aquatic", "armored"),
        stat_scale={"health": 1.0, "attack": 0.9, "defense": 1.9, "speed": 0.5},
        abilities=("pinca", "carapaca"),
    ),
    "hellhound": _s(
        key="hellhound", name="Cão Infernal", kind="creature", archetype=BodyArchetype.QUADRUPED,
        description="Chamas escapam das suas costas quando corre.",
        rarity=Rarity.EPIC, creature="demon", eyes="red", body_size=1.05, spikes=4, tails=("flame",),
        tags=("monster", "infernal", "fire", "pack"),
        stat_scale={"health": 1.4, "attack": 1.6, "defense": 1.0, "speed": 1.45},
        abilities=("mordida_flamejante", "uivo"),
    ),
    "mushroom": _s(
        key="mushroom", name="Fungo Andarilho", kind="creature", archetype=BodyArchetype.BIPED,
        description="Solta esporos que confundem o alvo.",
        creature="slime", body_size=0.75, head_size=1.35, limb_thickness=0.8,
        tags=("monster", "plant", "poison", "spore"),
        stat_scale={"health": 0.85, "attack": 0.7, "defense": 0.8, "speed": 0.6},
        abilities=("esporos", "absorver"),
    ),
}


def get_species(key: str) -> Species:
    """Retorna a espécie; cai para ``human`` se a chave não existir.

    A fallback deliberada evita que um blueprint inválido quebre a geração —
    o comportamento é registrado na resposta da API como aviso.
    """
    return SPECIES.get(key, SPECIES["human"])


def list_species(kind: Kind | None = None) -> list[Species]:
    items = list(SPECIES.values())
    if kind is not None:
        items = [s for s in items if s.kind == kind]
    return sorted(items, key=lambda s: s.name)


def species_for_kind(kind: Kind) -> list[str]:
    return [s.key for s in list_species(kind)]


def archetypes() -> list[str]:
    return sorted({s.archetype.value for s in SPECIES.values()})
