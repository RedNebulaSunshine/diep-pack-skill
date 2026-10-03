"""Dragonfly: worked example of a figurative tank built with compose.py.

Top view, facing forward (+x). Thorax = hull, head + abdomen = polygon chain, four
wings = tapered rod strips, six legs = thin rods, two mandible barrels are the weapon.
Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/dragonfly.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design, bezier  # noqa: E402

d = Design("Dragonfly", level=45, parents=[8])          # off Tri-Angle: fast, fragile
d.hull(size=34, color=C.forest)                          # thorax
d.set(helpText="Both mandibles fire; hold to strafe like a real one",
      speedMultiplier=1.15, zoomMultiplier=0.9)

# legs first so wings and body paint over them
for leg, root, tip in [("front leg", (26, 18), (72, 58)), ("middle leg", (4, 30), (-2, 78)),
                       ("rear leg", (-18, 26), (-62, 66))]:
    d.mirror(d.rod(root, tip, width=8, color=C.charcoal, name=leg))

# wings: two rods each so the membrane widens mid-span then tapers to the tip
fore = d.strip([(14, 24), (40, 132), (60, 228)], widths=[28, 44, 14], color=C.white, name="fore wing")
hind = d.strip([(-10, 26), (-34, 128), (-52, 218)], widths=[30, 48, 16], color=C.white, name="hind wing")
d.mirror(fore + hind)

# abdomen: nine shrinking hexagons along a gentle curve, alternating two greens
segments = d.chain(bezier((-36, 0), (-120, 6), (-200, -4), (-268, 2), 9), sizes=(19, 8),
                   sides=6, color=C.forest, name="abdomen")
for i, seg in enumerate(segments):
    if i % 2:
        seg["color"] = C.green
d.shape(3, 14, at=(-282, 0), angle=180, color=C.forest, name="tail tip")

# head and eyes
d.shape(6, 25, at=(54, 0), color=C.forest, name="head")
eye = d.shape(8, 10, at=(62, 15), color=C.charcoal, name="eye")
d.mirror(eye)

# weapon: two mandibles that alternate
bullet = d.projectile("Bite", "bullet", sides=-1)
d.weapon(projectile=bullet, angle=-10, offset=-9, gap=58, length=42, width=14, muzzle=0.7,
         color=C.charcoal, damageMultiplier=0.8, reloadMultiplier=0.6, delay=0.5, name="left mandible")
d.weapon(projectile=bullet, angle=10, offset=9, gap=58, length=42, width=14, muzzle=0.7,
         color=C.charcoal, damageMultiplier=0.8, reloadMultiplier=0.6, name="right mandible")

d.save()
