"""Construtor procedural de criaturas não-humanoides.

Cobre os arquétipos ``quadruped``, ``arachnid``, ``serpent``, ``flyer`` e
``blob``. Cada camada recebe **tags** semânticas (``leg``, ``gait``, ``wing``,
``tail``, ``segment``...) que o animador usa para aplicar o movimento correto
sem conhecer a anatomia específica — o mesmo mecanismo dos humanoides.
"""

from __future__ import annotations

import math

from app.core.rng import SeedRandom, stable_hash
from app.domain.models import BodyArchetype, Direction, ProceduralBlueprint
from app.domain.species import Species, get_species
from app.generator.colors import SpriteColors, resolve_colors
from app.generator.procedural import parts as P
from app.generator.rig import Layer, PartKind, Rig
from app.pixel.canvas import PixelCanvas
from app.pixel.palette import Ramp

__all__ = ["CreatureBuilder", "build_creature_rig"]


class CreatureBuilder:
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
    def build(self, direction: Direction | str = Direction.DOWN) -> Rig:
        direction = Direction(direction)
        draw_dir = Direction.LEFT if direction == Direction.RIGHT else direction
        arch = self.bp.archetype
        if arch == BodyArchetype.QUADRUPED:
            rig = self._quadruped(draw_dir)
        elif arch == BodyArchetype.ARACHNID:
            rig = self._arachnid(draw_dir)
        elif arch == BodyArchetype.SERPENT:
            rig = self._serpent(draw_dir)
        elif arch == BodyArchetype.FLYER:
            rig = self._flyer(draw_dir)
        elif arch == BodyArchetype.BLOB:
            rig = self._blob(draw_dir)
        else:  # BIPED / HUMANOID_BRUTE
            from app.generator.procedural.humanoid import HumanoidBuilder

            rig = HumanoidBuilder(
                self.bp, species=self.species, colors=self.colors,
                frame_width=self.frame_width, frame_height=self.frame_height,
            )._build_single(draw_dir)
        rig.direction = direction.value
        if direction == Direction.RIGHT:
            self._mirror(rig)
        return rig

    def _mirror(self, rig: Rig) -> None:
        for layer in rig.layers:
            layer.canvas = layer.canvas.flipped_x()
            layer.pivot = (self.frame_width - 1 - layer.pivot[0], layer.pivot[1])
        rig.joints = {k: (self.frame_width - 1 - v[0], v[1]) for k, v in rig.joints.items()}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _new(self) -> PixelCanvas:
        return PixelCanvas(self.frame_width, self.frame_height)

    def _add(self, rig: Rig, canvas: PixelCanvas, name: str, kind: str, pivot: tuple[int, int], *, outline: bool = True, tags: dict[str, float] | None = None) -> Layer:
        final = P.outline_layer(canvas, self.style.outline_color) if (outline and self.style.outline) else canvas
        layer = Layer(name=name, kind=kind, canvas=final, pivot=pivot, tags=tags or {})
        rig.add(layer)
        return layer

    def _metrics(self, direction: Direction) -> dict[str, float]:
        body = float(self.bp.body_size) * float(self.species.body_size)
        profile = direction in (Direction.LEFT, Direction.RIGHT)
        cx = self.frame_width / 2.0
        ground = self.frame_height - 5.0
        return {
            "body": body,
            "profile": 1.0 if profile else 0.0,
            "cx": cx,
            "ground": ground,
            "by": ground - 16.0 * body,          # centro vertical do corpo
            "brx": 11.0 * body,                  # raio horizontal do corpo
            "bry": 6.5 * body,                   # raio vertical do corpo
            "head_rx": 5.6 * body * float(self.species.head_size),
            "head_ry": 5.0 * body * float(self.species.head_size),
            "leg_len": 11.0 * body,
            "limb": 2.4 * body * float(self.species.limb_thickness),
        }

    def _ramp(self) -> Ramp:
        return self.colors.creature

    # ------------------------------------------------------------------
    # QUADRÚPEDE
    # ------------------------------------------------------------------
    def _quad_head(self, canvas: PixelCanvas, hx: float, hy: float, m: dict[str, float], view: str) -> None:
        ramp = self._ramp()
        rx, ry = m["head_rx"], m["head_ry"]
        P.draw_head(canvas, hx, hy, rx, ry, self.colors.creature, shape="round", style=self.style)
        # focinho
        if view == "profile":
            P.blob(canvas, [(hx - rx * 0.7, hy + ry * 0.1), (hx - rx * 1.5, hy + ry * 0.35)], rx * 0.42, ramp.at(2))
            canvas.set(int(hx - rx * 1.5), int(hy + ry * 0.2), (30, 26, 34))
        elif view == "down":
            P.blob(canvas, [(hx, hy + ry * 0.5), (hx, hy + ry * 1.05)], rx * 0.42, ramp.at(2))
            canvas.set(int(hx), int(hy + ry * 1.05), (30, 26, 34))
        # orelhas
        for sign in ((-1, 1) if view != "profile" else (1,)):
            P.blob(canvas, [(hx + sign * rx * 0.7, hy - ry * 0.6), (hx + sign * rx * 1.0, hy - ry * 1.35)], 1.3, ramp.at(3))
        # olhos
        eye_style = "glow" if ("infernal" in self.species.tags or "undead" in self.species.tags) else "beast"
        spacing = rx * (0.42 if view != "profile" else 0.5)
        P.draw_eyes(canvas, hx - (rx * 0.15 if view == "profile" else 0), hy - ry * 0.05, spacing, self.colors.eyes, style=eye_style, direction=view, scale=max(0.6, rx / 5.6))

    def _quad_leg(self, canvas: PixelCanvas, hip: tuple[float, float], m: dict[str, float], *, hind: bool, dark: bool) -> None:
        ramp = self._ramp()
        col = ramp.at(3) if dark else ramp.at(2)
        hx, hy = hip
        knee_off = 2.2 if hind else -1.2
        P.capsule(canvas, (hx, hy), (hx + knee_off, hy + m["leg_len"] * 0.5), m["limb"] * 0.6, col)
        P.capsule(canvas, (hx + knee_off, hy + m["leg_len"] * 0.5), (hx + knee_off * 0.4, hy + m["leg_len"]), m["limb"] * 0.5, col)
        P.draw_foot(canvas, hx + knee_off * 0.4, hy + m["leg_len"], m["limb"] * 0.8, m["limb"] * 0.5, ramp)

    def _quadruped(self, direction: Direction) -> Rig:
        m = self._metrics(direction)
        ramp = self._ramp()
        cx, by, brx, bry = m["cx"], m["by"], m["brx"], m["bry"]
        rig = Rig(width=self.frame_width, height=self.frame_height, direction=direction.value,
                  species=self.species.key, archetype="quadruped", outline_color=tuple(self.colors.outline))
        view = "profile" if direction in (Direction.LEFT, Direction.RIGHT) else direction.value

        shadow = self._new()
        P.draw_shadow(shadow, cx, m["ground"] + 0.5, brx * 2.4)
        self._add(rig, shadow, "shadow", PartKind.SHADOW, (int(cx), int(m["ground"])), outline=False)

        if view == "profile":
            # --- pernas do lado distante (atrás do corpo) ---
            for i, (lx, hind) in enumerate([(cx - brx * 0.55, False), (cx + brx * 0.62, True)]):
                c = self._new()
                self._quad_leg(c, (lx, by + bry * 0.4), m, hind=hind, dark=True)
                self._add(rig, c, f"leg_far_{i}", PartKind.LEG_BACK, (int(lx), int(by + bry * 0.4)),
                          tags={"leg": 1, "gait": i, "far": 1})
            # --- cauda ---
            tail = self._new()
            tail_kind = self.bp.tail or (self.species.tails[0] if self.species.tails else "bushy")
            P.draw_tail(tail, tail_kind, (cx + brx * 0.95, by - bry * 0.2), ramp, direction=view, length=m["body"])
            self._add(rig, tail, "tail", PartKind.TAIL_BACK, (int(cx + brx * 0.9), int(by)), tags={"tail": 1})
            # --- corpo ---
            body = self._new()
            P.blob(body, [(cx - brx * 0.5, by), (cx + brx * 0.2, by - bry * 0.15), (cx + brx * 0.85, by + bry * 0.1)], bry * 0.95, (0, 0, 0, 255))
            P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
            # pelagem/espinhos no dorso
            for i in range(max(0, self.bp.spikes)):
                t = i / max(1, self.bp.spikes - 1)
                sx = cx - brx * 0.5 + t * brx * 1.3
                P.blob(body, [(sx, by - bry * 0.85), (sx + 0.6, by - bry * 1.5)], 1.0, ramp.at(4))
            self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(by)), tags={"body": 1})
            # --- pernas próximas ---
            for i, (lx, hind) in enumerate([(cx - brx * 0.62, False), (cx + brx * 0.72, True)]):
                c = self._new()
                self._quad_leg(c, (lx, by + bry * 0.5), m, hind=hind, dark=False)
                self._add(rig, c, f"leg_near_{i}", PartKind.LEG_FRONT, (int(lx), int(by + bry * 0.5)),
                          tags={"leg": 1, "gait": 1 - i, "near": 1})
            # --- cabeça ---
            head = self._new()
            hx, hy = cx - brx * 1.05, by - bry * 1.05
            P.capsule(head, (cx - brx * 0.7, by - bry * 0.5), (hx + m["head_rx"] * 0.5, hy + m["head_ry"] * 0.4), m["limb"] * 0.8, ramp.at(2))
            self._quad_head(head, hx, hy, m, view)
            if self.bp.horns or self.species.horns:
                P.draw_horns(head, self.bp.horns or self.species.horns[0], hx, hy, m["head_rx"], m["head_ry"], self.colors.extras["bone"], direction=view)
            self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy + m["head_ry"])), tags={"head": 1}, outline=False)
        elif view == "down":
            # vista frontal: cabeça à frente, corpo atrás, 4 patas
            for i, (lx, hind) in enumerate([(cx - brx * 0.75, True), (cx + brx * 0.75, True)]):
                c = self._new()
                self._quad_leg(c, (lx, by + bry * 0.2), m, hind=hind, dark=True)
                self._add(rig, c, f"leg_far_{i}", PartKind.LEG_BACK, (int(lx), int(by)), tags={"leg": 1, "gait": i, "far": 1})
            body = self._new()
            body.ellipse(cx, by + bry * 0.2, brx * 0.72, bry * 0.9, (0, 0, 0, 255))
            P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
            self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(by)), tags={"body": 1})
            for i, (lx, hind) in enumerate([(cx - brx * 0.62, False), (cx + brx * 0.62, False)]):
                c = self._new()
                self._quad_leg(c, (lx, by + bry * 0.6), m, hind=hind, dark=False)
                self._add(rig, c, f"leg_near_{i}", PartKind.LEG_FRONT, (int(lx), int(by + bry * 0.6)), tags={"leg": 1, "gait": 1 - i, "near": 1})
            head = self._new()
            hx, hy = cx, by - bry * 1.1
            self._quad_head(head, hx, hy, m, view)
            if self.bp.horns or self.species.horns:
                P.draw_horns(head, self.bp.horns or self.species.horns[0], hx, hy, m["head_rx"], m["head_ry"], self.colors.extras["bone"], direction=view)
            self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy + m["head_ry"])), tags={"head": 1}, outline=False)
        else:  # up
            body = self._new()
            body.ellipse(cx, by, brx * 0.78, bry * 0.95, (0, 0, 0, 255))
            P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
            self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(by)), tags={"body": 1})
            tail = self._new()
            tail_kind = self.bp.tail or (self.species.tails[0] if self.species.tails else "bushy")
            P.draw_tail(tail, tail_kind, (cx, by + bry * 0.8), ramp, direction=view, length=m["body"])
            self._add(rig, tail, "tail", PartKind.TAIL_BACK, (int(cx), int(by + bry * 0.6)), tags={"tail": 1})
            for i, lx in enumerate([cx - brx * 0.6, cx + brx * 0.6]):
                c = self._new()
                self._quad_leg(c, (lx, by + bry * 0.5), m, hind=True, dark=False)
                self._add(rig, c, f"leg_near_{i}", PartKind.LEG_FRONT, (int(lx), int(by + bry * 0.5)), tags={"leg": 1, "gait": 1 - i, "near": 1})
            head = self._new()
            hx, hy = cx, by - bry * 1.5
            P.draw_head(head, hx, hy, m["head_rx"] * 0.9, m["head_ry"] * 0.85, ramp, shape="round", style=self.style)
            for sign in (-1, 1):
                P.blob(head, [(hx + sign * m["head_rx"] * 0.7, hy - m["head_ry"] * 0.6), (hx + sign * m["head_rx"], hy - m["head_ry"] * 1.3)], 1.3, ramp.at(3))
            self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy + m["head_ry"])), tags={"head": 1}, outline=False)

        self._finalize(rig, m)
        return rig

    # ------------------------------------------------------------------
    # ARACNÍDEO
    # ------------------------------------------------------------------
    def _arachnid(self, direction: Direction) -> Rig:
        m = self._metrics(direction)
        ramp = self._ramp()
        cx, by = m["cx"], m["by"] + 2
        rig = Rig(width=self.frame_width, height=self.frame_height, direction=direction.value,
                  species=self.species.key, archetype="arachnid", outline_color=tuple(self.colors.outline))
        view = "profile" if direction in (Direction.LEFT, Direction.RIGHT) else direction.value

        shadow = self._new()
        P.draw_shadow(shadow, cx, m["ground"] + 0.5, m["brx"] * 2.0)
        self._add(rig, shadow, "shadow", PartKind.SHADOW, (int(cx), int(m["ground"])), outline=False)

        leg_count = 4 + max(0, min(4, self.bp.extra_limbs // 2))
        # pernas distantes
        for i in range(leg_count):
            t = (i / max(1, leg_count - 1)) - 0.5
            c = self._new()
            self._spider_leg(c, (cx + t * m["brx"] * 1.2, by), m, side=-1, dark=True, index=i)
            self._add(rig, c, f"leg_far_{i}", PartKind.LEG_BACK, (int(cx + t * m["brx"]), int(by)), tags={"leg": 1, "gait": i % 2, "far": 1})
        # abdome + cefalotórax
        body = self._new()
        body.ellipse(cx + m["brx"] * 0.45, by - m["bry"] * 0.2, m["brx"] * 0.62, m["bry"] * 0.85, (0, 0, 0, 255))
        body.ellipse(cx - m["brx"] * 0.45, by, m["brx"] * 0.42, m["bry"] * 0.6, (0, 0, 0, 255))
        P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
        # marca no abdome
        body.ellipse(cx + m["brx"] * 0.5, by - m["bry"] * 0.45, m["brx"] * 0.16, m["bry"] * 0.22, ramp.at(1))
        self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(by)), tags={"body": 1})
        # pernas próximas
        for i in range(leg_count):
            t = (i / max(1, leg_count - 1)) - 0.5
            c = self._new()
            self._spider_leg(c, (cx + t * m["brx"] * 1.2, by + 1), m, side=1, dark=False, index=i)
            self._add(rig, c, f"leg_near_{i}", PartKind.LEG_FRONT, (int(cx + t * m["brx"]), int(by + 1)), tags={"leg": 1, "gait": (i + 1) % 2, "near": 1})
        # cabeça + quelíceras
        head = self._new()
        hx, hy = cx - m["brx"] * 0.95, by + m["bry"] * 0.1
        head.ellipse(hx, hy, m["head_rx"] * 0.8, m["head_ry"] * 0.7, (0, 0, 0, 255))
        P.shade_by_light(head, ramp, bbox=head.bbox(), style=self.style)
        cluster = 4 if view != "profile" else 2
        for i in range(cluster):
            ex = hx - m["head_rx"] * 0.35 + (i % 2) * m["head_rx"] * 0.5
            ey = hy - m["head_ry"] * 0.25 + (i // 2) * m["head_ry"] * 0.4
            head.rect(int(ex), int(ey), 1, 1, self.colors.eyes.at(-1))
            head.rect(int(ex), int(ey), 1, 1, self.colors.eyes.at(2))
        for offset in (-0.5, 0.5):
            P.blob(head, [(hx - m["head_rx"] * 0.5, hy + m["head_ry"] * (0.5 + offset)), (hx - m["head_rx"] * 0.8, hy + m["head_ry"] * (1.2 + offset))], 0.9, (235, 230, 210))
        self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy)), tags={"head": 1}, outline=False)

        self._finalize(rig, m)
        return rig

    def _spider_leg(self, canvas: PixelCanvas, hip: tuple[float, float], m: dict[str, float], *, side: int, dark: bool, index: int) -> None:
        ramp = self._ramp()
        col = ramp.at(4) if dark else ramp.at(3)
        hx, hy = hip
        spread = (index - 1.5) * 0.5
        up_x = hx + spread * m["brx"] * 0.42 - side * m["brx"] * 0.30
        up_y = hy - m["leg_len"] * 0.55
        mid_x = hx + spread * m["brx"] * 0.72 - side * m["brx"] * 0.56
        mid_y = hy - m["leg_len"] * 0.2
        foot_x = hx + spread * m["brx"] * 0.86 - side * m["brx"] * 0.70
        foot_y = m["ground"] - 1
        P.capsule(canvas, (hx, hy), (up_x, up_y), m["limb"] * 0.42, col)
        P.capsule(canvas, (up_x, up_y), (mid_x, mid_y), m["limb"] * 0.36, col)
        P.capsule(canvas, (mid_x, mid_y), (foot_x, foot_y), m["limb"] * 0.3, col)

    # ------------------------------------------------------------------
    # SERPENTE
    # ------------------------------------------------------------------
    def _serpent(self, direction: Direction) -> Rig:
        m = self._metrics(direction)
        ramp = self._ramp()
        cx, ground = m["cx"], m["ground"]
        rig = Rig(width=self.frame_width, height=self.frame_height, direction=direction.value,
                  species=self.species.key, archetype="serpent", outline_color=tuple(self.colors.outline))
        view = "profile" if direction in (Direction.LEFT, Direction.RIGHT) else direction.value

        shadow = self._new()
        P.draw_shadow(shadow, cx, ground + 0.5, m["brx"] * 2.0)
        self._add(rig, shadow, "shadow", PartKind.SHADOW, (int(cx), int(ground)), outline=False)

        segments = 5
        for i in range(segments):
            t = i / (segments - 1)
            c = self._new()
            if view == "profile":
                sx = cx + m["brx"] * (0.9 - t * 1.9)
                sy = ground - 3 - math.sin(t * math.pi) * m["bry"] * (1.4 + t)
                rad = m["bry"] * (0.55 + 0.45 * (1 - t))
            else:
                sx = cx + math.sin(t * math.pi * 1.2) * m["brx"] * 0.5 * (1 if view == "down" else -1)
                sy = ground - 3 - t * m["bry"] * 2.2
                rad = m["bry"] * (0.55 + 0.4 * (1 - t))
            c.ellipse(sx, sy, rad, rad * 0.9, (0, 0, 0, 255))
            P.shade_by_light(c, ramp, bbox=c.bbox(), style=self.style)
            if i == segments - 1:
                P.draw_tail(c, "snake", (sx, sy), ramp, direction=view, length=m["body"] * 0.6)
            self._add(rig, c, f"seg_{i}", PartKind.TORSO, (int(sx), int(sy)), tags={"segment": i, "body": 1})
        # cabeça no topo/frente
        head = self._new()
        if view == "profile":
            hx, hy = cx - m["brx"] * 1.0, ground - 3 - m["bry"] * 1.1
        else:
            hx, hy = cx, ground - 3 - m["bry"] * 2.4
        P.draw_head(head, hx, hy, m["head_rx"] * 0.95, m["head_ry"] * 0.85, ramp, shape="round", style=self.style)
        P.draw_eyes(head, hx, hy - m["head_ry"] * 0.1, m["head_rx"] * 0.42, self.colors.eyes, style="beast", direction=view, scale=0.8)
        # língua
        head.vline(int(hx), int(hy + m["head_ry"] * 0.8), 3, (220, 60, 70))
        head.set(int(hx) - 1, int(hy + m["head_ry"] * 0.8) + 2, (220, 60, 70))
        head.set(int(hx) + 1, int(hy + m["head_ry"] * 0.8) + 2, (220, 60, 70))
        self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy)), tags={"head": 1}, outline=False)

        self._finalize(rig, m)
        return rig

    # ------------------------------------------------------------------
    # VOADOR
    # ------------------------------------------------------------------
    def _flyer(self, direction: Direction) -> Rig:
        m = self._metrics(direction)
        ramp = self._ramp()
        cx, by = m["cx"], m["by"] - 2
        rig = Rig(width=self.frame_width, height=self.frame_height, direction=direction.value,
                  species=self.species.key, archetype="flyer", outline_color=tuple(self.colors.outline))
        view = "profile" if direction in (Direction.LEFT, Direction.RIGHT) else direction.value

        shadow = self._new()
        P.draw_shadow(shadow, cx, m["ground"] + 0.5, m["brx"] * 1.4, alpha=50)
        self._add(rig, shadow, "shadow", PartKind.SHADOW, (int(cx), int(m["ground"])), outline=False)

        # asas traseiras
        wings = self._new()
        wing_style = "bat" if self.species.key in ("bat", "ghost") else ("demon" if "infernal" in self.species.tags or self.species.key == "dragon" else "feather")
        P.draw_wings(wings, cx, by, m["brx"] * 1.4 + 4, ramp, style=wing_style, direction=view)
        self._add(rig, wings, "wings", PartKind.WING_BACK, (int(cx), int(by)), tags={"wing": 1})
        # corpo
        body = self._new()
        body.ellipse(cx, by, m["brx"] * 0.62, m["bry"] * 0.95, (0, 0, 0, 255))
        P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
        for i in range(max(0, self.bp.spikes)):
            t = i / max(1, self.bp.spikes - 1)
            sx = cx - m["brx"] * 0.4 + t * m["brx"] * 0.8
            P.blob(body, [(sx, by - m["bry"] * 0.8), (sx, by - m["bry"] * 1.3)], 0.9, ramp.at(4))
        self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(by)), tags={"body": 1})
        # patas pequenas
        for sign in (-1, 1):
            c = self._new()
            P.capsule(c, (cx + sign * m["brx"] * 0.3, by + m["bry"] * 0.6), (cx + sign * m["brx"] * 0.35, by + m["bry"] * 1.3), m["limb"] * 0.4, ramp.at(3))
            self._add(rig, c, f"leg_{'l' if sign < 0 else 'r'}", PartKind.LEG_FRONT, (int(cx + sign * m["brx"] * 0.3), int(by + m["bry"] * 0.6)), tags={"leg": 1, "gait": 0 if sign < 0 else 1})
        # cauda
        tail_kind = self.bp.tail or (self.species.tails[0] if self.species.tails else None)
        if tail_kind:
            tail = self._new()
            P.draw_tail(tail, tail_kind, (cx, by + m["bry"] * 0.8), ramp, direction=view, length=m["body"])
            self._add(rig, tail, "tail", PartKind.TAIL_BACK, (int(cx), int(by + m["bry"] * 0.6)), tags={"tail": 1})
        # cabeça
        head = self._new()
        hx, hy = cx - (m["brx"] * 0.55 if view == "profile" else 0), by - m["bry"] * 1.0
        self._quad_head(head, hx, hy, m, view)
        if self.bp.horns or self.species.horns:
            P.draw_horns(head, self.bp.horns or self.species.horns[0], hx, hy, m["head_rx"], m["head_ry"], self.colors.extras["bone"], direction=view)
        self._add(rig, head, "head", PartKind.HEAD, (int(hx), int(hy + m["head_ry"])), tags={"head": 1}, outline=False)

        self._finalize(rig, m)
        return rig

    # ------------------------------------------------------------------
    # BLOB / SLIME
    # ------------------------------------------------------------------
    def _blob(self, direction: Direction) -> Rig:
        m = self._metrics(direction)
        ramp = self._ramp()
        cx, ground = m["cx"], m["ground"]
        rig = Rig(width=self.frame_width, height=self.frame_height, direction=direction.value,
                  species=self.species.key, archetype="blob", outline_color=tuple(self.colors.outline))

        shadow = self._new()
        P.draw_shadow(shadow, cx, ground + 0.5, m["brx"] * 1.6, alpha=60)
        self._add(rig, shadow, "shadow", PartKind.SHADOW, (int(cx), int(ground)), outline=False)

        body = self._new()
        h = m["bry"] * 2.0 * m["body"]
        w = m["brx"] * 1.15 * m["body"]
        body.ellipse(cx, ground - h * 0.5, w, h * 0.55, (0, 0, 0, 255))
        body.ellipse(cx, ground - h * 0.35, w * 1.05, h * 0.35, (0, 0, 0, 255))
        P.shade_by_light(body, ramp, bbox=body.bbox(), style=self.style)
        # brilho gelatinoso
        body.ellipse(cx - w * 0.35, ground - h * 0.72, w * 0.2, h * 0.14, ramp.at(0))
        # bolhas internas
        body.circle(cx + w * 0.3, ground - h * 0.35, max(1.0, w * 0.12), ramp.at(1))
        self._add(rig, body, "body", PartKind.TORSO, (int(cx), int(ground - h * 0.4)), tags={"body": 1, "blob": 1})

        face = self._new()
        eye_y = ground - h * 0.62
        if direction != Direction.UP:
            spacing = w * (0.34 if direction != Direction.LEFT else 0.3)
            P.draw_eyes(face, cx - (w * 0.15 if direction == Direction.LEFT else 0), eye_y, spacing, self.colors.eyes, style="normal", direction=direction.value, scale=0.9)
            P.draw_mouth(face, cx - (w * 0.2 if direction == Direction.LEFT else 0), eye_y + h * 0.22, 3, self.colors.eyes.at(-1))
        self._add(rig, face, "face", PartKind.FACE, (int(cx), int(eye_y)))

        self._finalize(rig, m)
        return rig

    # ------------------------------------------------------------------
    def _finalize(self, rig: Rig, m: dict[str, float]) -> None:
        cx, by = m["cx"], m["by"]
        rig.joints = {
            "body": (int(cx), int(by)),
            "head": (int(cx - m["brx"]), int(by - m["bry"])),
            "ground": (int(cx), int(m["ground"])),
        }
        rig.proportions = {
            "height": m["ground"] - (by - m["bry"] * 2.2),
            "body_width": m["brx"] * 2,
            "body_height": m["bry"] * 2,
            "leg_length": m["leg_len"],
            "stride": max(2.0, m["leg_len"] * 0.5),
        }
        rig.palette_colors = self.colors.all_colors()
        rig.outline_color = tuple(self.colors.outline)


def build_creature_rig(
    blueprint: ProceduralBlueprint,
    direction: Direction | str = Direction.DOWN,
    *,
    frame_width: int = 64,
    frame_height: int = 64,
) -> Rig:
    return CreatureBuilder(blueprint, frame_width=frame_width, frame_height=frame_height).build(direction)
