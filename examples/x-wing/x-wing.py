"""X-Wing: a T-65 starfighter from above, S-foils in attack position. Four wingtip laser
cannons fire Salmon bolts in sequence on left click; right click fires a proton torpedo
from the chin tube and lights all four engines (Booster-style recoil) for a burst of speed.
R2-D2 rides behind the canopy and turns his dome toward the nearest enemy. Level 120 off
Tri-Angle. Run from the folder where the pack should land (it writes ./output/):  python examples/x-wing/x-wing.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design  # noqa: E402

d = Design("X-Wing", level=120, parents=[8])
d.set(speedMultiplier=1.2, zoomMultiplier=0.85, statsMaxLevel=[7, 12, 7, 3, 12, 7, 7, 7],   # a tester's balance
      helpText="Left click: wingtip lasers. Right click: proton torpedo and afterburners")

HULL = C.box          # starfighter grey-white
DARK = C.charcoal
RED = C.salmon        # Red Five markings and laser bolts

bolt = d.bullet("laser bolt", color=RED)
exhaust = d.bullet("engine exhaust", color=C.orange)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# --- wings first (everything else sits on top of their roots) ---
for s, side in ((1, "right"), (-1, "left")):
    wings = {"upper": ((-4, 14 * s), (-26, 150 * s)), "lower": ((-28, 14 * s), (-70, 128 * s))}
    for which, (root, tip) in wings.items():
        d.rod(root, tip, width=52, end_width=34, color=HULL, name=f"{which} wing {side}")
        d.rod(lerp(root, tip, 0.62), lerp(root, tip, 0.74), width=38, color=RED, name=f"{which} wing stripe {side}")
        d.line(lerp(root, tip, 0.1), lerp(root, tip, 0.58), width=5, color=DARK, above=False,
               name=f"{which} wing panel line {side}")

# --- wingtip laser cannons: each on a cursor pivot so all four converge on the cursor while
# --- firing (rest straight ahead), and they fire one after another ---
for i, (side, which, tip) in enumerate((("right", "upper", (-26, 150)), ("left", "lower", (-70, -128)),
                                        ("right", "lower", (-70, 128)), ("left", "upper", (-26, -150)))):
    mount = d.cursor_pivot(at=tip, angle=0, arc=25, size=9, color=DARK, name=f"{which} cannon mount {side}")
    d.cannon(length=104, width=10, muzzle=1.3, color=DARK, projectile=bolt, mountTurret=mount,
             damageMultiplier=0.3, penetrationMultiplier=0.6, speedMultiplier=1.8, bulletSizeMultiplier=0.4,
             spreadMultiplier=0, reloadMultiplier=0.28, recoilMultiplier=0.1, delay=0.25 * i,
             name=f"laser cannon {which} {side}")

# --- engines: four nacelles at the wing roots, real rear barrels for the afterburner ---
for s, side in ((1, "right"), (-1, "left")):
    for which, y in (("inner", 27), ("outer", 49)):
        with d.frame(at=(-22, y * s), angle=180):
            d.cannon(length=80, width=20, muzzle=1.25, color=HULL, projectile=exhaust, right_click=True,
                     damageMultiplier=0.15, lifetime=0.5, recoilMultiplier=2.4, bulletSizeMultiplier=0.7,
                     name=f"engine {which} {side}")
        d.circle(9, at=(-104, y * s), color=RED, name=f"exhaust glow {which} {side}")

# --- fuselage: wing-root block (the hitbox), tail, nose ---
d.shape(4, 42, at=(-46, 0), color=HULL, collidable=True, name="wing root block")
for s, side in ((1, "right"), (-1, "left")):
    for which, y in (("inner", 27), ("outer", 49)):
        d.shape(4, 7, at=(-18, y * s), color=DARK, name=f"engine intake {which} {side}")
d.rod((-15, 0), (-95, 0), width=24, color=HULL, name="tail spine")
d.rod((14, 0), (206, 0), width=30, end_width=10, color=HULL, name="nose")
d.rod((118, -13), (118, 13), width=6, color=RED, name="nose stripe 1")
d.rod((138, -12), (138, 12), width=6, color=RED, name="nose stripe 2")
d.circle(6, at=(207, 0), color=DARK, name="nose tip")

# --- proton torpedo tube under the chin (right click) ---
d.missile_launcher(gap=34, thrusters="rocketeer", base=False, right_click=True, name="torpedo tube",
                   distance=66, heightMultiplier=0.45, muzzleScale=1.0, color=DARK, reloadMultiplier=5)

# --- hull (small: the fuselage is drawn), canopy, astromech ---
d.hull(size=16, color=HULL)
d.rod((6, 0), (64, 0), width=20, end_width=10, color=DARK, above=True, name="canopy")
d.rod((12, 0), (54, 0), width=10, end_width=5, color=C.cyan, above=True, name="canopy glass")
d.eye(at=(-16, 0), size=15, pupil=7, color=C.white, pupil_color=C.blue, look=5, arc=180, name="R2-D2")

d.save()
