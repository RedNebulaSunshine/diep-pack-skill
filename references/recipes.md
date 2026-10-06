# Recipes: how every stock mechanic is expressed in a `.diep-pack`

Each section quotes the distinguishing fields of a real stock tank, copied verbatim from
the stock tanks copied out of the game (float noise trimmed). Fields not shown are at default and omitted.
These excerpts are a subset: the source of truth is the editor's own roster export,
`references/stock-tanks.diep-pack`, served one tank at a time by `ref.py stock <name>`. A design
that must keep a stock tank's mechanics exactly (a reskin, "a Penta Shot with ears", an "X
variant") clones that tank from `ref.py stock` instead of assembling it from the sections here.
Every tank also carries the always-written envelope:

```json
{"id":100001,"name":"…","minLevel":45,"body":{"sides":0},
 "invisibility":{"gain":0.03076923076923077,"lossOnHit":0.05},
 "statsMaxLevel":[7,7,7,7,7,7,7,7],
 "projectiles":[{"name":"Bullet","base":"bullet","sides":-1}],
 "barrels":[{"bulletType":"bullet","projectile":0}]}
```

**Import budget (spec §7a, the editor's own check):** the lobby refuses a tank over **120
entities per second**, **250 alive**, **2000 room** (bullet areas, size squared), **64 per volley**,
**96 drones** or **96 pieces**, counted over every firing barrel and live sub-barrel with every
trigger held and the Reload stat at its cap: a barrel fires every ⌈15 × 0.914^cap ×
`reloadMultiplier`⌉ ticks, and each shot counts 1 + what its projectile carries. With caps of 12
a plain barrel costs 4.2/s, reload 0.5 costs 8.3 and 0.25 costs 12.5; with caps of 7 about three
quarters of that. A Twin costs 8.3, an Octo 33 at cap 12. The limits are exact (the validator
reproduces every refusal seen), so design right up to them; `save()` prints all six figures.
Lowering the Reload cap is the cheap way to buy budget.

**Balance envelope (the 55 stock tanks, read 2026-09-30).** Every stock tank has `baseHealth` 50
and knockback taken 1; body damage 5 (Spike 7); speed 1 (the near-gunless Smasher line 1.1); Stat caps
7 (the Smasher line `[10,0,0,0,0,10,10,10]`, Auto Smasher all 10). Specialisation comes from the
guns and the caps, not from base stats: a "tank" class gets caps of 10 on body damage, max health
and regen, not extra `baseHealth`. Per barrel: damage 0.1-3, reload 0.5 or slower, recoil at most
17, drones up to 24. Gun output (damage x shots per reload, Tank = 1.0) climbs about 1.3-1.4 at
15, 2.0 at 30, 2.2-2.5 at 45. Stay inside these unless the user asks otherwise, and say so when a
request steps outside them (a 1.3 speed, a 20 recoil).

Geometry defaults: hull radius 50, barrel length 95 (`distance`), width 42
(`heightMultiplier` scales it). Angles are radians clockwise from the aim direction:
front 0, right π/2, back π, left −π/2. Multipliers default to 1.

**Every recipe below is one call in `scripts/mechanics.py`** (mixed into `compose.Tank`),
with these numbers built in. In a design script prefer the preset and override only what
the request changes; hand-written JSON copies the numbers from the sections.

| Recipe | Preset | Notes |
|---|---|---|
| 1 cannon | `d.cannon(angle, offset, gap, length, width)` | |
| 2 Twin / Octo / Quad | `d.twin(spacing=26)`, `d.cannon_ring(n)` | ring damage 0.75 at 4, 0.65 at 8 |
| 3 Sniper / Machine Gun / Destroyer | `d.sniper()` (sets zoom 0.9), `d.machine_gun()`, `d.destroyer()` | `destroyer(right_click=True)` = Striker |
| 4 Hitman | `d.hitman()` | tip rod + barrel, zoom 0.65 |
| Gunner, Penta Shot | `d.gunner()`, `d.spread(angles, lengths)` | |
| 5 Overlord spawner | `d.spawner(angle, count=2, controllable=True)` | `controllable=False` = Hybrid's rear spawner |
| 6 Battleship swarm | `d.swarm_spawner(angle, count=24)` | pass `projectile=d.drone("…", cruise=True, color=…)` for a custom look |
| 7 Necromancer | `d.necromancer(raises=("square",), angles=(-90, 90))` | sets body sides and `raises` |
| 8 Skimmer / Rocketeer / Glider | `d.missile_launcher(thrusters="skimmer"\|"rocketeer"\|"glider")` | base rod under the tube unless `base=False` |
| 9 Factory | `d.minion_factory(count=6)` | |
| 10 Trapper / Mega Trapper | `d.trap_launcher(mega=False)` | launcher + mounted tip, zoom 0.9 |
| 11 Smasher family | `d.smasher(sides, size, spin, plates, body_damage)` | sets the stat caps |
| 12 Stalker / Landmine | `d.stealth(reveal, zoom, gain, fire_without_reveal, move_loss)` | |
| 13 Auto Tank / Auto 3 | `d.auto_turret(at, angle)`, `d.side_turrets(n)` | |
| 14 Shotgun / Pellet Shot | `d.shotgun(pellets=4)` | |
| 15 Firework | `d.firework_launcher(shards=24)` | writes the help text |
| 16 right click / Predator scope | `right_click=True` on any preset, `d.scope()` | |
| §5 of figurative.md | `d.animate(rods, phase)`, `d.pendulum(at, angle, arc)`, `d.pulse(at, size)` | piston and pendulum motion; a pulsing light from two counter-rotating stars |
| 19 auto-fire | `auto_fire=True` on any gun preset | fires without a click (`flags.forceFire`) |
| 20 trail / body that follows | `d.trail(seconds, size, sides, taper)`, `stages=[(size, s, sides, color, parts), …]` | stationary bullets dropped behind; stages = one dropper per size, graded taper with decorated segments |
| 21 bite / contact damage | `d.jaws(...)`, `d.contact_damage(at, damage, turret)` | cursor-following jaws with hot points |
| 22 cursor pivot, eye | `d.cursor_pivot(at, angle, arc)`, `d.eye(at, size, pupil)` | hands and held items; a watching eye |
| 23 armed / decorated projectiles | `d.turreted_bullet()`, `d.projectile(parts=[d.part(...)])` | both confirmed in play; parts are hull-scale and sit under the disc unless `above=True` |
| 24 custom arena shapes, total conversion | `pack.custom_shape(...)`, `pack.hidden`, `pack.starters`, `pack.hidden_shapes` | spec §1, §1a |
| 25 dash | `d.dash(power, reload)` | a right-click leap from backward recoil |
| 26 melee: fists and a sword sweep | `d.punch(reach, range)`, `d.blade(length, hits, turret)` | hits that land only within reach; a line of hits on a click |
| 27 living limbs, jointed legs | `d.living_limb(at, angle, arc, range)`, `d.leg(at, angle, side)` | limbs that react to enemies and to the cursor; spider legs |
| 28 drawn projectiles | `d.proj_rod(a, b)`, `d.web()`, `d.egg()` | line art on any projectile; a web; eggs that hatch |
| 29 figure drones | `d.figure_drone(name, parts, rods, turrets)`, `d.summon(idx)` | a drone that is a whole character with arms, fists and a lunge |
| 30 walkers and buildings | `d.walker()`, `d.sentry()`, `d.place(idx, right_click)` | a golem that walks by recoil; a placed ballista |
| 31 random rolls | `lifetime=[a, b]`, `damageMultiplier=[a, b]`, `projectile=[a, b]` on any weapon | per-shot ranges and choices |
| 32 class folders | `d.folder()` + `d.set(advancesInto=[…])` | picker nodes drawn as icons |
| 33 guided missiles | `d.missile(seeker, range, arc, warhead, proximity)`, `d.missile_launcher(missile=i)` or `thrusters="seeker"`, `d.cluster_launcher(count, shards)` | a heat seeker (an engine on a tracking turret), a warhead that bursts, a proximity fuse, a salvo of drone missiles that splits |

## 1. Plain cannon (Tank)

```json
"barrels":[{"bulletType":"bullet","projectile":0}]
```

## 2. Alternating pairs and rings (Twin, Octo Tank)

Twin: two barrels side by side via `offset`, the second fires half a reload later.

```json
"barrels":[
 {"offset":-26,"bulletType":"bullet","projectile":0,"damageMultiplier":0.65,"penetrationMultiplier":0.9,"recoilMultiplier":0.75},
 {"offset":26, "bulletType":"bullet","projectile":0,"damageMultiplier":0.65,"penetrationMultiplier":0.9,"recoilMultiplier":0.75,"delay":0.5}]
```

Octo Tank: eight barrels at 45° steps; the diagonals carry `delay: 0.5` so the ring
alternates. Angles ±0.785, ±2.356 (delayed) and 0, ±1.571, 3.142 (not delayed).
Damage is scaled down per barrel (0.65) so total output stays sane; do the same when
adding barrels.

## 3. Sniper, machine gun, destroyer (the three basic barrel personalities)

```json
Sniper:      {"distance":110,"bulletType":"bullet","projectile":0,"speedMultiplier":1.4,"reloadMultiplier":1.5,"spreadMultiplier":0.3,"recoilMultiplier":3}   + tank "zoomMultiplier":0.9
Machine Gun: {"muzzleScale":1.75,"bulletType":"bullet","projectile":0,"damageMultiplier":0.7,"reloadMultiplier":0.5,"spreadMultiplier":3}
Destroyer:   {"heightMultiplier":1.7,"bulletType":"bullet","projectile":0,"damageMultiplier":3,"penetrationMultiplier":2,"speedMultiplier":0.7,"reloadMultiplier":4,"recoilMultiplier":15,"knockbackMultiplier":0.1}
```

Long barrel + low spread + slow reload = sniper. Flared muzzle (`muzzleScale` > 1) + fast
reload + high spread = machine gun. Wide barrel + big damage + slow reload + huge recoil =
destroyer. `zoomMultiplier` below 1 widens the view (0.9 tier-4 snipers, 0.75 Stalker,
0.65 Hitman).

## 4. Precision with a detached tip (Hitman)

```json
"barrels":[
 {"distance":50,"startDistance":15,"heightMultiplier":1.75,"muzzleScale":0.5714,"bulletType":"none","projectile":-1,"order":1},
 {"distance":135,"bulletType":"bullet","projectile":0,"damageMultiplier":1.2,"speedMultiplier":1.5,"reloadMultiplier":2,"spreadMultiplier":0,"recoilMultiplier":4}]
```

`spreadMultiplier: 0` fires perfectly straight. Decorative barrels are `bulletType: none`,
`projectile: -1`; `startDistance` is the gap from the hull centre where the barrel starts.

## 5. Spawner / drones (Overlord)

```json
"projectiles":[{"name":"Drone","base":"drone","sides":-1}],
"barrels":[{"flags":{"forceFire":true},"angle":-1.5707964,"distance":70,"muzzleScale":1.75,
            "bulletType":"drone","projectile":0,"damageMultiplier":0.7,"penetrationMultiplier":2,
            "speedMultiplier":0.8,"reloadMultiplier":6,"numDrones":2,"droneAggressiveCrashRadius":900}, …×4]
```

A spawner is a short flared trapezoid (`distance` 70, `muzzleScale` 1.75) with
`forceFire` so it spawns without clicking. `numDrones` is the cap per barrel (Overlord
4 × 2 = 8). Always write `numDrones` and `droneAggressiveCrashRadius` on drone barrels.

## 6. Swarm drones and AI-only drones (Battleship, Hybrid)

```json
Battleship projectiles:
 {"name":"Swarm drone","base":"drone","sides":-1,"drone":{"idle":"cruise"}},
 {"name":"Swarm drone","base":"drone","sides":-1,"drone":{"idle":"cruise","controllable":false}}
Battleship barrel: {"angle":1.5707964,"offset":-20,"distance":75,"heightMultiplier":1.225,"muzzleScale":0.5714,
  "bulletType":"drone","projectile":1,"damageMultiplier":0.15,"bulletSizeMultiplier":0.4286,"lifetime":4.2,
  "knockbackMultiplier":0.3,"numDrones":24,"droneAggressiveCrashRadius":1600}
Hybrid rear spawner: {"flags":{"forceFire":true},"angle":3.1415927,"distance":70,"muzzleScale":1.75,"bulletType":"drone",
  "projectile":1,"damageMultiplier":0.7,"penetrationMultiplier":1.4,"reloadMultiplier":6,"numDrones":2,
  "droneControllable":false,"droneAggressiveCrashRadius":900}   with projectile "drone":{"controllable":false}
```

`drone.idle: "cruise"` = Battleship-style swarm that wanders; absent = Overlord-style. Short
`lifetime` (4.2 s) makes swarm drones expendable. For AI-only drones the switch that counts
is `drone.controllable: false` on the **projectile**; the barrel's `droneControllable` does
nothing alone (confirmed 2026-09-26), but stock tanks write both, so do too. Note Battleship's spawners have no
`forceFire` and still spawn: drone barrels spawn regardless.

## 7. Necromancer (raises + holdsRaised)

```json
"body":{"sides":4},"raises":["square"],
"barrels":[{"flags":{"forceFire":true,"holdsRaised":true},"angle":-1.5707964,"distance":70,"muzzleScale":1.75,
            "bulletType":"drone","projectile":-1,"damageMultiplier":0.42,"penetrationMultiplier":2,
            "speedMultiplier":0.76,"reloadMultiplier":6,"numDrones":11,"droneAggressiveCrashRadius":900}, …×2]
```

No `projectiles` at all: the slots are filled by killed polygons named in `raises`
(`square`, `triangle`, `pentagon`, `big_pentagon`, `hexagon`, `small_crasher`,
`big_crasher`). Resurrector adds `"preSpawn":2`: each raiser emits two free squares right after spawn (confirmed 2026-09-26; `preSpawn` does nothing on projectile-drone spawners).

## 8. Missiles (Skimmer, Rocketeer, Glider)

```json
Skimmer projectile 0:
 {"name":"Missile","base":"bullet","sides":-1,"spin":0.1,"spinFlipsOnSecondary":true,
  "barrels":[{"flags":{"forceFire":true},"distance":70,"heightMultiplier":0.9,"bulletType":"bullet","projectile":1,
              "damageMultiplier":0.6,"penetrationMultiplier":0.4,"speedMultiplier":0.63,"reloadMultiplier":0.35,
              "lifetime":0.9,"delay":0.5,"color":27},
             {…same…,"angle":3.1415927}]}
Skimmer launcher: {"distance":80,"heightMultiplier":1.7,"bulletType":"bullet","projectile":0,"penetrationMultiplier":4,
  "speedMultiplier":0.63,"bulletSizeMultiplier":1.2,"reloadMultiplier":4,"lifetime":3.9,"recoilMultiplier":3,"knockbackMultiplier":0.1}
plus a base: {"distance":92.63,"heightMultiplier":0.8,"muzzleScale":1.75,"bulletType":"none","projectile":-1,"order":-1}
```

A missile is a bullet carrying sub-barrels with `forceFire`; `color: 27` paints them in
the owner's colour; `projectile: 1` on the sub-barrels points at a plain bullet in the
**tank's** list. Rocketeer's single rear thruster has `"angle":π, "recoilMultiplier":3.8,
"spreadMultiplier":3, "delay":7` (waits seven short reloads, then pushes) and the launcher
fires fast then cruises slow: `"speedMultiplier":0.2, "initialVelocityMultiplier":1.2`.
Glider's two thrusters sit at ±144° (2.513, 3.770) so it accelerates forward.

## 9. Minions (Factory, Automator)

```json
Factory projectile 0:
 {"name":"Minion","base":"drone","sides":0,"drone":{"keepDistanceMin":300,"keepDistanceMax":800},
  "barrels":[{"distance":85,"heightMultiplier":1.2,"bulletType":"bullet","projectile":1,
              "damageMultiplier":0.4,"penetrationMultiplier":0.4,"speedMultiplier":0.8,"delay":0.01}]}
Factory spawner: {"flags":{"forceFire":true},"distance":70,"muzzleScale":1.75,"bulletType":"drone","projectile":0,
  "damageMultiplier":0.7,"penetrationMultiplier":4,"speedMultiplier":0.56,"bulletSizeMultiplier":0.8485,
  "reloadMultiplier":3,"knockbackMultiplier":1.2,"numDrones":6,"droneAggressiveCrashRadius":1200}
Automator spawner: same but "projectile":[0,1,2,3,4]  (five minion types, one picked at random per spawn)
```

A minion is a round drone (`sides: 0`) with ordinary sub-barrels (no flag) that fire on the
owner's click. `keepDistance` makes it hold range **from its target** (confirmed 2026-09-26: with a 300–400 band plain drones circle a shape without touching it and nuzzle the owner when idle). A list in `projectile` picks randomly.

## 10. Trappers (Trapper, Auto Trapper)

```json
"projectiles":[{"name":"Trap","base":"trap","sides":-1}],
"barrels":[
 {"distance":60,"bulletType":"trap","projectile":0,"damageMultiplier":1.2,"penetrationMultiplier":1.5,"speedMultiplier":2,
  "bulletSizeMultiplier":1.1,"reloadMultiplier":1.5,"lifetime":24,"knockbackMultiplier":0.4},
 {"distance":20,"startDistance":30,"muzzleScale":1.75,"mount":0,"bulletType":"none","projectile":-1}]
```

The launcher is a short barrel plus a flared tip mounted on it (`mount: 0` = index of the
launcher in the same array). Traps live 24 s. Mega Trapper scales size and damage up,
Tri-Trapper repeats the pair three times.

## 11. Smasher family (Smasher, Spike, Landmine, Blender)

```json
Smasher: "statsMaxLevel":[10,0,0,0,0,10,10,10], no barrels, no projectiles,
         "bodyShapes":[{"sides":6,"size":57.5,"angle":1,"spinSpeed":0.1}]
Spike:   "baseBodyDamage":7,"speedMultiplier":1.1, four triangles {"sides":3,"size":65,"angle":1.7|2.747|2.224|3.271,"spinSpeed":0.17}
Landmine: Smasher + second hexagon {"sides":6,"size":57.5,"angle":0.5,"spinSpeed":0.05} +
         "invisibility":{"enabled":true,"gain":0.004,"revealDistance":650,"lossOnAttack":0,"lossOnMovement":0.16,"lossOnHit":0.05}
Blender: "baseBodyDamage":8, caps [12,0,0,0,0,12,12,12], three squares {"sides":4,"size":60,"spinSpeed":0.25}
```

Stat caps run Movement, Reload, Bullet Damage, Bullet Penetration, Bullet Speed, Body
Damage, Max Health, Regen (reverse of the in-game 1–8 keys); 0 removes the stat. Body
shapes default to dark grey (colour 0) and sit under the hull.

## 12. Stealth (Stalker)

```json
"invisibility":{"enabled":true,"gain":0.03076923076923077,"revealDistance":450,"lossOnHit":0.05},
"zoomMultiplier":0.75,
"barrels":[{"distance":120,"heightMultiplier":1.75,"muzzleScale":0.5714,"bulletType":"bullet","projectile":0,
            "speedMultiplier":1.5,"bulletSizeMultiplier":0.5714,"reloadMultiplier":2,"spreadMultiplier":0.1,"recoilMultiplier":4}]
```

`gain` is opacity lost per tick (default fades in ~1.3 s; Landmine 0.004 ≈ 10 s).
`lossOnAttack: 0` lets a tank fire without revealing (Landmine, Boss).

## 13. Auto turrets (Auto Tank, Auto 3, Auto 7)

```json
Top-mounted (Auto Tank, Auto Trapper, Auto Gunner):
 "turrets":[{"angle":3.1415927}],
 turret barrel: {"distance":55,"heightMultiplier":0.7,"mountTurret":0,"bulletType":"bullet","projectile":0,
                 "damageMultiplier":0.3,"speedMultiplier":1.2,"recoilMultiplier":0.3,"delay":0.01}
Side-mounted (Auto 3; Auto 5 and Auto 7 add turrets on the same ring of radius 40):
 "body":{"sides":0,"spinSpeed":0.01},
 "turrets":[{"xOffset":40,"range":2000,"arc":1.4137,"controllable":true,"aboveBody":false},
            {"xOffset":-20,"yOffset":34.64,"range":2000,"angle":2.0944,"arc":1.4137,"controllable":true,"aboveBody":false},
            {"xOffset":-20,"yOffset":-34.64,"range":2000,"angle":4.1888,"arc":1.4137,"controllable":true,"aboveBody":false}],
 each turret barrel: {…,"mountTurret":i,"damageMultiplier":0.5,"delay":0.5}
```

A turret is a mount; its gun is a tank barrel with `mountTurret`. Place N side turrets at
`xOffset = 40·cos θ`, `yOffset = 40·sin θ`, `angle = θ`, θ = 2πk/N. `controllable: true`
lets the player aim them; `aboveBody: false` draws side turrets under the hull rim.

## 14. Shotguns (Shotgun, Pellet Shot)

```json
Shotgun barrel: {"distance":90,"muzzleScale":1.75,"bulletType":"bullet","projectile":0,"damageMultiplier":0.5,
  "penetrationMultiplier":0.6,"speedMultiplier":1.1,"bulletSizeMultiplier":0.7,"numBullets":4,"reloadMultiplier":4,
  "spreadMultiplier":2.75,"lifetime":1.8,"recoilMultiplier":0.6,"knockbackMultiplier":0.5,"initialVelocityMultiplier":1.5}
Pellet Shot: "numBullets":10, "speedMultiplier":[1.08,1.32], "initialVelocityMultiplier":[0.75,2.25]
```

`numBullets` pellets per shot, scattered by `spreadMultiplier`. Stock shotguns stack three
overlapping barrels with different spreads (2.75 / 1.2 / 0.9) for a dense-centre cloud.
A `[min, max]` pair on a speed field rolls each pellet randomly.

## 15. Burst / explode on command (Firework)

```json
"helpText":"Right click to explode your bullets",
projectile 0: {"name":"Shell","base":"bullet","sides":6,"burst":{"onSecondary":true},
  "barrels":[ 24 × {"flags":{"firesOnDeath":true},"angle":θ,"distance":0,"heightMultiplier":0.85,"bulletType":"bullet",
                    "projectile":1,"damageMultiplier":0.6,"penetrationMultiplier":0.6|0.4,"speedMultiplier":0.8|0.6|0.4|0.2,
                    "reloadMultiplier":20,"spreadMultiplier":0.5,"lifetime":0.48,"recoilMultiplier":0,"knockbackMultiplier":0.25,
                    "initialVelocityMultiplier":0.8|0.6|0.4},
              {"flags":{"forceFire":true},"angle":3.1415927,"distance":63.9,"bulletType":"bullet","projectile":1,
               "reloadMultiplier":0.5,"recoilMultiplier":5.6,"lifetime":0.6,"delay":0.5,"color":27} ]}
```

`burst.onSecondary` / `onDestroyed` / `onExpire` end the projectile; `firesOnDeath`
sub-barrels fire once at that moment. `distance: 0` keeps them invisible until then.
Without any `firesOnDeath` barrel a burst just makes the projectile vanish.

## 16. Right-click barrels (Striker, Dual-Barrel)

```json
Striker front: {"flags":{"firesOnSecondary":true},"heightMultiplier":1.7,"bulletType":"bullet","projectile":0,
  "damageMultiplier":2,"penetrationMultiplier":2,"speedMultiplier":0.63,"reloadMultiplier":4,"recoilMultiplier":6,"knockbackMultiplier":0.1}
"helpText":"Right click to fire your front barrel"
```

`firesOnSecondary` moves a barrel to the right mouse button. Add a `helpText` saying so.
Predator-style scope instead: tank `"scopeDistance":1500` slides the camera on right-click.

## 17. Decorated hulls (Tenk, Automator, Cyclone)

```json
Tenk: "statsMaxLevel":[10,10,10,10,10,10,10,10],"upgradesFrom":[0],
      "bodyShapes":[{"sides":4,"size":20,"aboveBody":true,"order":1,"color":1}]
Octagon hull (Automator, Resurrector, Battalion): "body":{"sides":8,"angle":0.3927,"size":44.23}
Star hull: "body":{"sides":18,"star":true,"angle":3.1416,"size":67,"color":22}
```

`aboveBody` draws a part over the hull; `xOffset` forward, `yOffset` right. Official
octagons use radius 44.23 (polygon hulls draw at 1.3 × size, so 44.23 renders as 57.5)
and rotate π/8 so a flat faces front. Anything beyond a decoration or two (a creature, a
vehicle, a many-part figure) is built with `scripts/compose.py`; see `figurative.md`. Palette: 2 player blue, 4 enemy red, 8 square yellow, 9 triangle red, 10 pentagon
blue, 22 dark blue, 25 green, 26 purple, 27 owner colour; full table in the spec §10.

## 18. Tree links (10th Anniversary pack)

```json
{"id":100076,"name":"Cyclone","minLevel":60,"upgradesFrom":[54], …}
{"id":100082,"name":"Triple Flank","minLevel":60,"upgradesFrom":[13,2], …}
{"id":100084,"name":"Mega Smasher","minLevel":45,"upgradesFrom":[36],"knockbackMultiplier":0.2, …}
```

A custom line: tank A `"upgradesFrom":[6]` (Sniper) at 30, tank B `"upgradesFrom":[100001]`
at 45, where 100001 is A's id in this pack. `advancesInto` on the parent is optional; the
child's `upgradesFrom` alone places it on the ladder (that is all the official pack uses).

## 19. Auto-fire (human packs)

```json
{"angle":3.1416,"distance":5,"startDistance":40,"bulletType":"bullet","projectile":1,"invisible":true,"flags":{"forceFire":true}, …}
```

`flags.forceFire` on a tank-level bullet barrel makes it fire continuously without a click
(the stock tanks only use it on spawners and missile thrusters). `invisible: true` hides
the barrel while it keeps firing. `auto_fire=True` on any preset writes the flag.

## 20. Trail: a body that follows the tank (a player-built snake)

```json
projectile 1: {"name":"","base":"bullet","sides":-1,"burst":{"onExpire":true},
  "barrels":[{"flags":{"forceFire":true,"firesOnDeath":true},"angle":3.1416,"distance":5,"startDistance":-20,"bulletType":"bullet","projectile":2,
              "penetrationMultiplier":5,"speedMultiplier":0,"bulletSizeMultiplier":1.8,"reloadMultiplier":0.25,"spreadMultiplier":0,
              "lifetime":0.75,"recoilMultiplier":0,"initialVelocityMultiplier":0}]}
projectile 2: {"name":"","base":"bullet","sides":-1}
dropper: {"angle":-3.1416,"distance":5,"startDistance":40,"bulletType":"bullet","projectile":1,"penetrationMultiplier":5,
  "speedMultiplier":0,"bulletSizeMultiplier":2,"reloadMultiplier":0.25,"spreadMultiplier":0,"lifetime":2,"recoilMultiplier":0,
  "initialVelocityMultiplier":0,"invisible":true,"flags":{"forceFire":true}}
```

A stationary bullet (`speedMultiplier` 0, `initialVelocityMultiplier` 0) stays where it was
fired. Dropped every quarter reload from an invisible rear barrel, the segments form a chain
along the tank's path that lasts `lifetime` seconds (the snake body in
a player-built snake's in-play screenshot); `burst.onExpire` plus a `firesOnDeath` sub-barrel spawns a
smaller segment as each one dies, so the tail tapers. Confirmed 2026-09-26 (serpent A/B):
`firesOnDeath` alone gives a hard step from segments to end pieces; the snake's extra
`forceFire` makes the end pieces also shimmer out from under the living segments, a soft
fade. The end piece's `bulletSizeMultiplier` is **relative to the segment, half per unit**
(2.0 segment: 0.5 → ¼, 1.0 → ½, 2.0 → 1.2×; 1.5 segment: 1.15 → ½, croc 2026-09-27), so 1.6
gives an 0.8 step and the snake's 1.8 is 0.9; `d.trail()` defaults to a 1.0 end (half).
Polygon segments draw 1.3× bigger than round ones of the same size. `d.trail()` writes
all of this (`taper`, `end_force_fire`, `end_color`); give it `sides` and `color` for a
segmented or coloured body. For a graded taper pass `stages=[(size, seconds, sides, color,
parts), …]` (croc, 2026-09-27): one invisible dropper per stage, all firing at the same spot,
stage i living the sum of the first i `seconds`, so the big pieces die first and uncover the
smaller ones behind; `parts` (`d.part(...)`, hull-scale, `above=True`) decorate a stage, e.g.
Mint ridges on a croc tail. Each dropper costs budget (6.8/s at reload 0.7, cap 12). Do not
chain stages through a spawned bullet's own sub-barrel: nothing past the first spawn ever
showed in play (spec §5).

## 21. Bite: contact damage and cursor-following jaws (a player-built snake)

```json
turrets: {"xOffset":40,"yOffset":-20,"baseSize":10,"range":0,"angle":-0.7854,"arc":1.0472,"controllable":true,"aboveBody":false,"color":27}
jaw bar: {"offset":-10,"distance":140,"mountTurret":0,"bulletType":"none","projectile":-1,"color":27}
tooth:   {"sides":3,"size":20,"xOffset":110,"yOffset":10,"angle":1.5708,"color":1,"mountTurret":0}
bite:    {"angle":1.5708,"offset":-80,"distance":5,"startDistance":-30,"mountTurret":0,"bulletType":"bullet","projectile":0,
          "damageMultiplier":0.75,"penetrationMultiplier":20,"bulletSizeMultiplier":0.5,"reloadMultiplier":0.25,"spreadMultiplier":0,
          "lifetime":0.1,"recoilMultiplier":0,"knockbackMultiplier":0,"initialVelocityMultiplier":0,"invisible":true,"flags":{"forceFire":true}}
```

Budget: each bite point is counted at the tank's Reload cap toward the 120/s import limit
(§7a): with cap 12, 13/s at 0.25 and 9.5 at 0.5; with cap 7, 12 and 6. `contact_damage()` defaults
to reload 0.5 and lifetime 0.2 and jaws carry three per side; the croc (caps 12) was refused at
196/s with ten bites at 0.25 plus legs and tail, and at 121/s with six bites at 0.5. The serpent
gets away with eight fast barrels because its Reload cap is 0.

A turret with `range: 0` never auto-targets; with `controllable: true` it follows the cursor
within `arc` of its rest `angle`, and only **while the fire button is held**; released, it
sits at `angle` (confirmed 2026-09-26 whatever the pivot carries; a pivot with no `arc`
wanders when released, so always set one). Two of them at (40, ±20) resting at ±45° with a 60°
arc are jaws: released → open at ±45°, left click held → both aim forward and close on what
is between them (`arc` ≥ `rest`, or they never meet). Shapes ride the turret through
`mountTurret` (teeth, fangs), and invisible auto-firing barrels whose stationary 0.1 s
bullets sit along the inside of each jaw make anything between the jaws take damage. In a
design script: `d.jaws()`; a single hot point anywhere is `d.contact_damage(at)`; a bare
cursor-following mount is `d.cursor_pivot(at)`.

## 22. A watching eye (a player-built snake)

```json
turret: {"xOffset":15,"baseSize":30,"arc":1.5708,"color":19}
pupil:  {"sides":0,"size":15,"xOffset":10,"aboveBody":true,"mountTurret":2}
```

The turret disc is the eyeball (`baseSize` 30, White); the pupil is a circle mounted on it,
drawn above the disc, 10 units off centre, so it looks at whatever the turret tracks.
`d.eye(at)`.

## 23. Decorated and armed projectiles (player-built packs)

```json
Turreted bullet: {"name":"Bullet","base":"bullet","sides":-1,"turrets":[{}],
  "barrels":[{"distance":55,"heightMultiplier":0.7,"mountTurret":0,"bulletType":"bullet","projectile":1,"damageMultiplier":0.3,
              "penetrationMultiplier":0.5,"speedMultiplier":1.2,"reloadMultiplier":3,"recoilMultiplier":0.3}]}
Star bullet with an eye: {"name":"","base":"bullet","sides":7,"star":true,
  "parts":[{"sides":0,"size":12,"aboveBody":true,"color":4},{"sides":0,"size":8,"aboveBody":true,"order":1,"color":20}]}
Familiar: {"name":"Familiar","base":"drone","sides":0,"spin":0.05,"drone":{"repel":false},
  "parts":[{"sides":6,"size":60,"spinSpeed":0.0001}],"barrels":[{"distance":75,…,"damageMultiplier":3,"penetrationMultiplier":8}]}
```

`parts` on a projectile are body shapes in the projectile's frame; `turrets` are turrets a
sub-barrel can `mountTurret` on. Confirmed 2026-09-26: the turret is drawn on the bullet and
its gun shoots shapes and enemies on its own until the bullet expires, flagged or not.
`d.projectile(parts=[d.part(...)])`, `d.turreted_bullet()`.

## 24. Custom arena shapes and total conversions (player-built packs)

```json
"shapes":[{"id":"custom_shape_1","name":"Hexagon","sides":6,"size":100,"maxHealth":1500,"xpBounty":1500,"damageOnTouch":4,
           "knockbackOnTouch":10,"knockbackMultiplier":0.1,"color":"#35c5db","ai":{"floatSpeed":0.05},
           "spawn":{"densityMultiplier":999},"editor":{"replaces":"hexagon"}}],
"hiddenShapes":["hexagon"],
"hidden":[1,2,3,…,64],"starters":[100001]
```

Spec §1 and §1a. `pack.custom_shape(...)` returns an id a Necromancer-style tank can put in
`raises`; `pack.hidden`, `pack.starters` and `pack.hidden_shapes` are plain lists. Confirmed
2026-09-26 (the `arena-test` test build): `density=1.0` made the custom shape 40–50 % of all
spawns beside the vanilla shapes; `hidden` alone empties the class tree and `starters` picks the
spawn tank (a total-conversion import). For a themed arena (roles, rings, weights, shares) follow
`arena.md`; `Pack.spawn_shares()` predicts the mix and `save()` prints it.

## 25. Dash: a leap on right click

```json
{"angle":3.141592653589793,"distance":5,"startDistance":-43,"bulletType":"trap","projectile":0,"invisible":true,
 "damageMultiplier":0,"penetrationMultiplier":0,"speedMultiplier":0,"bulletSizeMultiplier":1.6,"reloadMultiplier":4.2,
 "spreadMultiplier":0,"lifetime":0.1,"recoilMultiplier":16.3,"knockbackMultiplier":0,"initialVelocityMultiplier":3,
 "flags":{"firesOnSecondary":true},"editor":{"name":"Dash"}}
projectile 0: {"name":"Dash","base":"trap","sides":0,"star":true,"spin":0.01}
```

Forty-five of a player-built pack's tanks carry this: a barrel that points **backward**, tucked
inside the hull, firing a harmless one-frame shot with huge recoil, so each right click throws
the tank forward. Recoil 12–20 and reload 4–12 set the leap and how often; the big spider
stacks three barrels at recoil 20, reload 12. Tank `knockbackMultiplier` 0–0.8 keeps the
leaper from being shoved back. `d.dash(power, reload)`. Costs almost nothing on the fire
budget. **Confirmed 2026-09-28** (the lab's Dash Punch: recoil 16.3, reload 4.2 leapt a tank
length or more, once every few seconds).

## 26. Melee: fists that land only within reach, and a sword sweep

```json
"turrets":[{"range":300,"arc":0.3490658503988659,"aboveBody":false}]          // no baseSize: hidden under the hull
"barrels":[{"angle":0.017,"offset":32,"distance":5,"startDistance":80,"heightMultiplier":1.12,"muzzleScale":0.089,
            "mountTurret":0,"bulletType":"bullet","projectile":2,"invisible":true,"damageMultiplier":5.7,"penetrationMultiplier":7.5,
            "speedMultiplier":0,"bulletSizeMultiplier":3,"reloadMultiplier":0.3,"spreadMultiplier":0,"lifetime":0.1,
            "recoilMultiplier":0,"knockbackMultiplier":0.6,"delay":0.5},
           {… "offset":-62, "damageMultiplier":1.6,"penetrationMultiplier":2.4 …}]
projectile 2: {"name":"Punch","base":"bullet","sides":7,"star":true,"spin":0.02,"color":19}
```

"Get close to punch" (51 tanks, from the level-1 class up): two invisible stationary one-frame
shots of size 3 appear 80 ahead of an **auto-turret** (not controllable) whose `range` is
only 300, so its guns fire (the Auto Tank rule: turret guns fire on their own at targets in
range and arc) only when something is within arm's reach. The turret sits under the hull
(`aboveBody: false`, default disc) so nothing shows. `d.punch()`. **Confirmed 2026-09-28**
(the lab's Dash Punch): the fists fire only at what is inside the turret's front cone (backing
into a shape never triggers them) and keep firing, hit or miss, for as long as it stays in
range. The fists reach only about 150 (80 ahead plus a size-3 star), so a player-built pack's range 300
throws punches at 3–4 body lengths that land short; `d.punch()` defaults to 180 so a punch
fires only when it can land. The dash of §25 was confirmed in the same test: a leap of a tank
length or more on right click, repeatable every few seconds.

A king's "Right click to slash" is the same idea along a line: twelve invisible trap
barrels at `startDistance` 122…449 on one `offset` (−53), each a stationary size-3 hit
(1.1 at the tip) with lifetime 0.12, reload 14, damage 18, all `firesOnSecondary`; the sword
rod they follow rides a living-limb pivot (§27), so the cut swings. `d.blade(turret=i)`.

## 27. Living limbs and jointed legs

```json
// A spider, one of eight leg pivots, and the three rods and two stars that ride it
{"xOffset":16,"yOffset":-25,"baseSize":18,"angle":-1.0471975511965976,"arc":0.5235987755982988,"controllable":true,"aboveBody":false}
{"angle":0.035,"distance":134,"heightMultiplier":0.92,"muzzleScale":0.40,"mountTurret":0,"bulletType":"none","projectile":-1}
{"angle":0.785,"offset":-84,"distance":179,"startDistance":86,"heightMultiplier":0.52,"muzzleScale":0.37,"mountTurret":0,…}
{"angle":1.152,"offset":-170,"distance":173,"startDistance":200,"heightMultiplier":0.2,"muzzleScale":0.65,"mountTurret":0,"color":0,…}
{"sides":4,"star":true,"size":19,"xOffset":125,"yOffset":3,"angle":0.209,"color":20,"mountTurret":0}
// A warrior's arm: the same with an enemy range
{"xOffset":26,"yOffset":65,"baseSize":19,"range":750,"angle":-0.89,"arc":0.349,"controllable":true,"aboveBody":false}
```

Seventy-two tanks put their limbs on `controllable` turrets with a rest `angle`, a narrow
`arc` (15° legs and arms, 20–40° hands) and an enemy `range` (250 arms, 100 a plume or
cape, 750 a warrior's arms, none on the spider's legs), instead of the `range: 0`
cursor pivot of §22. Such a limb turns toward enemies inside its range while the player is
idle and toward the cursor while firing, so eight legs each twitch a little toward whatever
passes, which is what makes the spider look alive. **Confirmed 2026-09-28** (Limb Lab: the
living-limb arm turned to a shape within 250 while the range-0 arm ignored it; both followed
the cursor while firing; both sat still at rest with nothing near). A limb follows the cursor
only inside its wedge (rest `angle` ± `arc`): the lab's two backward-resting legs ignored a
forward cursor, so legs mostly live by tracking what passes their side (Leg Range Lab, 2026-09-28: sideways legs with arc 30 never followed the cursor either, since the hull always faces it; with `range` unset, as on the spider, they still twitch at passing shapes and react from further than 250, so unset means a longer reach, not off), and by swinging as the
body turns (the pendulum lag of §5). `d.living_limb()`; `d.leg()` builds the spider's three tapering rods with a
star at each bend on one pivot (eight legs = 24 rods, 16 stars, 8 pivots: the 32/32 caps).

## 28. Projectiles that are drawings: a web, a trident, an egg

```json
// A spider's web: a trap, its disc a 4-star, drawn with 24 decorative sub-barrels and two hooks
{"name":"Web","base":"trap","sides":4,"star":true,"color":19,
 "parts":[{"sides":10,"star":true,"size":12,"yOffset":-83,"collidable":true,"color":19},{… "yOffset":88 …}],
 "barrels":[{"angle":1.5708,"distance":200,"heightMultiplier":0.2,"muzzleScale":0.5,"bulletType":"none","projectile":-1,"flags":{"aboveBody":true}},  // 8 spokes
            {"angle":-1.5708,"offset":-86,"distance":71,"startDistance":-36,"heightMultiplier":0.1,"bulletType":"none","projectile":-1,"flags":{"aboveBody":true}}, …]}  // 2 rings x 8 chords
fired by: {"distance":5,"startDistance":100,"bulletType":"trap","projectile":0,"invisible":true,"penetrationMultiplier":20,"speedMultiplier":3,
           "bulletSizeMultiplier":1.2,"reloadMultiplier":0.9,"spreadMultiplier":1.7,"lifetime":5.18,"recoilMultiplier":0.5,"initialVelocityMultiplier":3}
// A hen's egg: a trap that hatches
{"name":"Egg","base":"trap","sides":0,"star":true,"color":19,"burst":{"onDestroyed":true,"onExpire":true},
 "parts":[{"sides":0,"size":50,"yOffset":-4,"aboveBody":true,"color":19},{… -8 …},{… -11 …}],
 "barrels":[{"distance":0,"heightMultiplier":2.5,"bulletType":"bullet","projectile":3,"invisible":true,"damageMultiplier":3.5,"penetrationMultiplier":4.6,
             "bulletSizeMultiplier":1.2,"reloadMultiplier":0.1,"lifetime":0.2,"knockbackMultiplier":7.5,"flags":{"firesOnDeath":true}},
            {"distance":0,"heightMultiplier":2.5,"bulletType":"trap","projectile":1,"invisible":true,"damageMultiplier":1.4,"penetrationMultiplier":1.2,
             "bulletSizeMultiplier":3,"reloadMultiplier":0.1,"lifetime":0.1,"knockbackMultiplier":2.5,"flags":{"firesOnDeath":true}}]}
laid by: {"angle":3.14159,"distance":0,"startDistance":29,"bulletType":"trap","projectile":[0,4],"invisible":true,"bulletSizeMultiplier":[1.2,1.6],
          "reloadMultiplier":2.6,"lifetime":[12,22.5],"knockbackMultiplier":0,"flags":{"firesOnSecondary":true}}
```

A projectile's `barrels` need not fire: with `bulletType: "none"` they are rods in the
projectile's frame, drawn over its disc with `flags.aboveBody`, exactly like line art on a
hull (57 projectiles of a player-built pack: the web above, a trident's shaft and tines, a chick's beak, a
golem's arms). **Each rod counts against the import budget** as one more entity per shot
(spec §7a): the web is 1 + 24 rods + its hooks, so fire it from a tank with Reload cap 0 and reload about 1, as the
spider does (the lab's Web Lab at cap 7 was refused at 437/250 in the air).
**Confirmed in play** (the lab's Web Lab, 2026-09-28: the web drew as designed and lasted about 5.5 s; shapes took damage only from its centre disc and its two collidable hook stars, never from the rods, and were not pushed back). So drawn rods on a projectile are picture
only: what hits is the projectile's disc plus its `collidable` parts. To make a whole drawing
catch, scatter small collidable parts over it, **at most three** (the editor makes every
collidable part after the third drawing-only, spec §5; `d.web(hooks=3)`). Every part, rod and
hook adds 1 to each shot's cost and collidable ones add room (§7a). `render_pack.py --projectiles` draws them. `d.proj_rod(a, b)` makes one;
`d.web()` builds the web; `d.egg()` the egg (a `burst` trap whose `firesOnDeath` sub-barrels
throw a yolk bullet that shoves and a white trap that splashes). The layer barrel shows two
per-shot rolls at once: `projectile: [egg, golden egg]` picks one per shot, `lifetime:
[12, 22.5]` makes the eggs hatch at different times (spec §7). **Confirmed in play** (the lab's Egg Lab, 2026-09-28: a layer with projectile [egg, golden egg] and lifetime [12, 22.5] dropped a golden egg about every other time, the eggs hatched at clearly different times, and each burst's yolk and white hurt and shoved nearby shapes).

## 29. Figure drones: a drone that is a whole character

```json
{"name":"Twin","base":"drone","sides":0,"color":16,"drone":{"controllable":false,"repel":false,"keepDistanceMin":100,"keepDistanceMax":200},
 "parts":[ …24 shapes: the owner's helmet, face and hands copied verbatim… ],
 "turrets":[{"xOffset":24,"yOffset":65,"baseSize":19,"range":750,"angle":-0.89,"arc":0.349,"controllable":true,"aboveBody":false},   // arms
            {"xOffset":24,"yOffset":-65, …},
            {"range":650,"arc":0.349,"aboveBody":false}],                                                                             // melee pivot
 "barrels":[ …12 decorative rods…,
            {"angle":-3.14159,"distance":5,"startDistance":-43,"bulletType":"trap","projectile":0,"damageMultiplier":0,…,"recoilMultiplier":16.3,
             "initialVelocityMultiplier":3,"flags":{"forceFire":true,"firesOnSecondary":true},"editor":{"name":"Dash"}},                // lunges by itself
            {"angle":0.017,"offset":32,"distance":5,"startDistance":80,"mountTurret":2,"bulletType":"bullet","projectile":1,"invisible":true,
             "damageMultiplier":7.7,"penetrationMultiplier":10.4,"speedMultiplier":0,"bulletSizeMultiplier":3,"reloadMultiplier":0.5,"lifetime":0.1,"delay":0.5}, …]}
spawned by: {"angle":-3.14159,"offset":1,"distance":8,"startDistance":44,"heightMultiplier":1.7,"bulletType":"drone","projectile":3,"invisible":true,
             "damageMultiplier":7,"penetrationMultiplier":9,"speedMultiplier":1.6,"reloadMultiplier":5,"knockbackMultiplier":0.6,"numDrones":2,
             "droneAggressiveCrashRadius":1300,"flags":{"aboveBody":true,"forceFire":true,"firesOnSecondary":true}}
```

Twenty-two tanks of a player-built pack spawn drones built like tanks: `parts` for the body (one
warrior's drone is a copy of himself; the hen's chicks have a body, a head turret with
a beak, wings and star feet), `turrets` for living-limb arms (§27) and a hidden melee pivot,
`barrels` for rods, a §25 dash flagged `forceFire` so the drone lunges on its own, and §26
fists. AI-only (`controllable: false`), `repel: false`, holding 100–200 from its target. The
spawner is invisible with `forceFire`, so the two drones are always out. `d.figure_drone()`,
`d.summon()`. **Confirmed in play** (the lab's Summon Lab, 2026-09-28: both twins appeared on their own as soon as the tank spawned, one shortly after the other, never more than two, with no click; they hunted shapes, boosted themselves toward them with their own recoil barrel and punched; their controllable arms ignored the owner's cursor and moved on their own, turning toward shapes). Two consequences: a summon is a
companion that is always out, not a right-click ability (the drone spawner ignores the button
flags, like Overlord's), and a figure drone's limbs are its own living limbs, never puppets of
the owner's cursor. The arm rest angles set the pose (the warrior holds one arm tucked);
mirror them for a symmetric figure.

## 30. Walkers and buildings: a golem that walks, a ballista that shoots

```json
// An engineer, "Right click to build golems": a trap pushed toward enemies by recoil
{"name":"Golem","base":"trap","sides":-1,"color":23,"parts":[…5…],
 "turrets":[{…two living-limb arms…},{"range":1950,"arc":1.309}],
 "barrels":[…, {"angle":-3.14159,"distance":5,"startDistance":-43,"mountTurret":2,"bulletType":"bullet","projectile":4,"invisible":true,
                "damageMultiplier":0.1,"penetrationMultiplier":0,"speedMultiplier":0,"bulletSizeMultiplier":0.2,"reloadMultiplier":0.3,
                "lifetime":0.1,"recoilMultiplier":4.6,"initialVelocityMultiplier":3,"editor":{"name":"Dash"}}]}
// "Left click to build carts": a stationary bullet carrying an auto-turret, one of two picked at random
{"name":"Ballista","base":"bullet","sides":6,"color":23,"parts":[…7…],
 "turrets":[{"baseSize":11,"range":2000,"arc":1.745},{"range":1300,"arc":0.785}],
 "barrels":[{"distance":5,"startDistance":10,"mountTurret":0,"bulletType":"bullet","projectile":1,"invisible":true,"damageMultiplier":8,
             "penetrationMultiplier":6,"speedMultiplier":3,"bulletSizeMultiplier":1.5,"reloadMultiplier":5,"spreadMultiplier":1.2,"lifetime":4,
             "knockbackMultiplier":2,"initialVelocityMultiplier":3,"delay":0.2}, …]}
placed by: {"offset":-47,"distance":5,"startDistance":101,"bulletType":"bullet","projectile":[5,8],"invisible":true,"damageMultiplier":10,
            "penetrationMultiplier":12,"speedMultiplier":0,"bulletSizeMultiplier":2.6,"reloadMultiplier":14,"lifetime":27,"initialVelocityMultiplier":0.5}
```

A **walker** is a trap (no cruise speed) with an enemy-tracking turret whose only gun points
backward with recoil 4.6 at reload 0.3: every harmless shot nudges it toward whatever the
turret watches. A **building** is a bullet placed with `speedMultiplier` 0 and a 27 s
lifetime, carrying auto-turrets that shoot; the placing barrel's damage and penetration are
its contact damage and health. `d.walker()`, `d.sentry()`, `d.place(idx)`. **Confirmed in
play** (the lab's Builder Lab, 2026-09-28: both buildings lasted about 27 s. The ballista stayed put and its turret gun shot bolts at nearby shapes on its own, but its arrow picture, drawn on the ballista's body, never turned, so the bolts seemed to leave from any side. The bolts kept their own colour and seven sides, and at size 1.5 off a 2.6 ballista they came out almost as big as the ballista. The golem walked forward on its own, meandering a little and punching shapes on its way, until it left the map: its auto-firing walk barrel pushes it even with no target, and the turret only bends the path inside its 75-degree cone). So: draw a building's weapon on its turret (`sentry(aim_rods=…,
aim_parts=…)`) so it visibly aims; keep bolts small (`bolt_size` 0.6); and a walker is a marcher
unless its walk barrel is a plain turret gun (`walker(wander=False)`, full-circle turret, which
holds still until a shape comes in range, walks over and kills it, moves on to the next one in range, and sits again when none is left: **Confirmed**, Golem Wait Lab 2026-09-28). **Budget**: a building's guns fire once per
live copy, and at 27 s there are about six of each alive: Builder Lab at Reload cap 7 was
refused at 132/s; at cap 0 (the engineer's) it is 39.

## 31. Random rolls: ranges and choices per shot

`lifetime`, `damageMultiplier`, `penetrationMultiplier`, `knockbackMultiplier` join
`speedMultiplier`, `initialVelocityMultiplier` and `bulletSizeMultiplier` as fields that may
be a `[min, max]` pair rolled per shot (spec §7: 17 tanks roll `lifetime`, for eggs and fire
breath of uneven reach); `projectile: [a, b]` picks one definition per shot (Automator,
hen, engineer). Any preset takes them: `d.trap_launcher(lifetime=[8, 16])`.
**Confirmed in play** for `lifetime` and `projectile: [a, b]` (the lab's Egg Lab, 2026-09-28: a layer with projectile [egg, golden egg] and lifetime [12, 22.5] dropped a golden egg about every other time, the eggs hatched at clearly different times, and each burst's yolk and white hurt and shoved nearby shapes).

## 32. Class folders: picker nodes drawn as icons

```json
{"id":100046,"name":"Human","minLevel":1,"body":{"sides":0,"size":1,"spinSpeed":0.00001},"speedMultiplier":0.1,"zoomMultiplier":5,
 "knockbackMultiplier":0,"baseHealth":1,"baseBodyDamage":1,"statsMaxLevel":[0,0,0,0,0,0,0,0],"advancesInto":[100006],
 "barrels":[ …a pitchfork drawn with six rods… ],"projectiles":[{"name":"Bullet","base":"bullet","sides":-1}]}
```

Eighteen of a player-built pack's tanks are not playable classes but folders: "Human" leads to
hunters, mages, warriors and more; "Monster" to nine creatures; "Spider" to the
big spider. A radius-1 hull, health 1, speed 0.1, zoom 5 and zero stat caps make the node
useless to play, while its rods and shapes draw the icon the tree shows (a pitchfork, a paw,
a fang). The whole tree is wired with `advancesInto` (45 tanks) and `starters` names the six
root folders. `d.folder()` sets the fields; draw the icon with rods and shapes as usual.
**Confirmed in play** (the lab's Folder, 2026-09-28: it showed as a pitchfork with no visible hull, barely moved, had no stats to spend, and offered its child (Limb Lab) as an upgrade straight away).

## 33. Guided missiles: an engine, a seeker, a warhead, a proximity fuse, a cluster salvo

From a player's write-up and sample pack (2026-10-05); every number below is as they shipped
it, and **confirmed in play by them** (the pack imports and validates here; the lab has not
replayed it yet). Presets: `d.missile(...)` builds the projectile, `d.missile_launcher(missile=i)`
or any gun fires it, `d.cluster_launcher()` builds the cluster salvo.

```json
Engine (every missile is a bullet; "projectile":1 is a plain bullet in the tank's list):
 {"name":"Missile","base":"bullet","sides":-1,
  "barrels":[{"flags":{"forceFire":true},"angle":3.1415927,"distance":188,"heightMultiplier":2.4,"bulletType":"bullet","projectile":1,
              "damageMultiplier":0,"penetrationMultiplier":0,"speedMultiplier":0,"bulletSizeMultiplier":0.8,"reloadMultiplier":0.5,
              "spreadMultiplier":0,"lifetime":0.2,"recoilMultiplier":5,"knockbackMultiplier":0,"initialVelocityMultiplier":0.5,"color":27}]}
Seeker: the same plus "turrets":[{"range":2000,"arc":0.4363,"aboveBody":false}] and "mountTurret":0 on the engine
Warhead: "burst":{"onSecondary":true,"onDestroyed":true,"onExpire":true} and a second sub-barrel
 {"flags":{"firesOnDeath":true},"distance":27,"bulletType":"bullet","projectile":1,"speedMultiplier":2,"numBullets":10,
  "spreadMultiplier":10,"lifetime":0.3,"recoilMultiplier":0,"knockbackMultiplier":0,"initialVelocityMultiplier":1.5}
Proximity fuse: a second turret {"range":400,"arc":1.3963,"aboveBody":false} carrying the warhead as an auto gun instead:
 {"distance":68,"startDistance":-81,"mountTurret":1,"invisible":true,"reloadMultiplier":20, ...the same shot, no firesOnDeath...}
Launcher: a plain cannon {"bulletType":"bullet","projectile":0} in the sample; a Skimmer tube (section 8) costs a fifth of the budget
Cluster missile (a DRONE; the second one has the splitter at -90 degrees):
 {"name":"Cluster missile 1","base":"drone","sides":0,"burst":{"onSecondary":true,"onDestroyed":true,"onExpire":true},
  "barrels":[{...the warhead above with "numBullets":4...},
             {"angle":1.5707963,"distance":12,"bulletType":"bullet","projectile":0,"damageMultiplier":0,"penetrationMultiplier":0,
              "speedMultiplier":0,"bulletSizeMultiplier":0.2,"reloadMultiplier":20,"spreadMultiplier":20,"lifetime":0.1,
              "recoilMultiplier":20,"knockbackMultiplier":0,"initialVelocityMultiplier":0.2,"delay":0.1},
             {"angle":3.1415927,"distance":200,"heightMultiplier":2.4,"bulletType":"none","projectile":-1,"color":27}]}
Cluster tube (two of them, one per missile): {"bulletType":"drone","projectile":1,"numBullets":6,"reloadMultiplier":6,"spreadMultiplier":0,
  "lifetime":3,"recoilMultiplier":0,"knockbackMultiplier":0,"numDrones":2,"droneAggressiveCrashRadius":900}
```

**The engine.** A missile is a bullet that pushes itself: a rear sub-barrel (`angle` π) with
**Always fire**, a short reload (0.5) and high recoil (5; 3 or more; lower it to keep more of
the launcher's own speed) firing a shot that does nothing (damage 0, speed 0, launch 0.5, size
0.8) and vanishes in 0.2 s, which is what keeps the tank under the import budget. Drawn 188
long and 2.4 wide in the owner's colour (`color` 27) it is also the missile's body: in the
projectile's frame the bullet counts as a radius-50 hull, so the tail scales with the shot. A
plain cannon firing such a missile costs 65/120 per second at reload 1 (the engine fires once per
live missile); the Skimmer tube's reload 4 brings it to 21.

**The seeker (a heat-seeking missile).** Put an auto turret on the missile, **drawn under the
bullet** (`aboveBody: false`, no disc to see; the engine draws over it), facing 0, and mount the
engine on it (`mountTurret: 0`) still at `angle` π: do not turn the turret round. The turret
turns toward the nearest target inside its `range` and `arc` and the recoil pushes the missile at
it. A manually guided missile is the same engine on a controllable drone instead. Two rules from
the write-up:

- **The arc is measured from the direction the missile was fired**, not from its nose as it
  turns, so an arc-limited seeker can be escaped by moving round it. **Only `arc` 0 (the full
  circle) can chase**, and a chaser needs a short `range`, or it locks on to whatever is behind
  the tank at launch.
- Arc and range together are the missile's **target field**. A large field (wide arc, long range)
  covers more ground but picks a specific target worse; a small one is precise. Wide arc with
  short range, or narrow arc with long range, work best; with a wide arc let the recoil, not the
  launcher's speed, do the driving. The sample: 25 degrees of arc and 2000 of range.

**The warhead (an explosive missile).** `burst` on the missile (right click, destroyed,
expired: any or all) and a `firesOnDeath` sub-barrel that fires the payload as it dies. The
cheap payload is **one short barrel with high spread and many bullets per shot** (10 at spread
10); the consistent one is several short accurate barrels round the bullet, which can be
`invisible` and placed anywhere, give a full-circle burst and cost more entities; spinning the
bullet randomises either. Keep payload barrels **very short** (27 here) or they clip through
and fire behind what the missile struck. The payload's launch speed and bullet speed set how
fast the burst expands and its lifetime how far: fast (2 and 1.5) and brief (0.3 s) hits hard and
costs little. Bullets or traps work for a burst; drones only for a right-click payload on a
missile that stays alive (`flags.firesOnSecondary` on the payload barrel instead of `firesOnDeath`).
The player who sent this could not make a payload mounted on the seeker turret itself work (as
of 2026-10-05): keep it on the bullet, or on its own turret as below.

**The proximity fuse (a flak missile).** A second, tighter turret (`range` 400, `arc` 80) with
the payload as its **auto gun** (`mountTurret: 1`, invisible, 68 long starting at -81 so it
sits across the missile, no `firesOnDeath`): a turret gun on a projectile fires by itself at
targets in its field (section 23), so the missile goes off when something comes close. Its
**reload (20) is the rate limiter**: without it the payload fires again and again for the
missile's whole life; at 20 it is about one blast per missile. The fuse arc must not be wide
(80 or less), or the firing goes wrong. `burst` still ends the missile (onSecondary = a
self-destruct) but fires nothing, since nothing has `firesOnDeath`; the validator says so.

**The cluster salvo (jointly targeted missiles).** Several missiles fired **at
once** (nothing splits off a parent in flight: a spawned shot can carry nothing, section 5), each
bursting into `shards` bullets. The missiles are **drones**, which keeps the per-second budget
at nothing (drones count against the 96 and room, not per second) and lets one barrel fire a
whole salvo: `numBullets` 6, `spreadMultiplier` 0 and `recoilMultiplier` 0 written on the drone
barrel. The editor's form hides those three for a drone barrel, but its import reads them, its
export writes them and the game obeys them (checked in the editor's code 2026-10-05); the
write-up's trick is to set them while the projectile is a bullet, then switch it back to a
drone. Each missile carries a **splitter**: a sideways sub-barrel (+90 degrees on one tube's
missile, -90 on the other's) with recoil 20 and spread 20, a harmless 0.2-size 0.1 s shot, reload
20, `delay` 0.1, so a tenth of a second out every missile is kicked off the line and the salvo
fans out. The splitters have no flag: on a drone a plain sub-barrel fires on the owner's click
(section 9), so **hold left click** after firing or the salvo never splits. The tubes need **spread
0 and knockback 0** or the missiles drift apart before the splitters act. The limit is the
**64 per volley**: two tubes x 6 missiles x (1 + 4 shards) is 60 of it (the validator prints
58, counting the splitter shot too). Open: what `numDrones` 2 does when 6 are fired per shot.

## 34. Custom bosses: a boss copy, two brains, five behaviours, the rotation

**Confirmed (editor code) 2026-10-06; the worked example is the game's own export of its six bosses
(`ref.py spec 1b`; `references/stock-bosses.diep-pack`); nothing played yet.** A boss is a pack-level
record that wraps a tank (spec §1b). Build the tank as usual (a figurative build with the whole
toolkit: parts, turrets, drones, a trail), then add the record:

```python
d = Design("Headless Horseman", level=1, author="☀️", boss=True)   # boss=True: editor.boss, out of the tree
... parts, jaws, spawner, cannon ...
d.pack.boss(d, name="Headless Horseman", brain="simple", behaviour="charge", idle="wander",
            size=2.5, health=6000, xp=50000, ring=(0, 0.4), weight=1,
            message="Hoofbeats... the Headless Horseman rides!")
d.pack.boss_rotation(every=30, first=10, max_alive=1)                  # optional: the lobby's clock
```

What the JSON carries, sparse like the game's own records: `{"tank":100001,"name":"Headless
Horseman","spawnMessage":"…","maxHealth":6000,"xpBounty":50000,"scale":2.5,"ai":{"aggressiveCrashRadius":1500}}`
plus `"editor":{"boss":true}` and `statsMaxLevel` all 7 on the tank.

**Sizing against the stock bosses.** The five lobby bosses are `scale` 1.55 (Guardian), 1.72
(Summoner, Defender), 2.09 (the Fallen pair) at **3000 health**, and Decade 2.87 at 10000 / 100000
score. Health does not grow with scale, so a scale-4 record at 3000 is a big, soft target: 2–3 at
4000–8000 health is boss-grade for a sandbox lobby; keep the figure's own `baseHealth` and
`baseBodyDamage` stock (the record's `damageOnTouch` 10, Fallen Booster 12, is the body damage).
Every stat plays at **level 7**, so a boss with a Reload cap of 12 fires like one at 7; the budget
rates it that way. Big parts, strong contrast and few colours survive the scale; fine line art
does not (render with `--boss` and look).

**Which brain.** `simple` (the editor: "drifts, rams, shoots") is the stock bosses' brain: it
drifts, turns toward a player it spots and fires every gun; its turrets and drones fight on their
own. It suits a monster, a vehicle, a thing without a player's cunning. `bot` ("plays like a
player") drives the body's guns like a sandbox bot, with `skill` 0–1 and `retreat` (backs off to
recover under that much health; 0 fights to the death): it suits a rival tank, a duellist, a
"dark version of you". A necromancer boss needs `neutral=False` to raise shapes.

**Which behaviour** (the editor's "When it spots a player", within `spot_range`, default 1500):
- `charge` (and ram, at `charge_speed`): a bull, a horseman, a cannonball with legs;
- `hold` (stop and shoot): artillery, a tower, a sniper's nest;
- `kite` (keep distance `keep=(near, far)` and strafe): a gunship, an archer, a wasp;
- `shoot` (wander and shoot): a patrol, a drifting mine-layer;
- `none` (ignore them: only its turrets and drones fight): a hive, a carrier, a shrine; Decade and
  four of the five stock bosses are built this way, with `spot_range` absent.
Idle is `wander` or `circle` (the map centre at `circle_radius`; 0 = from the map size, the
Guardian's way). `min_level` (15) leaves low players alone; 0 attacks everyone. `faces_forward`
turns the hull to its drift, the way the Guardian and Fallen Booster do.

**The rotation.** `boss_rotation(every, first, max_alive, min_players, stock_weights)` sets the
lobby's clock while the pack is loaded; `stock_weights={"Guardian": 0, …}` keeps a stock boss out,
`hide_stock_bosses = True` removes all five, `hidden_bosses = ["Summoner"]` some. A record with
`weight=0` spawns only by `spawn_boss <name>` (the name lower-cased without spaces). Bosses spawn
on their own only where **Boss Auto-Spawn** is on (the sandbox admin panel); say so in the
delivery. A boss from a **stock tank** needs no tank in the pack: `pack.boss("Octo Tank", size=4)`.

**Open in play** (spec §13 item 22): the simple and bot brains with custom guns; `minDamageMultiplier`
(4 on the stock records, 6 on Fallen Booster; a damage floor is the guess); whether a boss copy's
cursor pivots and living limbs do anything under an AI driver (expect living limbs to track
targets, cursor pivots to rest).

## 35. Parts that ride parts: moons, a wheel, a gun ring, a chained tail

**Confirmed (editor code) 2026-10-06; orbiting in play is a Phase-3 test.** `shape(ride=carrier)`
puts a part on another part (`mountPart`, spec §8): its offsets are measured from the carrier's
centre along the carrier's angle, so a spinning carrier swings everything on it round. Chains nest
four deep (a root part and four riders); a rider is **looks only** (its hitbox is cleared on
import), so put `collidable` on the carrier. Barrels ride parts too (`rod(ride=…)`, `weapon(ride=…)`).

```python
planet = d.shape(0, 40, at=(-70, 0), color=C.indigo, name="planet")
d.orbit(planet, n=3, radius=60, size=10, color=C.yellow, spin=0.03, name="moon")   # spins the planet
hub = d.shape(0, 1, at=(0, -60), name="wheel hub")              # an invisible hub for a lantern wheel
d.orbit(hub, n=6, radius=45, sides=4, size=8, color=C.orange, spin=0.05, name="lantern")
d.gun_ring(plate, n=4, radius=40, auto_fire=True)                # guns on a spinning plate
```

Uses: moons and electrons; a clock (two riders of different radii on a slow hub, or two hubs with
different spins); lanterns, bells or gondolas on a wheel; a halo of motes without drones (so it
costs no budget); a chained tail of beads that spins as one piece (riders on riders, four deep);
an eye whose pupil rides the eyeball and a brow that rides the eye. A rider's `aboveBody` and
`order` place it in the draw sequence like any part. **A gun ring** (`gun_ring()`, the game's
change notes' "rotating gun ring") is an open question: the editor's budget counts riding barrels
as firing and the notes say they fire, but the editor's tooltip on such a barrel says "Looks only;
it fires nothing"; `save()` notes it, the probe pack tests it. Spin rates: 0.03 per tick is a turn
in about 8 s; 0.1 is brisk; a planet at 0.01 drifts.

**Fixed rotation** (`shape(fixed=True)`, spec §8) keeps a part's **angle** in the world while the
tank turns ("like a dominator's base", the editor). Only the angle is fixed: a part off the centre
still swings round with the aim, so a fixed part sits at the centre: `base()` for a dominator-style
square under the hull, `compass()` for a needle over it (a needle that always points north is a
tell for a navigator, a ship, an explorer). A fixed part may also spin? No: the editor's Rotation
choice is one of With the aim / Fixed / Spins.

## 36. Exact colours: true-to-subject palettes, and opacity as an offer

**Confirmed (editor code) 2026-10-06; opacity in play is untested.** Every `color` takes a hex string
`#rrggbb` or `#rrggbbaa` besides the palette (spec §10): `C.rgb(230, 120, 40)`, `C.rgba(255, 255,
255, 0.35)`, `C.alpha(C.cyan, 0.5)`. The editor shows them as Custom color with Hex and Opacity.

- **Default to the palette.** Players read the stock colours (yellow food, pink crashers, grey
  barrels, Fallen grey bosses), the picker's names are what a tester can say back, and the team
  recipe (a team hull under a same-size cover) is simpler with a palette hull.
- **Reach for hex** when the subject has a colour the palette lacks and a fan would notice: a
  brand or a flag, a real animal's coat, a film character's suit, a themed arena whose shapes
  already use hex. Keep the set small (two or three exact colours plus the palette) and offer it in
  the one question ("exact colours or the palette?") when the subject does not settle it.
- **27 on a hex hull**: parts at 27 take the hull's colour, as with a palette hull (the editor's
  preview does so; play expected to match, Phase 3). Team accents on a hex-coloured figure keep the
  recipe of spec §10: team hull, same-size cover in the exact colour, 27 details.
- **Opacity** (a ghost, glass, smoke, a shadow, water): the editor stores and shows it; whether the
  game draws a translucent part is unknown, so it is an **offer marked untested**, never a default,
  and the recap says so. The validator warns on every alpha until it is confirmed.
- The new swatch **Fallen** (17, `#C0C0C0`) is the stock Fallen bosses' grey: a "fallen" or
  undead tank line, armour, stone.

## 37. A brood of mixed hatchlings, and shots in a forced colour

**From the game's own Decade (2026-10-06); High for the pack format, open in play for a custom
pack.** Decade's five drone barrels each carry `projectile: [0, 1, 2, 3, 4, 5, 6, 7]`, eight minion
types from one barrel, so one spawner hatches a mix. In a design: three drone projectiles, one
barrel with `projectile=[a, b, c]` and `numDrones` for the whole brood. The editor imports the list
as a primary plus alternatives of the same base (at most 16), the budget counts the costliest, and
each shot rolls one. Pair it with `lifetime` ranges (recipe §31) for a nest that hatches different
things at different times.

Decade's and the Fallen bosses' barrels also carry `forcedBulletColor` with `flags.forceBulletColor`
(spec §7): the shot takes that colour whoever fires it, which is how each stock boss's drones wear
the boss's colour even when the record is on another team. The editor keeps the pair raw (no form);
a projectile's own `color` is the usual way to colour a shot, and which wins when both are set is a
Phase-3 question. Summoner's barrels carry `droneSides: 4` the same way; prefer the projectile's `sides`.
