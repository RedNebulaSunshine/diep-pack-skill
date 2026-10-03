# Figurative tanks: building a subject out of parts

How to turn "a tank that looks like a dragonfly / dragon / crab / starship" into a pack.
Mechanics live in `recipes.md`; this file is about *shape*. Everything here is built with
`scripts/compose.py` and checked with `scripts/render_pack.py`; `scripts/ref.py api` lists its
calls (and `ref.py api <call>` prints one in full) without loading the source.

## 1. The building blocks

Everything the format can draw, in tank units (hull radius 50, barrel 95 × 42). All rows
are Confirmed in `references/schema/` unless marked.

| Primitive | Made from | Placement | Notes |
|---|---|---|---|
| Regular polygon, any side count | `bodyShapes[]`, `compose.shape()` | centre (x, y), rotation, circumradius | Squares are axis-aligned at angle 0 (vertex at 45°); every other polygon has a vertex at angle 0, so a triangle at angle 0 points forward. Size defaults to 25. |
| Star polygon | shape with `star: true` | same | 2 × sides vertices, inner radius **0.4 × size**, points at odd multiples of π/sides (confirmed in three human exports). Sparkles, glitch bursts, spiked plates, suns. |
| Circle | shape with `sides: 0` (or 1) | same | Confirmed a circle (exports). Eyes, pupils, joints, rings. |
| Rectangle / trapezoid | decorative barrel, `compose.rod(a, b, width, end_width)` | any two endpoints | Up to 500 long; width 42 × multiplier (0.1–2.5 confirmed); taper 0.04–7.5 confirmed (needle points, wide fans). May cross the hull centre. Draws **under** the hull unless `above=True` (`flags.aboveBody`). |
| Line | `compose.line(a, b, width=5)` | endpoints | A hair-thin rod over the hull: mouths, brows, scars, seams, vein lines. Under ~8 wide it is outline only, so pick the colour for its 72 % stroke (Charcoal reads as black, White as light grey). |
| Disc, any radius and colour | `turrets[]` (`baseSize`, `color`) | centre (x, y) | Drawn by the game; it turns to face targets (or the cursor, or nothing: `range: 0`). Radius 1 hides it; 30 White is an eyeball; 10 in the owner colour is a joint. |
| Hull | `body` | origin | Circle of radius `size`, or a polygon drawn at **1.3 × size** (with `angle`). Paints over everything except `aboveBody` shapes, `flags.aboveBody` barrels and turrets. Size 5–8 makes it vanish behind the parts. |

Fixed facts that decide what you can and cannot make:

- **Layering.** Parts paint in ascending `order` (compose uses creation order: later on top).
  The hull then paints over all of them except what is marked above it: shapes with
  `above=True`, rods/weapons with `above=True`, turrets. So a wing or leg that crosses the
  hull is either drawn under it (design the hull as one body segment and attach everything
  to its rim) or raised above it (a fan of dark rods over the body, like a wing). Parts
  mounted on a turret draw under its disc unless `above=True`.
- **Outline.** Every part gets a dark outline of 7.5 units (72 % of its fill colour). Parts
  under about 8 units across become outline only. Two touching parts of the same colour
  still show a seam; hide seams under a small "joint" polygon drawn later.
- **Team colour is required** (players must tell teams apart): every tank shows a team-coloured
  area and every damaging shot carries the team colour. Part colour 27 takes the **hull's**
  colour, so leave the hull team-coloured and cover it exactly with a same-size `above=True` face
  shape (drawn before the face details); then accents at 27 follow the team. Shots: leave `color`
  unset; for a figure in a fixed colour (a black cat, a white egg-like ghost) cover the team disc
  with a size-50 `above=True` part and add small 27 parts as the team highlight (Confirmed
  2026-09-30, spec §10). Keep the team subtle where the figure's own colour matters (eggs white).
- **Colour.** Palette indices only (spec §10, `compose.C`). About 18 distinct colours; no
  gradients or transparency. 27 takes the owner's team colour, and **3–6 are team slots that
  end up following the player's team too** (tested 2026-09-26): `C.red` is 9 (Salmon), `C.green` is 13
  (Mint), `C.blue` is 2, all fixed; `C.team_red` etc. exist for deliberate team tinting.
  `compose.C` carries the editor's swatch names (White, Box, Cannon, Charcoal, Crimson,
  Salmon, Orange, Brown, Yellow, Shiny, Mint, Forest, Cyan, Teal, Blue, Indigo, Periwinkle,
  Plum, Pink); use those names in recaps.
- **No ellipses, curves, free polygons or per-vertex control.** A curve is a chain of
  polygons or a strip of short rods. A tapered limb is a trapezoid (rod with `end_width`).
- **Everything on the tank moves as one rigid body** and turns with the aim, except turrets
  (tracking enemies, following the cursor, or fixed) and what rides them, and spinning
  parts. What is *not* on the tank can trail: stationary bullets left behind (§5).
- **Coordinates run in the hundreds.** The official pack uses offsets up to 221; human packs
  reach 320. **The editor keeps 32 body shapes and 32 barrels per tank** and silently drops
  the rest (the croc's 42 shapes came out as 32, pupils missing; spec §9c); the most turrets
  seen is 7. Spend shapes on what reads at a glance (teeth, eyes, plates) and put line art in
  barrels; `save()` warns and the validator errors over the cap. **And 96 pieces in all per tank**, counting the
  projectiles' parts, sub-barrels and turrets too (spec §9c): a drawn companion or shot eats hull art.

## 2. Workflow

Do the design on paper (in the reply, briefly) before writing the script.

1. **Choose the view.** The game is top-down and the tank faces its aim, which the
   renderer draws as *up*. Pick subjects with a strong overhead silhouette: insects,
   spiders, crabs, fish, rays, birds, bats, dragons in flight, aircraft, ships, snowflakes,
   flowers, gears. A side-view subject (a horse, a person) needs a top-down proxy; say so
   and offer the closest thing.
2. **Set the size budget.** Hull 30–50. Whole figure 300–600 across. Smallest part 8–10.
   The hitbox is the hull (it scales with `body.size`: a size-8 hull collides at a dot) plus
   any part marked `collidable=True`, which collides at between half and two thirds of its
   drawn radius (a 120 octagon made contact at 60–80; confirmed 2026-09-26). Everything else
   is picture only, so a big figure is a bigger *picture* unless its main mass is collidable;
   to give a figure a hitbox of radius R, mark a part of size about 1.5–2 R collidable.
3. **List the anatomy** and map each part to a primitive:

   | Feature | Build it as |
   |---|---|
   | Body segments, abdomen, tail, neck, tentacle | `chain(points, sizes=(big, small))` along a `bezier` or `arc`, hexagons or octagons; alternate two shades for stripes |
   | Head | one polygon in front of the hull, overlapping it by a few units; or the hull itself with a face drawn on it (§7) |
   | Eyes | two small 8-gons drawn after the head, charcoal or white; an eye that *looks* at enemies is `eye(at)`: a White turret disc with a pupil riding it |
   | Mouth, brows, scars, seams | `line()` / `polyline()`: hair-thin rods over the hull (Charcoal for black) |
   | A biting mouth | `jaws(at, rest, arc, length)`: two cursor-following pivots carrying jaw bars, teeth, fangs and bite points |
   | Hands, a held sword, brush or broom | `cursor_pivot(at)` and mount the item on it (`rod(turret=i)`, `shape(turret=i)`) |
   | A long body or tail that trails behind | `trail(seconds, size, sides)`: stationary bullets dropped behind the tank (the only thing in the format that bends) |
   | Rings, bezels, bevels, a gem in a setting | concentric polygons in alternating shades drawn largest first (several player-built packs) |
   | Wings, fins, sails | `strip([root, mid, tip], widths=[narrow, wide, narrow])`, white or silver; two pairs for insects; a `spokes` fan for feathered wings |
   | Legs, antennae, whiskers | thin rods (width 6–10), always `mirror`ed; draw them first so the body covers their roots |
   | Jointed legs, arms, tentacles | `limb(points, widths)`: a strip plus a polygon at every bend, drawn after the rods so the mitre seam is hidden (crab, spider) |
   | Irregular filled areas: bat wing, fish tail, cape, fin | `fan(apex, outline)`: tapered rods from one point to an outline, overlapping into a solid; the seams read as veins or feathers |
   | A claw, gun pod, nacelle, head: anything with several parts at an angle | build it once in `with d.frame(at, angle):` in its own coordinates, then `mirror()` the parts |
   | Claws, mandibles, horns | two tapered rods in a V, or triangles pointing outward (`angle` = outward direction) |
   | Spikes, thorns, teeth | `ring` or `spokes` of small triangles around a rim |
   | Shell, carapace, armour plates | a large `above=True` polygon over the hull, or overlapping polygons in two shades |
   | Joints, knuckles, eyes on stalks | small polygons drawn after the rods they cover |
   | Jets, nacelles, gun pods | rods with `end_width` flare at the back |

4. **Plan layers.** Roots of limbs under the body, body over them, details (eyes, plates,
   stripes) last. Anything that must show on top of the hull is an `above=True` shape.
   **Name every part** as you go (`name="fore wing"`, mirrored copies become "fore wing
   right" / "fore wing left"); the editor lists parts by these names and so do your
   recaps and test instructions.
5. **Pick two or three colours.** Body in one hue with a second shade for stripes,
   membranes white/silver, hard parts charcoal. The automatic outline does the rest.
6. **Make the weapons part of the anatomy**, never bolted on: mandibles, a stinger
   spawner in the tail, claw cannons, eye turrets, exhaust launchers. Use the presets in
   `mechanics.py` (`d.destroyer(...)`, `d.spawner(...)`, `d.swarm_spawner(...)`,
   `d.auto_turret(...)`; full list in `recipes.md`): each carries the stock tank's numbers,
   takes the same geometry arguments as `weapon()` (angle, offset, gap, length, width), works
   inside a `frame`, and accepts any spec field as an override. `right_click=True` moves a
   system to the right mouse button and writes the help text. Keep it to one or two
   mechanics per tank.
7. **Build, render, critique, repeat** (at most three passes). Run the script. `save()`
   prints a `HIDDEN` line for every part the hull would swallow and the figure's overall
   span (check it against the size budget). Then open the PNG under `output/renders/` and ask: is the silhouette recognisable at thumbnail size?
   Is it symmetric where the subject is? Does the hull swallow anything? Any stray seams
   or parts floating unattached? Proportions right (a dragonfly's abdomen is longer than
   its wings; a crab is wider than long)? Fix the script, not the JSON.

## 3. Worked example: Dragonfly (`assets/archetypes/dragonfly.py`)

29 parts, one weapon mechanic (alternating mandibles), off Tri-Angle at 45.

| Feature | Parts | How |
|---|---|---|
| Thorax | hull | circle 34, forest green |
| Legs | 6 rods | three `rod`s of width 8 from the thorax rim, `mirror`ed, drawn first |
| Wings | 8 rods | two `strip`s per side, widths 28→44→14 and 30→48→16, white, `mirror`ed |
| Abdomen | 9 hexagons + triangle | `chain` along a `bezier` from x=−36 to −268, sizes 19→8, every other segment lighter green, triangle at 180° as the tail tip |
| Head, eyes | 3 polygons | hexagon 25 at x=54, two charcoal 8-gons at (62, ±15) |
| Mandibles | 2 barrels | `weapon` at ±10°, gap 58, length 42, width 14, taper 0.7, `delay: 0.5` on one |

Render: `output/renders/dragonfly-dragonfly.png`. The script is the source; the pack is
build output. Imported into the editor 2026-09-26: its SVG export (its editor SVG export)
matches the render on every element, so what `compose.py` places is what the game draws.

### 3b. More worked subjects (`assets/archetypes/`)

Each is an archetype to copy from; all render under `output/renders/`.

| Subject | Archetype | Parts | What it demonstrates |
|---|---|---|---|
| `crab.py` (confirmed in game 2026-09-26) | wider than long, bilateral, limbs everywhere | 43 | `limb()` legs; a claw built in a `frame()` (palm, fixed pincer, and a Destroyer barrel as the moving pincer), then mirrored; the right claw fires on left click and the left claw on right click (`flags.firesOnSecondary` set on the mirrored copy); side lobes under the hull that widen the carapace |
| `starship.py` | vehicle, long axis, hard geometry | 21 | a nacelle assembled in a `frame()` and mirrored; `twin()` phasers, a glider-style `missile_launcher(right_click=True)` torpedo, an `auto_turret()` dome aft; the bridge in owner colour (`C.owner`) so the team colour still shows on a silver hull |
| `spider.py` (confirmed in game 2026-09-26: fangs alternate, spiderlings stream, shins pump in two phases; the pumping shins need a 24-wide base, and thighs pumping under their knee joints showed nothing) | radial-ish limbs, big rear mass | 35 | eight `limb()` legs with `animate()` so two pairs pump out of phase while firing; `above=True` eyes on the hull; inward-angled fang cannons; a `swarm_spawner()` at `gap=146` so the spinneret sits at the tail, with a custom charcoal `drone()` projectile |
| `dragonfly-flap.py` / `-tail.py` | long axis, wings | 29 / 28 | piston wings, pendulum tail (§5) |
| `croc.py` (level 60 off Smasher; first build refused for firing too much, see spec §7a) | a head with a long split snout, a trailing tail | 60 | two cursor pivots as a crocodile's jaws with White teeth and click-only bite points (no `forceFire`, so the jaws are picture only and bite only while held); `eye()` pair; `line()` brows; a cursor-pivot hand holding a martini glass; `animate()`d 24-wide legs that paddle and puff White specks; `trail()` with Mint `end_color`; stat caps 12 |
| `president-prism.py` | a portrait: a face painted on the hull (§7) | 42 | Face art: Charcoal hair as a `chain` of circles over the crown, `eye()` turrets whose pupils track, `line()` brows, a `polyline` smile over a row of White teeth, suit and ears under the hull; seven `cannon()`s fanning from a White "prism" triangle, each with its own coloured bullet |
| `x-wing.py` | vehicle, wide crossed wings, many systems on two buttons | 43 | four wingtip `cannon()` lasers with `delay` 0/0.25/0.5/0.75 for sequential fire; four engine `cannon()`s built in `frame(angle=180)` with Booster recoil 2.4 and `right_click=True` for an afterburner; a Rocketeer `missile_launcher(right_click=True)` torpedo under the chin; a size-16 hull hidden under the fuselage with a `collidable` wing-root square as the hitbox; an `eye()` as R2-D2's dome |
| `serpent.py` (built from the human creature pack; confirmed in game 2026-09-26: the body trails like a snake and tapers, the jaws close while left click is held and bite, the pupil tracks) | a head whose body trails behind it | 25 | `jaws()` (cursor-following biting mouth with contact-damage teeth), `trail()` (hexagonal stationary bullets dropped behind for two seconds, tapering), `eye()` (a tracking eyeball with a pupil), `line()` brows; smasher-style stat caps since it fights by biting |

Sizes for scale: hull 32–58, figures 180–410 long; the spider and crab are about 360 wide.

## 4. `compose.py` at a glance

| Call | Makes |
|---|---|
| `Design(name, level, parents)` / `Pack(name).tank(...)` | one tank / a multi-tank pack |
| `hull(sides, size, color, angle, star, spin)` | the body |
| `shape(sides, size, at, angle, color, above, spin, name, star, turret, mount, stays_visible)` | one polygon; `circle(size, at)` = sides 0; `turret=i` / `mount=i` rides a turret / barrel |
| `part(sides, size, at, ...)` | a shape dict for a projectile: `projectile(parts=[part(...)])` decorates bullets and drones |
| `rod(a, b, width, end_width, color, name, above, turret)` | trapezoid between two points (decorative barrel); `above=True` draws it over the hull |
| `line(a, b, width=5)` / `polyline(points)` | line art over the hull |
| `rod_polar(angle, length, gap, offset, width)` | rod in editor terms |
| `chain(points, sizes, sides, color, name, follow)` | polygons along a path |
| `strip(points, widths, color, name)` | rods along a path with widths at each point |
| `limb(points, widths, joint, ...)` | strip plus joint polygons at the bends, drawn after; returns `(rods, joints)` |
| `fan(apex, outline, base_width)` | tapered rods from a point to an outline, overlapping into a filled region |
| `with frame(at, angle):` | everything created inside is placed at `at`, rotated `angle`; nests; weapons and turrets too |
| `ring(n, radius, sides, size, ...)` / `spokes(n, length, gap, width, ...)` | radial repeats |
| `mirror(part or list)` | copies across the aim axis |
| `projectile(...)`, `weapon(projectile, angle, offset, length, gap, width, muzzle, above, invisible, auto_fire, **fields)` | real barrels; `invisible=True` fires unseen, `auto_fire=True` fires without a click |
| `turret(at, angle, arc, range, controllable, above, size, color)` | auto-turret; `weapon(mountTurret=i)`, `rod(turret=i)`, `shape(turret=i)` ride it; `size` is the disc radius, `range=0` = no auto-targeting |
| `pendulum(at, angle, arc, cover_color)` / `cover(i)` | arc-limited swinging pivot with an automatic cover polygon over its grey disc |
| `cursor_pivot(at, angle, arc)` | a pivot that follows the cursor: hands, held items, jaws |
| `eye(at, size, pupil)` | an eyeball turret with a pupil that looks at the nearest enemy |
| `jaws(at, rest, arc, length, teeth)` | a biting mouth on two cursor pivots with contact-damage teeth |
| `trail(seconds, size, sides, taper)` | stationary bullets dropped behind the tank: a body that follows |
| `contact_damage(at, damage, turret)` | an invisible auto-firing point that hurts what touches it |
| `turreted_bullet()` | a bullet carrying its own auto-turret that shoots in flight (confirmed) |
| `animate(rods, phase)` | turns decorative rods into speck-firing pistons (§5), `phase=0.5` for the other half of a pair |
| `twin() sniper() destroyer() spawner() swarm_spawner() trap_launcher() missile_launcher() auto_turret() side_turrets() smasher() stealth() …` | stock weapon systems with the real numbers (`mechanics.py`; table in `recipes.md`); `auto_fire=True` on any of them |
| `set(**tank_fields)` | statsMaxLevel, helpText, speedMultiplier, invisibility … |
| `Pack.custom_shape(...)`, `Pack.starters`, `Pack.hidden`, `Pack.hidden_shapes` | arena shapes and total-conversion packs (spec §1, §1a) |
| `save()` | writes `output/<slug>-<version>.diep-pack` (SKILL.md §5a; `Pack(..., version=...)`), validates, renders PNGs, prints the part table, `HIDDEN` parts and the span |

Paths: `arc(center, r, start, end, n)`, `bezier(p0, p1, p2, p3, n)`, `line(a, b, n)`,
`polar(r, deg, at)`. Angles are degrees clockwise, 0 = forward, y positive = tank's right.

## 5. Motion: what can move, and what cannot

The tank itself is one rigid sprite; what bends or trails is made of bullets left behind it.
**Give every tank some movement unless told not to**: a still figure
reads as a sticker. Cheap moves that cost no shape: `forceFire` on `animate()`d legs so they
paddle on their own (the croc), a pendulum pivot under a limb so it swings on turns, brows
mounted on an `eye()` turret so they move with the gaze, a `spin` on a wheel or gem. For
sparkle, make the piston specks spinning star bullets (`d.projectiles[d.speck()].update(sides=4,
star=True, spin=0.3)` and a bigger, slower, scattered speck on the rods) or add one invisible
auto-firing "sparkler" barrel throwing spinning Yellow stars (the croc, about 5 shots/s each).
**Every moving trick below is a firing barrel and spends the import budget** (spec §7a): the
lobby refuses a tank over 120 entities per second or 250 alive (plus room, volley, drone and
piece limits), every barrel and live sub-barrel counted with every trigger held at the tank's
Reload cap: with caps of 12, 12.5/s at reload 0.25, 8.3 at 0.5, 4.2 at 1; with caps of 7 about
three quarters. Pistons, bite points and trail droppers add up fast; the croc (caps 12) was
refused twice (196/s with ten bites, four legs and a trail; 121/s with six bites at 0.5), while
the serpent's Reload cap of 0 makes its eight fast barrels cheap. The validator's figures are
exact, so plan to the limit in the design sheet: `save()` prints them. **Drawn and armed
projectiles spend it too**: every shot counts as 1 + everything its projectile carries (parts,
rods, guns, turrets), so a web of 24 rods fired 3.4 times a second was refused at 437 in the
air, and a building that lives 27 s counts its guns once per live copy (132/s refused). Set
the Reload cap to 0 on such tanks, as a player-built pack does on 47 of its 60 playable classes.
The engine offers exactly these movements (stock mechanics; the last four rows come from packs built by other players):

| Movement | Mechanism | Use it for | Status |
|---|---|---|---|
| Piston pump on each shot | any barrel that fires (`bulletType` bullet/trap/drone) | flapping wings, pumping legs, pistons: make the part a firing barrel whose shot is a harmless speck (`d.animate(rods)`; the `dragonfly-flap` test build: damage 0.01, size 0.15, lifetime 0.1, recoil 0). `delay: 0.5` puts pairs out of phase. Only while the player fires (or auto-fire). **Two conditions for the pump to show** (the `pump-test` test build, `pump-test-2.py`, 2026-09-26): the barrel must be at least about 22 wide (22, 28 and 42 pump plainly; 12 is "almost imperceptible" whatever its length or gap; recoil, bullet size, speed and damage change nothing), and its **muzzle end must be exposed**: the travel is along the axis, so a joint polygon or any later part painted over the tip hides it, as the hull hides the root end. Animate the **last** segment of a limb (shin, hand, wingtip): its tip is free and the movement is at the end, which reads naturally; give it a wide base (widths like `[24, 24, 8]`). **Thin and moving are at odds**: a limb is either slender (6–12) and still, or about 24 wide and pumping; when a request wants delicate legs that move, say so and offer the choice. `limb(exposed=i)` is for the rarer case of animating an inner segment; `save()` prints `PUMP HIDDEN` when an animated rod's muzzle is covered. | **Confirmed** 2026-09-26: wings pump, pairs alternate, the white specks read as sparkles; 22-wide spider thighs under knee joints showed nothing until exposed |
| Continuous rotation | `spinSpeed` on a shape or the hull | propellers, gears, saw blades, orbiting moons | Confirmed |
| Tracks the nearest enemy (any turret, weapon or not) | turret (`turrets[]`) holding decorative rods and/or weapons via `mountTurret`; no `arc` | a head that looks at threats, eyes on stalks, a stinger, an antenna that points at danger. Draws over the hull by default; a grey disc marks the pivot. | **Confirmed** 2026-09-26 (the `dragonfly-sting` test build) |
| Pendulum: lags the body's turns, settles back | the same turret with a narrow `arc` (about 20°) around a rest `angle` pointing away from where enemies usually are (straight back) | a tail, mane, cape or trailing antenna that swings out when the tank turns and drifts back to rest: the closest thing to "flowing" this format has. Targets inside the wedge still pull it (an armed one fires at them). | **Confirmed** 2026-09-26 (the `dragonfly-tail` test build) |
| A jointed chain (segment carries the next) | **not possible.** Turrets cannot be mounted on turrets or barrels: a `mountTurret` on a turret is ignored and the turret lands at its raw offset (the SVG export of a three-turret chain test). Barrels on a turret do follow it, and barrels on barrels follow their base, but none of those rotate by themselves. | | tested 2026-09-26 |
| Loose parts that orbit and bob | uncontrolled drones (`droneControllable: false`, projectile `drone.controllable: false`), projectile `sides`/`color` to match the body, small `droneAggressiveCrashRadius` to keep them near | satellites, fireflies, a bubbling cloud, a halo of shards: things that live *around* the tank. **Not a tail**: at rest they orbit and bob around the hull centre; when moving they trail in a leapfrog conveyor (the last one jumps forward to the body), so nothing reads as a chain. They chase shapes; tanks less so. `preSpawn` did not make all eight appear at once. | tested 2026-09-26 (the `dragonfly-swarm` test build) |
| **A body that follows the path** (snake, worm, comet tail, ink trail, footprints) | `d.trail()`: an invisible auto-firing rear barrel dropping **stationary** bullets (`speedMultiplier` 0, `initialVelocityMultiplier` 0, `lifetime` 2, reload 0.25, size 2). Each segment stays where the tank was, so the chain traces the path and bends round corners; `taper` chains a smaller bullet on expiry so the tail thins; `end_color` colours those end pieces. With `end_force_fire` (default, the serpent's flags) the end pieces also shimmer out from under the living segments, a soft fade; without it the tail steps hard from segment to end piece. `stages=[…]` gives a graded taper with one dropper per size and growing lifetimes (the croc: four hexagon sizes with Mint ridges, then a triangle tip); a spawned piece cannot spawn the next, so chains beyond one step never show (spec §5). Segments are bullets: the owner's colour, any `sides`, with health, and they damage and block enemies. At rest they pile up under the tank. | **Confirmed** 2026-09-26 (`assets/archetypes/serpent.py`, both flag variants) |
| Follows the cursor **while fire is held**, not enemies (hands, a held brush or sword, jaws) | `d.cursor_pivot()`: a turret with `range: 0` and `controllable: true`, arc-limited; mount rods, shapes and weapons on it. It rests at `angle` until the player holds left click, then swings to the cursor within `arc`; release and it returns to rest. So a pivot is a two-state part: rest pose, held pose. What it carries (nothing, a player gun, an auto gun) changes nothing, except that a **right-click** gun on it never fires (SpongeBob, 2026-09-28: put it on the hull where the item rests); always give it an `arc`, since a free pivot wanders when released; it lets go of the cursor once the cursor leaves the wedge or passes the tip. A rest angle of 0 (a player-built skeleton's floating hands) looks like "always follows" only because the hull faces the cursor. | every tank of a player-built character pack holds something this way; the serpent's jaws | **Confirmed** 2026-09-26 (serpent, the `pivot-test` test build) |
| **A mouth that opens and bites** | `d.jaws()`: two cursor pivots at (40, ±20) resting at ±45° (mouth open) with ±60° of travel. Hold left click and each pivot aims at the cursor from its own spot, so both bars swing forward and the mouth closes (parallel, teeth interlocked); release and it falls open. `arc` must be ≥ `rest` or the jaws can never meet (30° left the serpent stuck 15° open). Three `contact_damage()` points along each jaw's inside (invisible auto-firing barrels dropping a 0.1 s stationary bullet with penetration 20) kill shapes held between the jaws. | the serpent's mouth | **Confirmed** 2026-09-26 (serpent) |
| An eye that watches enemies | `d.eye()`: a White turret disc (`baseSize` 30) with the pupil (`sides` 0, `aboveBody`) mounted 10 ahead of centre, `arc` 90 | the serpent's eye | drawing confirmed; tracking follows from the turret rule |
| **Limbs that react** to enemies *and* the cursor (legs, arms, hands, a plume, a cape) | `d.living_limb()`: a `controllable` turret with a rest `angle`, a narrow `arc` (15°) and an enemy `range` (250; 100 for a plume; unset on the spider's legs, which tracks from further than 250). Turns toward enemies in range while idle and toward the cursor while firing, so every limb twitches at what passes. `d.leg()` puts three tapering rods with star joints on one | a spider's eight legs, a fighter's arms, a king's plume and cape (a player-built pack, 72 tanks): the single biggest reason its creatures look alive | **Confirmed** 2026-09-28 (Limb Lab): tracks shapes within range while idle, the cursor while firing, but only inside its wedge (backward legs ignore a forward cursor); an unset range tracks from further (Leg Range Lab). Whether click pistons pump on a living limb is untested: a 2026-09-30 build whose sleeves and chain links showed nothing had their tips covered by the hands and links under 22 wide (`save()` said PUMP HIDDEN), so read that warning; click guns are confirmed on a `cursor_pivot` (wands, thrown bats, a hinged lid) |
| A leap on right click | `d.dash()`: an invisible backward barrel, harmless shot, recoil 16 | any creature that pounces, a fleeing thief, a charging bull | **Confirmed** 2026-09-28 (Dash Punch) |
| Hits that land only within reach | `d.punch()`: a hidden auto-turret (front cone, range 180) with two invisible stationary fists that fire, hit or miss, while anything is in the cone; `d.blade()`: a line of hits on a click | fists, bites, a sword sweep, a golem's slam | **Confirmed** 2026-09-28 (Dash Punch); `blade` High |
| A creature that **walks by itself** | `d.walker()`: a trap carrying an enemy-tracking turret whose rear recoil barrel pushes it; by default it marches forward and veers toward shapes in its cone; `wander=False` makes it a guard: it sits until a shape comes in range, walks over and kills it, moves on to the next, then sits again | golems, summoned beasts, a homing mine with legs | **Confirmed** 2026-09-28 (Builder Lab: marched, veered, punched, left the map; Golem Wait Lab: `wander=False` waits and hunts) |
| A building that aims and shoots | `d.sentry()` placed with `d.place()`: a stationary long-lived bullet with a turret gun; draw the weapon with `aim_rods`/`aim_parts` so it turns | a ballista, a tower, a turret nest, a totem | **Confirmed** 2026-09-28 (Builder Lab) |
| **A drone that is a character** | `d.figure_drone()`: parts, rods, living-limb arms that track shapes on their own, hidden fists, a self-firing lunge; `d.summon()` keeps two out at all times (a companion, not a click ability) | a twin, chicks that follow a hen, a knight, a familiar with a face | **Confirmed** 2026-09-28 (Summon Lab) |
| A projectile that is a picture | `d.proj_rod()` rods on any projectile; `d.web()`, `d.egg()`. The rods are picture only: the disc and `collidable` parts do the hitting, so scatter up to three small collidable parts where the drawing should catch (`web(hooks=3)`; the editor makes any further ones drawing-only) | a web, a thrown trident, an egg that hatches, a boulder with chips | **Confirmed** 2026-09-28 (Web Lab: drawn in play, only disc and hooks hit; Egg Lab: eggs hatch at rolled times into a shoving yolk and splash) |

## 6. Guesses to verify in game (then update the spec §13)

- More than 70 parts; rods longer than 500; `sides: 2` shapes.
- Resolved by the human exports (2026-09-26): star inner radius 0.4, `sides` 0/1 circles,
  negative `startDistance`, widths 0.1–2.5, tapers 0.04–7.5, `body.angle` applied, 70 parts.

## 7. Lessons from packs built by other players

Six packs by other players (326 tanks) were dissected; every tank matches the renderer, and
`render_pack.py --sheet` of any of them is a picture book. What they do that the stock tanks
never do:

- **Faces on the hull.** A skeleton character: a White hull, two Charcoal squares as eye sockets, a
  small triangle nose, `line()` mouths; teeth as a row of small squares; eyes as stacked
  circles (socket, iris, pupil) with `above=True`. Another pack's eye tank is
  three concentric circles (Plum iris, Border pupil) on a white hull.
- **Line art with barrels.** One tank draws a whole face on a green hull with
  0.1–0.15-wide Charcoal barrels flagged `aboveBody`, some with negative `startDistance`
  so a stroke crosses the centre. Muzzle taper near 0 gives a needle; 7.5 gives a flare
  (a beast skull's horns).
- **Things held in hands.** A `cursor_pivot()` (small disc in the owner colour) at the end
  of an arm, carrying a star (a skeleton's hands), a brush (a painter), a jaw (the serpent). The
  held thing turns toward the cursor within its arc.
- **Rings and bezels.** A boss-shape pack and a hexagon tank line nest
  polygons of the same shape in alternating shades (Yellow, Charcoal, White, Box) drawn
  largest first, giving a bevelled gem or a boss "shell". A polygon hull with a same-sided
  shape inside it reads as a rim.
- **Wings and capes as fans of rods** flagged above the body (a winged character), dark on a light
  hull; `fan()` does this in one call (add `above=True`).
- **Hiding the hull.** `body.size` 5–8 with everything else built from parts ("dual
  portal", "4x speed": chevrons of thin rods). A big `collidable` shape then stands in for
  the body (a boss tank: a White circle of 53 over a White hull). Confirmed: the tiny hull
  collides only at its dot and the collidable shape carries the collision.
- **Glitch and horror looks**: Charcoal star polygons (11 points) as
  bursts, Crimson triangles and circles as eyes, a `staysVisible` blue eye on a stealth
  tank, huge spiky stars (`size` 240) as auras.
- **Decorated and armed projectiles.** Bullets with a triangle riding them, star bullets
  with an eye, spinning cross-shaped bullets (`spin` 0.25 with four circles on a long rod),
  a bullet that carries an auto-turret (`turreted_bullet()`), a drone "familiar" with a
  hexagon body and a big gun (`drone.repel: false` so right-click does not push it away).
- **Damage without a visible gun.** Invisible auto-firing barrels (`invisible: true`,
  `flags.forceFire`) with stationary short-lived bullets: teeth, a "power cell" weak point,
  a beam charged by `delay` 9 then fired as a fast penetration-20 square (a charged skull blaster).
- **Total conversions.** `hidden` listing every stock tank, `starters` naming the pack's
  level-1 tanks, `hiddenShapes` plus custom `shapes` replacing the arena's polygons, tanks
  at level 120 with `editor.disabled` as admin-only.

### 7b. Lessons from a player-built character pack (read 2026-09-28)

The seventh pack is the most inventive: not tanks with faces but **characters**, and every
one of them does something. What it adds (recipes §25–32; all High from the data unless a
lab test says otherwise):

- **Every part that could move, moves.** Legs, arms, hands, a plume and a cape are all
  `controllable` turrets with a rest angle, a narrow arc and an enemy range (`living_limb`).
  Its big spider spends every one of its 8 turrets, 32 barrels and 27 shapes on eight legs
  that each react on their own. Design creatures this way first, then spend what is left on
  decoration.
- **Abilities on the right button.** Almost every class has a right-click move: a dash
  (`dash`), laying eggs (`egg`), throwing a trident, placing a tower or a golem (`place`).
  A tank without a right-click ability feels unfinished next to these. Summoned companions
  (`summon`) are not among them: a drone spawner keeps its drones out whatever the button.
- **Melee is a turret with no gun showing.** "Get close to punch" is the beginner class's
  weapon (`punch`); a sword is a line of hits on a pivot (`blade`).
- **Projectiles are drawings and characters, not dots.** A web of 24 rods on a trap, a
  trident with collidable tines, an egg that hatches into a yolk and a white, a boulder that
  bursts into chips, a chick with a beak turret, a warrior twin with arms and fists and a
  lunge, a golem that walks, a ballista that shoots (`proj_rod`, `web`, `egg`,
  `figure_drone`, `walker`, `sentry`). When a subject has a signature projectile (a spider's
  web, a wizard's fireball, a hen's egg), draw it; `render_pack.py --projectiles` shows it.
- **Copy the owner into the drone.** One warrior's summoned twin reuses his own 24
  shapes and 15 rods verbatim, so the summon reads as "another one of me". In compose, build
  the figure once as part()/proj_rod() dicts and reuse them for hull and drone.
- **The tree is part of the picture** (confirmed with the lab's Folder). Eighteen unplayable folder nodes (`folder`) drawn as
  icons (a pitchfork, a paw) group the 67 real classes under "Human", "Monster", "Animal";
  six of them are `starters`. Levels 1 / 45 / 60 / 100 with `advancesInto` on 45 tanks.
- **Rolls everywhere.** `lifetime: [12, 22.5]` on eggs, `damageMultiplier: [a, b]` on fire
  breath, `projectile: [egg, golden egg]` for a rare drop.
- **Reload cap 0 pays for it all.** 47 of the 60 playable classes set `statsMaxLevel[1]` to 0:
  each web counts as 1 + 24 rods + its hooks against the import limit and the spiders sit at
  247–249 of 250 in the air. Copy the cap with the technique.
- **Limits it proves**: 8 turrets import (two spiders), duplicate tank names are fine (two
  Peasants, two Goblins: the renderer now pairs them in roster order), custom arena shapes may
  omit `maxHealth` or `size`.
