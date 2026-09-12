"""Construtor procedural de personagens humanoides.

Produz um :class:`~app.generator.rig.Rig` por direção a partir de um
:class:`~app.domain.models.ProceduralBlueprint`. O desenho é feito de baixo para
cima (pés -> quadril -> ombros -> cabeça) e escalado pelos parâmetros
``body_size`` / ``head_size`` / ``limb_thickness``, o que permite ir de um
halfling a um ogro sem trocar de código.

A direção ``right`` é gerada espelhando ``left``, garantindo simetria perfeita
e economizando metade do trabalho de autoria.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.rng import SeedRandom, stable_hash
from app.domain.models import BodyArchetype, Direction, ProceduralBlueprint
from app.domain.species import Species, get_species
from app.generator.colors import DEFAULT_OUTFIT_COLOR, SpriteColors, resolve_colors
from app.generator.procedural import parts as P
from app.generator.rig import Layer, PartKind, Rig
from app.pixel.canvas import PixelCanvas
from app.pixel.palette import PALETTES, Ramp, ramp_from_color

PALETTE_CLOTH_KEYS: frozenset[str] = frozenset(PALETTES["cloth"].ramps)

__all__ = ["BodyMetrics", "HumanoidBuilder", "build_humanoid_rig"]


@dataclass
class BodyMetrics:
    """Pontos anatômicos absolutos no quadro."""

    cx: float
    ground_y: float
    head_cx: float
    head_cy: float
    head_rx: float
    head_ry: float
    neck_y: float
    shoulder_y: float
    shoulder_half: float
    torso_top: float
    torso_h: float
    hip_y: float
    hip_half: float
    knee_y: float
    ankle_y: float
    limb: float
    profile: bool


def compute_metrics(
    bp: ProceduralBlueprint,
    species: Species,
    frame_w: int,
    frame_h: int,
    direction: Direction | str,
) -> BodyMetrics:
    profile = direction in (Direction.LEFT, Direction.RIGHT, "left", "right")

    body = float(bp.body_size) * float(species.body_size)
    head = float(bp.head_size) * float(species.head_size)
    limb = float(bp.limb_thickness) * float(species.limb_thickness)

    cx = frame_w / 2.0
    ground_y = frame_h - 4.0

    leg_len = 15.0 * body
    torso_h = 16.0 * body
    head_ry = 6.6 * head * body**0.3
    head_rx = (5.0 if profile else 6.3) * head * body**0.3

    hip_y = ground_y - leg_len
    torso_top = hip_y - torso_h
    shoulder_y = torso_top + 2.6
    neck_y = torso_top - 0.5
    head_cy = neck_y - head_ry - 0.6

    bulky = bp.archetype == BodyArchetype.HUMANOID_BRUTE
    shoulder_half = (9.4 if bulky else 8.1) * body * (0.60 if profile else 1.0)
    hip_half = (4.6 if bulky else 4.1) * body * (0.62 if profile else 1.0)

    return BodyMetrics(
        cx=cx,
        ground_y=ground_y,
        head_cx=cx - (1.0 if profile else 0.0),
        head_cy=head_cy,
        head_rx=head_rx,
        head_ry=head_ry,
        neck_y=neck_y,
        shoulder_y=shoulder_y,
        shoulder_half=shoulder_half,
        torso_top=torso_top,
        torso_h=torso_h,
        hip_y=hip_y,
        hip_half=hip_half,
        knee_y=hip_y + leg_len * 0.52,
        ankle_y=ground_y - 1.6,
        limb=2.9 * limb * body**0.5,
        profile=profile,
    )


class HumanoidBuilder:
    """Monta rigs humanoides em cada direção."""

    def __init__(
        self,
        blueprint: ProceduralBlueprint,
        *,
        species: Species | None = None,
        colors: SpriteColors | None = None,
        frame_width: int = 64,
        frame_height: int = 64,
    ) -> None:
        self.bp = blueprint
        self.species = species or get_species(blueprint.species)
        self.colors = colors or resolve_colors(blueprint.palette, self.species, blueprint.custom_colors)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.style = P.PartStyle(
            outline=bool(blueprint.outline),
            shading=bool(blueprint.shading),
            outline_color=tuple(self.colors.outline),
        )
        self.rng = SeedRandom(seed=(blueprint.seed or stable_hash(blueprint.species)) & 0xFFFFFFFF)

    # ------------------------------------------------------------------
    # Resolução de variações (determinística por seed)
    # ------------------------------------------------------------------
    def _resolve(self) -> dict[str, object]:
        bp, sp, rng = self.bp, self.species, self.rng
        hair = bp.hair_style or rng.choice(list(sp.hair_styles) or ["short"])
        outfit = bp.outfit if bp.outfit in (sp.outfits or ()) or not sp.outfits else rng.choice(list(sp.outfits))
        weapon = bp.weapon or (rng.choice([w for w in sp.weapons]) if sp.weapons and rng.chance(0.72) else None)
        offhand = bp.offhand
        if offhand is None and weapon and rng.chance(0.35):
            offhand = rng.choice(["shield", "buckler", "torch", "book", "orb"])
        headgear = bp.headgear
        if headgear is None and sp.headgear:
            headgear = rng.choice(list(sp.headgear))
        horns = bp.horns or (rng.choice(list(sp.horns)) if sp.horns and rng.chance(0.6) else None)
        tail = bp.tail or (rng.choice(list(sp.tails)) if sp.tails and rng.chance(0.6) else None)
        wings = bool(bp.wings or (sp.wings and rng.chance(0.8)))
        cape = bool(bp.cape or rng.chance(0.22))
        facial_hair = bool(bp.facial_hair or (bp.gender != "female" and rng.chance(0.28)))
        eyes = bp.eyes_style
        if eyes == "normal":
            if self.species.archetype == BodyArchetype.HUMANOID_BRUTE:
                eyes = "beast"
            elif "undead" in sp.tags or "infernal" in sp.tags:
                eyes = "glow"
        # a cor do vestuário vem do outfit, a menos que o blueprint traga uma
        # cor customizada ou uma rampa nomeada válida
        explicit_cloth = "cloth" in bp.custom_colors or bp.palette.cloth in PALETTE_CLOTH_KEYS
        cloth_ramp = self.colors.cloth if explicit_cloth else ramp_from_color(
            bp.custom_colors.get("outfit") or DEFAULT_OUTFIT_COLOR.get(outfit, DEFAULT_OUTFIT_COLOR["adventurer"]),
            name="cloth",
        )
        return {
            "hair": hair,
            "outfit": outfit,
            "weapon": weapon,
            "offhand": offhand,
            "headgear": headgear,
            "horns": horns,
            "tail": tail,
            "wings": wings,
            "cape": cape,
            "facial_hair": facial_hair,
            "eyes": eyes,
            "cloth_ramp": cloth_ramp,
        }

    # ------------------------------------------------------------------
    def build(self, direction: Direction | str = Direction.DOWN) -> Rig:
        direction = Direction(direction)
        draw_dir: Direction = Direction.LEFT if direction == Direction.RIGHT else direction
        rig = self._build_single(draw_dir)
        rig.direction = direction.value
        if direction == Direction.RIGHT:
            for layer in rig.layers:
                layer.canvas = layer.canvas.flipped_x()
                layer.pivot = (self.frame_width - 1 - layer.pivot[0], layer.pivot[1])
            rig.joints = {
                k: (self.frame_width - 1 - v[0], v[1]) for k, v in rig.joints.items()
            }
        return rig

    # ------------------------------------------------------------------
    def _build_single(self, direction: Direction) -> Rig:
        bp = self.bp
        sp = self.species
        v = self._resolve()
        m = compute_metrics(bp, sp, self.frame_width, self.frame_height, direction)
        profile = m.profile
        view = "profile" if profile else direction.value
        bulky = bp.archetype == BodyArchetype.HUMANOID_BRUTE

        rig = Rig(
            width=self.frame_width,
            height=self.frame_height,
            direction=direction.value,
            species=sp.key,
            archetype=bp.archetype.value,
            outline_color=tuple(self.colors.outline),
        )

        cloth_ramp: Ramp = v["cloth_ramp"]  # type: ignore[assignment]
        hair_style = str(v["hair"])
        outfit = str(v["outfit"])

        # ---------------- sombra de contato ----------------
        shadow_canvas = PixelCanvas(self.frame_width, self.frame_height)
        body_w = m.shoulder_half * 2.0 + 4
        P.draw_shadow(shadow_canvas, m.cx, m.ground_y + 0.5, body_w)
        rig.add(Layer(name="shadow", kind=PartKind.SHADOW, canvas=shadow_canvas, pivot=(int(m.cx), int(m.ground_y))))

        # ---------------- capa (traseira) ----------------
        if v["cape"]:
            layer = self._new_layer()
            self._draw_cape(layer, m, cloth_ramp, view)
            rig.add(self._finish(layer, "cape_back", PartKind.CAPE_BACK, pivot=(int(m.cx), int(m.torso_top + 2))))

        # ---------------- cauda (traseira) ----------------
        if v["tail"]:
            layer = self._new_layer()
            P.draw_tail(layer, str(v["tail"]), (m.cx + (2 if profile else 0), m.hip_y + 1), self.colors.creature, direction=view)
            rig.add(self._finish(layer, "tail_back", PartKind.TAIL_BACK, pivot=(int(m.cx), int(m.hip_y))))

        # ---------------- cabelo traseiro ----------------
        hair_back = self._new_layer()
        P.draw_hair_back(
            hair_back, m.head_cx, m.head_cy, m.head_rx, m.head_ry, self.colors.hair,
            style=hair_style, direction=view, length=bp.hair_length,
        )
        if not hair_back.is_empty():
            rig.add(self._finish(hair_back, "hair_back", PartKind.HAIR_BACK, pivot=(int(m.head_cx), int(m.head_cy))))

        # ---------------- asas (traseiras) ----------------
        if v["wings"]:
            layer = self._new_layer()
            P.draw_wings(layer, m.cx, m.torso_top + 4, m.shoulder_half * 1.9 + 4, self.colors.extras["shadow"], style="demon" if "infernal" in sp.tags else "feather", direction=view)
            rig.add(self._finish(layer, "wing_back", PartKind.WING_BACK, pivot=(int(m.cx), int(m.torso_top + 4))))

        # ---------------- perna traseira ----------------
        leg_back = self._new_layer()
        hip_bx = m.cx + (1.4 if profile else m.hip_half)
        self._draw_leg(leg_back, (hip_bx, m.hip_y), m, self.colors.leather, self.colors.skin, boots=True)
        rig.add(self._finish(leg_back, "leg_back", PartKind.LEG_BACK, pivot=(int(hip_bx), int(m.hip_y))))

        # ---------------- braço traseiro (+ escudo) ----------------
        arm_back = self._new_layer()
        sh_bx = m.cx + (1.2 if profile else m.shoulder_half - 0.8)
        hand_b = self._draw_arm(arm_back, (sh_bx, m.shoulder_y), m, cloth_ramp, self.colors.skin)
        if v["offhand"]:
            P.draw_offhand(arm_back, str(v["offhand"]), hand_b, self.colors.leather, self.colors.metal, direction=view)
        rig.add(self._finish(arm_back, "arm_back", PartKind.ARM_BACK, pivot=(int(sh_bx), int(m.shoulder_y))))
        rig.layers[-1].tags["hand"] = 1.0

        # ---------------- torso ----------------
        torso = self._new_layer()
        P.draw_torso(
            torso, m.cx, m.torso_top, m.shoulder_half * 2.0, m.torso_h, cloth_ramp,
            style=self.style, outfit=outfit, accent=self.colors.accent, bulky=bulky, direction=view,
        )
        if bulky:
            # pescoço grosso de bruto
            P.capsule(torso, (m.cx, m.torso_top), (m.head_cx, m.neck_y + 1), m.limb * 0.9, self.colors.skin.at(2))
        rig.add(self._finish(torso, "torso", PartKind.TORSO, pivot=(int(m.cx), int(m.hip_y))))

        # ---------------- perna dianteira ----------------
        leg_front = self._new_layer()
        hip_fx = m.cx - (1.4 if profile else m.hip_half)
        self._draw_leg(leg_front, (hip_fx, m.hip_y), m, self.colors.leather, self.colors.skin, boots=True)
        rig.add(self._finish(leg_front, "leg_front", PartKind.LEG_FRONT, pivot=(int(hip_fx), int(m.hip_y))))

        # ---------------- cabeça ----------------
        head = self._new_layer()
        head_shape = "profile" if profile else ("square" if bulky else "round")
        P.draw_head(head, m.head_cx, m.head_cy, m.head_rx, m.head_ry, self.colors.skin, shape=head_shape, style=self.style)
        # pescoço
        P.capsule(head, (m.cx, m.neck_y + 2), (m.head_cx, m.head_cy + m.head_ry * 0.7), m.limb * 0.62, self.colors.skin.at(3))
        # orelhas
        if not profile and sp.key == "elf":
            for sign in (-1, 1):
                P.blob(head, [(m.head_cx + sign * m.head_rx * 0.9, m.head_cy), (m.head_cx + sign * m.head_rx * 1.7, m.head_cy - m.head_ry * 0.7)], 1.2, self.colors.skin.at(2))
        elif profile:
            P.blob(head, [(m.head_cx + m.head_rx * 0.75, m.head_cy + 0.5), (m.head_cx + m.head_rx * 1.05, m.head_cy - 0.5)], 1.1, self.colors.skin.at(2))
        rig.add(self._finish(head, "head", PartKind.HEAD, pivot=(int(m.head_cx), int(m.neck_y)), outline=False))

        # ---------------- rosto ----------------
        face = self._new_layer()
        eye_style = str(v["eyes"])
        eye_y = m.head_cy + m.head_ry * 0.18
        spacing = m.head_rx * (0.42 if not profile else 0.55)
        P.draw_eyes(face, m.head_cx - (m.head_rx * 0.15 if profile else 0), eye_y, spacing, self.colors.eyes, style=eye_style, direction=view, scale=max(0.7, m.head_rx / 7.2))
        if direction != Direction.UP:
            mouth_y = m.head_cy + m.head_ry * 0.62
            if profile:
                P.draw_mouth(face, m.head_cx - m.head_rx * 0.42, mouth_y, 2, self.colors.skin.at(4), fangs=bulky)
                # nariz em perfil
                P.blob(face, [(m.head_cx - m.head_rx * 0.95, m.head_cy + m.head_ry * 0.1), (m.head_cx - m.head_rx * 1.15, m.head_cy + m.head_ry * 0.28)], 1.0, self.colors.skin.at(2))
            else:
                fangs = bulky or sp.key in ("orc", "demon", "troll", "goblin")
                P.draw_mouth(face, m.head_cx, mouth_y, max(2, int(m.head_rx * 0.5)), self.colors.skin.at(4), fangs=fangs)
        rig.add(Layer(name="face", kind=PartKind.FACE, canvas=face, pivot=(int(m.head_cx), int(m.head_cy))))

        # ---------------- cabelo frontal ----------------
        # capuz e elmo cobrem a cabeça: o cabelo frontal é suprimido para não
        # aparecer "atravessando" a cobertura
        hair_front = self._new_layer()
        if str(v["headgear"]) not in ("hood", "helm"):
            P.draw_hair(
                hair_front, m.head_cx, m.head_cy, m.head_rx, m.head_ry, self.colors.hair,
                style=hair_style, direction=view, length=bp.hair_length,
                facial_hair=bool(v["facial_hair"]),
            )
        elif bool(v["facial_hair"]):
            P.draw_hair(
                hair_front, m.head_cx, m.head_cy, m.head_rx, m.head_ry, self.colors.hair,
                style="bald", direction=view, facial_hair=True,
            )
        rig.add(self._finish(hair_front, "hair_front", PartKind.HAIR_FRONT, pivot=(int(m.head_cx), int(m.head_cy))))

        # ---------------- chifres ----------------
        if v["horns"]:
            horns = self._new_layer()
            horn_ramp = self.colors.extras["bone"]
            P.draw_horns(horns, str(v["horns"]), m.head_cx, m.head_cy, m.head_rx, m.head_ry, horn_ramp, direction=view)
            rig.add(self._finish(horns, "horns", PartKind.HEADGEAR, pivot=(int(m.head_cx), int(m.head_cy))))

        # ---------------- cobertura de cabeça ----------------
        if v["headgear"]:
            gear = self._new_layer()
            gear_ramp = self.colors.metal if str(v["headgear"]) in ("helm", "crown", "circlet") else (
                self.colors.cloth if str(v["headgear"]) in ("hood", "cap", "bandana") else self.colors.accent
            )
            P.draw_headgear(gear, str(v["headgear"]), m.head_cx, m.head_cy, m.head_rx, m.head_ry, gear_ramp, accent=self.colors.accent, direction=view, style=self.style)
            rig.add(self._finish(gear, "headgear", PartKind.HEADGEAR, pivot=(int(m.head_cx), int(m.neck_y))))

        # ---------------- braço dianteiro (+ arma) ----------------
        arm_front = self._new_layer()
        sh_fx = m.cx - (2.2 if profile else m.shoulder_half - 0.8)
        hand_f = self._draw_arm(arm_front, (sh_fx, m.shoulder_y), m, cloth_ramp, self.colors.skin)
        if v["weapon"]:
            P.draw_weapon(arm_front, str(v["weapon"]), hand_f, self.colors.extras["wood"], self.colors.metal, direction=view, outward=-1)
        rig.add(self._finish(arm_front, "arm_front", PartKind.ARM_FRONT, pivot=(int(sh_fx), int(m.shoulder_y))))

        # ---------------- capa frontal (gola) ----------------
        if v["cape"]:
            layer = self._new_layer()
            P.capsule(layer, (m.cx - m.shoulder_half, m.torso_top + 2), (m.cx + m.shoulder_half, m.torso_top + 2), 1.6, self.colors.cloth.at(3))
            rig.add(self._finish(layer, "cape_front", PartKind.CAPE_FRONT, pivot=(int(m.cx), int(m.torso_top + 2))))

        # ---------------- metadados ----------------
        rig.joints = {
            "head": (int(m.head_cx), int(m.head_cy)),
            "neck": (int(m.cx), int(m.neck_y)),
            "shoulder_front": (int(sh_fx), int(m.shoulder_y)),
            "shoulder_back": (int(sh_bx), int(m.shoulder_y)),
            "hand_front": (int(hand_f[0]), int(hand_f[1])),
            "hand_back": (int(hand_b[0]), int(hand_b[1])),
            "hip": (int(m.cx), int(m.hip_y)),
            "hip_front": (int(hip_fx), int(m.hip_y)),
            "hip_back": (int(hip_bx), int(m.hip_y)),
            "knee_front": (int(hip_fx), int(m.knee_y)),
            "knee_back": (int(hip_bx), int(m.knee_y)),
            "foot_front": (int(hip_fx), int(m.ankle_y)),
            "foot_back": (int(hip_bx), int(m.ankle_y)),
            "ground": (int(m.cx), int(m.ground_y)),
        }
        rig.proportions = {
            "height": m.ground_y - (m.head_cy - m.head_ry),
            "head_height": m.head_ry * 2,
            "torso_height": m.torso_h,
            "leg_length": m.ground_y - m.hip_y,
            "arm_length": abs(hand_f[1] - m.shoulder_y),
            "shoulder_width": m.shoulder_half * 2,
            "body_width": m.shoulder_half * 2 + 4,
            "stride": max(2.0, m.torso_h * 0.42),
        }
        rig.palette_colors = self.colors.all_colors()
        rig.outline_color = tuple(self.colors.outline)
        return rig

    # ------------------------------------------------------------------
    # Helpers de desenho
    # ------------------------------------------------------------------
    def _new_layer(self) -> PixelCanvas:
        return PixelCanvas(self.frame_width, self.frame_height)

    def _finish(self, canvas: PixelCanvas, name: str, kind: str, *, pivot: tuple[int, int], outline: bool = True) -> Layer:
        final = canvas
        if outline and self.style.outline:
            final = P.outline_layer(canvas, self.style.outline_color)
        return Layer(name=name, kind=kind, canvas=final, pivot=pivot)

    def _draw_arm(
        self,
        canvas: PixelCanvas,
        shoulder: tuple[float, float],
        m: BodyMetrics,
        cloth_ramp: Ramp,
        skin_ramp: Ramp,
    ) -> tuple[float, float]:
        """Desenha um braço articulado e retorna a posição da mão."""
        sx, sy = shoulder
        elbow = (sx + (-0.6 if m.profile else 0.4), sy + m.torso_h * 0.42)
        hand = (sx + (-1.0 if m.profile else 0.6), sy + m.torso_h * 0.86)
        # manga curta/longa conforme o vestuário
        sleeve_end = (sx + (elbow[0] - sx) * 0.75, sy + (elbow[1] - sy) * 0.75)
        P.capsule(canvas, (sx, sy), sleeve_end, m.limb * 0.62, cloth_ramp.at(2))
        P.draw_limb(canvas, (sx, sy), elbow, hand, m.limb * 1.3, skin_ramp, style=self.style, hand=True, hand_ramp=skin_ramp)
        # ombreira
        P.capsule(canvas, (sx, sy - 0.5), (sx + (0.4 if not m.profile else -0.2), sy + 1.2), m.limb * 0.72, cloth_ramp.at(1))
        return hand

    def _draw_leg(
        self,
        canvas: PixelCanvas,
        hip: tuple[float, float],
        m: BodyMetrics,
        leather_ramp: Ramp,
        skin_ramp: Ramp,
        *,
        boots: bool = True,
    ) -> None:
        """Desenha uma perna com bota opcional."""
        hx, hy = hip
        knee = (hx + (0.4 if m.profile else 0.2), m.knee_y)
        ankle = (hx + (0.8 if m.profile else 0.0), m.ankle_y)
        if boots:
            P.draw_limb(canvas, (hx, hy), knee, ankle, m.limb * 1.7, leather_ramp, style=self.style, foot=True, hand_ramp=leather_ramp)
        else:
            P.draw_limb(canvas, (hx, hy), knee, ankle, m.limb * 1.7, skin_ramp, style=self.style, foot=True, hand_ramp=skin_ramp)

    def _draw_cape(self, canvas: PixelCanvas, m: BodyMetrics, cloth_ramp: Ramp, view: str) -> None:
        wide = m.shoulder_half * (1.5 if not m.profile else 0.9)
        bottom = m.hip_y + m.torso_h * 0.85
        canvas.polygon(
            [
                (m.cx - wide, m.torso_top + 2),
                (m.cx + wide, m.torso_top + 2),
                (m.cx + wide * 1.12, bottom),
                (m.cx + wide * 0.3, bottom - 3),
                (m.cx - wide * 0.4, bottom + 1),
                (m.cx - wide * 1.12, bottom - 2),
            ],
            cloth_ramp.at(3),
        )
        canvas.polygon(
            [
                (m.cx - wide, m.torso_top + 2),
                (m.cx - wide * 0.1, m.torso_top + 2),
                (m.cx - wide * 0.35, bottom),
                (m.cx - wide * 1.12, bottom - 2),
            ],
            cloth_ramp.at(4),
        )
        _ = view


def build_humanoid_rig(
    blueprint: ProceduralBlueprint,
    direction: Direction | str = Direction.DOWN,
    *,
    frame_width: int = 64,
    frame_height: int = 64,
) -> Rig:
    """Função de conveniência: blueprint -> rig em uma direção."""
    return HumanoidBuilder(blueprint, frame_width=frame_width, frame_height=frame_height).build(direction)
