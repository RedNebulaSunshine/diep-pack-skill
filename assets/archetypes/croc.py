"""Croc: a crocodile bartender. A Forest hull for the head, a long snout split into two
cursor-following jaws with White teeth that bite only while left click is held (invisible,
click-only bite points at three teeth per side dropping stationary White triangles, so the jaws
are picture only), two eyes that watch the nearest enemy with brows behind them that swing with
the gaze, a Crimson bow tie, a rigid body of octagon plates with scutes and sparkles, four
stubby legs that paddle on their own (auto-fire pistons throwing spinning White star sparkles)
with the rear pair on pendulum pivots that swing out on turns, a sparkler at the tail root
scattering spinning Yellow stars, and a trailing tail of stationary hexagons in four sizes dropped by four rear
barrels with growing lifetimes (ridged, then a Mint triangle tip), so it steps down along its length.
Budget: 32 body shapes and 32 barrels per tank (spec §9c) and 120 shots/s at the Reload cap
(spec §7a). Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/croc.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design  # noqa: E402

d = Design("Croc", level=60, parents=[36])                     # a biter off Smasher
d.hull(size=44, color=C.forest)                                # the head
d.set(statsMaxLevel=[12] * 8,                                  # every stat maxed
      speedMultiplier=1.1, zoomMultiplier=0.9,
      helpText="Hold left click to bite: the jaws close and the teeth do the damage")

# --- legs first so the hull and body plates cover their roots ----------------------------------
LEG_W = 24                                                      # >= 22 so the paddle pump shows in game
legs = []
for s, side in ((1, "right"), (-1, "left")):
    # front legs: fixed rods that pump
    legs.append(d.rod((-18, 30 * s), (-6, 92 * s), width=LEG_W, color=C.forest, name=f"front leg {side}"))
    # rear legs: on a small pendulum pivot under the hip plate, so they swing out when he turns
    t = d.turret(at=(-94, 22 * s), angle=112 * s, arc=25, controllable=False, above=False, size=6,
                 color=C.forest, name=f"rear hip {side}")
    legs.append(d.rod((0, 0), (64, 0), width=LEG_W, color=C.forest, turret=t, name=f"rear leg {side}"))
# every leg is a piston that fires White sparkle specks on its own (forceFire), diagonal pairs
# half a beat apart, so he paddles whether or not you are biting
d.animate([legs[0], legs[3]], phase=0)          # front right, rear left
d.animate([legs[2], legs[1]], phase=0.5)        # front left, rear right
for leg in legs:
    leg["reloadMultiplier"] = 1                 # 4.75/s each at the Reload cap of 12
    leg["flags"] = {"forceFire": True}
    # the specks become sparkles: bigger, spinning White stars that drift off the feet
    leg.update(bulletSizeMultiplier=0.35, speedMultiplier=0.4, lifetime=0.35, spreadMultiplier=2)
d.projectiles[d.speck()].update(sides=4, star=True, spin=0.3)

# --- the rigid body: three plates behind the head, shrinking toward the tail --------------------
d.shape(6, 40, at=(-52, 0), color=C.forest, name="back plate")          # all hexagons, no rotation
d.shape(6, 34, at=(-94, 0), color=C.forest, name="hip plate")
d.shape(6, 26, at=(-130, 0), color=C.forest, name="tail root")
# two rows of dorsal scutes and two sparkles on top of the plates
for k, x in enumerate((-48, -70, -92), 1):
    d.shape(3, 9, at=(x, 9), color=C.mint, above=True, name=f"scute right {k}")
    d.shape(3, 9, at=(x, -9), color=C.mint, above=True, name=f"scute left {k}")
d.shape(3, 8, at=(-126, 8), color=C.mint, above=True, name="scute tail right")
d.shape(3, 8, at=(-126, -8), color=C.mint, above=True, name="scute tail left")
d.shape(4, 15, at=(-66, -24), color=C.white, star=True, above=True, name="sparkle left")
# and a sparkler: an invisible auto-firing barrel at the tail root scattering spinning Yellow stars
glitter = d.projectile("Glitter", base="bullet", sides=4, star=True, color=C.yellow, spin=0.3)
d.weapon(projectile=glitter, angle=180, gap=140, length=5, invisible=True, auto_fire=True, name="tail sparkler",
         damageMultiplier=0.01, penetrationMultiplier=0.2, bulletSizeMultiplier=0.3, speedMultiplier=0.5,
         initialVelocityMultiplier=1, spreadMultiplier=3, lifetime=0.5, reloadMultiplier=1, recoilMultiplier=0,
         knockbackMultiplier=0)
d.shape(4, 12, at=(-104, 22), color=C.white, star=True, above=True, name="sparkle right")

# --- the snout: two cursor pivots, each carrying half the jaw with White teeth ------------------
bite = d.projectile("Bite", base="bullet", sides=3, color=C.white)   # a White triangle at the tooth
JAW = 150
for s, side in ((1, "right"), (-1, "left")):
    t = d.cursor_pivot(at=(34, 18 * s), angle=35 * s, arc=50, size=10, color=C.forest,
                       name=f"jaw pivot {side}")
    xs = [44, 70, 96, 122] if s > 0 else [57, 83, 109, 135]         # interlocking teeth
    for k, x in enumerate(xs, 1):
        d.shape(3, 16, at=(x, -5 * s), angle=-90 * s, color=C.white, turret=t,
                name=f"tooth {side} {k}")
    d.rod((0, 8 * s), (JAW, 8 * s), width=32, end_width=22, color=C.forest, turret=t,
          name=f"snout {side}")
    d.shape(0, 11, at=(JAW, 8 * s), color=C.forest, turret=t, name=f"snout tip {side}")
    d.shape(0, 4, at=(JAW - 4, 12 * s), color=C.charcoal, turret=t, name=f"nostril {side}")
    for k, x in zip((1, 2, 4), (xs[0], xs[1], xs[3])):             # bite points at teeth 1, 2 and 4
        at = (x, -17 * s)
        r = math.hypot(*at)
        d.weapon(projectile=bite, angle=math.degrees(math.atan2(at[1], at[0])), gap=r - 5, length=5,
                 invisible=True, mountTurret=t, name=f"bite {side} {k}",
                 damageMultiplier=1.0, penetrationMultiplier=20, bulletSizeMultiplier=0.4,
                 reloadMultiplier=0.8, spreadMultiplier=0, lifetime=0.15, recoilMultiplier=0,
                 knockbackMultiplier=0, initialVelocityMultiplier=0)

# --- the face: eyes that watch, brows behind them that swing with the gaze, and the bow tie -----
er = d.eye(at=(14, 24), size=18, pupil=9, color=C.white, pupil_color=C.charcoal, arc=80, look=6, name="eye right")
el = d.eye(at=(14, -24), size=18, pupil=9, color=C.white, pupil_color=C.charcoal, arc=80, look=6, name="eye left")
# in each eye's frame x is the gaze; the brow sits just behind the rim (x about -20)
d.rod((-23, -12), (-17, 14), width=6, color=C.charcoal, turret=er, above=True, name="brow right")   # cocked
d.rod((-20, 13), (-20, -13), width=6, color=C.charcoal, turret=el, above=True, name="brow left")    # flat
d.shape(3, 12, at=(-28, 11), angle=-90, color=C.crimson, above=True, name="bow tie right")
d.shape(3, 12, at=(-28, -11), angle=90, color=C.crimson, above=True, name="bow tie left")
d.shape(0, 5, at=(-28, 0), color=C.crimson, above=True, name="bow tie knot")

# --- the tail: four droppers fire at the same spot behind the tail root, each a different
# size with a longer life (spec §7 stages): hexagons like the body, the root piece with two
# Mint ridge triangles, the next two with one, and a Mint triangle tip that outlives them all,
# so the tail steps down 1.0 -> 0.8 -> 0.6 -> 0.4 along its length. Chained stages (a spawned
# piece spawning the next) never showed in game, hence one dropper per stage.
# import budget (spec §7a, 120/s at cap 12): bites, legs, the four droppers and the tail
# sparkler; save() prints the exact figure
def ridge(y=0, size=14):
    return d.part(3, size, at=(-4, y), color=C.mint, above=True)


d.trail(gap=150, reload=0.7, damage=0.25, name="tail dropper", stages=[
    (1.0, 0.5, 6, C.forest, [ridge(-15), ridge(15)]),
    (0.8, 0.5, 6, C.forest, [ridge()]),
    (0.6, 0.5, 6, C.forest, [ridge(size=16)]),
    (0.4, 0.5, 3, C.mint, None)])

d.save()
