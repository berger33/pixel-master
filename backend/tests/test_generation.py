"""Testes do gerador procedural, do animador e da determinística."""

from __future__ import annotations

import pytest

from app.animation.animator import AnimationParams, animate_rig, build_clips
from app.domain.models import BodyArchetype, Direction, ProceduralBlueprint
from app.domain.species import SPECIES, get_species
from app.generator.procedural.creature import build_creature_rig
from app.generator.rig import compose_rig

ALL_DIRECTIONS = [Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.UP]


def _bp(**kw) -> ProceduralBlueprint:
    base = {"seed": 99, "species": "human", "outfit": "adventurer"}
    base.update(kw)
    return ProceduralBlueprint(**base)


@pytest.mark.parametrize("direction", ALL_DIRECTIONS)
def test_humanoid_builds_in_all_directions(direction):
    rig = build_creature_rig(_bp(), direction)
    img = compose_rig(rig)
    assert not img.is_empty()
    bbox = img.bbox()
    assert bbox is not None
    # o personagem cabe dentro do quadro com margem de segurança
    assert bbox[0] >= 0 and bbox[1] >= 0 and bbox[2] <= 64 and bbox[3] <= 64
    assert img.color_count() <= 64  # pixel art: paleta contida


def test_right_is_mirror_of_left():
    left = compose_rig(build_creature_rig(_bp(), Direction.LEFT))
    right = compose_rig(build_creature_rig(_bp(), Direction.RIGHT))
    assert left.flipped_x().data.tolist() == right.data.tolist()


def test_determinism_same_seed_same_bytes():
    a = compose_rig(build_creature_rig(_bp(seed=777), Direction.DOWN)).to_bytes()
    b = compose_rig(build_creature_rig(_bp(seed=777), Direction.DOWN)).to_bytes()
    assert a == b


def test_different_seed_changes_art():
    a = compose_rig(build_creature_rig(_bp(seed=1), Direction.DOWN)).to_bytes()
    b = compose_rig(build_creature_rig(_bp(seed=2), Direction.DOWN)).to_bytes()
    assert a != b


@pytest.mark.parametrize("species_key", sorted(SPECIES))
def test_every_species_generates(species_key):
    species = get_species(species_key)
    bp = _bp(seed=5, species=species_key, archetype=species.archetype)
    rig = build_creature_rig(bp, Direction.DOWN)
    img = compose_rig(rig)
    assert not img.is_empty(), f"espécie {species_key} produziu sprite vazio"
    assert rig.archetype == species.archetype.value


@pytest.mark.parametrize(
    "archetype",
    [
        BodyArchetype.BIPED,
        BodyArchetype.HUMANOID_BRUTE,
        BodyArchetype.QUADRUPED,
        BodyArchetype.ARACHNID,
        BodyArchetype.SERPENT,
        BodyArchetype.FLYER,
        BodyArchetype.BLOB,
    ],
)
def test_every_archetype_builds(archetype):
    bp = _bp(seed=3, archetype=archetype)
    for direction in ALL_DIRECTIONS:
        rig = build_creature_rig(bp, direction)
        assert not compose_rig(rig).is_empty(), f"{archetype} {direction}"


def test_equipment_layers_appear():
    plain = compose_rig(build_creature_rig(_bp(seed=8, weapon=None, offhand=None, headgear=None), Direction.DOWN))
    armed = compose_rig(
        build_creature_rig(_bp(seed=8, weapon="greatsword", offhand="shield", headgear="helm"), Direction.DOWN)
    )
    assert armed.to_bytes() != plain.to_bytes()
    # o equipamento adiciona pixels de metal acima do ombro (capacete)
    assert (armed.data[..., 3] > 0).sum() > (plain.data[..., 3] > 0).sum()


def test_idle_and_walk_frames_differ():
    rig = build_creature_rig(_bp(seed=21), Direction.LEFT)
    clips = animate_rig(rig, Direction.LEFT, AnimationParams(idle_frames=4, walk_frames=4))
    by_name = {c.name: c for c in clips}
    idle = [compose_rig(rig) for rig in []]  # noqa: F841 (apenas clareza)
    idle_bytes = {f.to_bytes() for f in by_name["idle"].frames_by_direction["left"]}
    walk_bytes = {f.to_bytes() for f in by_name["walk"].frames_by_direction["left"]}
    assert len(idle_bytes) >= 2, "idle precisa de pelo menos 2 quadros distintos"
    assert len(walk_bytes) >= 3, "walk precisa de pelo menos 3 quadros distintos"


def test_death_ends_faded_and_low():
    rig = build_creature_rig(_bp(seed=21), Direction.DOWN)
    clips = animate_rig(rig, Direction.DOWN, AnimationParams(death_frames=6))
    death = next(c for c in clips if c.name == "death")
    frames = death.frames_by_direction["down"]
    first, last = frames[0], frames[-1]
    fb, lb = first.bbox(), last.bbox()
    assert fb and lb
    # o corpo termina deitado: a caixa final é mais baixa e mais larga
    assert (lb[3] - lb[1]) < (fb[3] - fb[1])
    # e semitransparente/dessaturado (cadáver)
    assert last.data[..., 3].max() < 255


def test_build_clips_merges_directions():
    clips = build_clips(lambda d: build_creature_rig(_bp(seed=1), d))
    names = {c.name for c in clips}
    assert names == {"idle", "walk", "death"}
    walk = next(c for c in clips if c.name == "walk")
    assert set(walk.frames_by_direction) == {"down", "left", "right", "up"}
    for direction, frames in walk.frames_by_direction.items():
        assert len(frames) == 4, direction
