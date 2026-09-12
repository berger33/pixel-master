"""Rig de camadas — representação animável de um sprite.

Um sprite do Pixel Master não é uma imagem única: é um conjunto de **camadas**
(cabeça, torso, braço da frente, braço de trás, perna da frente, perna de trás,
arma, capa, cabelo traseiro...) cada uma com um **pivô** de rotação e uma
ordem de empilhamento (``z``).

Essa representação é o ponto de encontro dos dois modos do produto:

* no modo **procedural**, as camadas são desenhadas do zero por primitivas;
* no modo **foto de IA**, as camadas são recortadas da imagem importada por
  segmentação de silhueta.

Em ambos os casos o mesmo ``Animator`` produz ``idle``, ``walk`` (4 direções) e
``death``, garantindo consistência de movimento entre personagens gerados por
caminhos diferentes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.pixel.canvas import PixelCanvas

__all__ = ["Layer", "Rig", "PartKind", "compose_rig"]


class PartKind:
    """Nomes canônicos de partes — a ordem aqui é a ordem de desenho padrão."""

    SHADOW = "shadow"
    TAIL_BACK = "tail_back"
    WING_BACK = "wing_back"
    CAPE_BACK = "cape_back"
    HAIR_BACK = "hair_back"
    LEG_BACK = "leg_back"
    ARM_BACK = "arm_back"
    EXTRA_LIMB_BACK = "extra_limb_back"
    TORSO = "torso"
    HEAD = "head"
    HAIR_FRONT = "hair_front"
    HEADGEAR = "headgear"
    FACE = "face"
    LEG_FRONT = "leg_front"
    ARM_FRONT = "arm_front"
    EXTRA_LIMB_FRONT = "extra_limb_front"
    WING_FRONT = "wing_front"
    CAPE_FRONT = "cape_front"
    WEAPON = "weapon"
    OFFHAND = "offhand"
    TAIL_FRONT = "tail_front"
    EFFECT = "effect"


# ordem de empilhamento (z crescente = desenhado por cima)
Z_ORDER: tuple[str, ...] = (
    PartKind.SHADOW,
    PartKind.TAIL_BACK,
    PartKind.WING_BACK,
    PartKind.CAPE_BACK,
    PartKind.HAIR_BACK,
    PartKind.LEG_BACK,
    PartKind.ARM_BACK,
    PartKind.EXTRA_LIMB_BACK,
    PartKind.TORSO,
    PartKind.LEG_FRONT,
    PartKind.HEAD,
    PartKind.FACE,
    PartKind.HAIR_FRONT,
    PartKind.HEADGEAR,
    PartKind.CAPE_FRONT,
    PartKind.ARM_FRONT,
    PartKind.EXTRA_LIMB_FRONT,
    PartKind.WING_FRONT,
    PartKind.OFFHAND,
    PartKind.WEAPON,
    PartKind.TAIL_FRONT,
    PartKind.EFFECT,
)

_Z_INDEX = {name: i for i, name in enumerate(Z_ORDER)}


def z_for(kind: str) -> int:
    return _Z_INDEX.get(kind, len(Z_ORDER))


@dataclass
class Layer:
    """Uma parte do sprite com pivô de articulação."""

    name: str
    kind: str
    canvas: PixelCanvas
    pivot: tuple[int, int] = (0, 0)
    z: int | None = None
    # transformações de pose aplicadas antes da composição
    dx: int = 0
    dy: int = 0
    angle: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    opacity: float = 1.0
    flip_x: bool = False
    tags: dict[str, float] = field(default_factory=dict)

    @property
    def z_index(self) -> int:
        return self.z if self.z is not None else z_for(self.kind)

    def transformed(self) -> PixelCanvas:
        """Aplica a pose da camada preservando o tamanho original da tela."""
        out = self.canvas
        if self.flip_x:
            out = out.flipped_x()
        if abs(self.scale_x - 1.0) > 1e-6 or abs(self.scale_y - 1.0) > 1e-6:
            new_w = max(1, int(round(out.width * self.scale_x)))
            new_h = max(1, int(round(out.height * self.scale_y)))
            scaled = out.scaled(new_w, new_h)
            holder = PixelCanvas(out.width, out.height)
            # mantém o pivô fixo durante a escala
            px = int(self.pivot[0] * self.scale_x)
            py = int(self.pivot[1] * self.scale_y)
            holder.blit(scaled, self.pivot[0] - px, self.pivot[1] - py)
            out = holder
        if abs(self.angle) > 1e-6:
            out = out.rotated(self.angle, pivot=self.pivot)
        if self.dx or self.dy:
            out = out.translated(self.dx, self.dy)
        if self.opacity < 0.999:
            out = out.multiply_alpha(self.opacity)
        return out

    def copy(self) -> Layer:
        return Layer(
            name=self.name,
            kind=self.kind,
            canvas=self.canvas.copy(),
            pivot=self.pivot,
            z=self.z,
            dx=self.dx,
            dy=self.dy,
            angle=self.angle,
            scale_x=self.scale_x,
            scale_y=self.scale_y,
            opacity=self.opacity,
            flip_x=self.flip_x,
            tags=dict(self.tags),
        )


@dataclass
class Rig:
    """Conjunto de camadas + metadados de um sprite animável."""

    width: int = 64
    height: int = 64
    layers: list[Layer] = field(default_factory=list)
    direction: str = "down"
    species: str = "human"
    archetype: str = "biped"
    # pontos de referência anatômica (pixels absolutos no quadro)
    joints: dict[str, tuple[int, int]] = field(default_factory=dict)
    palette_colors: list[tuple[int, int, int]] = field(default_factory=list)
    outline_color: tuple[int, int, int] = (24, 22, 32)
    # proporções medidas, usadas pelo animador para escalar o movimento
    proportions: dict[str, float] = field(default_factory=dict)

    def add(self, layer: Layer) -> None:
        self.layers.append(layer)

    def layer(self, kind: str) -> Layer | None:
        for candidate in sorted(self.layers, key=lambda lay: lay.z_index):
            if candidate.kind == kind:
                return candidate
        return None

    def layers_of(self, kind: str) -> list[Layer]:
        return [lay for lay in sorted(self.layers, key=lambda lay: lay.z_index) if lay.kind == kind]

    def joint(self, name: str, default: tuple[int, int] = (0, 0)) -> tuple[int, int]:
        return self.joints.get(name, default)

    def sorted_layers(self) -> list[Layer]:
        return sorted(self.layers, key=lambda lay: (lay.z_index, lay.name))

    def pose(self, **transforms: dict[str, object]) -> Rig:
        """Retorna uma cópia do rig com poses sobrepostas por nome de camada."""
        clone = self.clone()
        for layer in clone.layers:
            spec = transforms.get(layer.name)
            if not spec:
                continue
            layer.dx = int(spec.get("dx", layer.dx))
            layer.dy = int(spec.get("dy", layer.dy))
            layer.angle = float(spec.get("angle", layer.angle))
            layer.scale_x = float(spec.get("scale_x", layer.scale_x))
            layer.scale_y = float(spec.get("scale_y", layer.scale_y))
            layer.opacity = float(spec.get("opacity", layer.opacity))
            if "flip_x" in spec:
                layer.flip_x = bool(spec["flip_x"])
        return clone

    def clone(self) -> Rig:
        return Rig(
            width=self.width,
            height=self.height,
            layers=[lay.copy() for lay in self.layers],
            direction=self.direction,
            species=self.species,
            archetype=self.archetype,
            joints=dict(self.joints),
            palette_colors=list(self.palette_colors),
            outline_color=self.outline_color,
            proportions=dict(self.proportions),
        )


def compose_rig(rig: Rig) -> PixelCanvas:
    """Compõe todas as camadas em um único quadro na ordem correta de z."""
    out = PixelCanvas(rig.width, rig.height)
    for layer in rig.sorted_layers():
        transformed = layer.transformed()
        if transformed.width == out.width and transformed.height == out.height:
            out.blend_region(0, 0, transformed.data)
        else:
            out.blit(transformed, 0, 0)
    return out


def compose_layers(width: int, height: int, layers: Iterable[Layer]) -> PixelCanvas:
    out = PixelCanvas(width, height)
    for layer in sorted(layers, key=lambda lay: lay.z_index):
        transformed = layer.transformed()
        out.blend_region(0, 0, transformed.data)
    return out
