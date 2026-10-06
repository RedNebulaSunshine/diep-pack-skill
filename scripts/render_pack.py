#!/usr/bin/env python3
"""Render every tank in a .diep-pack to PNG (and optionally SVG) the way the game draws it.

Usage:
  python render_pack.py <pack> [--out DIR] [--size PX] [--heading up|right|svg] [--svg]
                               [--sheet] [--no-grid] [--projectiles]

--boss also draws every boss record's tank at the boss's scale beside a plain level-1 tank for size
(files <pack>-boss-<name>.png; spec section 1b).
--projectiles also draws every projectile that carries parts, sub-barrels or turrets (a web,
a chick, a summoned warrior) as if it were a tank: its disc is a hull of radius 50 (the
frame projectile parts are drawn in, spec section 5b), polygon projectiles at 1.3 x like a
polygon hull. Files are named <pack>-<tank>-proj-<projectile>.png. The tank's barrel scales
the whole picture by its bulletSizeMultiplier in play.
  python render_pack.py <pack> --compare <editor-export.svg>

The drawing rules are reverse-engineered from the editor's own SVG exports in
the editor's SVG exports  (see references/schema/ section 9b) and verified with --compare, which
resolves every transform in an editor export and diffs the resulting polygons against ours.

Coordinates: x forward, y to the tank's right (screen y-down), radians clockwise positive.
Needs Pillow for PNG output; SVG output and --compare are stdlib only.
"""
import json
import math
import os
import re
import sys

# --- constants from the exports -----------------------------------------------------------

PALETTE = [
    "#555555", "#999999", "#00B2E1", "#999999", "#F14E54", "#BF7FF5", "#00E16E", "#8AFF69",
    "#FFE869", "#FC7677", "#768DFC", "#F177DD", "#999999", "#43FF91", "#BBBBBB", "#999999",
    "#FCC376", "#C0C0C0", "#35C5DB", "#FFFFFF", "#3D3D3D", "#12A5A5", "#4A57C8", "#A9724A",
    "#B5323A", "#2E9E5B", "#7B4FA8", "#00B2E1", "#999999", "#999999",
]
OWNER_COLOR = 2          # index 27 on a team-coloured hull is the team colour; we show the player blue
# index 17 is "Fallen" (#C0C0C0) since the editor update of 2026-10-06 (spec section 10)
HULL_RADIUS = 50
BARREL_LENGTH = 95
BARREL_HALF_WIDTH = 21   # default width 42
POLY_HULL_FACTOR = 1.3   # polygon hulls are drawn with circumradius 1.3 x size (Necromancer 50 -> 65)
TURRET_RADIUS = 25       # default turret disc radius; `baseSize` overrides it (human packs use 1-53)
SHAPE_SIZE = 25          # a body shape without `size` draws at 25 (user exports omit it, SVG shows 25)
STROKE_WIDTH = 7.5
STROKE_FACTOR = 0.72     # stroke = round(fill * 0.72) per channel
STAR_INNER = 0.4         # inner/outer radius ratio of `star: true` polygons (three user exports agree)
BACKGROUND = (205, 205, 205)
GRID_COLOUR = (190, 190, 190)


def hexrgb(h):
    """'#rrggbb' -> (r, g, b); '#rrggbbaa' -> (r, g, b, a) with a in 0-255 (spec section 10, 2026-10-06)."""
    rgb = tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    return rgb + (int(h[7:9], 16),) if len(h) == 9 else rgb


def is_hex(c):
    return isinstance(c, str) and len(c) in (7, 9) and c[0] == "#" and all(ch in "0123456789abcdefABCDEF" for ch in c[1:])


def stroke_of(rgb):
    return tuple(round(c * STROKE_FACTOR) for c in rgb[:3]) + tuple(rgb[3:])


def palette_rgb(idx, default, owner=None):
    """A colour value -> rgb (or rgba when a hex string carries alpha). A palette index, or since
    2026-10-06 a hex string '#rrggbb' / '#rrggbbaa'. 27 is "same color as the body": the hull's own
    colour when the hull has one (spec section 10, Confirmed in play 2026-09-30), else the team colour,
    for which we show player blue. `owner` is the hull's resolved colour (None = team-coloured hull)."""
    if idx is None:
        idx = default
    if is_hex(idx):
        return hexrgb(idx)
    if idx == 27:
        if owner is not None:
            return owner
        idx = OWNER_COLOR
    if not isinstance(idx, int) or not 0 <= idx < len(PALETTE):
        idx = default
    return hexrgb(PALETTE[idx])


# --- geometry -------------------------------------------------------------------------------

def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def regular_polygon(sides, radius, angle=0.0, star=False, inner=STAR_INNER):
    """Vertices of the game's regular polygon. Squares start at 45 deg (axis aligned).
    A star has 2*sides vertices starting on an INNER vertex at angle 0 and stepping by
    pi/sides, so its points sit at odd multiples of pi/sides (user exports, 2026-09-26)."""
    if star:
        n = sides * 2
        return [((radius * inner if k % 2 == 0 else radius) * math.cos(angle + math.pi * k / sides),
                 (radius * inner if k % 2 == 0 else radius) * math.sin(angle + math.pi * k / sides))
                for k in range(n)]
    base = math.pi / 4 if sides == 4 else 0.0
    pts = []
    for k in range(sides):
        a = base + angle + 2 * math.pi * k / sides
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    return pts


class Frame:
    """Origin and rotation of a local coordinate system inside the tank frame."""

    def __init__(self, origin=(0.0, 0.0), angle=0.0):
        self.origin, self.angle = origin, angle

    def apply(self, p):
        return add(rot(p, self.angle), self.origin)

    def child(self, origin, angle):
        return Frame(self.apply(origin), self.angle + angle)


def barrel_points(b, frame):
    x0 = float(b.get("startDistance", 0))
    x1 = x0 + min(float(b.get("distance", BARREL_LENGTH)), 500.0)   # the editor clamps length to 500
    off = float(b.get("offset", 0))
    hw0 = BARREL_HALF_WIDTH * float(b.get("heightMultiplier", 1))
    hw1 = hw0 * float(b.get("muzzleScale", 1))
    a = float(b.get("angle", 0))
    local = [(x0, off + hw0), (x1, off + hw1), (x1, off - hw1), (x0, off - hw0)]
    return [frame.apply(rot(p, a)) for p in local]


def barrel_mid_frame(b, frame):
    """Frame a barrel mounted on `b` is drawn in: the midpoint of b's axis, rotated with b."""
    x0 = float(b.get("startDistance", 0))
    mid = (x0 + min(float(b.get("distance", BARREL_LENGTH)), 500.0) / 2, float(b.get("offset", 0)))
    return frame.child(rot(mid, float(b.get("angle", 0))), float(b.get("angle", 0)))


def barrel_above(b):
    return bool((b.get("flags") or {}).get("aboveBody"))


def rides_part(d):
    """The body shape index a part or barrel rides (`mountPart`, spec section 8), or -1. `mount` wins,
    then `mountTurret`, as in the editor's import."""
    mp = d.get("mountPart", -1)
    if "mount" in d or "mountTurret" in d or not isinstance(mp, int) or isinstance(mp, bool) or mp < 0:
        return -1
    return mp


def tank_ops(tank, exporter_quirks=False, aim=0.0):
    """Ordered draw ops: ("poly", points, rgb) and ("circle", (cx, cy), r, rgb).

    `aim` is the world angle the tank's aim will be drawn at (the renderer's heading), so a part
    with `fixedRotation` can keep its own angle in the world (spec section 8, 2026-10-06).

    Rules (spec section 9b; the human-pack exports of 2026-09-26 added the mounted-part,
    invisible, aboveBody-barrel, star, turret-size/colour and default-size rules):
      * parts draw in ascending `order`; barrels, shapes and turrets share one sequence
      * the hull paints after every part except: shapes with `aboveBody`, barrels with
        `flags.aboveBody`, and turrets (unless `aboveBody: false`)
      * a part with `mount: i` draws in barrel i's midpoint frame, before barrel i
      * a part with `mountTurret: i` draws in turret i's frame: before the disc, or after it
        when the part is flagged aboveBody
      * `invisible: true` barrels are not drawn at all
      * the turret disc has radius `baseSize` (default 25) and palette `color` (default 1)
      * a shape without `size` draws at 25; a star starts on an inner vertex (ratio 0.4)
      * `body.angle` rotates a polygon hull (the exporter writes it as a rotate transform)
      * colour 27 is "same color as the body": the hull's own `color` when it has one (a palette
        index or a hex string), else the team colour (player blue here); the exporter does the same
      * a part or barrel with `mountPart: i` draws in body shape i's frame (its centre, rotated by
        its angle), chains included; a riding shape has no hitbox, so it is drawn like any other
      * a shape with `fixedRotation` keeps its angle in the world: here, angle minus `aim`
      * a hex `color` may carry alpha; the op's colour is then rgba and the PNG blends it
    """
    ops = []
    barrels = tank.get("barrels") or []
    shapes = tank.get("bodyShapes") or []
    turrets = tank.get("turrets") or []
    body = tank.get("body") or {}
    owner = palette_rgb(body["color"], 2) if body.get("color") is not None and body.get("color") != 27 else None

    def colour(part, default):
        return palette_rgb(part.get("color"), default, owner)

    def shape_angle(s):
        a = float(s.get("angle", 0))
        return a - aim if s.get("fixedRotation") else a

    def part_frame(i, depth=0):
        """The frame a part riding body shape i draws in: shape i's centre and angle, inside the frame
        shape i itself sits in (the hull, a turret, a barrel's midpoint or another shape)."""
        if not (0 <= i < len(shapes)) or depth > 5:
            return Frame()
        c = shapes[i]
        base = Frame()
        if "mount" in c and 0 <= c["mount"] < len(barrels) and "mountTurret" not in c:
            base = barrel_mid_frame(barrels[c["mount"]], Frame())
        elif "mountTurret" in c and 0 <= c["mountTurret"] < len(turrets):
            t = turrets[c["mountTurret"]]
            base = Frame((float(t.get("xOffset", 0)), float(t.get("yOffset", 0))), float(t.get("angle", 0)))
        elif rides_part(c) >= 0 and rides_part(c) != i:
            base = part_frame(rides_part(c), depth + 1)
        return base.child((float(c.get("xOffset", 0)), float(c.get("yOffset", 0))), shape_angle(c))

    def mounted_on_barrel(i):
        """(order, kind, index) of parts carried by barrel i, in draw order."""
        items = [(int(b.get("order", 0)), 0, j, "barrel") for j, b in enumerate(barrels)
                 if b.get("mount") == i and "mountTurret" not in b]
        items += [(int(s.get("order", 0)), 1, j, "shape") for j, s in enumerate(shapes)
                  if s.get("mount") == i and "mountTurret" not in s]
        return sorted(items)

    def riding_frame(d, frame):
        """The frame to draw `d` in: its carrier shape's frame when it rides one, else `frame`."""
        r = rides_part(d)
        return part_frame(r) if r >= 0 else frame

    def emit_barrel(i, frame, seen):
        if i in seen:
            return
        seen.add(i)
        b = barrels[i]
        if b.get("invisible"):
            return
        frame = riding_frame(b, frame)
        # parts mounted on this barrel draw inside its group, at its midpoint: before the
        # barrel, or after it when flagged aboveBody (same rule as parts on a turret disc)
        sub = barrel_mid_frame(b, frame)
        mounted = mounted_on_barrel(i)

        def emit_mounted(j, kind):
            if kind == "barrel":
                emit_barrel(j, sub, seen)
            else:
                emit_shape(shapes[j], sub)

        def is_above(j, kind):
            return barrel_above(barrels[j]) if kind == "barrel" else bool(shapes[j].get("aboveBody"))

        for _, _, j, kind in mounted:
            if not is_above(j, kind):
                emit_mounted(j, kind)
        ops.append(("poly", barrel_points(b, frame), colour(b, 1)))
        for _, _, j, kind in mounted:
            if is_above(j, kind):
                emit_mounted(j, kind)

    def emit_turret(t, i):
        # turrets always sit in the tank frame: a mountTurret on a turret is ignored by the
        # editor (export of a nested-turret test placed the turret at its raw offset)
        frame = Frame((float(t.get("xOffset", 0)), float(t.get("yOffset", 0))), float(t.get("angle", 0)))
        # ties in `order` among a turret's mounted parts draw shapes before barrels (the
        # opposite of the top-level array order; a player-built pack's wizard export, 2026-09-28)
        items = [(int(b.get("order", 0)), 1, j, "barrel", barrel_above(b)) for j, b in enumerate(barrels)
                 if b.get("mountTurret") == i]
        items += [(int(s.get("order", 0)), 0, j, "shape", bool(s.get("aboveBody"))) for j, s in enumerate(shapes)
                  if s.get("mountTurret") == i]
        items.sort(key=lambda k: k[:3])
        seen = set()
        for _, _, j, kind, above_disc in items:
            if not above_disc:
                emit_barrel(j, frame, seen) if kind == "barrel" else emit_shape(shapes[j], frame)
        ops.append(("circle", frame.origin, float(t.get("baseSize", TURRET_RADIUS)), colour(t, 1)))
        for _, _, j, kind, above_disc in items:
            if above_disc:
                emit_barrel(j, frame, seen) if kind == "barrel" else emit_shape(shapes[j], frame)

    def emit_shape(s, parent=None):
        parent = riding_frame(s, parent or Frame())
        frame = parent.child((float(s.get("xOffset", 0)), float(s.get("yOffset", 0))), shape_angle(s))
        sides = int(s.get("sides", 0))
        size = float(s.get("size", SHAPE_SIZE))
        if sides <= 2:
            ops.append(("circle", frame.origin, size, colour(s, 0)))
            return
        pts = regular_polygon(sides, size, 0.0, bool(s.get("star")))
        ops.append(("poly", [frame.apply(p) for p in pts], colour(s, 0)))

    # 1. parts under the hull, in `order` (ties keep array order: barrels, shapes, turrets)
    under, above = [], []
    for i, b in enumerate(barrels):
        if "mountTurret" in b or "mount" in b:
            continue
        (above if barrel_above(b) else under).append((int(b.get("order", 0)), 0, i, "barrel"))
    for i, s in enumerate(shapes):
        if "mountTurret" in s or "mount" in s:
            continue
        (above if s.get("aboveBody") else under).append((int(s.get("order", 0)), 1, i, "shape"))
    for i, t in enumerate(turrets):
        (above if t.get("aboveBody", True) else under).append((int(t.get("order", 0)), 2, i, "turret"))
    under.sort(key=lambda k: (k[0], k[1], k[2]))
    above.sort(key=lambda k: (k[0], k[1], k[2]))

    def emit(item):
        _, _, i, kind = item
        if kind == "barrel":
            emit_barrel(i, Frame(), set())
        elif kind == "shape":
            emit_shape(shapes[i])
        else:
            emit_turret(turrets[i], i)

    for item in under:
        emit(item)

    # 2. hull
    sides = int(body.get("sides", 0))
    size = float(body.get("size", HULL_RADIUS))
    rgb = owner if owner is not None else hexrgb(PALETTE[OWNER_COLOR])
    if sides <= 2:
        ops.append(("circle", (0.0, 0.0), size, rgb))
    else:
        ops.append(("poly", regular_polygon(sides, size * POLY_HULL_FACTOR, float(body.get("angle", 0)),
                                            bool(body.get("star"))), rgb))

    # 3. parts over the hull
    for item in above:
        emit(item)
    return ops


def ops_bbox(ops):
    xs, ys = [], []
    for op in ops:
        if op[0] == "poly":
            for x, y in op[1]:
                xs.append(x)
                ys.append(y)
        else:
            (cx, cy), r = op[1], op[2]
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
    pad = STROKE_WIDTH
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


# --- PNG ------------------------------------------------------------------------------------

HEADINGS = {"up": -math.pi / 2, "right": 0.0, "svg": -math.pi / 4}


def render_png(tank, path, size_px=600, heading="up", grid=True, exporter_quirks=False, label=None, ops=None):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit("Pillow is required for PNG output: pip install pillow")
    ss = 3
    h = HEADINGS[heading]
    ops = tank_ops(tank, exporter_quirks, aim=h) if ops is None else ops
    rops = []
    for op in ops:
        if op[0] == "poly":
            rops.append(("poly", [rot(p, h) for p in op[1]], op[2]))
        else:
            rops.append(("circle", rot(op[1], h), op[2], op[3]))
    x0, y0, x1, y1 = ops_bbox(rops)
    extent = max(x1 - x0, y1 - y0, 2 * HULL_RADIUS + 2 * STROKE_WIDTH) * 1.12
    scale = size_px / extent
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    W = size_px * ss

    def to_img(p):
        return ((p[0] - cx) * scale * ss + W / 2, (p[1] - cy) * scale * ss + W / 2)

    img = Image.new("RGB", (W, W), BACKGROUND)
    d = ImageDraw.Draw(img)
    if grid:
        step = 50
        gx = math.floor((cx - extent) / step) * step
        while gx < cx + extent:
            X = to_img((gx, 0))[0]
            d.line([(X, 0), (X, W)], fill=GRID_COLOUR, width=ss)
            gx += step
        gy = math.floor((cy - extent) / step) * step
        while gy < cy + extent:
            Y = to_img((0, gy))[1]
            d.line([(0, Y), (W, Y)], fill=GRID_COLOUR, width=ss)
            gy += step
    sw = max(1, round(STROKE_WIDTH * scale * ss))
    img = img.convert("RGBA")
    for op in rops:
        fill = op[2] if op[0] == "poly" else op[3]
        translucent = len(fill) == 4 and fill[3] < 255
        # a translucent part (hex colour with alpha, spec section 10) is drawn on its own layer and
        # blended, since ImageDraw overwrites instead of blending
        layer = Image.new("RGBA", (W, W), (0, 0, 0, 0)) if translucent else None
        dd = ImageDraw.Draw(layer) if translucent else ImageDraw.Draw(img)
        if op[0] == "poly":
            pts = [to_img(p) for p in op[1]]
            dd.polygon(pts, fill=fill)
            dd.line(pts + [pts[0]], fill=stroke_of(fill), width=sw, joint="curve")
            # round caps at the start vertex so the closed loop has no notch
            r = sw / 2
            dd.ellipse([pts[0][0] - r, pts[0][1] - r, pts[0][0] + r, pts[0][1] + r], fill=stroke_of(fill))
        else:
            (px, py), r = to_img(op[1]), op[2] * scale * ss
            dd.ellipse([px - r, py - r, px + r, py + r], fill=fill, outline=stroke_of(fill), width=sw)
        if translucent:
            img = Image.alpha_composite(img, layer)
    out = img.convert("RGB").resize((size_px, size_px), Image.LANCZOS)
    if label:
        ImageDraw.Draw(out).text((8, 6), label, fill=(40, 40, 40))
    out.save(path)
    return path


def render_sheet(tanks, path, size_px=300, heading="up", grid=False):
    from PIL import Image
    tmp = []
    n = len(tanks)
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size_px, rows * size_px), BACKGROUND)
    for i, t in enumerate(tanks):
        p = path + f".tmp{i}.png"
        render_png(t, p, size_px, heading, grid, label=t.get("name"))
        sheet.paste(Image.open(p), ((i % cols) * size_px, (i // cols) * size_px))
        tmp.append(p)
    sheet.save(path)
    for p in tmp:
        os.remove(p)
    return path


# --- SVG (editor-export style) -------------------------------------------------------------

def render_svg(tank, exporter_quirks=False):
    ops = tank_ops(tank, exporter_quirks)
    x0, y0, x1, y1 = ops_bbox([("poly", [rot(p, -math.pi / 4) for p in op[1]], op[2]) if op[0] == "poly"
                               else ("circle", rot(op[1], -math.pi / 4), op[2], op[3]) for op in ops])
    side = max(x1 - x0, y1 - y0) + 20
    vx, vy = (x0 + x1) / 2 - side / 2, (y0 + y1) / 2 - side / 2
    parts = []
    def paint(rgb):
        fill, st = "#%02X%02X%02X" % tuple(rgb[:3]), "rgb(%d, %d, %d)" % tuple(stroke_of(rgb)[:3])
        op_ = f' opacity="{rgb[3] / 255:.3f}"' if len(rgb) == 4 and rgb[3] < 255 else ""
        return fill, st, op_

    for op in ops:
        if op[0] == "poly":
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in op[1])
            fill, st, op_ = paint(op[2])
            parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{st}" stroke-width="{STROKE_WIDTH}"{op_}/>')
        else:
            (cx, cy), r = op[1], op[2]
            fill, st, op_ = paint(op[3])
            tr = f' transform="translate({cx:.1f} {cy:.1f})"' if (abs(cx) > 1e-6 or abs(cy) > 1e-6) else ""
            parts.append(f'<circle{tr} r="{r:g}" fill="{fill}" stroke="{st}" stroke-width="{STROKE_WIDTH}"{op_}/>')
    return (f'<svg viewBox="{vx:.1f} {vy:.1f} {side:.1f} {side:.1f}" stroke-linejoin="round" '
            f'xmlns="http://www.w3.org/2000/svg" width="512" height="512"><g transform="rotate(-45)">'
            + "".join(parts) + "</g></svg>")


# --- compare against an editor export -----------------------------------------------------

_TAG = re.compile(r"<(/?)(svg|g|polygon|circle|text)\b([^>]*?)(/?)>(?:([^<]*)</text>)?", re.S)


def parse_export(svg_text):
    """Per tank sub-SVG: [label, [absolute ("poly", pts, fill) / ("circle", c, r, fill)]]."""
    tanks, cur, stack = [], None, []
    for m in _TAG.finditer(svg_text):
        closing, tag, attrs, selfclose, text = m.groups()
        if tag == "svg" and "viewBox" in attrs and not closing:
            if "<svg" in svg_text[m.end():m.end() + 200000] and m.start() == svg_text.find("<svg"):
                continue  # outer wrapper of a roster export; the per-tank <svg>s follow
            cur = []
            tanks.append([None, cur])
            stack = []
            continue
        if tag == "text":
            if tanks and text:
                tanks[-1][0] = text.strip()
            continue
        if tag == "g":
            if closing:
                if stack:
                    stack.pop()
            else:
                tr = re.search(r'transform="([^"]*)"', attrs)
                stack.append(_parse_transform(tr.group(1)) if tr else ((0.0, 0.0), 0.0))
            continue
        if cur is None:
            continue
        fill = re.search(r'fill="([^"]*)"', attrs)
        fill = fill.group(1) if fill else ""

        def absolute(p):
            for origin, ang in reversed(stack):
                p = add(rot(p, ang), origin)
            return p

        if tag == "polygon":
            pts = [tuple(float(v) for v in xy.split(",")) for xy in re.search(r'points="([^"]*)"', attrs).group(1).split()]
            tr = re.search(r'transform="([^"]*)"', attrs)
            if tr:  # the hull polygon carries body.angle as its own rotate(...)
                origin, ang = _parse_transform(tr.group(1))
                pts = [add(rot(p, ang), origin) for p in pts]
            cur.append(("poly", [absolute(p) for p in pts], fill))
        elif tag == "circle":
            r = float(re.search(r'r="([^"]*)"', attrs).group(1))
            tr = re.search(r'transform="([^"]*)"', attrs)
            c = _parse_transform(tr.group(1))[0] if tr else (0.0, 0.0)
            cur.append(("circle", absolute(c), r, fill))
    return tanks


def _parse_transform(s):
    origin, ang = (0.0, 0.0), 0.0
    m = re.search(r"translate\(\s*([-\d.eE]+)[ ,]+([-\d.eE]+)\s*\)", s)
    if m:
        origin = (float(m.group(1)), float(m.group(2)))
    m = re.search(r"rotate\(\s*([-\d.eE]+)\s*\)", s)
    if m:
        ang = math.radians(float(m.group(1)))
    return origin, ang


def compare(pack, svg_path, tol=0.3):
    exported = parse_export(open(svg_path, encoding="utf-8").read())
    tanks = pack["tanks"]
    # roster exports label each tank; match by name (the pack's copies are "<name> copy"),
    # otherwise fall back to position
    by_label = {}
    for lbl, ops in exported:
        if lbl:
            by_label.setdefault(lbl.strip(), []).append(ops)
    pairs = []
    for i, t in enumerate(tanks):
        name = t.get("name", "")
        key = (name[:-5] if name.endswith(" copy") else name).strip()
        if by_label.get(key):
            # duplicate names pair in roster order (a player-built pack reuses several names)
            pairs.append((t, by_label[key].pop(0)))
        elif not by_label and i < len(exported):
            pairs.append((t, exported[i][1]))
    if len(pairs) != len(tanks):
        print(f"NOTE export has {len(exported)} tank(s), pack has {len(tanks)}; {len(pairs)} matched by name/position")
    bad = 0
    for t, ex in pairs:
        # the export wraps everything in rotate(-45); our ops are unrotated, so undo it
        ex = [("poly", [rot(p, math.pi / 4) for p in op[1]], op[2]) if op[0] == "poly"
              else ("circle", rot(op[1], math.pi / 4), op[2], op[3]) for op in ex]
        mine = tank_ops(t, exporter_quirks=True)
        problems = []
        if len(mine) != len(ex):
            problems.append(f"{len(mine)} elements vs {len(ex)} in export")
        for k, (a, b) in enumerate(zip(mine, ex)):
            if a[0] != b[0]:
                problems.append(f"#{k}: {a[0]} vs {b[0]}")
                continue
            fa = "#%02X%02X%02X" % tuple((a[2] if a[0] == "poly" else a[3])[:3])
            if fa != b[2 if b[0] == "poly" else 3].upper():
                problems.append(f"#{k}: fill {fa} vs {b[2 if b[0] == 'poly' else 3]}")
            if a[0] == "poly":
                if len(a[1]) != len(b[1]):
                    problems.append(f"#{k}: {len(a[1])} vertices vs {len(b[1])}")
                    continue
                dev = max(math.dist(p, q) for p, q in zip(a[1], b[1]))
                if dev > tol:
                    problems.append(f"#{k}: vertex deviation {dev:.2f} (mine {[(round(x, 1), round(y, 1)) for x, y in a[1]]})")
            else:
                if math.dist(a[1], b[1]) > tol or abs(a[2] - b[2]) > tol:
                    problems.append(f"#{k}: circle {a[1]} r={a[2]} vs {b[1]} r={b[2]}")
        status = "OK " if not problems else "DIFF"
        bad += bool(problems)
        print(f"{status} {t.get('name')}: {len(mine)} elements" + ("" if not problems else "\n     " + "\n     ".join(problems[:4])))
    print(f"{len(pairs) - bad}/{len(pairs)} tanks match the export within {tol} units")
    return 1 if bad else 0


# --- main -----------------------------------------------------------------------------------

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "tank"


def projectile_as_tank(tank, i):
    """A projectile's drawing as a pseudo-tank (spec section 5b: parts, sub-barrels and
    turrets draw in a frame where the projectile's own radius counts as 50, like a hull)."""
    pr = (tank.get("projectiles") or [])[i]
    sides = int(pr.get("sides", 0))
    body = {"sides": max(sides, 0), "size": HULL_RADIUS}
    if pr.get("star"):
        body["star"] = True
    if "color" in pr:
        body["color"] = pr["color"]
    return {"name": f"{tank.get('name', 'tank')} / {pr.get('name') or 'projectile'}",
            "body": body,
            "bodyShapes": pr.get("parts") or [],
            "barrels": pr.get("barrels") or [],
            "turrets": pr.get("turrets") or []}


def boss_scene(pack, boss, heading="up"):
    """Draw ops for a boss record (spec section 1b): its tank scaled by `scale` (the editor scales the
    tank and everything on it) with a plain level-1 tank beside it for size. Returns (ops, label) or
    None when the boss's tank is not in the pack (a stock-tank boss is not drawn: no stock roster here)."""
    tanks = {t.get("id"): t for t in pack.get("tanks") or []}
    t = tanks.get(boss.get("tank"))
    if t is None:
        return None
    k = float(boss.get("scale", 2))
    ops = tank_ops(t, aim=HEADINGS[heading])
    scaled = [("poly", [(x * k, y * k) for x, y in op[1]], op[2]) if op[0] == "poly"
              else ("circle", (op[1][0] * k, op[1][1] * k), op[2] * k, op[3]) for op in ops]
    x0, y0, x1, y1 = ops_bbox(scaled)
    # the reference tank: hull 50 and a stock barrel, off to the tank's right at the picture's edge
    off = (0.0, y1 + 50 + 60)
    ref = [("poly", [(x + off[0], y + off[1]) for x, y in barrel_points({}, Frame())], hexrgb(PALETTE[1])),
           ("circle", off, float(HULL_RADIUS), hexrgb(PALETTE[OWNER_COLOR]))]
    return ref + scaled, f"{boss.get('name') or 'Boss'} boss x{k:g} (next to a level-1 tank)"


def decorated_projectiles(tank):
    """Indexes of the tank's projectiles that carry parts, sub-barrels or turrets."""
    return [i for i, pr in enumerate(tank.get("projectiles") or [])
            if pr.get("parts") or pr.get("barrels") or pr.get("turrets")]


def render_pack(pack, out_dir, size_px=600, heading="up", grid=True, svg=False, sheet=False,
                projectiles=False, bosses=False):
    os.makedirs(out_dir, exist_ok=True)
    # renders keep the unversioned name, so they always show the latest iteration (SKILL.md §5a)
    base = slug(re.sub(r"\s+v\d+\.\d+\.\d+$", "", pack.get("name", "pack")))
    paths = []
    used = {}
    for t in pack.get("tanks", []):
        name = f"{base}-{slug(t.get('name', 'tank'))}"
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            name += f"-{used[name]}"
        p = os.path.join(out_dir, name + ".png")
        render_png(t, p, size_px, heading, grid, label=t.get("name"))
        paths.append(p)
        if svg:
            sp = os.path.join(out_dir, name + ".svg")
            with open(sp, "w", encoding="utf-8") as f:
                f.write(render_svg(t))
            paths.append(sp)
        if projectiles:
            for i in decorated_projectiles(t):
                pt = projectile_as_tank(t, i)
                pp = os.path.join(out_dir, f"{name}-proj-{slug(pt['name'].split(' / ', 1)[1])}.png")
                render_png(pt, pp, size_px, heading, grid, label=pt["name"])
                paths.append(pp)
                if svg:
                    sp = pp[:-4] + ".svg"
                    with open(sp, "w", encoding="utf-8") as f:
                        f.write(render_svg(pt))
                    paths.append(sp)
    if bosses:
        for b in pack.get("bosses") or []:
            scene = boss_scene(pack, b, heading) if isinstance(b, dict) else None
            if scene:
                bp = os.path.join(out_dir, f"{base}-boss-{slug(b.get('name') or 'boss')}.png")
                render_png({}, bp, size_px, heading, grid, label=scene[1], ops=scene[0])
                paths.append(bp)
    if sheet and len(pack.get("tanks", [])) > 1:
        paths.append(render_sheet(pack["tanks"], os.path.join(out_dir, base + "-sheet.png"), heading=heading))
    return paths


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # tank names may carry emoji (Windows consoles default to cp1252)
    except (AttributeError, ValueError):
        pass
    pack = json.load(open(argv[1], encoding="utf-8"))
    args = argv[2:]

    def opt(name, default=None):
        if name in args:
            i = args.index(name)
            return args[i + 1]
        return default

    if "--compare" in args:
        return compare(pack, opt("--compare"))
    out = opt("--out", os.path.join(os.path.dirname(os.path.abspath(argv[1])), "renders"))
    paths = render_pack(pack, out, int(opt("--size", 600)), opt("--heading", "up"),
                        grid="--no-grid" not in args, svg="--svg" in args, sheet="--sheet" in args,
                        projectiles="--projectiles" in args, bosses="--boss" in args)
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
