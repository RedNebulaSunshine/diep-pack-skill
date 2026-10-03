"""President Prism: a front-on portrait of a president's head painted on the hull (face-art
face art), with a rainbow prism as its weapon: a white prism at the crown and seven coloured
rays fanning out of it, each firing bullets of its own colour. Level 60 off Triple Shot.
Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/president-prism.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design, arc  # noqa: E402

d = Design("President Prism", level=60, parents=[3])
d.set(helpText="Seven colours from one prism")

# --- under the hull: suit, collar, tie, ears (drawn first so the head covers their roots) ---
d.rod((-50, -78), (-50, 78), width=36, color=C.charcoal, name="suit shoulders")
d.shape(3, 14, at=(-62, 0), angle=180, color=C.white, name="collar")
d.rod((-58, 0), (-84, 0), width=9, color=C.crimson, name="tie")
d.mirror(d.circle(14, at=(-2, 60), color=C.brown, name="ear"))

# --- the rainbow: seven rays out of the crown, under the hair, each its own colour ---
rainbow = [("red", C.salmon), ("orange", C.orange), ("yellow", C.yellow), ("green", C.mint),
           ("blue", C.cyan), ("indigo", C.indigo), ("violet", C.plum)]
for i, (label, colour) in enumerate(rainbow):
    angle = -36 + 12 * i
    ray = d.bullet(f"{label} ray", color=colour)
    d.cannon(angle=angle, gap=48, length=62, width=12, color=colour, projectile=ray,
             damageMultiplier=0.4, recoilMultiplier=0.3, name=f"{label} ray barrel")

# --- the head ---
d.hull(size=55, color=C.brown)

# --- over the hull: hair, face, prism ---
d.chain(arc((0, 0), 49, -72, 72, 11), sizes=13, sides=0, color=C.charcoal, above=True, name="hair")
d.mirror(d.line((22, 27), (25, 9), width=7, color=C.charcoal, name="brow"))
d.eye(at=(10, 17), size=10, pupil=5, look=3, arc=60, name="eye right")
d.eye(at=(10, -17), size=10, pupil=5, look=3, arc=60, name="eye left")
d.circle(6, at=(-4, 0), color=C.brown, above=True, name="nose")
for i, p in enumerate(arc((-8, 0), 22, 152, 208, 5)):
    d.shape(4, 7, at=p, color=C.white, above=True, name=f"tooth {i + 1}")
d.polyline(arc((-8, 0), 26, 138, 222, 7), width=5, color=C.charcoal, name="smile")
d.shape(3, 16, at=(52, 0), angle=0, color=C.white, above=True, name="prism")

d.save()
