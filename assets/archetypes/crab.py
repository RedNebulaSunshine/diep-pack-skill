"""Crab: a wide carapace with eight jointed legs, eye stalks, and two claws that are the guns.
The right claw fires a Destroyer shell on left click, the left claw on right click.
Exercises: frame() for the claw sub-assembly, limb() for jointed legs, mirror(), a
right-click weapon, side lobes that widen the hull. Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/crab.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design, polar  # noqa: E402

d = Design("Crab", level=45, parents=[10])            # off Destroyer
d.hull(size=40, color=C.red)
d.set(helpText="Left click snaps the right claw, right click the left claw",
      speedMultiplier=0.9, baseHealth=1.15)

# legs first so the carapace covers their roots: root on the rim, knee out, tip down and back
for k, (root, knee, tip) in enumerate([((30, 26), (66, 84), (118, 72)),
                                        ((14, 38), (30, 112), (66, 150)),
                                        ((-8, 40), (-30, 112), (-70, 148)),
                                        ((-28, 32), (-84, 84), (-134, 100))], 1):
    rods, joints = d.limb([root, knee, tip], widths=(14, 7), color=C.maroon, name=f"leg {k}")
    d.mirror(rods + joints)

# carapace: hull plus lobes under it that widen the silhouette
d.shape(8, 32, at=(-8, 38), color=C.red, name="carapace lobe right")
d.shape(8, 32, at=(-8, -38), color=C.red, name="carapace lobe left")
d.shape(8, 26, at=(-34, 0), color=C.red, name="carapace rear")

# right claw: arm to a palm, then pincers built in the palm's own frame
arm, arm_joints = d.limb([(36, 18), (66, 74), (112, 84)], widths=(20, 18), color=C.red, name="claw arm")
with d.frame(at=(112, 84), angle=-25):                  # local x points forward-inward
    palm = d.shape(8, 24, at=(0, 0), color=C.red, name="claw palm")
    lower = d.rod((6, 12), (58, 26), width=16, end_width=5, color=C.red, name="lower pincer")
    gun = d.destroyer(gap=10, length=56, width=18, muzzle=0.35, offset=-10, angle=-12, color=C.red,
                      name="upper pincer", reloadMultiplier=3, recoilMultiplier=6)
d.mirror(arm + arm_joints + [palm, lower, gun])
left_gun = d.parts[-1][1]                                # the mirrored copy fires on right click
left_gun["flags"] = {"firesOnSecondary": True}

# eye stalks and eyes at the front
for side, y in (("right", 1), ("left", -1)):
    d.rod((28, 8 * y), (58, 20 * y), width=8, color=C.maroon, name=f"eye stalk {side}")
    d.shape(8, 9, at=(62, 22 * y), color=C.charcoal, name=f"eye {side}")

d.save()
