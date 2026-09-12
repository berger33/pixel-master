"""Animador procedural compartilhado por todos os arquétipos.

A partir de um :class:`~app.generator.rig.Rig` em pose neutra, produz os clipes
``idle``, ``walk`` (nas 4 direções) e ``death``. O movimento é decidido por
**tags** das camadas (``leg``/``gait``, ``wing``, ``tail``, ``segment``...) e
pelos pivôs já definidos no rig, então o mesmo código anima um cavaleiro, um
lobo, uma aranha ou um slime — inclusive sprites recortados de uma foto
importada, que recebem um rig com as mesmas tags.

Regra de ouro de pixel art: todos os deslocamentos são **inteiros** e as
rotações são reamostradas por vizinho mais próximo, nunca interpoladas.
"""

from __future__ import annotations

import math

from app.domain.models import AnimationKind, Direction
from app.generator.rig import Layer, PartKind, Rig, compose_rig
from app.pixel.canvas import PixelCanvas
from app.pixel.spritesheet import AnimationClip

__all__ = ["AnimationParams", "animate_rig", "build_clips"]


class AnimationParams:
    """Parâmetros ajustáveis de cada clipe."""

    def __init__(
        self,
        *,
        idle_frames: int = 4,
        walk_frames: int = 4,
        death_frames: int = 6,
        idle_fps: int = 6,
        walk_fps: int = 8,
        death_fps: int = 10,
    ) -> None:
        self.idle_frames = max(2, int(idle_frames))
        self.walk_frames = max(2, int(walk_frames))
        self.death_frames = max(3, int(death_frames))
        self.idle_fps = max(1, int(idle_fps))
        self.walk_fps = max(1, int(walk_fps))
        self.death_fps = max(1, int(death_fps))


_HEAD_KINDS = (PartKind.HEAD, PartKind.FACE, PartKind.HAIR_FRONT, PartKind.HAIR_BACK, PartKind.HEADGEAR)
_LEG_KINDS = (PartKind.LEG_FRONT, PartKind.LEG_BACK, PartKind.EXTRA_LIMB_FRONT, PartKind.EXTRA_LIMB_BACK)
_ARM_KINDS = (PartKind.ARM_FRONT, PartKind.ARM_BACK)


def _is_head(layer: Layer) -> bool:
    return layer.kind in _HEAD_KINDS


def _is_leg(layer: Layer) -> bool:
    return layer.kind in _LEG_KINDS or layer.tags.get("leg", 0) == 1


def _is_arm(layer: Layer) -> bool:
    return layer.kind in _ARM_KINDS


def _is_body(layer: Layer) -> bool:
    return layer.kind == PartKind.TORSO or layer.tags.get("body", 0) == 1


def _is_wing(layer: Layer) -> bool:
    return layer.tags.get("wing", 0) == 1 or layer.kind in (PartKind.WING_BACK, PartKind.WING_FRONT)


def _is_tail(layer: Layer) -> bool:
    return layer.tags.get("tail", 0) == 1 or layer.kind in (PartKind.TAIL_BACK, PartKind.TAIL_FRONT)


def _phase(t: float, offset: float = 0.0) -> float:
    return math.sin((t + offset) * math.pi * 2)


def _ibob(value: float) -> int:
    return int(round(value))


# ----------------------------------------------------------------------
# IDLE
# ----------------------------------------------------------------------
def _idle_frame(rig: Rig, t: float, direction: Direction) -> Rig:
    posed = rig.clone()
    bob = _ibob(math.sin(t * math.pi * 2) * 0.9)
    is_blob = any(lay.tags.get("blob", 0) == 1 for lay in rig.layers)
    is_flyer = rig.archetype == "flyer"

    for layer in posed.layers:
        if layer.kind == PartKind.SHADOW:
            continue
        if is_blob and _is_body(layer):
            squash = math.sin(t * math.pi * 2)
            layer.scale_y = 1.0 + squash * 0.06
            layer.scale_x = 1.0 - squash * 0.05
            layer.dy = _ibob(-squash * 1.2)
        elif is_blob and layer.kind == PartKind.FACE:
            layer.dy = _ibob(-math.sin(t * math.pi * 2) * 1.4)
        elif _is_wing(layer):
            layer.angle = math.sin(t * math.pi * 2) * (6 if is_flyer else 2)
        elif _is_tail(layer):
            layer.angle = math.sin(t * math.pi * 2 + 0.25) * 4
        elif _is_head(layer):
            layer.dy = -bob
        elif _is_body(layer):
            layer.dy = -bob
        elif _is_arm(layer):
            layer.dy = -bob + _ibob(math.sin(t * math.pi * 2 + 0.5) * 0.6)
        elif _is_leg(layer):
            layer.dy = 0
        else:
            layer.dy = -bob
    return posed


# ----------------------------------------------------------------------
# WALK
# ----------------------------------------------------------------------
def _walk_frame(rig: Rig, t: float, direction: Direction) -> Rig:
    posed = rig.clone()
    profile = direction in (Direction.LEFT, Direction.RIGHT)
    frontal = not profile
    arch = rig.archetype

    bob = _ibob(abs(math.sin(t * math.pi * 2)) * (1.6 if profile else 1.0))
    is_blob = any(lay.tags.get("blob", 0) == 1 for lay in rig.layers)
    is_flyer = arch == "flyer"
    is_serpent = arch == "serpent"

    if is_blob:
        squash = math.sin(t * math.pi * 4)
        for layer in posed.layers:
            if layer.kind == PartKind.SHADOW:
                continue
            if _is_body(layer):
                layer.scale_y = 1.0 + squash * 0.10
                layer.scale_x = 1.0 - squash * 0.08
                layer.dx = _ibob(math.sin(t * math.pi * 2) * 1.2)
            elif layer.kind == PartKind.FACE:
                layer.dy = _ibob(-squash * 1.6)
                layer.dx = _ibob(math.sin(t * math.pi * 2) * 1.2)
        return posed

    if is_serpent:
        for layer in posed.layers:
            seg = layer.tags.get("segment")
            if seg is not None:
                layer.dx = _ibob(math.sin(t * math.pi * 2 + int(seg) * 0.35) * 1.6)
                layer.dy = _ibob(math.cos(t * math.pi * 2 + int(seg) * 0.35) * 0.8)
            elif _is_head(layer):
                layer.dx = _ibob(math.sin(t * math.pi * 2 - 0.3) * 1.8)
            elif _is_tail(layer):
                layer.angle = math.sin(t * math.pi * 2 + 1.2) * 6
        return posed

    leg_amp = 27.0 if profile else 0.0
    arm_amp = 22.0 if profile else 0.0

    for layer in posed.layers:
        if layer.kind == PartKind.SHADOW:
            layer.scale_x = 1.0 + math.sin(t * math.pi * 4) * 0.03
            continue

        if is_flyer and _is_wing(layer):
            layer.angle = math.sin(t * math.pi * 4) * 14
            continue
        if _is_wing(layer):
            layer.angle = math.sin(t * math.pi * 4) * 8
            continue
        if _is_tail(layer):
            layer.angle = math.sin(t * math.pi * 2 + 0.3) * (7 if profile else 4)
            continue

        if _is_leg(layer):
            gait = int(layer.tags.get("gait", 0))
            far = layer.tags.get("far", 0)
            off = 0.0 if gait == 0 else 0.5
            if profile:
                amp = leg_amp * (0.8 if far else 1.0)
                layer.angle = _phase(t, off) * amp
                layer.dy = _ibob(-max(0.0, _phase(t, off)) * 1.0) - bob
            else:
                lift = max(0.0, _phase(t, off))
                layer.dy = -_ibob(lift * 2.0) - bob
                layer.dx = _ibob(_phase(t, off + 0.25) * (0.6 if frontal else 0))
            continue

        if _is_arm(layer):
            gait = int(layer.tags.get("gait", 1))
            off = 0.0 if gait == 0 else 0.5
            if profile:
                layer.angle = -_phase(t, off) * arm_amp
            else:
                layer.dy = -_ibob(max(0.0, -_phase(t, off)) * 1.0) - bob
                layer.dx = _ibob(_phase(t, off) * 0.7)
            continue

        if _is_head(layer):
            layer.dy = -bob + _ibob(math.sin(t * math.pi * 4) * 0.4)
            if is_flyer:
                layer.dy += _ibob(math.sin(t * math.pi * 4) * 1.0)
            continue

        if _is_body(layer):
            layer.dy = -bob
            if is_flyer:
                layer.dy += _ibob(math.sin(t * math.pi * 4) * 1.4)
            continue

        layer.dy = -bob

    return posed


# ----------------------------------------------------------------------
# DEATH (colapso sobre a imagem composta)
# ----------------------------------------------------------------------
def _death_frames(rig: Rig, count: int, direction: Direction) -> list[PixelCanvas]:
    base = compose_rig(rig)
    bbox = base.bbox()
    if bbox is None:
        return [PixelCanvas(rig.width, rig.height) for _ in range(count)]
    ground_x, ground_y = rig.joints.get("ground", (rig.width // 2, rig.height - 4))
    pivot = (float(ground_x), float(ground_y))

    frames: list[PixelCanvas] = []
    n = max(3, count)
    for i in range(n):
        t = i / (n - 1)
        canvas = PixelCanvas(rig.width, rig.height)
        if t <= 0.001:
            # quadro de impacto: leve clarão
            canvas = base.tint((255, 240, 230), 0.18)
        else:
            fall = min(1.0, t / 0.72)
            eased = fall * fall * (3 - 2 * fall)  # smoothstep
            angle = -84.0 * eased * (1 if direction != Direction.RIGHT else -1)
            squash = 1.0 - 0.55 * eased
            drop = eased * (rig.height - ground_y) * 0.35

            rotated = base.rotated(angle, pivot=pivot)
            # achata verticalmente (o corpo "assenta" no chão ao cair)
            new_h = max(2, int(round(rotated.height * squash)))
            shrunk = rotated.scaled(rotated.width, new_h)
            fb = shrunk.bbox()
            canvas = PixelCanvas(rig.width, rig.height)
            if fb is not None:
                dy = rig.height - 3 - fb[3]
                canvas.blit(shrunk, 0, dy)
            else:
                canvas = shrunk
            _ = drop
            if t > 0.72:
                fade_t = (t - 0.72) / 0.28
                canvas = canvas.multiply_alpha(1.0 - 0.45 * fade_t)
                canvas = canvas.desaturate(0.75 * fade_t)
        frames.append(canvas)
    return frames


# ----------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------
def animate_rig(
    rig: Rig,
    direction: Direction | str,
    params: AnimationParams | None = None,
    *,
    kinds: list[AnimationKind] | None = None,
) -> list[AnimationClip]:
    """Gera os clipes de animação de um rig em uma direção."""
    params = params or AnimationParams()
    direction = Direction(direction)
    kinds = kinds or [AnimationKind.IDLE, AnimationKind.WALK, AnimationKind.DEATH]
    clips: list[AnimationClip] = []

    if AnimationKind.IDLE in kinds:
        frames = [compose_rig(_idle_frame(rig, i / params.idle_frames, direction)) for i in range(params.idle_frames)]
        clips.append(AnimationClip(name="idle", frames_by_direction={direction.value: frames}, fps=params.idle_fps, loops=True))

    if AnimationKind.WALK in kinds:
        frames = [compose_rig(_walk_frame(rig, i / params.walk_frames, direction)) for i in range(params.walk_frames)]
        clips.append(AnimationClip(name="walk", frames_by_direction={direction.value: frames}, fps=params.walk_fps, loops=True))

    if AnimationKind.DEATH in kinds:
        frames = _death_frames(rig, params.death_frames, direction)
        clips.append(AnimationClip(name="death", frames_by_direction={direction.value: frames}, fps=params.death_fps, loops=False))

    return clips


def build_clips(
    rig_factory,
    *,
    directions: list[Direction] | None = None,
    params: AnimationParams | None = None,
    kinds: list[AnimationKind] | None = None,
) -> list[AnimationClip]:
    """Monta clipes agregados por direção usando uma fábrica ``direction -> rig``.

    ``rig_factory`` recebe uma :class:`Direction` e devolve o rig em pose
    neutra daquela direção. Os frames de cada direção são mesclados nos mesmos
    clipes (``idle`` terá ``down``, ``left``, ``right``, ``up``).
    """
    params = params or AnimationParams()
    directions = directions or [Direction.DOWN, Direction.LEFT, Direction.RIGHT, Direction.UP]
    kinds = kinds or [AnimationKind.IDLE, AnimationKind.WALK, AnimationKind.DEATH]

    merged: dict[str, AnimationClip] = {}
    for direction in directions:
        rig = rig_factory(direction)
        for clip in animate_rig(rig, direction, params, kinds=kinds):
            target = merged.get(clip.name)
            if target is None:
                merged[clip.name] = clip
            else:
                target.frames_by_direction.update(clip.frames_by_direction)
    return [merged[k.value] for k in kinds if k.value in merged]
