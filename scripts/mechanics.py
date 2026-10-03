"""mechanics.py: stock weapon systems as one-call presets for compose.Tank.

Every preset copies the distinguishing numbers of a real stock tank from references/recipes.md
(which quotes the stock tanks copied out of the game ), names the parts it makes, and returns the barrel dict(s) so a
design can tweak them afterwards. Geometry is given in editor terms (degrees clockwise, 0 =
forward; length; gap from the hull centre; side offset), exactly like Tank.weapon().

    d = Design("Crab", level=45, parents=[10])
    d.destroyer(angle=-25, offset=-40, gap=60, length=70, name="left claw")
    d.spawner(angle=180, count=3)                         # Overlord rear spawner
    d.trap_launcher(angle=90); d.trap_launcher(angle=-90)
    d.sniper(right_click=True)                            # firesOnSecondary + helpText

Every keyword the preset does not consume passes through to the barrel, so any spec field
(reloadMultiplier, delay, color, mountTurret, flags ...) can override the stock value.

Combining systems: add `delay` to stagger, `right_click=True` to move a system to the right
mouse button, and scale `damageMultiplier` down as barrel count goes up (cannon_ring does).
"""
import math

BARREL_LENGTH = 95.0
BARREL_WIDTH = 42.0

# The confirmed harmless "speck" shot that makes a decorative rod pump like a piston
# (figurative.md section 5, the `dragonfly-flap` test build).
SPECK_FIELDS = dict(damageMultiplier=0.01, penetrationMultiplier=0.2, bulletSizeMultiplier=0.15,
                    speedMultiplier=0.1, lifetime=0.1, recoilMultiplier=0, knockbackMultiplier=0,
                    reloadMultiplier=0.5, spreadMultiplier=0)

RAISABLE = ("square", "triangle", "pentagon", "big_pentagon", "hexagon", "small_crasher", "big_crasher")

# A player-built pack's dash: a harmless backward shot with huge recoil (recipes.md section 25)
DASH_FIELDS = dict(damageMultiplier=0, penetrationMultiplier=0, speedMultiplier=0, bulletSizeMultiplier=1.6,
                   reloadMultiplier=4.2, spreadMultiplier=0, lifetime=0.1, recoilMultiplier=16.3,
                   knockbackMultiplier=0, initialVelocityMultiplier=3)


def polar(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def _rod_dict(a, b, width, end_width=None):
    """Geometry of a decorative barrel from point a to point b (compose.rod without the tank)."""
    if end_width is None:
        end_width = width
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-6:
        raise ValueError("rod endpoints coincide")
    theta = math.atan2(dy, dx)
    sx = ax * math.cos(theta) + ay * math.sin(theta)
    off = -ax * math.sin(theta) + ay * math.cos(theta)
    h = width / BARREL_WIDTH
    m = end_width / width if width else 1
    d = {"bulletType": "none", "projectile": -1}
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
    return d



def _merge(stock, over):
    """Stock fields with the caller's overrides on top; a None override removes a field."""
    out = dict(stock)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
    return out


class Mechanics:
    """Mixin for compose.Tank. Needs self.weapon, self.rod, self.shape, self.turret,
    self.projectile, self.set, self.fields, self.projectiles, self.body, self.warn."""

    # --- projectiles, created once per kind and reused -------------------------------------
    def _proj(self, key, **spec):
        cache = self.__dict__.setdefault("_proj_cache", {})
        if key not in cache:
            cache[key] = self.projectile(**spec)
        return cache[key]

    def bullet(self, name="Bullet", **extra):
        """Index of a plain bullet projectile (created on first use)."""
        return self._proj(("bullet", name), name=name, base="bullet", sides=-1, **extra)

    def drone(self, name="Drone", cruise=False, controllable=True, **extra):
        """Index of a drone projectile: Overlord style, or Battleship swarm with cruise=True."""
        dr = {}
        if cruise:
            dr["idle"] = "cruise"
        if not controllable:
            dr["controllable"] = False
        if dr:
            extra["drone"] = dr
        return self._proj(("drone", name, cruise, controllable), name=name, base="drone", sides=-1, **extra)

    def trap(self, name="Trap", **extra):
        return self._proj(("trap", name), name=name, base="trap", sides=-1, **extra)

    # --- the common gun builder --------------------------------------------------------------
    def _gun(self, stock, angle, offset, gap, length, width, muzzle, name, projectile, right_click,
             help_text, over):
        over = dict(over)
        muzzle = over.pop("muzzle", muzzle)        # presets fix the taper; a caller may still override it
        auto = over.pop("auto_fire", False)        # any gun can fire by itself (flags.forceFire, human packs)
        fields = _merge(stock, over)
        if right_click:
            flags = dict(fields.get("flags") or {})
            flags["firesOnSecondary"] = True
            fields["flags"] = flags
            if help_text and "helpText" not in self.fields:
                self.set(helpText=help_text)
        if auto:
            flags = dict(fields.get("flags") or {})
            flags["forceFire"] = True
            fields["flags"] = flags
        return self.weapon(projectile=projectile, angle=angle, offset=offset, length=length, gap=gap,
                           width=width, muzzle=muzzle, name=name, **fields)

    # --- bullets -------------------------------------------------------------------------------
    def cannon(self, angle=0, offset=0, gap=0, length=BARREL_LENGTH, width=BARREL_WIDTH, muzzle=1,
               name="cannon", projectile=None, right_click=False, **over):
        """Plain Tank cannon."""
        p = self.bullet() if projectile is None else projectile
        return self._gun({}, angle, offset, gap, length, width, muzzle, name, p, right_click,
                         "Right click to fire the " + name, over)

    def twin(self, angle=0, offset=0, spacing=26, gap=0, length=BARREL_LENGTH, width=BARREL_WIDTH, name="cannon",
             projectile=None, right_click=False, **over):
        """Twin: two cannons `spacing` either side of `offset`, the right one half a reload behind.
        Returns [left, right]."""
        stock = dict(damageMultiplier=0.65, penetrationMultiplier=0.9, recoilMultiplier=0.75)
        p = self.bullet() if projectile is None else projectile
        left = self._gun(stock, angle, offset - spacing, gap, length, width, 1,
                         f"left {name}", p, right_click, "Right click to fire the twin " + name, over)
        right = self._gun(_merge(stock, dict(delay=0.5)), angle, offset + spacing, gap, length, width, 1,
                          f"right {name}", p, right_click, None, over)
        return [left, right]

    def gunner(self, angle=0, offset=0, gap=0, name="gunner barrel", projectile=None, right_click=False, **over):
        """Gunner: four thin barrels, outer pair shorter, firing in a 0/0.25/0.5/0.75 round."""
        p = self.bullet() if projectile is None else projectile
        stock = dict(damageMultiplier=0.5, penetrationMultiplier=0.5, speedMultiplier=1.1, recoilMultiplier=0.2)
        out = []
        for i, (off, length, delay) in enumerate([(-32, 65, 0.5), (32, 65, 0.75), (-17, 85, 0), (17, 85, 0.25)]):
            f = dict(stock)
            if delay:
                f["delay"] = delay
            out.append(self._gun(f, angle, offset + off, gap, length, BARREL_WIDTH * 0.6, 1, f"{name} {i + 1}", p,
                                 right_click, "Right click to fire the " + name, over))
        return out

    def spread(self, angles=(-45, -22.5, 0, 22.5, 45), lengths=(80, 95, 110, 95, 80), name="spread barrel",
               projectile=None, damage=0.5, recoil=0.5, **over):
        """Penta Shot style fan of cannons (the middle one longest). Spread Shot: eleven barrels."""
        p = self.bullet() if projectile is None else projectile
        stock = dict(damageMultiplier=damage, recoilMultiplier=recoil)
        return [self._gun(stock, a, 0, 0, L, BARREL_WIDTH, 1, f"{name} {i + 1}", p, False, None, over)
                for i, (a, L) in enumerate(zip(angles, lengths))]

    def cannon_ring(self, n=8, start=0, gap=0, length=BARREL_LENGTH, width=BARREL_WIDTH, name="cannon",
                    alternate=True, projectile=None, damage=None, **over):
        """Octo Tank style ring of n cannons; every other one delayed half a reload.
        Damage per barrel scales down with n (Octo: 0.65 at 8) unless `damage` is given."""
        p = self.bullet() if projectile is None else projectile
        dmg = damage if damage is not None else {1: 1, 2: 0.65, 3: 0.75, 4: 0.75}.get(n, 0.65)   # Twin, Tri-Angle-ish, Quad, Octo
        out = []
        for i in range(n):
            f = dict(damageMultiplier=dmg)
            if alternate and i % 2:
                f["delay"] = 0.5
            out.append(self._gun(f, start + 360 * i / n, 0, gap, length, width, 1, f"{name} {i + 1}", p,
                                 False, None, over))
        return out

    def sniper(self, angle=0, offset=0, gap=0, length=110, width=BARREL_WIDTH, name="sniper barrel",
               projectile=None, right_click=False, zoom=0.9, **over):
        """Sniper barrel; also widens the view (zoomMultiplier 0.9) unless zoom=None."""
        stock = dict(speedMultiplier=1.4, reloadMultiplier=1.5, spreadMultiplier=0.3, recoilMultiplier=3)
        if zoom is not None and "zoomMultiplier" not in self.fields:
            self.set(zoomMultiplier=zoom)
        p = self.bullet() if projectile is None else projectile
        return self._gun(stock, angle, offset, gap, length, width, 1, name, p, right_click,
                         "Right click to fire the " + name, over)

    def hitman(self, angle=0, offset=0, name="precision barrel", projectile=None, **over):
        """Hitman: a long dead-straight barrel with a detached wide tip (drawn under it)."""
        p = self.bullet() if projectile is None else projectile
        tip = self.rod_polar(angle, 50, gap=15, offset=offset, width=BARREL_WIDTH * 1.75,
                             end_width=BARREL_WIDTH, name=name + " tip")
        stock = dict(damageMultiplier=1.2, speedMultiplier=1.5, reloadMultiplier=2, spreadMultiplier=0,
                     recoilMultiplier=4)
        gun = self._gun(stock, angle, offset, 0, 135, BARREL_WIDTH, 1, name, p, False, None, over)
        if "zoomMultiplier" not in self.fields:
            self.set(zoomMultiplier=0.65)
        return [tip, gun]

    def machine_gun(self, angle=0, offset=0, gap=0, length=BARREL_LENGTH, width=BARREL_WIDTH,
                    name="machine gun", projectile=None, right_click=False, **over):
        stock = dict(damageMultiplier=0.7, reloadMultiplier=0.5, spreadMultiplier=3)
        p = self.bullet() if projectile is None else projectile
        return self._gun(stock, angle, offset, gap, length, width, 1.75, name, p, right_click,
                         "Right click to fire the " + name, over)

    def destroyer(self, angle=0, offset=0, gap=0, length=BARREL_LENGTH, width=BARREL_WIDTH * 1.7, name="heavy cannon",
                  projectile=None, right_click=False, **over):
        """Destroyer: slow, huge shell, big recoil. Striker = destroyer(right_click=True)."""
        stock = dict(damageMultiplier=3, penetrationMultiplier=2, speedMultiplier=0.7, reloadMultiplier=4,
                     recoilMultiplier=15, knockbackMultiplier=0.1)
        if right_click:
            stock.update(damageMultiplier=2, speedMultiplier=0.63, recoilMultiplier=6)   # Striker's numbers
        p = self.bullet() if projectile is None else projectile
        return self._gun(stock, angle, offset, gap, length, width, 1, name, p, right_click,
                         "Right click to fire the " + name, over)

    def shotgun(self, angle=0, offset=0, gap=0, length=90, width=BARREL_WIDTH, name="shotgun", pellets=4,
                projectile=None, right_click=False, **over):
        """Shotgun: numBullets pellets per shot in a wide cone. Pellet Shot = pellets=10 with
        speedMultiplier=[1.08,1.32], initialVelocityMultiplier=[0.75,2.25]."""
        stock = dict(damageMultiplier=0.5, penetrationMultiplier=0.6, speedMultiplier=1.1, bulletSizeMultiplier=0.7,
                     numBullets=pellets, reloadMultiplier=4, spreadMultiplier=2.75, lifetime=1.8,
                     recoilMultiplier=0.6, knockbackMultiplier=0.5, initialVelocityMultiplier=1.5)
        p = self.bullet() if projectile is None else projectile
        return self._gun(stock, angle, offset, gap, length, width, 1.75, name, p, right_click,
                         "Right click to fire the " + name, over)

    # --- drones --------------------------------------------------------------------------------
    def spawner(self, angle=180, offset=0, gap=0, count=2, controllable=True, name="spawner",
                projectile=None, color=None, **over):
        """Overlord spawner: short flared trapezoid, forceFire, `count` drones per barrel.
        controllable=False makes them AI-only (Hybrid: both projectile and barrel switches)."""
        p = self.drone(controllable=controllable) if projectile is None else projectile
        stock = dict(flags={"forceFire": True}, damageMultiplier=0.7, penetrationMultiplier=2, speedMultiplier=0.8,
                     reloadMultiplier=6, numDrones=count, droneAggressiveCrashRadius=900)
        if not controllable:                       # Hybrid's rear spawner
            stock.update(droneControllable=False, penetrationMultiplier=1.4)
            stock.pop("speedMultiplier")
        if color is not None:
            stock["color"] = color
        return self._gun(stock, angle, offset, gap, 70, BARREL_WIDTH, 1.75, name, p, False, None, over)

    def swarm_spawner(self, angle=90, offset=-20, gap=0, count=24, controllable=True, name="swarm spawner",
                      projectile=None, **over):
        """Battleship spawner: many small short-lived cruising drones from a tapered barrel."""
        p = self.drone("Swarm drone", cruise=True, controllable=controllable) if projectile is None else projectile
        stock = dict(damageMultiplier=0.15, bulletSizeMultiplier=0.4286, lifetime=4.2, knockbackMultiplier=0.3,
                     numDrones=count, droneAggressiveCrashRadius=1600)
        if not controllable:
            stock["droneControllable"] = False
        return self._gun(stock, angle, offset, gap, 75, BARREL_WIDTH * 1.225, 0.5714, name, p, False, None, over)

    def minion_factory(self, angle=0, offset=0, gap=0, count=6, name="factory", **over):
        """Factory: round drones that carry a cannon fired on the owner's click and hold range."""
        bullet = self.bullet()
        minion = self._proj(("minion",), name="Minion", base="drone", sides=0,
                            drone={"keepDistanceMin": 300, "keepDistanceMax": 800},
                            barrels=[dict(distance=85, heightMultiplier=1.2, bulletType="bullet", projectile=bullet,
                                          damageMultiplier=0.4, penetrationMultiplier=0.4, speedMultiplier=0.8,
                                          delay=0.01)])
        stock = dict(flags={"forceFire": True}, damageMultiplier=0.7, penetrationMultiplier=4, speedMultiplier=0.56,
                     bulletSizeMultiplier=0.8485, reloadMultiplier=3, knockbackMultiplier=1.2, numDrones=count,
                     droneAggressiveCrashRadius=1200)
        return self._gun(stock, angle, offset, gap, 70, BARREL_WIDTH, 1.75, name, minion, False, None, over)

    def necromancer(self, raises=("square",), angles=(-90, 90), count=11, sides=4, name="raiser", **over):
        """Necromancer: no projectiles; killed polygons named in `raises` become drones.
        preSpawn=N (Resurrector 2) makes each raiser emit N free drones right after spawn; the
        field does nothing on projectile-drone spawners (2026-09-26)."""
        bad = [r for r in raises if r not in RAISABLE]
        if bad:
            raise ValueError(f"raises {bad}: allowed {RAISABLE}")
        self.body["sides"] = sides
        self.set(raises=list(raises))
        stock = dict(flags={"forceFire": True, "holdsRaised": True}, damageMultiplier=0.42, penetrationMultiplier=2,
                     speedMultiplier=0.76, reloadMultiplier=6, numDrones=count, droneAggressiveCrashRadius=900)
        return [self.weapon(projectile=-1, bullet_type="drone", angle=a, length=70, muzzle=1.75,
                            name=f"{name} {i + 1}", **_merge(stock, over)) for i, a in enumerate(angles)]

    # --- missiles, traps, bursts ---------------------------------------------------------------
    def missile_launcher(self, angle=0, offset=0, gap=0, thrusters="skimmer", name="missile launcher",
                         base=True, right_click=False, **over):
        """Skimmer / Rocketeer / Glider launcher: a wide tube (with a flared base under it) firing a
        missile whose owner-coloured sub-barrels push it. thrusters: skimmer (spins, two sideways
        thrusters), rocketeer (one rear thruster after a pause), glider (two rear-angled thrusters)."""
        bullet = self.bullet()
        thrust = dict(flags={"forceFire": True}, distance=70, heightMultiplier=0.9, bulletType="bullet",
                      projectile=bullet, damageMultiplier=0.6, penetrationMultiplier=0.4, speedMultiplier=0.63,
                      reloadMultiplier=0.35, lifetime=0.9, delay=0.5, color=27)
        spec = dict(name="Missile", base="bullet", sides=-1)
        if thrusters == "skimmer":
            spec.update(spin=0.1, spinFlipsOnSecondary=True,
                        barrels=[dict(thrust), dict(thrust, angle=math.pi)])
        elif thrusters == "rocketeer":
            spec["barrels"] = [dict(thrust, angle=math.pi, recoilMultiplier=3.8, spreadMultiplier=3, delay=7)]
        elif thrusters == "glider":
            spec["barrels"] = [dict(thrust, angle=2.513), dict(thrust, angle=3.770)]
        else:
            raise ValueError("thrusters must be skimmer, rocketeer or glider")
        missile = self._proj(("missile", thrusters), **spec)
        stock = dict(penetrationMultiplier=4, speedMultiplier=0.63, bulletSizeMultiplier=1.2, reloadMultiplier=4,
                     lifetime=3.9, recoilMultiplier=3, knockbackMultiplier=0.1)
        if thrusters == "rocketeer":
            stock.update(speedMultiplier=0.2, initialVelocityMultiplier=1.2)
        parts = []
        if base:
            parts.append(self.rod_polar(angle, 92.63, gap=gap, offset=offset, width=BARREL_WIDTH * 0.8,
                                        end_width=BARREL_WIDTH * 1.4, name=name + " base", order=-1))
        parts.append(self._gun(stock, angle, offset, gap, 80, BARREL_WIDTH * 1.7, 1, name, missile, right_click,
                               "Right click to fire missiles", over))
        return parts

    def trap_launcher(self, angle=0, offset=0, gap=0, name="trap launcher", mega=False, projectile=None, **over):
        """Trapper: short launcher plus a flared tip mounted on it; traps live 24 s."""
        p = self.trap() if projectile is None else projectile
        stock = dict(damageMultiplier=1.2, penetrationMultiplier=1.5, speedMultiplier=2, bulletSizeMultiplier=1.1,
                     reloadMultiplier=1.5, lifetime=24, knockbackMultiplier=0.4)
        w = 1.3 if mega else 1
        if mega:
            stock.update(damageMultiplier=1.8, penetrationMultiplier=2.25, speedMultiplier=2.5, bulletSizeMultiplier=1.54,
                         reloadMultiplier=3.375)
        if "zoomMultiplier" not in self.fields:
            self.set(zoomMultiplier=0.9)
        launcher = self._gun(stock, angle, offset, gap, 60, BARREL_WIDTH * w, 1, name, p, False, None, over)
        idx = [d for k, d in self.parts if k == "barrel"].index(launcher)
        tip = self.rod_polar(0, 26 if mega else 20, gap=30, width=BARREL_WIDTH * w, end_width=BARREL_WIDTH * w * 1.75,
                             name=name + " tip", mount=idx)
        return [launcher, tip]

    def firework_launcher(self, angle=0, offset=0, gap=0, shards=24, name="firework launcher", **over):
        """Firework: a hexagonal shell that bursts into `shards` bullets on right-click."""
        bullet = self.bullet()
        subs = []
        for i in range(shards):
            ring = i % 4
            subs.append(dict(flags={"firesOnDeath": True}, angle=round(2 * math.pi * i / shards, 4), distance=0,
                             heightMultiplier=0.85, bulletType="bullet", projectile=bullet, damageMultiplier=0.6,
                             penetrationMultiplier=0.6 if ring < 2 else 0.4, speedMultiplier=[0.8, 0.6, 0.4, 0.2][ring],
                             reloadMultiplier=20, spreadMultiplier=0.5, lifetime=0.48, recoilMultiplier=0,
                             knockbackMultiplier=0.25, initialVelocityMultiplier=[0.8, 0.6, 0.4, 0.4][ring]))
        subs.append(dict(flags={"forceFire": True}, angle=math.pi, distance=63.9, bulletType="bullet", projectile=bullet,
                         reloadMultiplier=0.5, recoilMultiplier=5.6, lifetime=0.6, delay=0.5, color=27))
        shell = self._proj(("firework",), name="Shell", base="bullet", sides=6, burst={"onSecondary": True}, barrels=subs)
        if "helpText" not in self.fields:
            self.set(helpText="Right click to explode your bullets")
        stock = dict(reloadMultiplier=3, speedMultiplier=0.7, bulletSizeMultiplier=1.2)
        return self._gun(stock, angle, offset, gap, 80, BARREL_WIDTH * 1.5, 1, name, shell, False, None, over)

    # --- turrets -------------------------------------------------------------------------------
    def auto_turret(self, at=(0, 0), angle=180, controllable=False, arc=None, range=None, name="auto turret",
                    projectile=None, above=None, **over):
        """Auto Tank style turret with its own small gun. Returns (turret index, barrel)."""
        p = self.bullet() if projectile is None else projectile
        t = self.turret(at=at, angle=angle, arc=arc, range=range, controllable=controllable, above=above, name=name)
        stock = dict(damageMultiplier=0.3, speedMultiplier=1.2, recoilMultiplier=0.3, delay=0.01, mountTurret=t)
        gun = self._gun(stock, 0, 0, 0, 55, BARREL_WIDTH * 0.7, 1, name + " gun", p, False, None, over)
        return t, gun

    def side_turrets(self, n=3, radius=40, start=0, name="side turret", controllable=True, spin=0.01,
                     projectile=None, **over):
        """Auto 3/5/7: n player-aimable turrets on a ring under the hull rim, hull slowly spinning."""
        p = self.bullet() if projectile is None else projectile
        if spin:
            self.body["spinSpeed"] = spin
        out = []
        for i in range(n):
            th = start + 360 * i / n
            a = math.radians(th)
            t = self.turret(at=(radius * math.cos(a), radius * math.sin(a)), angle=th, arc=81, range=2000,
                            controllable=controllable, above=False, name=f"{name} {i + 1}")
            stock = dict(damageMultiplier=0.5 if n <= 3 else 0.4, speedMultiplier=1.2, recoilMultiplier=0.3,
                         delay=0.5, mountTurret=t)
            out.append(self._gun(stock, 0, 0, 0, 55, BARREL_WIDTH * 0.7, 1, f"{name} {i + 1} gun", p, False,
                                 None, over))
        return out

    def pendulum(self, at, angle=180, arc=20, name="pivot", cover=True, cover_color=None, cover_sides=8,
                 cover_size=29, above=False):
        """A turret that rests at `angle` and only swings for targets inside +-arc: parts mounted on
        it (rod(turret=i), weapon(mountTurret=i)) lag the hull's turns and settle back. The grey
        disc is hidden by a cover polygon drawn afterwards (inradius > 25). Returns the turret index;
        draw the covered parts BEFORE calling with cover=True, or add the cover later with cover()."""
        t = self.turret(at=at, angle=angle, arc=arc, controllable=False, above=above, name=name)
        if cover:
            self._pending_covers = getattr(self, "_pending_covers", []) + [(t, at, cover_color, cover_sides, cover_size)]
        return t

    def cover(self, turret, color=None, sides=8, size=29, name=None):
        """Polygon over a turret's grey disc (radius 25). Octagon 29 has inradius 26.8."""
        tdict = [d for k, d in self.parts if k == "turret"][turret]
        at = (tdict.get("xOffset", 0), tdict.get("yOffset", 0))
        inr = size * math.cos(math.pi / sides)
        if inr <= 25:
            self.warn(f"cover for turret {turret}: inradius {inr:.1f} does not hide the 25-unit disc")
        return self.shape(sides, size, at=at, color=color, above=bool(tdict.get("aboveBody", False)),
                          name=name or (tdict.get("_name", "pivot") + " cover"))

    # --- body-level systems ----------------------------------------------------------------------
    def smasher(self, sides=6, size=57.5, spin=0.1, plates=1, color=None, caps=(10, 0, 0, 0, 0, 10, 10, 10),
                body_damage=None, name="smasher plate"):
        """Smasher family: spinning polygon plate(s) under the hull, bullet stats removed."""
        self.set(statsMaxLevel=list(caps))
        if body_damage is not None:
            self.set(baseBodyDamage=body_damage)
        out = []
        for i in range(plates):
            out.append(self.shape(sides, size, angle=math.degrees(1) + i * 30, spin=spin * (1 if i == 0 else 0.5),
                                  color=color, name=f"{name} {i + 1}" if plates > 1 else name))
        return out

    def stealth(self, reveal=450, zoom=0.75, gain=0.03076923076923077, fire_without_reveal=False, move_loss=None):
        """Stalker invisibility; Landmine = stealth(650, gain=0.004, fire_without_reveal=True, move_loss=0.16)."""
        inv = {"enabled": True, "gain": gain, "revealDistance": reveal, "lossOnHit": 0.05}
        if fire_without_reveal:
            inv["lossOnAttack"] = 0
        if move_loss is not None:
            inv["lossOnMovement"] = move_loss
        self.set(invisibility=inv)
        if zoom is not None and "zoomMultiplier" not in self.fields:
            self.set(zoomMultiplier=zoom)
        return inv

    def scope(self, distance=1500):
        """Predator: right-click slides the camera forward."""
        self.set(scopeDistance=distance)
        if "helpText" not in self.fields:
            self.set(helpText="Right click to extend your view")

    # --- tricks learned from human-built packs (player-built packs) ---------------------
    def cursor_pivot(self, at, angle=0, arc=None, size=10, color=27, above=False, name="pivot"):
        """A turret that ignores enemies (range 0) and follows the CURSOR (controllable) within
        +-arc of its rest `angle`. Confirmed in play 2026-09-26 (serpent, pivot-test): it sits
        at `angle` until the player HOLDS the fire button, then swings to the cursor within the
        arc; release and it returns to rest. What it carries makes no difference. Always give
        it an arc: with none it wanders when released. It lets go of the cursor once the cursor
        leaves the wedge or passes the tip, so a rest angle of 0 (a skeleton's floating hands) reads as
        "always pointing at the cursor" because the hull faces the cursor anyway; a rest angle
        off-axis gives a real two-pose part. Mount a rod, shape or weapon on it (rod(turret=i),
        shape(turret=i), weapon(mountTurret=i)) for a hand, a held sword, a jaw: player-built
        skeleton hands and the serpent's jaws are built this way. The disc is small (10) and in the
        owner colour so it reads as a joint. A RIGHT-click weapon (firesOnSecondary) mounted on
        the pivot never fired in play (SpongeBob, 2026-09-28): put it on the hull, invisible,
        where the held item rests, and draw the item on the pivot. Returns the turret index."""
        return self.turret(at=at, angle=angle, arc=arc, range=0, controllable=True, above=above,
                           size=size, color=color, name=name)

    def contact_damage(self, at, damage=0.75, size=0.5, lifetime=0.2, penetration=20, turret=None, mount=None,
                       name="contact damage", projectile=None, **over):
        # reload 0.5 and lifetime 0.2 since 2026-09-27: each point counts toward the engine's 120/s
        # import limit at the tank's Reload cap (spec 7a): 9.5/s at 0.5 and 13/s at 0.25 with cap 12
        """A point that hurts whatever touches it: an invisible auto-firing barrel whose muzzle is
        AT `at`, dropping a short-lived bullet with no launch speed every quarter reload (the
        creature's teeth). With turret=i the point is in that turret's frame and moves with it.
        High penetration keeps the bullet alive through a hit so it keeps biting."""
        p = self.bullet("Bite") if projectile is None else projectile
        r = math.hypot(at[0], at[1])
        ang = math.degrees(math.atan2(at[1], at[0])) if r > 1e-9 else 0.0
        fields = dict(damageMultiplier=damage, penetrationMultiplier=penetration, bulletSizeMultiplier=size,
                      reloadMultiplier=0.5, spreadMultiplier=0, lifetime=lifetime, recoilMultiplier=0,
                      knockbackMultiplier=0, initialVelocityMultiplier=0)
        fields.update(over)
        if turret is not None:
            fields["mountTurret"] = turret
        if mount is not None:
            fields["mount"] = mount
        return self.weapon(projectile=p, angle=ang, gap=max(r - 5, 0), length=5, invisible=True, auto_fire=True,
                           name=name, **fields)

    def jaws(self, at=(40, 20), rest=45, arc=60, length=140, width=BARREL_WIDTH, teeth=4, tooth=20, fang=27.5,
             color=27, tooth_color=1, bite=0.75, size=10, name="jaw"):
        """A biting mouth (from a player-built snake): two cursor pivots at (x, +-y) resting at
        +-rest with +-arc of travel, each carrying a jaw bar of `length`, `teeth` inward-pointing
        triangles, a hooked fang at the tip, and three contact-damage points along the inside.
        Confirmed in play 2026-09-26: the pivots rest at +-rest (mouth open) until the player
        holds left click; then each aims at the cursor from its own position, clamped to
        rest -+ arc, so both bars swing forward and the mouth closes (parallel, teeth
        interlocked) on whatever is between them; release and it falls open again. arc must
        be >= rest or the jaws can never close (a 30 arc left the serpent stuck 15 degrees open;
        the snake uses 45/60). Returns (right, left) turret indices."""
        out = []
        for s, side in ((1, "right"), (-1, "left")):
            t = self.cursor_pivot(at=(at[0], at[1] * s), angle=rest * s, arc=arc, size=size, color=color,
                                  name=f"{name} pivot {side}")
            step = (length - 0.35 * length) / max(teeth - 1, 1)
            for k in range(teeth):                                  # teeth first, the bar covers their bases
                self.shape(3, tooth, at=(length - step * k, -10 * s), angle=-90 * s, color=tooth_color, turret=t,
                           name=f"{name} {side} tooth {k + 1}")
            self.rod((0, 10 * s), (length, 10 * s), width=width, color=color, turret=t, name=f"{name} {side} bar")
            self.shape(3, fang, at=(length, -3 * s), angle=-150 * s, color=color, turret=t, name=f"{name} {side} fang")
            for k in range(3):
                self.contact_damage(at=(0.3 * length + 0.29 * length * k, -25 * s), damage=bite, turret=t,
                                    name=f"{name} {side} bite {k + 1}")
            out.append(t)
        if "helpText" not in self.fields:
            self.set(helpText="Hold left click to close the jaws on what is between them; release to open")
        return tuple(out)

    def trail(self, angle=180, gap=40, size=2.0, seconds=2.0, taper=(1.0, 0.75), reload=0.25, sides=-1, color=None,
              damage=None, penetration=5, end_color=None, end_force_fire=True, name="trail dropper", stages=None,
              **over):
        """A body that trails behind the tank (the snake in a player-built pack's in-play screenshot): an
        invisible auto-firing rear barrel drops STATIONARY bullets (speed 0, launch speed 0) that
        stay where the tank was for `seconds`, so moving leaves a chain of segments behind. Each
        segment is a bullet: it has health (`penetration`), blocks and damages enemies, and is the
        owner's colour unless `color` is set (sides -1 round, 6 hexagonal ...). taper=(size,
        seconds) spawns a smaller stationary bullet when a segment expires (burst.onExpire +
        firesOnDeath) so the tail thins out; None for none. Confirmed in play 2026-09-26
        (serpent A/B): firesOnDeath alone spawns the end piece on expiry, a hard step from the
        segments to the end pieces; with forceFire as well (the snake's flags, end_force_fire
        default True) end pieces also shimmer out from under the living segments, a soft fade
        the tester preferred. end_color colours the end pieces on their own (Yellow behind a
        Forest body read well). At rest the segments pile up under the tank. Returns the
        dropper barrel. The taper size (and every stage size after the first) is RELATIVE to
        the parent segment, half its radius per unit (2.0 segment: 0.5 / 1.0 / 2.0 end pieces
        were a quarter, a half and 1.2x; 1.5 segment: 1.15 gave a half, croc 2026-09-27), so the
        default (1.0, 0.75) halves the tail and 1.6 is an 0.8 step. Polygon segments (sides >= 3)
        draw about 1.3x bigger than round ones: a 1.0 octagon is about the size of a 32 hull.

        stages=[(size, seconds, sides, color, parts), ...] replaces size/seconds/sides/color/taper
        with a graded taper built from ONE DROPPER PER STAGE (croc, 2026-09-27): every dropper
        fires at the same spot each reload, stage i living the sum of the first i `seconds`, so
        the biggest piece dies first and uncovers the next; the droppers are created last stage
        first so the root piece is spawned last and drawn on top. Sizes are tank-barrel absolute.
        `parts` are projectile parts (d.part(...), hull-scale, above=True) that ride each stage:
        ridges on a tail. Chaining stages through firesOnDeath sub-barrels does NOT work beyond
        the first spawn: the croc's stages 3-5 never appeared and a colour change on stage 2 was
        never seen either (2026-09-27), so a bullet spawned by a projectile's sub-barrel is at
        most a plain copy and fires nothing of its own. Each dropper costs its own fire budget
        (spec §7a: 6.8/s at reload 0.7 with cap 12), so keep stages to three or four.

        Fire budget (spec §7a): the dropper and any forceFire sub-barrel are counted at the tank's
        Reload cap, 13/s each at 0.25 and 9.5 at 0.5 with cap 12 (12/s and 6 at cap 7); the
        two-stage sub-barrel uses the same `reload` since 2026-09-27."""
        if stages:
            last = None
            total = sum(float(st[1]) for st in stages)
            for i, st in reversed(list(enumerate(stages))):
                sz, secs, sd, col, parts = (list(st) + [None] * 5)[:5]
                spec = dict(name=f"Tail stage {i + 1}", base="bullet", sides=-1 if sd is None else sd)
                if col is not None:
                    spec["color"] = self.color(col)
                if parts:
                    spec["parts"] = list(parts)
                proj = self.projectile(**spec)
                life = sum(float(s2[1]) for s2 in stages[:i + 1])
                fields = dict(penetrationMultiplier=penetration, speedMultiplier=0, bulletSizeMultiplier=sz,
                              reloadMultiplier=reload, spreadMultiplier=0, lifetime=life, recoilMultiplier=0,
                              initialVelocityMultiplier=0)
                if damage is not None:
                    fields["damageMultiplier"] = damage
                fields.update(over)
                last = self.weapon(projectile=proj, angle=angle, gap=gap, length=5, invisible=True, auto_fire=True,
                                   name=f"{name} {i + 1}", **fields)
            return last
        if True:
            extra = {"color": color} if color is not None else {}
            spec = dict(name="Trail segment", base="bullet", sides=sides, **extra)
            if taper:
                end_extra = dict(extra)
                if end_color is not None:
                    end_extra["color"] = end_color
                end = self.projectile(name="Trail end", base="bullet", sides=sides, **end_extra)
                spec["burst"] = {"onExpire": True}
                flags = {"forceFire": True, "firesOnDeath": True} if end_force_fire else {"firesOnDeath": True}
                spec["barrels"] = [dict(flags=flags, angle=math.pi, distance=5, startDistance=-20,
                                        bulletType="bullet", projectile=end, penetrationMultiplier=penetration,
                                        speedMultiplier=0, bulletSizeMultiplier=taper[0], reloadMultiplier=reload,
                                        spreadMultiplier=0, lifetime=taper[1], recoilMultiplier=0,
                                        initialVelocityMultiplier=0)]
            seg = self.projectile(**spec)
        fields = dict(penetrationMultiplier=penetration, speedMultiplier=0, bulletSizeMultiplier=size,
                      reloadMultiplier=reload, spreadMultiplier=0, lifetime=seconds, recoilMultiplier=0,
                      initialVelocityMultiplier=0)
        if damage is not None:
            fields["damageMultiplier"] = damage
        fields.update(over)
        return self.weapon(projectile=seg, angle=angle, gap=gap, length=5, invisible=True, auto_fire=True,
                           name=name, **fields)

    def eye(self, at, size=30, pupil=15, color=19, pupil_color=0, arc=90, range=None, look=10, controllable=False,
            name="eye"):
        """An eyeball that looks at the nearest enemy (from a player-built snake): a turret disc of radius
        `size` (White) with the pupil mounted `look` units ahead of its centre and drawn over
        the disc. `arc` limits the glance either side of straight ahead. controllable=True
        makes it follow the cursor instead (range 0). Returns the turret index."""
        t = self.turret(at=at, arc=arc, range=0 if controllable and range is None else range,
                        controllable=True if controllable else None, size=size, color=color, name=name)
        self.shape(0, pupil, at=(look, 0), color=pupil_color, above=True, turret=t, name=f"{name} pupil")
        return t

    def turreted_bullet(self, name="Sentry shell", sides=-1, gun_damage=0.3, gun_reload=3, turret_size=None,
                        gun_color=None, auto_fire=False, **extra):
        """A bullet that carries its own auto-turret and gun (a player-built tank, level
        15 off Tank). Confirmed 2026-09-26: the turret rides the bullet and its gun fires at
        shapes and enemies on its own until the bullet expires, with or without forceFire
        (auto_fire=True adds the flag; it changes nothing). gun_color colours the turret's own
        shots. Returns the projectile index; fire it from any gun (`d.cannon(projectile=idx)`)."""
        b = self.bullet() if gun_color is None else self.bullet("Sentry shot " + str(gun_color), color=gun_color)
        turret = {} if turret_size is None else {"baseSize": turret_size}
        gun = dict(distance=55, heightMultiplier=0.7, mountTurret=0, bulletType="bullet", projectile=b,
                   damageMultiplier=gun_damage, penetrationMultiplier=0.5, speedMultiplier=1.2,
                   reloadMultiplier=gun_reload, recoilMultiplier=0.3)
        if auto_fire:
            gun["flags"] = {"forceFire": True}
        return self.projectile(name=name, base="bullet", sides=sides, turrets=[turret], barrels=[gun], **extra)

    # --- animation ---------------------------------------------------------------------------------
    def speck(self, color=19):
        """Projectile index of the harmless one-frame speck used to animate rods."""
        return self._proj(("speck", color), name="Wingbeat", base="bullet", sides=-1, color=color)

    def animate(self, parts, phase=0.0, color=19):
        """Turn decorative rod(s) into speck-firing barrels so they pump like pistons while the
        player fires (Confirmed). phase 0.5 puts this group half a beat out of step.
        Two conditions (pump tests 2026-09-26): the rod should be at least ~22 wide (12 is almost
        imperceptible), and its muzzle end must not be painted over by a joint or other part
        (save() prints PUMP HIDDEN); use limb(exposed=i) for an animated limb segment."""
        if isinstance(parts, dict):
            parts = [parts]
        p = self.speck(color)
        for r in parts:
            if r.get("bulletType") != "none":
                raise ValueError("animate: only decorative rods can be animated")
            w = BARREL_WIDTH * r.get("heightMultiplier", 1)
            if w < 20:
                self.warn(f"animate: {r.get('_name')} is {w:.0f} wide; pumps under ~20 wide are almost "
                          "invisible in game (travel scales with width)")
            r.update(bulletType="bullet", projectile=p, **SPECK_FIELDS)
            if phase:
                r["delay"] = phase
        return parts

    # --- Character-pack techniques (a player-built pack, read 2026-09-28) ---------------------------
    # Each preset copies the distinguishing numbers of a pattern that pack uses on many tanks
    # (recipes.md sections 25-32, figurative.md section 5). Tagged High from the data; none has
    # been isolated in a test build yet, so the docstrings say what is inferred.

    def dash(self, angle=180, power=16.3, reload=4.2, right_click=True, name="dash", **over):
        """"Right click to dash" (45 tanks of a player-built pack, from the level-1 class to the biggest spider):
        an invisible barrel pointing BACKWARD whose harmless shot carries huge recoil, so every
        shot throws the tank forward. Copied numbers: damage 0, penetration 0, speed 0, size 1.6,
        lifetime 0.1, recoil 16.3 (12-20 seen), initial velocity 3, reload 4.2 (one dash every
        few seconds; a big spider stacks three at recoil 20, reload 12, for a leap). The shot
        is a small spinning star trap that vanishes in a tenth of a second. Returns the barrel."""
        p = self._proj(("dash",), name="Dash", base="trap", sides=0, star=True, spin=0.01)
        fields = _merge(dict(DASH_FIELDS, recoilMultiplier=power, reloadMultiplier=reload), over)
        flags = {"firesOnSecondary": True} if right_click else {}
        b = self.weapon(projectile=p, angle=angle, gap=-43, length=5, invisible=True, name=name,
                        flags=flags, **fields)
        if right_click and "helpText" not in self.fields:
            self.set(helpText="Right click to dash")
        return b

    def punch(self, reach=80, damage=(5.7, 1.6), penetration=(7.5, 2.4), size=3, range=180, arc=20,
              reload=0.3, lifetime=0.1, offsets=(32, -62), at=(0, 0), knockback=0.6, projectile=None,
              name="punch"):
        """"Get close to punch" (51 tanks of a player-built pack): an enemy-tracking auto-turret hidden under
        the hull (aboveBody false, so no disc shows) carrying two invisible fists: stationary
        one-frame shots of size 3 that appear `reach` ahead of the turret, one each side, the
        second a half reload later so they alternate. Turret guns fire on their own at whatever
        is inside `range` and `arc` (the Auto Tank rule): melee with no visible gun. Confirmed in
        play 2026-09-28 (Dash Punch): the fists fire only at shapes in the front cone (backing
        into a shape never triggers them) and keep firing, hit or miss, while anything is in
        range. They reach only about reach + fist radius (~150), so a range beyond that throws
        stars into the air short of the target: a player-built pack's 300 fired at 3-4 body lengths. The
        default here is 180 so a punch fires only when it can land; widen `arc` (or add a second
        punch at angle 180) for a brawler that hits all round. The pack's other numbers: arc
        20, reload 0.3, offsets +32 / -62, a heavy and a light fist (5.7 / 1.6 damage). Each
        fist costs the fire budget at reload 0.3 (spec 7a). Returns the turret index."""
        p = self._proj(("punch",), name="Punch", base="bullet", sides=7, star=True, spin=0.02,
                       color=8) if projectile is None else projectile
        t = self.turret(at=at, range=range, arc=arc, above=False, name=name + " pivot")
        for k, off in enumerate(offsets):
            self.weapon(projectile=p, angle=1, offset=off, gap=reach, length=5, width=47, muzzle=0.089,
                        invisible=True, name=f"{name} fist {k + 1}", mountTurret=t,
                        damageMultiplier=damage[k % len(damage)], penetrationMultiplier=penetration[k % len(penetration)],
                        speedMultiplier=0, bulletSizeMultiplier=size, reloadMultiplier=reload, spreadMultiplier=0,
                        lifetime=lifetime, recoilMultiplier=0, knockbackMultiplier=knockback,
                        **({"delay": 0.5} if k == 0 else {}))
        if "helpText" not in self.fields:
            self.set(helpText="Get close to punch")
        return t

    def living_limb(self, at, angle, arc=15, range=250, size=19, color=None, above=False, name="limb pivot"):
        """The pivot that keeps a limb alive (72 tanks of a player-built pack: spider legs, arms and hands, a
        plume, a cape): a `controllable` turret with a rest `angle`, a narrow `arc` (15 for
        legs and arms, 20-40 for hands) and an enemy-tracking `range` (250 arms and legs, 100 a
        plume or cape, left at the default on a big spider's eight legs). Unlike
        cursor_pivot (range 0) it also turns toward enemies inside `range` while the player is
        idle, so limbs twitch toward passers-by and swing with the cursor while firing: the
        difference between a sticker and a creature. Confirmed 2026-09-28 (Limb Lab): it turned
        toward a shape within 250 while idle (a range-0 pivot did not) and followed the cursor
        while firing. It follows the cursor only while the cursor is inside its wedge (angle +-
        arc), so a limb resting backward never follows a forward cursor. Mount rods and shapes
        on it (rod(turret=i), shape(turret=i)). Click pistons on a living limb are untested (a
        2026-09-30 failure had covered tips, PUMP HIDDEN); click guns are confirmed on a
        cursor_pivot. Returns the turret index."""
        return self.turret(at=at, angle=angle, arc=arc, range=range, controllable=True, above=above,
                           size=size, color=color, name=name)

    def leg(self, at, angle, side=1, segments=((134, 0), (179, 45), (173, 66)), widths=(39, 22, 8),
            tips=(0.4, 0.37, 0.65), joint=17, foot=15, arc=15, range=250, color=None, joint_color=None,
            name="leg"):
        """A jointed leg on a living_limb pivot (a big spider: eight of them; 24 rods and 16
        joint stars, plus the pivots, at the 32/32 caps). Each segment is a rod in the pivot's
        frame starting where the last ended and bending by its own angle (degrees; `side` -1
        mirrors the bends), tapering to `tip` x its width, with a four-point star at every bend
        and a smaller one at the foot. The spider's segments: 134 straight, 179 bent 45, 173 bent
        66, widths 39 / 22 / 8. range 250 (a confirmed living limb) makes each leg turn toward
        shapes passing its side; range=None (the spider's) also tracks, from further away (Leg
        Range Lab, 2026-09-28), so pass it for a leg that reacts early and twitches more. A leg
        follows the cursor only when the cursor is inside its wedge, so rear legs (Limb Lab's,
        resting at 165 with arc 15) never follow a forward cursor. Returns the turret index."""
        t = self.living_limb(at=at, angle=angle, arc=arc, range=range, size=joint, color=color,
                             name=f"{name} pivot")
        jc = color if joint_color is None else joint_color
        p, heading = (0.0, 0.0), 0.0
        for k, (length, bend) in enumerate(segments):
            heading += bend * side
            q = (p[0] + length * math.cos(math.radians(heading)), p[1] + length * math.sin(math.radians(heading)))
            w = widths[k % len(widths)]
            self.rod(p, q, width=w, end_width=w * tips[k % len(tips)], color=color, turret=t,
                     name=f"{name} segment {k + 1}")
            last = k == len(segments) - 1
            self.shape(4, foot if last else joint, at=q, angle=heading + 45, star=True, color=jc, turret=t,
                       name=f"{name} {'foot' if last else 'joint ' + str(k + 1)}")
            p = q
        return t

    def blade(self, length=330, gap=122, hits=12, damage=18, penetration=7, reload=14, right_click=True,
              turret=None, offset=-53, angle=2, size=3, projectile=None, name="blade"):
        """A sword sweep (a king's "Right click to slash"): `hits` stationary one-frame hit
        points spaced from `gap` to gap + length along one line, all firing together, so a click
        cuts everything the blade overlaps at once. The king: twelve traps at reload 14, damage
        18, penetration 7, size 3 near the hilt and 1.1 at the tip, lifetime 0.12, spread 0.3.
        Put it on a living_limb holding the sword rod (turret=i) so the cut swings. Returns the
        list of barrel dicts."""
        p = self._proj(("slash",), name="slash", base="trap", sides=4, star=True, spin=0.02,
                       color=8) if projectile is None else projectile
        out = []
        flags = {"firesOnSecondary": True} if right_click else {}
        for k in range(hits):
            g = gap + length * k / max(hits - 1, 1)
            fields = dict(damageMultiplier=damage, penetrationMultiplier=penetration, speedMultiplier=0,
                          bulletSizeMultiplier=size if k < hits * 0.6 else size * 0.37, reloadMultiplier=reload,
                          spreadMultiplier=0.3, lifetime=0.12, recoilMultiplier=0, initialVelocityMultiplier=0)
            if turret is not None:
                fields["mountTurret"] = turret
            out.append(self.weapon(projectile=p, angle=angle, offset=offset, gap=g, length=1, width=26,
                                   muzzle=0.32, invisible=True, flags=flags, name=f"{name} hit {k + 1}", **fields))
        if right_click and "helpText" not in self.fields:
            self.set(helpText="Right click to slash")
        return out

    # --- drawing on projectiles ------------------------------------------------------------------
    def proj_rod(self, a, b, width=8, end_width=None, color=None, above=True, name=None, **extra):
        """A drawing-only barrel dict for a PROJECTILE (`projectile(barrels=[...])`), the way
        part() makes a shape dict: a rod from a to b in the projectile's frame (x = heading,
        radius ~50 like a hull), over the disc unless above=False. A player-built pack draws 57 projectiles
        this way: a web of spokes and rings, a trident's shaft, a chick's beak, a golem's arms.
        Not registered on the tank."""
        d = _rod_dict(a, b, width, end_width)
        if above:
            d["flags"] = {"aboveBody": True}
        if color is not None:
            d["color"] = self.color(color)
        if name:
            d["editor"] = {"name": name}
        d.update(extra)
        return d

    def web(self, spokes=8, radius=200, rings=(86, 149), spoke_width=8, ring_width=5, hooks=2, color=None,
            name="Web"):
        """A spider's web ("Left click to shoot webs"): a trap whose picture is 24
        drawing-only sub-barrels, all above its disc: `spokes` rods from the centre to `radius`
        (0.2 wide, tapering to half) and one octagonal ring of chords per entry in `rings`
        (apothem; 0.1-0.15 wide); the disc itself is a four-point star. Small collidable
        ten-point stars (`hooks`, the spider's 2) are spread evenly around the inner ring (where the spider puts them).
        Confirmed in play (Web Lab, 2026-09-28): the rods are picture only; shapes are hurt by
        the centre disc and the hooks alone, not pushed. hooks=3 is the most that catch: the
        editor keeps only the first three collidable parts of a projectile collidable (spec 5).
        Fire it from an invisible trap
        barrel: the spider's is gap 100, penetration 20, speed 3, size 1.2, reload 0.9, spread
        1.7, lifetime 5.2, on a tank with Reload cap 0 (spec 7a: each web counts as 1 + its
        pieces, 24 rods + the hooks, and at cap 7 a reload-0.9 web was refused at 437/250 in the
        air). Returns the projectile index."""
        if hooks > 3:
            raise ValueError("web(hooks=...): at most 3; the editor makes every collidable part after the third "
                             "drawing-only (spec 5)")
        rods, n = [], spokes
        for k in range(n):
            a = 360.0 * k / n
            rods.append(self.proj_rod((0, 0), polar(radius, a), width=spoke_width, end_width=spoke_width / 2,
                                      color=color, name=f"{name} spoke {k + 1}"))
        for r_i, apothem in enumerate(rings):
            R = apothem / math.cos(math.pi / n)
            for k in range(n):
                a0, a1 = 360.0 * k / n + 180.0 / n, 360.0 * (k + 1) / n + 180.0 / n
                rods.append(self.proj_rod(polar(R, a0), polar(R, a1), width=ring_width, color=color,
                                          name=f"{name} ring {r_i + 1} side {k + 1}"))
        ring = rings[0] if rings else radius * 0.43
        parts = [self.part(10, 12, at=polar(ring, 90 + 360.0 * k / max(hooks, 1)), star=True, collidable=True,
                           color=color, name=f"{name} hook {k + 1}") for k in range(hooks)]
        extra = {} if color is None else {"color": self.color(color)}
        return self.projectile(name=name, base="trap", sides=4, star=True, parts=parts, barrels=rods, **extra)

    def egg(self, name="Egg", yolk_damage=3.5, yolk_knockback=7.5, white_size=3, shells=3, color=None,
            yolk_color=None, white_color=None, **extra):
        """A trap that hatches (a hen's "Right click to lay eggs"): burst on destroyed and
        on expire, with two firesOnDeath sub-barrels: a yolk bullet (damage 3.5, penetration 4.6,
        size 1.2, lifetime 0.2, knockback 7.5: a shove) and an egg-white trap (size 3, lifetime
        0.1: a splash). Drawn as `shells` offset circles above the disc, a shaded shell. Lay it
        from a rear invisible barrel with lifetime=[12, 22.5] so eggs hatch at different
        times, and projectile=[egg, golden_egg] for a rare variant. Confirmed in play (Egg Lab,
        2026-09-28): one in two golden, hatching at different times, yolk and white hurting and
        shoving shapes. Returns the projectile index."""
        yolk = self.projectile(name=name + " yolk", base="bullet", sides=-1,
                               **({} if yolk_color is None else {"color": self.color(yolk_color)}))
        white = self.projectile(name=name + " white", base="trap", sides=8, spin=0.5,
                                **({} if white_color is None else {"color": self.color(white_color)}))
        parts = [self.part(0, 50, at=(0, -4 - 3.5 * k), above=True, color=color, name=f"{name} shell {k + 1}")
                 for k in range(shells)]
        subs = [dict(distance=0, heightMultiplier=2.5, bulletType="bullet", projectile=yolk, invisible=True,
                     damageMultiplier=yolk_damage, penetrationMultiplier=4.6, bulletSizeMultiplier=1.2,
                     reloadMultiplier=0.1, lifetime=0.2, knockbackMultiplier=yolk_knockback,
                     flags={"firesOnDeath": True}, editor={"name": name + " yolk burst"}),
                dict(distance=0, heightMultiplier=2.5, bulletType="trap", projectile=white, invisible=True,
                     damageMultiplier=1.4, penetrationMultiplier=1.2, bulletSizeMultiplier=white_size,
                     reloadMultiplier=0.1, lifetime=0.1, knockbackMultiplier=2.5,
                     flags={"firesOnDeath": True}, editor={"name": name + " white burst"})]
        e = {} if color is None else {"color": self.color(color)}
        e.update(extra)
        return self.projectile(name=name, base="trap", sides=0, star=True,
                               burst={"onDestroyed": True, "onExpire": True}, parts=parts, barrels=subs, **e)

    # --- projectiles that are characters, walkers and buildings -----------------------------------
    def proj_dash(self, power=16.3, reload=4.2, turret=None, auto=True):
        """The dash barrel as a dict for a projectile's `barrels`: a summoned warrior and a
        king's knight lunge on their own (forceFire + firesOnSecondary; recoil 12-16).
        With turret=i (an enemy-tracking turret) it points away from the target instead, so
        every shot pushes the projectile toward it: an engineer's walking golem uses
        recoil 4.6 at reload 0.3 with a 0.2-size shot for a steady crawl."""
        p = self._proj(("dash",), name="Dash", base="trap", sides=0, star=True, spin=0.01)
        d = dict(angle=math.pi, distance=5, startDistance=-43, bulletType="trap", projectile=p, invisible=True,
                 editor={"name": "dash"}, **DASH_FIELDS)
        d.update(recoilMultiplier=power, reloadMultiplier=reload)
        if turret is not None:
            d.update(mountTurret=turret, bulletSizeMultiplier=0.2, damageMultiplier=0.1)
        d["flags"] = {"forceFire": True, "firesOnSecondary": True} if auto else {"firesOnSecondary": True}
        return d

    def proj_punch(self, turret, reach=80, damage=(7.7, 3.6), penetration=(10.4, 5.3), reload=0.5, offsets=(32, -62)):
        """Two invisible fists as barrel dicts on a projectile's turret `turret` (an index into
        its own `turrets`), a summoned warrior's and a chick's punch."""
        p = self._proj(("punch",), name="Punch", base="bullet", sides=7, star=True, spin=0.02,
                       color=8)
        out = []
        for k, off in enumerate(offsets):
            d = dict(angle=0.017, offset=off, distance=5, startDistance=reach, heightMultiplier=1.12,
                     muzzleScale=0.089, mountTurret=turret, bulletType="bullet", projectile=p, invisible=True,
                     damageMultiplier=damage[k % len(damage)], penetrationMultiplier=penetration[k % len(penetration)],
                     speedMultiplier=0, bulletSizeMultiplier=3, reloadMultiplier=reload, spreadMultiplier=0,
                     lifetime=0.1, recoilMultiplier=0, knockbackMultiplier=0.6, editor={"name": f"fist {k + 1}"})
            if k == 0:
                d["delay"] = 0.5
            out.append(d)
        return out

    def proj_turret(self, at=(0, 0), angle=0, arc=None, range=None, controllable=None, above=None, size=None,
                    color=None, name=None):
        """A turret dict for a projectile's `turrets` (same fields as turret(); frame = the
        projectile's). Living limbs on a drone: controllable with a rest angle, arc 20 and
        range 750 (a summoned warrior's arms); a melee pivot: range 650, arc 20, above False."""
        t = {}
        if abs(at[0]) > 1e-9:
            t["xOffset"] = at[0]
        if abs(at[1]) > 1e-9:
            t["yOffset"] = at[1]
        if size is not None:
            t["baseSize"] = size
        if angle:
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
        if name:
            t["editor"] = {"name": name}
        return t

    def figure_drone(self, name, parts=(), rods=(), turrets=(), barrels=(), keep=(100, 200), repel=False,
                     controllable=False, dash=True, punch=True, punch_range=650, sides=0, color=None, **extra):
        """A drone that is a whole character (a warrior's summoned twin, a hen's
        chicks, a king's knight, a necromancer's minions: 22 tanks of a player-built pack). Give it
        the same parts and rods you would give a hull (part(), proj_rod(); a warrior's drone
        carries a copy of his own 24 shapes and 15 rods) and its own turrets (proj_turret():
        living-limb arms, a hidden melee pivot). dash=True adds a self-firing lunge, punch=True
        a melee pivot with two fists (added last, so index = len(turrets)). AI-only
        (controllable False), holds 100-200 from its target, cannot be repelled. Spawn it with
        summon(). Confirmed in play (Summon Lab, 2026-09-28): the drones hunt shapes, lunge with
        their own recoil barrel and punch; their controllable limb turrets ignore the owner's
        cursor and track shapes instead (living limbs of their own). Rest angles are the
        figure's pose: a warrior's (-51 and -7) hold one arm tucked and one forward; mirror
        them for a symmetric figure. A slow companion (a pet, a snail) needs both knobs: the
        lunge sets how darty it feels as much as summon(speed=...) does; dash=False with
        barrels=[proj_dash(power=7, reload=6)] and summon(speed=0.75) read as slow and steady in
        play (SpongeBob's Gary, 2026-09-28; speed 1.1 with the stock lunge was still too quick).
        Returns the projectile index."""
        turrets, barrels = list(turrets), list(barrels)
        if punch:
            turrets.append(self.proj_turret(range=punch_range, arc=20, above=False, name="punch pivot"))
            barrels += self.proj_punch(len(turrets) - 1)
        if dash:
            barrels.append(self.proj_dash())
        dr = {"controllable": bool(controllable), "repel": bool(repel)}
        if keep:
            dr.update(keepDistanceMin=keep[0], keepDistanceMax=keep[1])
        e = {} if color is None else {"color": self.color(color)}
        e.update(extra)
        return self.projectile(name=name, base="drone", sides=sides, drone=dr, parts=list(parts),
                               barrels=list(rods) + barrels, turrets=turrets, **e)

    def summon(self, projectile, count=2, angle=180, reach=1300, reload=5, damage=7, penetration=9, speed=1.6,
               size=1, knockback=0.6, right_click=False, name="summoner", **over):
        """The spawner for a figure_drone: an invisible drone barrel with forceFire. Confirmed
        in play (Summon Lab, 2026-09-28): the drones come out on their own from the moment the
        tank spawns and are topped up to `count`, whatever the flags; a warrior's
        firesOnSecondary (right_click=True here) did not make it a right-click summon. So a
        summon is a companion that is always out, not an ability. The drone's damage and health
        come from this barrel (7 / 9 for the warrior). Returns the barrel."""
        flags = {"forceFire": True, "aboveBody": True}
        if right_click:
            flags["firesOnSecondary"] = True
        return self.weapon(projectile=projectile, angle=angle, gap=44, length=8, width=71, invisible=True, name=name,
                           flags=flags, numDrones=count, droneAggressiveCrashRadius=reach, reloadMultiplier=reload,
                           damageMultiplier=damage, penetrationMultiplier=penetration, speedMultiplier=speed,
                           bulletSizeMultiplier=size, knockbackMultiplier=knockback, **over)

    def walker(self, name="Golem", parts=(), rods=(), turrets=(), barrels=(), range=1950, arc=75, thrust=4.6,
               reload=0.3, punch=True, sides=-1, color=None, base="trap", wander=True, **extra):
        """A projectile that walks (an engineer's golem, "Right click to build golems"):
        a trap (no cruise speed of its own) carrying an enemy-tracking turret (range 1950, arc
        75) whose only gun points BACKWARD with recoil 4.6, a harmless 0.2-size shot every 0.3
        reload, so each shot nudges the trap. Confirmed in play (Builder Lab, 2026-09-28) with
        wander=True, the pack's way: the walk barrel fires on its own, so the golem marches
        forward from where it was placed, meandering and veering toward shapes inside its cone,
        punching what it meets, until its lifetime ends or it walks off the map.
        wander=False drops the auto-fire and opens the cone to a full circle, so the golem stands
        still until a shape comes within `range`, walks to it and kills it, moves on to the next
        shape in range, and sits again when none is left (Confirmed, Golem Wait Lab 2026-09-28):
        a guard, not a marcher. punch=True adds fists on a second pivot; parts and rods
        draw the body. Place it with place(). Returns the projectile index."""
        turrets, barrels = list(turrets), list(barrels)
        turrets.append(self.proj_turret(range=range, arc=arc if wander else None, above=False, name="walk pivot"))
        step = self.proj_dash(power=thrust, reload=reload, turret=len(turrets) - 1, auto=wander)
        if not wander:
            step.pop("flags", None)          # a turret gun fires at targets on its own (spec 5b)
        barrels.append(step)
        if punch:
            turrets.append(self.proj_turret(range=250, arc=20, above=False, name="punch pivot"))
            barrels += self.proj_punch(len(turrets) - 1)
        e = {} if color is None else {"color": self.color(color)}
        e.update(extra)
        return self.projectile(name=name, base=base, sides=sides, parts=list(parts), barrels=list(rods) + barrels,
                               turrets=turrets, **e)

    def sentry(self, name="Ballista", parts=(), rods=(), aim_parts=(), aim_rods=(), gun_damage=8,
               gun_penetration=6, gun_reload=5, gun_range=2000, arc=None, spread=0.3, bolt=None, bolt_size=0.6,
               bolt_sides=3, bolt_color=None, sides=6, color=None, **extra):
        """A placed building (an engineer's ballista and turret, "Left click to build
        carts"): a bullet that never moves (placed with place(): speed 0) carrying an auto-turret
        with an invisible gun firing bolts (damage 8, penetration 6, speed 3, reload 5, lifetime
        4). `parts` and `rods` draw the fixed base; `aim_parts` and `aim_rods` ride the turret, so
        the weapon picture (a crossbow, an arrow, a cannon) turns to face what it shoots.
        Confirmed in play (Builder Lab, 2026-09-28): the building stays put for its lifetime and
        its gun shoots nearby shapes on its own; bolts keep their own `sides` and colour; a
        picture drawn in `parts`/`rods` does not turn, so the shots seemed to leave from any
        side; and a bolt at size 1.5 off a 2.6 building came out almost the building's size, so
        the default is 0.6 (a sub-barrel's shot scales with its parent, spec 7). A player-built pack's arc
        of 100 is widened to a full circle here. Returns the projectile index."""
        if bolt is None:
            bc = self.color(bolt_color) if bolt_color is not None else (self.color(color) if color is not None else None)
            b = self.projectile(name=name + " bolt", base="bullet", sides=bolt_sides, **({} if bc is None else {"color": bc}))
        else:
            b = bolt
        turrets = [self.proj_turret(size=11, range=gun_range, arc=arc, name=name + " pivot")]
        aimed_parts = [dict(p, mountTurret=0) for p in aim_parts]
        aimed_rods = [dict(r, mountTurret=0) for r in aim_rods]
        gun = dict(distance=5, startDistance=10, mountTurret=0, bulletType="bullet", projectile=b, invisible=True,
                   damageMultiplier=gun_damage, penetrationMultiplier=gun_penetration, speedMultiplier=3,
                   bulletSizeMultiplier=bolt_size, reloadMultiplier=gun_reload, spreadMultiplier=spread, lifetime=4,
                   recoilMultiplier=0, knockbackMultiplier=2, initialVelocityMultiplier=3, delay=0.2,
                   editor={"name": name + " gun"})
        e = {} if color is None else {"color": self.color(color)}
        e.update(extra)
        return self.projectile(name=name, base="bullet", sides=sides, parts=list(parts) + aimed_parts,
                               barrels=list(rods) + aimed_rods + [gun], turrets=turrets, **e)

    def place(self, projectile, lifetime=27, reload=14, angle=0, offset=-47, gap=101, health=(10, 12), size=2.6,
              right_click=False, name="builder", **over):
        """The placing barrel for a sentry or walker: invisible, a stationary shot (speed 0,
        initial velocity 0.5 so it slides clear of the hull) that lives `lifetime` seconds
        (27), reload 14. Its damage / penetration (10 / 12) are the building's contact damage
        and health. projectile=[a, b] builds one of several at random per click (an
        Engineer: ballista or turret). Budget (spec 7a): the building's guns count once per
        live copy, about six alive at reload 14 / lifetime 27, so give the tank a Reload cap of 0
        (at cap 7 the lab's Builder Lab was refused at 132/s). Returns the barrel."""
        flags = {"firesOnSecondary": True} if right_click else {}
        return self.weapon(projectile=projectile, angle=angle, offset=offset, gap=gap, length=5, invisible=True,
                           name=name, flags=flags, damageMultiplier=health[0], penetrationMultiplier=health[1],
                           speedMultiplier=0, bulletSizeMultiplier=size, reloadMultiplier=reload, spreadMultiplier=0,
                           lifetime=lifetime, recoilMultiplier=0, initialVelocityMultiplier=0.5, **over)

    def folder(self):
        """Turn this tank into a class-picker node (a player-built pack's folders for humans, monsters, animals, spiders:
        18 of its tanks): a hull of radius 1 with an imperceptible spin, health 1, body
        damage 1, speed 0.1, zoom 5 and every stat cap 0, so it is unplayable and the tree shows
        it only as the picture its parts draw (a pitchfork for a farmer line, a paw for the
        animals). Give it its children with set(advancesInto=[ids]) and level 1. Confirmed in play
        (Folder, 2026-09-28): an icon with no visible hull that barely moves, has no stats to
        spend and offers its children at once."""
        self.hull(0, 1, spin=1e-5)
        self.set(speedMultiplier=0.1, zoomMultiplier=5, knockbackMultiplier=0, baseHealth=1, baseBodyDamage=1,
                 statsMaxLevel=[0] * 8)
