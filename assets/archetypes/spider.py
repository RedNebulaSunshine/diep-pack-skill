"""Spider: cephalothorax hull, big abdomen with a red hourglass, eight jointed legs that pump
while firing (two pairs out of phase), two fangs that bite alternately, and a spinneret at
the tail that streams short-lived swarm spiderlings. Exercises: limb(), animate() on legs,
above=True eyes, swarm_spawner with a custom drone projectile, gap to place a barrel far
from the hull. Run from the folder where the pack should land (it writes ./output/):  python assets/archetypes/spider.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))  # this skill's scripts folder
from compose import C, Design  # noqa: E402

d = Design("Spider", level=45, parents=[11])           # off Overseer
d.hull(size=32, color=C.charcoal)
d.set(helpText="Hold fire: the fangs bite, the legs scuttle, the spinneret streams spiderlings",
      speedMultiplier=1.1, zoomMultiplier=0.9)

# legs: root on the rim, raised knee, tip; pairs 1+3 and 2+4 pump out of phase. The shins pump
# (the moving end is the muzzle, so the last segment with its free foot is the natural one);
# they must be about 22+ wide at the base to read
legs = [((24, 14), (96, 62), (172, 30)),
        ((12, 28), (62, 106), (132, 152)),
        ((-6, 30), (-30, 112), (-62, 178)),
        ((-22, 22), (-82, 82), (-134, 134))]
for k, pts in enumerate(legs, 1):
    rods, joints = d.limb(pts, widths=[24, 24, 8], color=C.charcoal, name=f"leg {k}")
    d.animate(rods[1], phase=0.5 if k % 2 == 0 else 0)      # shin: 24 wide at the knee, free foot, so the pump shows
    d.mirror(rods + joints)

# abdomen behind the hull, hourglass on it
d.shape(10, 44, at=(-70, 0), color=C.charcoal, name="abdomen")
d.shape(10, 30, at=(-124, 0), color=C.charcoal, name="abdomen tip")
d.shape(3, 13, at=(-56, 0), angle=180, color=C.red, name="hourglass front")   # tips meet at -69
d.shape(3, 13, at=(-82, 0), angle=0, color=C.red, name="hourglass back")

# eyes on top of the head
for name, at in (("eye inner right", (26, 6)), ("eye inner left", (26, -6)),
                 ("eye outer right", (18, 17)), ("eye outer left", (18, -17))):
    d.shape(8, 5, at=at, color=C.white, above=True, name=name)

# fangs: two short tapered cannons angled inward, alternating
bite = dict(damageMultiplier=0.7, reloadMultiplier=0.7, penetrationMultiplier=0.8, color=C.maroon)
d.cannon(angle=-7, offset=-10, gap=28, length=38, width=11, muzzle=0.35, name="left fang", **bite)
d.cannon(angle=7, offset=10, gap=28, length=38, width=11, muzzle=0.35, name="right fang", delay=0.5, **bite)

# spinneret at the tail: short-lived cruising spiderlings, uncontrolled, coloured like the body
spiderling = d.drone("Spiderling", cruise=True, controllable=False, color=C.charcoal)
d.swarm_spawner(angle=180, offset=0, gap=146, count=12, controllable=False, projectile=spiderling,
                name="spinneret", distance=48, heightMultiplier=0.5, lifetime=5, color=C.dark)

d.save()
