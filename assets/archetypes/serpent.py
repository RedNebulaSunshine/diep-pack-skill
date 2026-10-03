"""Serpent: a snake whose body is a trail of stationary bullets left behind the head, with a
biting mouth that opens toward the cursor and an eye that watches the nearest enemy.
Built from the tricks of a player-built snake tank: d.jaws(), d.trail(), d.eye(),
plus line() brows. Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/serpent.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design  # noqa: E402

d = Design("Serpent", level=45, parents=[36])         # a smasher-line brawler: no bullets to speak of
d.hull(size=58, color=C.forest)
d.set(speedMultiplier=1.4, zoomMultiplier=0.85, baseHealth=250, baseBodyDamage=12,
      statsMaxLevel=[10, 0, 0, 0, 0, 10, 10, 10])

# the body: hexagonal segments dropped behind the head for two seconds, thinning at the end
d.trail(gap=40, size=2.0, seconds=2.0, taper=(1.0, 0.75), sides=6, name="tail dropper")  # end pieces half size

# the mouth: two cursor-following jaws with teeth, fangs and bite points (arc 60 >= rest 45 so they close)
d.jaws(at=(40, 20), rest=45, arc=60, length=140, teeth=4, color=C.owner, tooth_color=C.cannon, bite=0.75)

# a single eye on top that tracks the nearest enemy, with a brow line over it
d.eye(at=(15, 0), size=30, pupil=15, color=C.white, pupil_color=C.border, arc=90, look=10, name="eye")
d.line((-12, -34), (28, -30), width=6, color=C.charcoal, name="brow left")
d.line((-12, 34), (28, 30), width=6, color=C.charcoal, name="brow right")

d.save()
