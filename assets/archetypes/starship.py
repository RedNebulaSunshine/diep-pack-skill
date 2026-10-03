"""Starship: saucer hull, neck, engineering hull, two warp nacelles on pylons. Twin phasers
alternate on left click, a torpedo (glider-style missile) on right click, and an aft phaser
dome tracks whatever gets behind. Exercises: frame() for the nacelle sub-assembly, mirror(),
mechanics presets (twin, missile_launcher, auto_turret), owner colour on the bridge.
Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/starship.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design  # noqa: E402

d = Design("Starship", level=45, parents=[19])          # off Hunter
d.hull(size=50, color=C.silver)                         # the saucer
d.set(zoomMultiplier=0.85, speedMultiplier=1.1)

# spine: neck, engineering hull, deflector
d.rod((-30, 0), (-100, 0), width=26, color=C.silver, name="neck")
d.rod((-92, 0), (-222, 0), width=54, end_width=38, color=C.silver, name="engineering hull")
d.shape(8, 27, at=(-92, 0), color=C.silver, name="engineering bow")
d.shape(8, 16, at=(-92, 0), color=C.peach, name="deflector dish")
d.shape(8, 19, at=(-222, 0), color=C.silver, name="engineering stern")

# right nacelle on its pylon, built in the nacelle's own frame, then mirrored
pylon = d.rod((-150, 22), (-176, 78), width=16, color=C.silver, name="pylon")
with d.frame(at=(-176, 82)):
    body = d.rod((64, 0), (-124, 0), width=28, color=C.silver, name="nacelle")
    grille = d.rod((40, 0), (-104, 0), width=8, color=C.cyan, name="nacelle grille")
    bussard = d.shape(8, 15, at=(66, 0), color=C.red, name="bussard collector")
    exhaust = d.shape(8, 12, at=(-126, 0), color=C.cyan, name="warp exhaust")
d.mirror([pylon, body, grille, bussard, exhaust])

# weapons
d.twin(spacing=30, length=92, width=14, name="phaser", color=C.grey,
       speedMultiplier=1.3, reloadMultiplier=0.8, damageMultiplier=0.55)
d.missile_launcher(gap=20, thrusters="glider", base=False, right_click=True, name="torpedo tube",
                   distance=58, heightMultiplier=0.75, reloadMultiplier=5)
d.set(helpText="Right click to fire a photon torpedo")
d.auto_turret(at=(-26, 0), angle=180, name="aft phaser dome")

# bridge in the owner's team colour, on top of the saucer
d.shape(8, 14, at=(16, 0), color=C.owner, above=True, name="bridge")

d.save()
