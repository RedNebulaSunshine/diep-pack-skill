#!/usr/bin/env python3
"""compose.py: build .diep-pack tanks from geometric intent instead of hand-typed numbers.

A design script does:

    import sys; sys.path.insert(0, "/path/to/diep-pack/scripts")   # this skill's scripts folder
    from compose import Design, polar, arc, bezier, C

    d = Design("Dragonfly", level=45, parents=[6])
    d.hull(size=34, color=C.forest)                        # thorax
    d.shape(6, 26, at=(58, 0), color=C.forest, name="head")
    d.chain(arc((0, 0), 60, 180, 150, 8), sizes=(22, 8), sides=6, color=C.forest, name="abdomen")
    wing = d.rod((10, 20), (70, 190), width=34, end_width=14, color=C.silver, name="fore wing")
    d.mirror(wing)
    d.weapon(length=95, projectile=d.projectile("Bullet"))
    d.save()                                                 # writes, validates, renders

Conventions (all confirmed in references/schema/ unless marked GUESS):
  * coordinates are tank units: x forward, y to the tank's RIGHT (screen y-down), hull radius 50
  * angles in this module are DEGREES, clockwise positive, 0 = forward; JSON gets radians
  * every part gets a unique editor name (pass name=...); refer to parts by these names
  * parts draw in creation order (later on top); the hull paints over every part unless the
    part is a shape with above=True or a rod/weapon with above=True (flags.aboveBody)
  * a rod is a decorative barrel (bulletType none); it is a rectangle or trapezoid up to
    500 long and 42*width-multiplier wide, placed anywhere by endpoints; line() is a hair-thin
    rod drawn over the hull (line art: mouths, brows, scars, seams)
  * shapes and rods can ride a turret (turret=i) or a barrel (mount=i): they then live in that
    part's frame and turn with it (jaws, eyes, hands)
  * `with d.frame(at, angle):` builds a sub-assembly in local coordinates (a claw, a gun pod,
    an eye pair) and places it; nest frames freely; mirror() the result afterwards
  * stock weapon systems are one call each (mechanics.py): d.twin(), d.spawner(), d.destroyer(),
    d.trap_launcher(), d.missile_launcher(), d.auto_turret(), d.side_turrets(), d.smasher() ...
    with the numbers of the real stock tank; any spec field can be passed to override;
    human-pack tricks are presets too: d.jaws(), d.trail(), d.eye(), d.cursor_pivot(),
    d.contact_damage(), d.turreted_bullet(), auto_fire=True on any gun
  * save() reports parts the hull would swallow and the figure's overall span
  * budget: 32 body shapes, 32 barrels and 8 turrets per tank (the editor drops the rest), and
    the lobby's import budget (120/s, 250 alive, 2000 room, 64 per volley, 96 drones, 96 pieces;
    spec 7a); save() warns and the validator errors when a design is over

Standard library only. Validation and rendering use the sibling scripts.
"""
import contextlib
import importlib.util
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def default_out_dir():
    """Where packs land: $DIEP_PACK_OUT when set (the older $DIEP_TANK_OUT still works), else ./output
    under the current working directory."""
    return os.environ.get("DIEP_PACK_OUT") or os.environ.get("DIEP_TANK_OUT") or os.path.join(os.getcwd(), "output")


BARREL_WIDTH = 42.0
BARREL_LENGTH = 95.0
INVIS_GAIN = 0.03076923076923077
INVIS_LOSS = 0.05
MAX_BARREL_LENGTH = 500
MAX_BODY_SHAPES = 32  # the editor keeps 32 body shapes and 32 barrels per tank and drops the rest (spec §9c)
MAX_BARRELS = 32
MAX_TURRETS = 8      # the editor keeps 8 turrets per tank and per projectile (spec §9c)
MAX_PIECES = 96       # shapes + barrels + turrets on the tank and all its projectiles (spec §9c)
TURRET_RADIUS = 25    # default turret disc radius (`baseSize`)
SHAPE_SIZE = 25       # a shape without `size` draws at 25


class C:
    """Palette indices (spec section 10). The lower-case names are the editor's own swatch
    names (what the tester sees in the per-part colour picker), so recaps can use them. Indices
    3-6 are the game's TEAM slots, which the picker calls Red, Purple and Green: in play they
    show a team colour and, once the player has been on that team, follow the player's current
    team (tested 2026-09-26). The fixed reds are salmon and crimson, the fixed greens mint and
    forest; `red` and `green` here point at the fixed ones on purpose."""
    # editor swatch names, in the picker's order
    white = 19        # #FFFFFF
    box = 14          # #BBBBBB
    cannon = 1        # #999999 (every stock barrel)
    border = 0        # #555555 "Border (grey)", smasher plates
    charcoal = 20     # #3D3D3D
    team_red = 4      # picker "Red" #F14E54: red TEAM slot, follows the player's team
    crimson = 24      # #B5323A
    salmon = 9        # #FC7677 (triangle)
    orange = 16       # #FCC376
    brown = 23        # #A9724A
    yellow = 8        # #FFE869 (square)
    shiny = 7         # #8AFF69
    team_green = 6    # picker "Green" #00E16E: green TEAM slot
    mint = 13         # #43FF91 (picker says #4FFF91)
    forest = 25       # #2E9E5B
    cyan = 18         # #35C5DB
    teal = 21         # #12A5A5
    blue = 2          # #00B2E1, fixed (never changed with team swaps)
    indigo = 22       # #4A57C8
    periwinkle = 10   # #768DFC (pentagon)
    team_purple = 5   # picker "Purple" #BF7FF5: purple TEAM slot
    plum = 26         # #7B4FA8
    pink = 11         # #F177DD (crasher)
    owner = 27        # "same color as the body": the owner's team colour
    team_blue = 3     # not in the picker: blue TEAM slot
    # aliases kept for existing scripts
    dark = 0
    grey = 1
    red = 9           # the fixed red (salmon); use team_red for deliberate team tinting
    green = 13        # the fixed green (mint)
    lime = 7
    silver = 14
    peach = 16
    navy = 22
    maroon = 24
    violet = 26

    NAMES = {}
    EDITOR = {}       # index -> editor swatch name


C.NAMES = {k: v for k, v in vars(C).items() if isinstance(v, int) and not k.startswith("_")}
C.EDITOR = {19: "White", 14: "Box", 1: "Cannon", 0: "Border (grey)", 20: "Charcoal", 4: "Red", 24: "Crimson",
            9: "Salmon", 16: "Orange", 23: "Brown", 8: "Yellow", 7: "Shiny", 6: "Green", 13: "Mint", 25: "Forest",
            18: "Cyan", 21: "Teal", 2: "Blue", 22: "Indigo", 10: "Periwinkle", 5: "Purple", 26: "Plum", 11: "Pink",
            27: "same color as the body"}


# --- point helpers (degrees, clockwise, forward = 0) -----------------------------------------

def polar(r, deg, at=(0, 0)):
    """Point at distance r from `at` in direction deg."""
    a = math.radians(deg)
    return (at[0] + r * math.cos(a), at[1] + r * math.sin(a))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def arc(center, radius, start_deg, end_deg, n):
    """n points on a circular arc from start_deg to end_deg (inclusive)."""
    if n == 1:
        return [polar(radius, start_deg, center)]
    return [polar(radius, start_deg + (end_deg - start_deg) * i / (n - 1), center) for i in range(n)]


def bezier(p0, p1, p2, p3, n):
    """n points on a cubic Bezier (inclusive of both ends)."""
    pts = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return pts


def line(a, b, n):
    return [lerp(a, b, i / (n - 1) if n > 1 else 0) for i in range(n)]


def spread(values, n):
    """Expand a size spec (number | (start, end) | list) to n values."""
    if isinstance(values, (int, float)):
        return [float(values)] * n
    if isinstance(values, tuple) and len(values) == 2 and n != 2:
        s, e = values
        return [s + (e - s) * (i / (n - 1) if n > 1 else 0) for i in range(n)]
    values = list(values)
    if len(values) != n:
        raise ValueError(f"expected {n} sizes, got {len(values)}")
    return [float(v) for v in values]


def num(v):
    """Compact number for JSON: ints stay ints, floats round to 4 places."""
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, int):
        return v
    r = round(float(v), 4)
    return int(r) if r == int(r) and abs(r) < 1e9 else r


# --- the builder -----------------------------------------------------------------------------

def _mechanics():
    spec = importlib.util.spec_from_file_location("mechanics", os.path.join(HERE, "mechanics.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Mechanics


class Tank(_mechanics()):
    def __init__(self, pack, name, level=45, parents=(), tank_id=None):
        self.pack = pack
        self.name = name
        self.level = level
        self.parents = list(parents)
        self.id = tank_id
        self.fields = {}          # extra tank-level fields (statsMaxLevel, helpText, ...)
        self.body = {"sides": 0}
        self.projectiles = []
        self.parts = []           # (kind, dict) in creation order; kind in barrel|shape|turret
        self.warnings = []
        self._order = 0
        self._names = set()
        self._frames = []         # stack of (origin, angle_deg) for frame()

    # --- local frames ---
    @contextlib.contextmanager
    def frame(self, at=(0, 0), angle=0):
        """Build in local coordinates: everything created inside is translated to `at` and
        rotated by `angle` degrees (nested frames compose). Example:
            with d.frame(at=(60, 45), angle=30):
                d.rod((0, 0), (50, 0), width=20, name="claw arm")
                d.shape(3, 14, at=(58, 8), angle=20, name="pincer")"""
        self._frames.append((tuple(at), float(angle)))
        try:
            yield self
        finally:
            self._frames.pop()

    def _pt(self, p):
        """Local point -> tank frame through the active frame stack."""
        x, y = float(p[0]), float(p[1])
        for at, ang in reversed(self._frames):
            a = math.radians(ang)
            x, y = at[0] + x * math.cos(a) - y * math.sin(a), at[1] + x * math.sin(a) + y * math.cos(a)
        return (x, y)

    def _ang(self, deg):
        return float(deg) + sum(a for _, a in self._frames)

    # --- hull ---
    def hull(self, sides=0, size=None, color=None, angle=0, star=False, spin=0):
        """Hull polygon. size is the radius (polygon hulls draw 1.3x bigger than a circle
        of the same size; use 44.23 for an octagon that matches a 50 circle). A tiny size
        (5-8) all but hides the hull so the figure is entirely custom parts (user packs do
        this); the hitbox presumably shrinks with it."""
        b = {"sides": int(sides)}
        if star:
            b["star"] = True
        if angle:
            b["angle"] = math.radians(angle)
        if size is not None:
            b["size"] = size
        if color is not None:
            b["color"] = self.color(color)
        if spin:
            b["spinSpeed"] = spin
        self.body = b
        return b

    # --- registration ---
    def _add(self, kind, d, order, name):
        if order is None:
            order = self._order
        self._order = max(self._order, order) + 1
        d["order"] = int(order)
        if not name:
            name = f"{kind} {sum(1 for k, _ in self.parts if k == kind) + 1}"
        if name in self._names:
            n = 2
            while f"{name} {n}" in self._names:
                n += 1
            name = f"{name} {n}"
        self._names.add(name)
        d["editor"] = {"name": name}          # every part is named; the editor shows it
        d["_name"] = name
        self.parts.append((kind, d))
        return d

    def color(self, c):
        if isinstance(c, str):
            if c not in C.NAMES:
                raise ValueError(f"unknown colour {c!r}; use C.<name> or an index 0-29")
            return C.NAMES[c]
        if not 0 <= int(c) <= 29:
            raise ValueError(f"palette index {c} out of range 0-29")
        return int(c)

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    # --- body shapes ---
    def shape(self, sides, size, at=(0, 0), angle=0, color=None, above=False, spin=0,
              name=None, order=None, star=False, collidable=None, turret=None, mount=None,
              stays_visible=None):
        """Regular polygon of circumradius `size` centred at `at`, rotated `angle` degrees.
        sides 0 (or 1) draws as a circle; star=True alternates inner vertices at 0.4 x size.
        turret=i mounts it on turret i (coordinates in the turret's frame; it turns with the
        turret; above=True puts it over the turret's disc). mount=i mounts it on barrel i
        (coordinates from the barrel's midpoint, along its axis). stays_visible=True keeps it
        drawn while the tank is faded (Medium confidence)."""
        s = {"sides": int(sides), "size": size}
        if turret is None and mount is None:          # mounted parts live in their base's frame
            at, angle = self._pt(at), self._ang(angle)
        if abs(at[0]) > 1e-9:
            s["xOffset"] = at[0]
        if abs(at[1]) > 1e-9:
            s["yOffset"] = at[1]
        if abs(angle) > 1e-9:
            s["angle"] = math.radians(angle)
        if spin:
            s["spinSpeed"] = spin
        if above:
            s["aboveBody"] = True
        if star:
            s["star"] = True
        if color is not None:
            s["color"] = self.color(color)
        if collidable is not None:
            s["collidable"] = bool(collidable)
        if stays_visible is not None:
            s["staysVisible"] = bool(stays_visible)
        if turret is not None:
            s["mountTurret"] = int(turret)
        if mount is not None:
            s["mount"] = int(mount)
        return self._add("shape", s, order, name)

    def circle(self, size, at=(0, 0), **kw):
        return self.shape(0, size, at, **kw)

    def part(self, sides, size, at=(0, 0), angle=0, color=None, above=False, spin=0, star=False,
             turret=None, name=None, collidable=None):
        """A shape dict for a PROJECTILE (`projectile(parts=[...])`): same fields as shape(),
        not registered on the tank. Coordinates are in the projectile's frame (x = its heading),
        which is scaled to the projectile so that its radius counts as ~50 like a hull (2026-09-26:
        a part 45 ahead on a 1.2 bullet was a tiny nose at the rim). Parts draw UNDER the
        projectile's disc unless above=True, so decorate as you would a hull: above=True for
        anything inside radius 50, offsets beyond 50 for things that stick out."""
        s = {"sides": int(sides), "size": size}
        if abs(at[0]) > 1e-9:
            s["xOffset"] = at[0]
        if abs(at[1]) > 1e-9:
            s["yOffset"] = at[1]
        if angle:
            s["angle"] = math.radians(angle)
        if spin:
            s["spinSpeed"] = spin
        if above:
            s["aboveBody"] = True
        if star:
            s["star"] = True
        if color is not None:
            s["color"] = self.color(color)
        if collidable is not None:          # collides at ~2/3 of its drawn radius (2026-09-26)
            s["collidable"] = bool(collidable)
        if turret is not None:
            s["mountTurret"] = int(turret)
        if name:
            s["editor"] = {"name": name}
        return s

    # --- rods (decorative barrels) ---
    def rod(self, a, b, width=BARREL_WIDTH, end_width=None, color=None, name=None, order=None,
            turret=None, above=False, **extra):
        """Rectangle/trapezoid from point a to point b, `width` units wide at a and
        `end_width` at b. Becomes a bulletType none barrel. Draws under the hull unless
        above=True (flags.aboveBody: over the hull, or over the disc when on a turret).
        turret=i / mount=i place it in that part's frame. A rod may cross the hull centre
        (negative startDistance draws fine)."""
        if end_width is None:
            end_width = width
        if turret is None and "mount" not in extra:      # mounted parts live in their base's frame
            a, b = self._pt(a), self._pt(b)
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length < 1e-6:
            raise ValueError("rod endpoints coincide")
        theta = math.atan2(dy, dx)
        # local coordinates of a in the barrel frame
        sx = ax * math.cos(theta) + ay * math.sin(theta)
        off = -ax * math.sin(theta) + ay * math.cos(theta)
        if sx < 0:
            # prefer the orientation whose startDistance is not negative (both draw correctly)
            theta2 = math.atan2(-dy, -dx)
            sx2 = bx * math.cos(theta2) + by * math.sin(theta2)
            if sx2 >= 0:
                a, b, width, end_width = b, a, end_width, width
                theta, sx = theta2, sx2
                off = -a[0] * math.sin(theta) + a[1] * math.cos(theta)
        if length > MAX_BARREL_LENGTH:
            self.warn(f"rod {name or ''} is {length:.0f} long; the editor clamps barrel length to 500")
        h = width / BARREL_WIDTH
        m = end_width / width if width else 1
        if not 0.1 <= h <= 6:
            self.warn(f"rod {name or ''} width multiplier {h:.2f} is outside anything seen (0.1-2.5)")
        d = {"bulletType": "none", "projectile": -1}
        if above:
            d["flags"] = {"aboveBody": True}
        if abs(theta) > 1e-9:
            d["angle"] = theta
        if abs(off) > 1e-6:
            d["offset"] = off
        if abs(length - BARREL_LENGTH) > 1e-6:
            d["distance"] = length
        if abs(sx) > 1e-6:
            d["startDistance"] = sx
        if abs(h - 1) > 1e-6:
            d["heightMultiplier"] = h
        if abs(m - 1) > 1e-6:
            d["muzzleScale"] = m
        if color is not None:
            d["color"] = self.color(color)
        if turret is not None:
            d["mountTurret"] = turret
        d.update(extra)
        return self._add("barrel", d, order, name)

    def rod_polar(self, angle, length, gap=0, offset=0, width=BARREL_WIDTH, end_width=None, **kw):
        """Rod the way the editor thinks: direction, length, gap from centre, side offset."""
        a = polar(gap, angle)
        a = (a[0] + offset * -math.sin(math.radians(angle)), a[1] + offset * math.cos(math.radians(angle)))
        b = polar(length, angle, a)
        return self.rod(a, b, width, end_width, **kw)

    def line(self, a, b, width=5, color=None, name=None, above=True, end_width=None, **kw):
        """Line art: a hair-thin rod drawn OVER the hull (user packs draw mouths, brows, scars
        and seams this way with heightMultiplier 0.1-0.15). Under about 8 wide a part is
        outline only, so the stroke colour is 72 % of `color`: Charcoal reads as black."""
        return self.rod(a, b, width, end_width, color=color, name=name, above=above, **kw)

    def polyline(self, points, width=5, color=None, name=None, **kw):
        """Connected line segments over the hull (a smile, a zigzag)."""
        pts = list(points)
        return [self.line(pts[i], pts[i + 1], width, color=color, name=f"{name} {i + 1}" if name else None, **kw)
                for i in range(len(pts) - 1)]

    # --- compound placers ---
    def chain(self, points, sizes, sides=6, color=None, name=None, above=False, follow=True, **kw):
        """A polygon at each point, sizes spread along the chain (number | (start, end) | list).
        follow=True turns each polygon to face the local direction of travel."""
        pts = list(points)
        out = []
        for i, (p, s) in enumerate(zip(pts, spread(sizes, len(pts)))):
            ang = 0
            if follow and len(pts) > 1:
                q = pts[min(i + 1, len(pts) - 1)]
                r = pts[max(i - 1, 0)]
                ang = math.degrees(math.atan2(q[1] - r[1], q[0] - r[0]))
            out.append(self.shape(sides, s, p, angle=ang, color=color, above=above,
                                  name=f"{name} {i + 1}" if name else None, **kw))
        return out

    def strip(self, points, widths, color=None, name=None, **kw):
        """Rods joining consecutive points; widths spread over the points (tapering strip)."""
        pts = list(points)
        ws = spread(widths, len(pts))
        return [self.rod(pts[i], pts[i + 1], ws[i], ws[i + 1], color=color,
                         name=f"{name} {i + 1}" if name else None, **kw) for i in range(len(pts) - 1)]

    def limb(self, points, widths, color=None, joint=None, joint_color=None, joint_sides=8, name=None,
             tip=False, exposed=None, **kw):
        """A jointed leg/arm/tentacle: rods along `points` (widths spread like strip) with a
        polygon at each interior bend drawn AFTER the rods to hide the seam. `joint` is the joint
        circumradius (default 0.62 x the local width, enough to cover the mitre). tip=True also
        caps the last point. `exposed=i` draws segment i after the joints instead, so its far end
        stays visible: needed when that segment is animated (a pump hidden under a joint polygon
        is invisible in game, pump-test-2 2026-09-26). Returns (rods, joints)."""
        pts = list(points)
        ws = spread(widths, len(pts))
        rods = []
        for i in range(len(pts) - 1):
            if i == exposed:
                rods.append(None)
                continue
            rods.append(self.rod(pts[i], pts[i + 1], ws[i], ws[i + 1], color=color,
                                 name=f"{name} {i + 1}" if name else None, **kw))
        joints = []
        idx = range(1, len(pts) - (0 if tip else 1))
        for k, i in enumerate(idx, 1):
            r = joint if joint is not None else ws[i] * 0.62
            joints.append(self.shape(joint_sides, r, pts[i], color=joint_color if joint_color is not None else color,
                                     name=f"{name} joint {k}" if name else None))
        if exposed is not None and 0 <= exposed < len(pts) - 1:
            rods[exposed] = self.rod(pts[exposed], pts[exposed + 1], ws[exposed], ws[exposed + 1], color=color,
                                     name=f"{name} {exposed + 1}" if name else None, **kw)
        return rods, joints

    def fan(self, apex, outline, color=None, name=None, base_width=8, overlap=1.15, **kw):
        """A filled irregular region: tapered rods from `apex` to each point of `outline`, each as
        wide at the rim as the spacing between its neighbours (times `overlap`), so they overlap
        into one shape. Good for a bat/bird wing, a fish tail, a fin, a cape; the seams read as
        veins or feathers."""
        pts = list(outline)
        if len(pts) < 2:
            raise ValueError("fan needs at least two outline points")
        out = []
        for i, p in enumerate(pts):
            prev_ = pts[max(i - 1, 0)]
            next_ = pts[min(i + 1, len(pts) - 1)]
            spacing = math.hypot(next_[0] - prev_[0], next_[1] - prev_[1]) / (2 if 0 < i < len(pts) - 1 else 1)
            out.append(self.rod(apex, p, base_width, max(spacing * overlap, base_width), color=color,
                                name=f"{name} {i + 1}" if name else None, **kw))
        return out

    def ring(self, n, radius, sides, size, color=None, name=None, at=(0, 0), start=0, sweep=360,
             face_out=True, **kw):
        """n polygons on a circle of `radius` around `at`, spread over `sweep` degrees."""
        step = sweep / n if sweep == 360 else sweep / max(n - 1, 1)
        out = []
        for i in range(n):
            ang = start + step * i
            out.append(self.shape(sides, size, polar(radius, ang, at), angle=ang if face_out else 0,
                                  color=color, name=f"{name} {i + 1}" if name else None, **kw))
        return out

    def spokes(self, n, length, gap=0, width=BARREL_WIDTH, end_width=None, color=None, name=None,
               at=(0, 0), start=0, sweep=360, **kw):
        """n rods radiating from `at`, spread over `sweep` degrees."""
        step = sweep / n if sweep == 360 else sweep / max(n - 1, 1)
        out = []
        for i in range(n):
            ang = start + step * i
            out.append(self.rod(polar(gap, ang, at), polar(gap + length, ang, at), width, end_width,
                                color=color, name=f"{name} {i + 1}" if name else None, **kw))
        return out

    def mirror(self, parts):
        """Duplicate part(s) across the aim axis (y -> -y). Returns the copies."""
        if isinstance(parts, dict):
            parts = [parts]
        parts = sorted(parts, key=lambda q: q.get("order", 0))   # copies keep the originals' draw order
        copies = []
        for p in parts:
            kind = next((k for k, d in self.parts if d is p), None)
            if kind is None:
                raise ValueError("mirror: part not found in this tank")
            if "mountTurret" in p or "mount" in p:
                self.warn(f"mirror: {p.get('_name')} is mounted on turret/barrel {p.get('mountTurret', p.get('mount'))}; "
                          "the copy stays on the SAME mount (build the other side's mount explicitly, as jaws() does)")
            q = {k: v for k, v in p.items() if k not in ("order", "editor", "_name")}
            if kind == "shape" or kind == "turret":
                if "yOffset" in q:
                    q["yOffset"] = -q["yOffset"]
                if "angle" in q:
                    q["angle"] = -q["angle"]
            else:
                if "offset" in q:
                    q["offset"] = -q["offset"]
                if "angle" in q:
                    q["angle"] = -q["angle"]
            nm = p.get("_name", kind)
            # the original is on the side its world midpoint says; name both so the editor's
            # part list reads "fore wing right" / "fore wing left"
            side = "right" if self._mid(kind, p)[1] > 1e-6 else "left"
            other = "left" if side == "right" else "right"
            if not re.search(rf"{side}", nm):
                p["_name"] = f"{nm} {side}"
                p["editor"]["name"] = p["_name"]
                self._names.add(p["_name"])
            copies.append(self._add(kind, q, None, f"{nm} {other}"))
        return copies

    def _mid(self, kind, d):
        """World-frame midpoint of a part (for naming and visibility checks)."""
        if kind != "barrel":
            return (d.get("xOffset", 0), d.get("yOffset", 0))
        a = d.get("angle", 0)
        x = d.get("startDistance", 0) + d.get("distance", BARREL_LENGTH) / 2
        y = d.get("offset", 0)
        return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))

    def _corners(self, kind, d):
        """World-frame points that bound a part (barrel corners or polygon vertices)."""
        if kind == "barrel":
            a = d.get("angle", 0)
            x0 = d.get("startDistance", 0)
            x1 = x0 + d.get("distance", BARREL_LENGTH)
            off = d.get("offset", 0)
            h0 = 21 * d.get("heightMultiplier", 1)
            h1 = h0 * d.get("muzzleScale", 1)
            pts = [(x0, off + h0), (x1, off + h1), (x1, off - h1), (x0, off - h0)]
            return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in pts]
        cx, cy = d.get("xOffset", 0), d.get("yOffset", 0)
        if kind == "turret":
            r = d.get("baseSize", TURRET_RADIUS)
            return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in (0, 1.5708, 3.1416, 4.7124)]
        n, r = max(int(d.get("sides", 0)), 3), d.get("size", SHAPE_SIZE)
        base = math.pi / 4 if n == 4 else 0
        return [(cx + r * math.cos(base + d.get("angle", 0) + 2 * math.pi * k / n),
                 cy + r * math.sin(base + d.get("angle", 0) + 2 * math.pi * k / n)) for k in range(n)]

    def hull_inradius(self):
        n = int(self.body.get("sides", 0))
        r = float(self.body.get("size", 50))
        return r if n <= 2 else 1.3 * r * math.cos(math.pi / n)

    def report(self):
        """Lines about parts the hull swallows and the figure's span (printed by save())."""
        lines = []
        rin = self.hull_inradius()
        xs, ys = [], []
        turrets = [d for k, d in self.parts if k == "turret"]
        barrels = [d for k, d in self.parts if k == "barrel"]

        def world_corners(kind, d):
            """Corners in the tank frame; parts on a turret are placed at the turret's rest angle,
            parts on a barrel at that barrel's midpoint."""
            pts = self._corners(kind, d)
            if "mountTurret" in d and 0 <= d["mountTurret"] < len(turrets):
                t = turrets[d["mountTurret"]]
                ox, oy, a = t.get("xOffset", 0), t.get("yOffset", 0), t.get("angle", 0)
            elif "mount" in d and 0 <= d["mount"] < len(barrels):
                b = barrels[d["mount"]]
                a = b.get("angle", 0)
                mx = b.get("startDistance", 0) + b.get("distance", BARREL_LENGTH) / 2
                my = b.get("offset", 0)
                ox, oy = mx * math.cos(a) - my * math.sin(a), mx * math.sin(a) + my * math.cos(a)
            else:
                return pts
            return [(ox + x * math.cos(a) - y * math.sin(a), oy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]

        for kind, d in self.parts:
            if d.get("invisible"):
                continue
            pts = world_corners(kind, d)
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
            above = d.get("aboveBody", kind == "turret") or bool((d.get("flags") or {}).get("aboveBody"))
            if kind == "turret":
                # a disc under the hull is fine when the parts it carries reach outside it
                carried = [world_corners(k2, d2) for k2, d2 in self.parts if d2.get("mountTurret") == turrets.index(d)]
                if any(math.hypot(x, y) > rin - 1 for c in carried for x, y in c):
                    continue
            if not above and all(math.hypot(x, y) <= rin - 1 for x, y in pts):
                lines.append(f"  HIDDEN  {d.get('_name')}: entirely under the hull (inradius {rin:.0f}); "
                             "raise it with above=True, move it, or drop it")
            if kind == "barrel" and d.get("lifetime") == 0.1 and d.get("damageMultiplier") == 0.01:
                # an animated rod: its pump only shows if the muzzle end is not painted over
                a = d.get("angle", 0)
                x1 = d.get("startDistance", 0) + d.get("distance", BARREL_LENGTH)
                off = d.get("offset", 0)
                mx, my = x1 * math.cos(a) - off * math.sin(a), x1 * math.sin(a) + off * math.cos(a)
                later = False
                mount = d.get("mountTurret")
                for k2, d2 in self.parts:
                    if d2 is d:
                        later = True
                    elif later and k2 == "shape" and not d2.get("aboveBody") and d2.get("mountTurret") == mount:
                        # same frame only: a rod on a pivot is compared with shapes on that pivot
                        n = max(int(d2.get("sides", 0)), 3)
                        inr = d2.get("size", 0) * math.cos(math.pi / n)
                        if math.hypot(mx - d2.get("xOffset", 0), my - d2.get("yOffset", 0)) < inr:
                            lines.append(f"  PUMP HIDDEN  {d.get('_name')}: its muzzle is under {d2.get('_name')!r}, "
                                         "so the pump will not show; draw the rod later (limb(exposed=i)) or move the shape")
                            break
                if mount is None and math.hypot(mx, my) < rin:
                    lines.append(f"  PUMP HIDDEN  {d.get('_name')}: its muzzle is under the hull")
        if xs:
            lines.append(f"  span {max(xs) - min(xs):.0f} long x {max(ys) - min(ys):.0f} wide "
                         f"(x {min(xs):.0f}..{max(xs):.0f}, y {min(ys):.0f}..{max(ys):.0f}); "
                         f"{len(self.parts)} parts")
        return lines

    # --- weapons, projectiles, turrets ---
    def projectile(self, name="Bullet", base="bullet", sides=-1, **extra):
        """Add a projectile; returns its index for weapon(projectile=...)."""
        p = {"name": name, "base": base, "sides": sides}
        p.update(extra)
        self.projectiles.append(p)
        return len(self.projectiles) - 1

    def weapon(self, projectile=0, bullet_type=None, angle=0, offset=0, length=BARREL_LENGTH, gap=0,
               width=BARREL_WIDTH, muzzle=1, name=None, order=None, color=None, above=False,
               invisible=False, auto_fire=False, **fields):
        """A firing barrel. Geometry in editor terms (degrees, length, gap, width in units);
        any spec field (reloadMultiplier, delay, numDrones, flags, ...) passes through.
        above=True draws it over the hull (flags.aboveBody); invisible=True fires without
        being drawn; auto_fire=True fires without the player clicking (flags.forceFire)."""
        if bullet_type is None:
            idx = projectile if isinstance(projectile, int) else projectile[0]
            bullet_type = self.projectiles[idx]["base"] if 0 <= idx < len(self.projectiles) else "bullet"
        d = {"bulletType": bullet_type, "projectile": projectile}
        flags = dict(fields.pop("flags", None) or {})
        if above:
            flags["aboveBody"] = True
        if auto_fire:
            flags["forceFire"] = True
        if flags:
            d["flags"] = flags
        if invisible:
            d["invisible"] = True
        if self._frames and "mountTurret" not in fields and "mount" not in fields:
            # express the barrel's start point in the tank frame, then back into polar terms
            a = math.radians(angle)
            start = self._pt((gap * math.cos(a) - offset * math.sin(a), gap * math.sin(a) + offset * math.cos(a)))
            angle = self._ang(angle)
            a = math.radians(angle)
            gap = start[0] * math.cos(a) + start[1] * math.sin(a)
            offset = -start[0] * math.sin(a) + start[1] * math.cos(a)
        if abs(angle) > 1e-9:
            d["angle"] = math.radians(angle)
        if abs(offset) > 1e-9:
            d["offset"] = offset
        if length != BARREL_LENGTH:
            d["distance"] = length
        if abs(gap) > 1e-9:
            d["startDistance"] = gap
        if width != BARREL_WIDTH:
            d["heightMultiplier"] = width / BARREL_WIDTH
        if muzzle != 1:
            d["muzzleScale"] = muzzle
        if color is not None:
            d["color"] = self.color(color)
        if bullet_type == "drone":
            d.setdefault("numDrones", 4)
            d.setdefault("droneAggressiveCrashRadius", 900)
        d.update(fields)
        return self._add("barrel", d, order, name)

    def turret(self, at=(0, 0), angle=0, arc=None, range=None, controllable=None, above=None,
               order=None, name=None, size=None, color=None):
        """Auto-turret mount; returns its index for weapon(mountTurret=i) / rod(turret=i) /
        shape(turret=i). `size` is the disc radius (baseSize, default 25; 1 hides it), `color`
        its palette colour (default Cannon grey; C.owner for the team colour, C.white for an
        eyeball). range=0 turns auto-targeting off: with controllable=True the turret then
        follows the cursor alone (a hand, a jaw), without it the turret is a fixed pivot.
        Turrets cannot be nested: a mountTurret on a turret is ignored (tested 2026-09-26)."""
        t = {}
        at, angle = self._pt(at), self._ang(angle)
        if abs(at[0]) > 1e-9:
            t["xOffset"] = at[0]
        if abs(at[1]) > 1e-9:
            t["yOffset"] = at[1]
        if size is not None:
            t["baseSize"] = size
        if abs(angle) > 1e-9:
            t["angle"] = math.radians(angle)
        if arc is not None:
            t["arc"] = math.radians(arc)
        if range is not None:
            t["range"] = range
        if controllable is not None:
            t["controllable"] = bool(controllable)
        if above is not None:
            t["aboveBody"] = bool(above)
        if color is not None:
            t["color"] = self.color(color)
        self._add("turret", t, order, name)
        return sum(1 for k, _ in self.parts if k == "turret") - 1

    def set(self, **fields):
        """Any tank-level field: statsMaxLevel, helpText, speedMultiplier, zoomMultiplier,
        invisibility, raises, editor, advancesInto, baseHealth ..."""
        self.fields.update(fields)
        return self

    # --- output ---
    def part_table(self):
        rows = []
        for kind, d in self.parts:
            tags = ""
            if d.get("aboveBody") or (d.get("flags") or {}).get("aboveBody"):
                tags += " ABOVE"
            if d.get("invisible"):
                tags += " INVISIBLE"
            if "mountTurret" in d:
                tags += f" on turret {d['mountTurret']}"
            if "mount" in d:
                tags += f" on barrel {d['mount']}"
            if kind == "shape":
                where = f"at ({num(d.get('xOffset', 0))}, {num(d.get('yOffset', 0))})"
                what = f"{d['sides']}-gon r={num(d.get('size', SHAPE_SIZE))}" + (" star" if d.get("star") else "")
            elif kind == "barrel":
                what = ("rod" if d["bulletType"] == "none" else d["bulletType"]) + \
                       f" len={num(d.get('distance', BARREL_LENGTH))} w={num(BARREL_WIDTH * d.get('heightMultiplier', 1))}"
                where = f"angle {math.degrees(d.get('angle', 0)):.0f} off {num(d.get('offset', 0))} gap {num(d.get('startDistance', 0))}"
            else:
                what = f"turret r={num(d.get('baseSize', TURRET_RADIUS))}"
                where = f"at ({num(d.get('xOffset', 0))}, {num(d.get('yOffset', 0))})"
            rows.append(f"  {d.get('order', 0):>3}  {kind:<6} {d.get('_name', ''):<22} {what + tags:<34} {where}")
        return "\n".join(rows)

    def build(self, tank_id):
        for t_idx, at, color, sides, size in getattr(self, "_pending_covers", []):
            self.cover(t_idx, color=color, sides=sides, size=size)
        self._pending_covers = []
        t = {"id": tank_id, "name": self.name, "minLevel": self.level, "body": self.body}
        if self.projectiles:
            t["projectiles"] = self.projectiles
        t["invisibility"] = self.fields.get("invisibility", {"gain": INVIS_GAIN, "lossOnHit": INVIS_LOSS})
        t["statsMaxLevel"] = self.fields.get("statsMaxLevel", [7] * 8)
        if self.parents:
            t["upgradesFrom"] = self.parents
        for k, v in self.fields.items():
            if k not in ("invisibility", "statsMaxLevel"):
                t[k] = v
        barrels = [d for k, d in self.parts if k == "barrel"]
        shapes = [d for k, d in self.parts if k == "shape"]
        turrets = [d for k, d in self.parts if k == "turret"]

        def clean(d):
            keep = bool(d.get("_stock"))      # a part cloned from a stock tank keeps its numbers unrounded
            return {k: (num(v) if not keep and not isinstance(v, (dict, list)) else v)
                    for k, v in d.items() if k not in ("_name", "_stock")}

        if barrels:
            t["barrels"] = [clean(b) for b in barrels]
        if shapes:
            t["bodyShapes"] = [clean(s) for s in shapes]
        if turrets:
            t["turrets"] = [clean(u) for u in turrets]
        if len(shapes) > MAX_BODY_SHAPES:
            self.warn(f"{len(shapes)} body shapes: the editor keeps only {MAX_BODY_SHAPES}; the rest are dropped on import")
        if len(barrels) > MAX_BARRELS:
            self.warn(f"{len(barrels)} barrels: the editor keeps only {MAX_BARRELS}; the rest are dropped on import")
        if len(turrets) > MAX_TURRETS:
            self.warn(f"{len(turrets)} turrets: the editor keeps only {MAX_TURRETS}; the rest are dropped on import")
        pieces = len(barrels) + len(shapes) + len(turrets) + sum(
            len(p.get(k) or []) for p in self.projectiles for k in ("parts", "barrels", "turrets"))
        if pieces > MAX_PIECES:
            self.warn(f"{pieces} pieces on the body and its projectiles: the game refuses more than {MAX_PIECES}")
        return t

    def save(self, *a, **kw):
        return self.pack.save(*a, **kw)


VANILLA_SHAPES = ("square", "triangle", "pentagon", "big_pentagon", "hexagon", "small_crasher", "big_crasher")
# spawn weight and band (radiusMin, radiusMax) of every vanilla shape, as the editor's own copy of
# each stock shape writes them (2026-10-04; arena.md section 2): food in the outer 80 %, Alpha
# Pentagons and crashers in the nest
VANILLA_SPAWN = {
    "square": (1, 0.2, 1), "triangle": (0.2, 0.2, 1), "pentagon": (0.05, 0.2, 1),
    "big_pentagon": (0.005, 0, 0.1), "big_crasher": (0.02, 0, 0.2), "small_crasher": (0.1, 0, 0.2),
    "hexagon": (0.004, 0.2, 1),
}
VANILLA_WEIGHT = {k: v[0] for k, v in VANILLA_SPAWN.items()}


def ring_density(inner, outer, crowd=1.0):
    """Density that crowds the square band inner-outer (0 = centre, 1 = edge) like `crowd` does
    the whole map: a band's spawns go with density x width, its area with outer^2 - inner^2,
    so even crowding needs density = crowd x (inner + outer). Spec 1a, "Spawn shares"."""
    return round(crowd * (inner + outer), 4)


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
VERSION_SUFFIX = re.compile(r"\s+v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def base_name(name):
    """A pack name without its " v1.2.3" version suffix."""
    return VERSION_SUFFIX.sub("", name or "")


class Pack:
    def __init__(self, name, author=None, first_id=100001, version=None):
        """version: the pack's semantic version, "MAJOR.MINOR.PATCH" (SKILL.md §5a). With it the
        pack is named "<name> v<version>" (the name is the only pack field the editor keeps that
        players see, so this is how they tell iterations apart) and saved as
        <slug>-<version>.diep-pack, so every iteration stays on disk."""
        if version is not None and not SEMVER.match(str(version)):
            raise ValueError(f"version {version!r} is not MAJOR.MINOR.PATCH (e.g. 0.3.1)")
        self.name = base_name(name)
        self.version = None if version is None else str(version)
        self.author = author
        self.first_id = first_id
        self.tanks = []
        self.hidden = None          # vanilla tank ids to remove from the class tree
        self.hidden_shapes = None   # vanilla shape names to stop spawning
        self.starters = None        # tank ids (vanilla or this pack's) the player can spawn as
        self.shapes = []            # custom arena polygons (spec section 1a)

    def tank(self, name, level=45, parents=(), tank_id=None):
        t = Tank(self, name, level, parents, tank_id)
        self.tanks.append(t)
        return t

    def from_stock(self, name, level=None, parents=(), as_name=None, replace=True, children=()):
        """A Tank pre-filled from the editor's own stock roster (references/stock-tanks.diep-pack;
        `name` is a stock tank's name or vanilla id, see `ref.py stock`): tank-level fields, body,
        projectiles, barrels, body shapes and turrets are loaded verbatim, numbers unrounded, and
        keep their indices, so presets, rod(), shape(), turret() and projectile parts go on top
        as decoration. level defaults to the stock tank's, `as_name` renames it (default: the
        stock name), parents are this pack's own tree links (upgradesFrom) and children the
        tanks it advances into (advancesInto: stock ids or this pack's ids, e.g. a starter that
        leads into a clone of Flank Guard). replace=True makes it stand in for
        the stock tank: editor.replaces is the vanilla id and the id joins this pack's `hidden`
        list, so the stock tank and its clone never both appear (not for the base Tank, which
        cannot be hidden). Parts added later draw after the stock ones unless given an order.
        save() lists every play-changing difference from the stock tank (validate_pack.py
        --cosmetic turns those into errors)."""
        ref = _load("ref")
        vid, st = ref.stock_tank(name)
        t = self.tank(as_name or st["name"], st["minLevel"] if level is None else level, parents)
        struct = ("id", "name", "minLevel", "body", "projectiles", "barrels", "bodyShapes", "turrets", "upgradesFrom")
        t.fields = {k: v for k, v in st.items() if k not in struct}
        t.body = st["body"]
        t.projectiles = st.get("projectiles", [])
        highest = -1
        for kind, key in (("barrel", "barrels"), ("shape", "bodyShapes"), ("turret", "turrets")):
            for i, d in enumerate(st.get(key, [])):
                d["_stock"] = True
                d["_name"] = f"stock {kind} {i + 1}"
                t._names.add(d["_name"])
                t.parts.append((kind, d))
                highest = max(highest, d.get("order", 0))
        t._order = highest + 1
        t.stock_id = vid
        if children:
            t.fields["advancesInto"] = list(children)
        if replace and vid:
            t.fields["editor"] = {"replaces": vid}
            self.hidden = list(self.hidden or [])
            if vid not in self.hidden:
                self.hidden.append(vid)
        return t

    def custom_shape(self, name, sides, size, health, xp, color="#FFE869", touch_damage=2, touch_knockback=8,
                     knockback=None, float_speed=0.05, crash_speed=None, crash_radius=None, density=None,
                     radius_min=None, radius_max=None, replaces=None, disabled=None, spawn_weight=None):
        """A custom arena polygon (spec section 1a): what user packs use for new food, crashers
        and bosses. `color` is a hex string, not a palette index. crash_speed/crash_radius make
        it hunt like a crasher; touch_damage 20 kills a tank with Max Health and Body Damage at
        7/7 in two touches (boss-grade; food is 2-4); density is spawn density (1.0 made the shape 40-50% of all
        spawns in play, so 0.1-0.3 is ordinary food, 0.001-0.01 a rarity); radius_min/max (0 = centre, 1 = edge)
        confine it to a band; the map is square, so a band is a square ring, and stacked bands
        layer the arena (squares at 0.8-1, triangles 0.4-0.8, hexagons 0-0.4). A shape's share
        of the map's shape cap goes with density x band width, not area, so the centre crowds:
        density 1.8 / 1.2 / 0.4 on those three bands crowds them evenly (spec 1a); float_speed is
        ignored on a crasher; replaces="hexagon" swaps out a vanilla shape (pair with
        hidden_shapes). Returns the id string, usable in a tank's `raises`."""
        sid = f"custom_shape_{len(self.shapes) + 1}"
        s = {"id": sid, "name": name, "sides": int(sides), "size": size, "maxHealth": health, "xpBounty": xp,
             "damageOnTouch": touch_damage, "knockbackOnTouch": touch_knockback, "color": color}
        if knockback is not None:
            s["knockbackMultiplier"] = knockback
        ai = {"floatSpeed": float_speed}
        if crash_speed is not None and crash_radius is None:
            crash_radius = 2000   # the radius is what switches chasing on (editor code); the editor's default
        if crash_speed is not None:
            ai["aggressiveCrashSpeed"] = crash_speed
        if crash_radius is not None:
            ai["aggressiveCrashRadius"] = crash_radius
        s["ai"] = ai
        spawn = {}
        if density is not None:
            spawn["densityMultiplier"] = density
        if radius_min is not None:
            spawn["radiusMin"] = radius_min
        if radius_max is not None:
            spawn["radiusMax"] = radius_max
        if spawn:
            s["spawn"] = spawn
        ed = {}
        if replaces is not None:
            ed["replaces"] = replaces
        if disabled is not None:
            ed["disabled"] = bool(disabled)
        if spawn_weight is not None:
            ed["spawnWeight"] = spawn_weight
        if ed:
            s["editor"] = ed
        self.shapes.append(s)
        return sid

    def spawn_shares(self):
        """Predicted share of the map's shape cap for every shape that spawns, with its crowding
        per area relative to the map average (spec 1a, "Spawn shares": a shape's share goes with
        density x band width, as if the game picked a spot and a shape by weight and kept the pair
        only when the spot lies in that shape's band; measured within about 5 in 100). Vanilla
        shapes that are not hidden or replaced count at their own weights and bands (VANILLA_SPAWN:
        food 0.2-1, crashers 0-0.2, Alpha Pentagons 0-0.1). Returns [(name, share, crowding)]."""
        hidden = set(self.hidden_shapes or ())
        hidden |= {(s.get("editor") or {}).get("replaces") for s in self.shapes}
        entries = [(k, w, lo, hi) for k, (w, lo, hi) in VANILLA_SPAWN.items() if k not in hidden]
        for s in self.shapes:
            sp = s.get("spawn", {})
            w = 0 if (s.get("editor") or {}).get("disabled") else sp.get("densityMultiplier", 0.01)
            if w > 0:
                entries.append((s["name"], w, sp.get("radiusMin", 0), sp.get("radiusMax", 1)))
        total = sum(w * (hi - lo) for _, w, lo, hi in entries) or 1
        out = []
        for name, w, lo, hi in entries:
            share = w * (hi - lo) / total
            area = hi * hi - lo * lo
            out.append((name, share, share / area if area else float("inf")))
        return out

    def id_of(self, tank):
        return tank.id if tank.id else self.first_id + self.tanks.index(tank)

    def display_name(self):
        return f"{self.name} v{self.version}" if self.version else self.name

    def filename(self):
        return f"{self.slug()}-{self.version}.diep-pack" if self.version else f"{self.slug()}.diep-pack"

    def changelog_path(self):
        """<design script>.changelog.md beside the script that is running (SKILL.md §5a)."""
        script = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
        return os.path.splitext(script)[0] + ".changelog.md" if script.endswith(".py") else None

    def build(self):
        p = {"version": 2, "name": self.display_name()}
        if self.author:
            p["author"] = self.author
        if self.shapes:
            p["shapes"] = self.shapes
        if self.hidden:
            p["hidden"] = self.hidden
        if self.hidden_shapes:
            p["hiddenShapes"] = list(self.hidden_shapes)
        if self.starters:
            p["starters"] = [self.id_of(t) if isinstance(t, Tank) else t for t in self.starters]
        if self.tanks or not self.shapes:   # the editor writes an arena-only pack with no tanks key
            p["tanks"] = [t.build(self.id_of(t)) for t in self.tanks]
        return p

    def slug(self):
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")

    def save(self, path=None, validate=True, render=True, quiet=False):
        """Write <out_dir()>/<slug>-<version>.diep-pack (one line; <slug>.diep-pack without a version),
        validate it, render PNGs next to it under renders/ (unversioned names). Prints VERSION notes
        for a missing version, a missing changelog entry, or an overwritten version. Returns the absolute pack path; raises SystemExit(1) on validation errors."""
        pack = self.build()
        path = os.path.abspath(path or os.path.join(default_out_dir(), self.filename()))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        text = json.dumps(pack, separators=(",", ":"))
        notes = []
        if self.version is None:
            notes.append("no version: give the pack one, Pack(..., version=\"0.1.0\") (SKILL.md §5a)")
        else:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    if f.read() != text:
                        notes.append(f"overwrote {os.path.basename(path)} with different content: fine while "
                                     f"iterating before delivery, but a version the user already has must "
                                     f"never change; bump it (SKILL.md §5a)")
            log = self.changelog_path()
            if log:
                entry = re.compile(r"^##\s+v?" + re.escape(self.version) + r"(?![\d.])", re.M)
                if not os.path.exists(log):
                    notes.append(f"no changelog: start {os.path.basename(log)} beside the design script (SKILL.md §5a)")
                else:
                    with open(log, encoding="utf-8") as f:
                        if not entry.search(f.read()):
                            notes.append(f"{os.path.basename(log)} has no entry for {self.version} yet")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        if not quiet:
            print("wrote", path, f"(version {self.version})" if self.version else "")
            for n in notes:
                print("  VERSION", n)
            for t in self.tanks:
                print(f"{t.name}: {len(t.parts)} parts")
                print(t.part_table())
                for line in t.report():
                    print(line)
                for w in t.warnings:
                    print("  NOTE", w)
            if self.shapes:
                print("spawn shares of the map's shape cap (about +-5 in 100; crowding per area, 1 = map average):")
                for name, share, crowd in self.spawn_shares():
                    print(f"  {name:24} {share * 100:5.1f} %   crowding x{crowd:.2f}")
        errors = 0
        if validate:
            mod = _load("validate_pack")
            rep = mod.validate(pack)
            for w in rep.warnings:
                print("WARNING " + w)
            for e in rep.errors:
                print("ERROR " + e)
            errors = len(rep.errors)
            twins = {self.id_of(t): t.stock_id for t in self.tanks if getattr(t, "stock_id", None) is not None}
            for label, _, _, diffs in mod.stock_twins(pack, twins):
                for line in diffs:
                    print(f"NOTE {label} differs from stock in play: {line}")
        if render and not errors:
            mod = _load("render_pack")
            out_dir = os.path.join(os.path.dirname(path), "renders")
            for p in mod.render_pack(pack, out_dir, sheet=len(pack.get("tanks", [])) > 1):
                print("render", p)
        if errors:
            raise SystemExit(1)
        return path


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def Design(name, level=45, parents=(), author=None, pack_name=None, version=None):
    """One-tank convenience: returns a Tank whose save() writes a pack named after it.
    `author` is the name shown in the editor; ask the user for it (omitted when None).
    `version` is the pack's semantic version (SKILL.md §5a)."""
    return Pack(pack_name or name, author, version=version).tank(name, level, parents)


if __name__ == "__main__":
    print(__doc__)
