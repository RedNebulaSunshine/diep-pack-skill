# `.diep-pack` quick reference

One page of everything a pack can say. Condensed from `references/schema/` (section numbers
`§N` point there); open the full section when a Medium or Low field matters to the design.
Confidence: **C** confirmed in game, in the editor or in the editor's own code, **H** pinned by
data, **M** inferred, **L** guess. "≤ N" is the editor's import limit: past it the value is
clamped (numbers) or dropped (lists), silently; the validator warns.

## Envelope and units

```json
{"version":2,"name":"My Tank","author":"Your Name","tanks":[
 {"id":100001,"name":"My Tank","minLevel":45,"body":{"sides":0},
  "invisibility":{"gain":0.03076923076923077,"lossOnHit":0.05},
  "statsMaxLevel":[7,7,7,7,7,7,7,7],
  "projectiles":[{"name":"Bullet","base":"bullet","sides":-1}],
  "barrels":[{"bulletType":"bullet","projectile":0}]}]}
```

- One line of UTF-8 JSON, extension `.diep-pack`. Omit fields at default; the block above is
  what is always written (§12). `author` is optional.
- **Angles** radians, clockwise positive, 0 = the aim direction. **Distances** in world units:
  hull radius 50, barrel 95 long × 42 wide. **`lifetime`** seconds. **`spin`, `spinSpeed`,
  `invisibility.gain`** per tick (25 ticks/s). **`delay`** in the barrel's own reload periods.
- Import: the editor takes a whole pack from a file (prefer the file over pasting) and "add to
  this pack" **reassigns tank ids**, so links to other packs are impossible. The engine
  validates on import and aborts on `tank <id> advancesInto unknown id <n>`, on a pack over
  900 KB, and on the import budget below (`fires too much: N/120 per second …`).
- The editor normalises every pack on import (§0): it clamps, drops past its counts, fills in
  defaults, keeps three `collidable` parts per tank and per projectile, and gives a projectile's
  barrel that fires a decorated or armed projectile a plain shot instead.

## Pack (§1)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `version` | int | | always 2 | C |
| `name` | string | | pack name (use the first tank's name; the editor fills in a generic one when missing) | C |
| `author` | string | omitted | display name shown in the editor | H |
| `tanks` | Tank[] | | the tanks; omitted in an arena-only (shapes-only) pack | C |
| `hidden` | int[] | | vanilla tank ids removed from the class tree; alone it empties the tree (total conversion). **Never 0**: the lobby refuses "the base tank cannot be hidden"; a total conversion hides the other 53 and sets `starters` | C |
| `starters` | int[] | | tank ids (vanilla 0 or this pack's level-1 tanks) a player can spawn as | C |
| `shapes` | CustomShape[] | | custom arena polygons (§1a): `id` `custom_shape_N`, `name`, `sides`, `size`, `maxHealth`, `xpBounty`, `damageOnTouch`, `knockbackOnTouch`, hex `color`, `ai.floatSpeed`, `ai.aggressiveCrashSpeed/Radius` (crasher), `spawn.densityMultiplier` (the editor's "spawn weight": square 1, triangle 0.2, pentagon 0.05; a shape's share of the spawns ∝ weight × band width), `spawn.radiusMin/Max` (square rings, 0 centre, 1 edge); design with `references/arena.md`, `editor.replaces` (vanilla kind), `editor.disabled` (writes density 0 and parks the weight in `editor.spawnWeight`). Missing size 50, health and xp 10. Ids are positional (`custom_shape_1…` in list order); ≤ 256 shapes | C |
| `hiddenShapes` | string[] | | vanilla kinds that stop spawning: `square` `triangle` `pentagon` `big_pentagon` `hexagon` `small_crasher` `big_crasher` | C |

## Tank (§2)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `id` | int | | 100001, 100002 … in pack order; below 100000 is vanilla | C |
| `name` | string | | display name | C |
| `minLevel` | int | | tier gate: 15 / 30 / 45; official tier 5 uses 60; 1–120 | C |
| `body` | Body | | §3 below | C |
| `baseHealth` | number | 50 | base max HP; ≤ 100000 | C |
| `baseBodyDamage` | number | 5 | Spike 7, Blender 8; ≤ 10000 | C |
| `speedMultiplier` | number | 1 | movement speed; ≤ 3 | C |
| `zoomMultiplier` | number | 1 | **inverse** of field of view: 0.9 = 111 % view (Sniper), 0.65 (Hitman); 0.5–5 | C |
| `scopeDistance` | number | none | camera slides this far toward the aim while right click is held (Predator 1500); ≤ 3000 | C |
| `knockbackMultiplier` | number | 1 | knockback the tank **receives** (Mega Smasher 0.2); ≤ 3 | C |
| `helpText` | string | | hint shown centred at the top of the screen; ≤ 80 characters | C |
| `raises` | string[] | | polygon kinds (or custom shape ids) that become drones when killed; needs a `holdsRaised` barrel | H |
| `projectiles` | Projectile[] | | §5; optional (smashers have none); ≤ 16 | C |
| `invisibility` | Invisibility | | §4; always written | C |
| `statsMaxLevel` | int[8] | `[7×8]` | caps, **reversed from the in-game 1–8 keys**: 0 Movement Speed, 1 Reload, 2 Bullet Damage, 3 Bullet Penetration, 4 Bullet Speed, 5 Body Damage, 6 Max Health, 7 Health Regen. 0 removes the stat. Smasher line `[10,0,0,0,0,10,10,10]`. Each 0–12. The Reload cap sets the import budget (§7a) | C |
| `upgradesFrom` | int[] | | parent ids, vanilla or same-pack; validated on import; **a tank offers at most 19 upgrades**, stock ones included (Tank has 6) | C |
| `advancesInto` | int[] | | child ids, the mirror of `upgradesFrom`; the official pack uses `upgradesFrom` only | C |
| `editor` | object | | `replaces: N` takes vanilla N's menu slot (pair with pack `hidden: [N]`); `disabled: true` keeps the tank out of the tree (its links are parked in `editor.upgradesFrom/advancesInto`) | C |
| `barrels`, `bodyShapes`, `turrets` | arrays | | §7, §8, §9; **at most 32 barrels, 32 body shapes and 8 turrets** (the editor drops the rest silently, §9c); **at most 96 pieces in all**: shapes + barrels + turrets on the tank plus every projectile's parts, sub-barrels and turrets (§9c) | C |

## Body (§3) and invisibility (§4)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `body.sides` | int | | 0 circle; polygons draw at 1.3 × size; ≤ 18; always written | C |
| `body.star` | bool | false | alternating inner (0.4) and outer vertices | C |
| `body.angle` | number | 0 | fixed rotation; official octagons π/8 | C |
| `body.size` | number | 50 | hull radius; 44.23 octagon matches a 50 circle; 5–8 hides the hull behind parts (hitbox shrinks with it); ≤ 67 | C |
| `body.color` | int | 27 team | palette index (§10). Parts at 27 ("same color as the body") take the hull's colour (C): for team accents on a coloured figure leave the hull team-coloured and cover it with a same-size `aboveBody` shape (§10); shots with no `color` are team-coloured | C |
| `body.spinSpeed` | number | 0 | radians per tick (0.0628 = one turn per 4 s); −0.5–0.5 | C |
| `invisibility.enabled` | bool | false | tank fades | C |
| `.gain` | number | 2/65 | the editor's "Time to vanish": gain = 1 ÷ (25 × seconds), 0.1–60 s (default 1.3 s; Landmine 10 s) | C |
| `.lossOnHit` | number | 0.05 | the editor's "Hits to reveal": 0.3 ÷ (hits − 1), so 0.05 = 7 hits, 0 = never | C |
| `.lossOnAttack` / `.lossOnMovement` | number | 0.23 / 0.08 | opacity regained per shot / tick moving; `lossOnAttack: 0` = firing does not reveal ; shots never fade, so auto-fire (a trail, a plume) still marks a faded tank (C) | H |
| `.revealDistance` | number | 0 | enemies this close see the faded tank faintly; 0 never (Stalker 450, Landmine 650); ≤ 3000 | C |

## Projectile (§5) and flags (§6)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `name` | string | | editor label; always written | C |
| `base` | enum | | `bullet` / `drone` / `trap` | C |
| `sides` | int | | -1 = the base's usual shape; else polygon sides, 0 circle; ≤ 18; always written | C |
| `star` | bool | false | star polygon | C |
| `spin` | number | 0 | rotation per tick (missiles 0.1); −0.5–0.5 | C |
| `spinFlipsOnSecondary` | bool | false | spin reverses while right click is held (Skimmer) | C |
| `color` | int | team | palette index; 27 = owner colour | C |
| `burst` | object | | `onSecondary` / `onDestroyed` / `onExpire`: ends the projectile; sub-barrels flagged `firesOnDeath` fire once as it dies (Firework), and only if a trigger is set | C |
| `barrels` | Barrel[] | | sub-barrels, same schema as §7, `projectile` indexes the **tank's** list. `forceFire` fires in flight (missiles), `firesOnDeath` fires once at death, unflagged fires on the owner's click (Factory minions) or, when on one of the projectile's `turrets`, on its own at targets. **A sub-barrel may only fire a projectile that carries nothing** (no parts, barrels, turrets) and is not its own; otherwise the editor gives it a plain default shot. ≤ 32 | C |
| `drone.idle` | enum | `hover` | `hover` standard (Overlord), `cruise` Battleship swarm | C |
| `drone.controllable` | bool | true | **the switch the engine reads**; the barrel's `droneControllable` does nothing alone (write both to look stock) | C |
| `drone.keepDistanceMin/Max` | number | | stand-off band measured **from the target** (Factory 300–800); ≤ 2000 | C |
| `drone.repel` | bool | true | false = right click does not push it away | C |
| `parts` | BodyShape[] | | decoration on the projectile, §8 schema, in a frame where the projectile's radius counts as 50; under its disc unless `aboveBody`; ≤ 32, three `collidable` at most | C (scale M) |
| `turrets` | Turret[] | | auto-turrets on the projectile, §9 schema; sub-barrels ride them via `mountTurret`; ≤ 8 | H |
| `flags.forceFire` | | | fires without input: spawners, missile thrusters, auto-fire guns, trail droppers | C |
| `flags.holdsRaised` | | | Necromancer spawner: slots filled by raised polygons, plus one per Reload stat point; `projectile: -1`; tank barrels only | C |
| `flags.firesOnSecondary` | | | right click instead of left | C |
| `flags.firesOnDeath` | | | sub-barrel fires once when its projectile dies | C |
| `flags.aboveBody` | | | draw the barrel over the hull (line art, rods over a turret disc) | C |

## Barrel (§7): tank barrels and sub-barrels alike

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `angle` | number | 0 | direction, radians clockwise from aim | C |
| `offset` | number | 0 | sideways shift (Twin ±26); ±500 | C |
| `distance` | number | 95 | **length** (editor "Length"); ±500 | C |
| `startDistance` | number | 0 | editor "Gap": where the barrel starts, from the hull centre; negative allowed; ±500 | C |
| `heightMultiplier` | number | 1 | width × 42; 0.1 is a hairline; ≤ 2.5; also scales the bullet | C |
| `muzzleScale` | number | 1 | muzzle ÷ base width: 1.75 spawner flare, 0.57 sniper taper, 0.04–7.5 seen | C |
| `bulletType` | enum | | `bullet` / `drone` / `trap` / `none`; keep equal to the projectile's `base`; `none` + `projectile: -1` = decorative rod; always written | C |
| `projectile` | int or int[] | | index into `projectiles[]`, -1 none; an array picks one at random per shot | C |
| `damageMultiplier` | number or [min,max] | 1 | a range rolls per shot; ≤ 20 | C |
| `penetrationMultiplier` | number or [min,max] | 1 | projectile health; a range rolls per shot; ≤ 20 | C |
| `speedMultiplier` | number or [min,max] | 1 | **0 with `initialVelocityMultiplier: 0` = stationary shot** (trails, damage points); ≤ 3 | C |
| `initialVelocityMultiplier` | number or [min,max] | 1 | launch speed relative to cruise (Rocketeer 1.2, Shotgun 1.5); ≤ 3 | C |
| `numBullets` | int | 1 | projectiles per shot, each with its own spread (Shotgun 4, Pellet Shot 10); 1–10 | C |
| `bulletSizeMultiplier` | number or [min,max] | 1 | projectile radius; on a sub-barrel the child is parent × this ÷ 2 (M); polygon bullets draw 1.3×; ≤ 3; size counts squared in the room budget | C |
| `reloadMultiplier` | number | 1 | higher = slower (Destroyer 4, spawners 3–6); ≤ 20 | C |
| `delay` | number | 0 | phase in reload periods: 0.5 alternates a pair; 0.2/0.4 staggers a burst; past 1 it sits out whole cycles first (a rocket coasting); ≤ 10 | C |
| `spreadMultiplier` | number | 1 | 0 = dead straight; ≤ 20 | H |
| `lifetime` | number or [min,max] | base default (bullet ≈ 3 s) | seconds (traps 24, swarm drones 4.2, missile 3.9); a range rolls per shot: eggs that hatch at different times; ≤ 30; unset counts 3 s in the budget | C |
| `recoilMultiplier` | number | 1 | recoil on the owner, or thrust on a carrying projectile; ≤ 20 | C |
| `knockbackMultiplier` | number | 1 | knockback dealt; ≤ 20 | H |
| `numDrones` | int | 24 | max live drones; ≤ 24; always written on drone barrels | C |
| `droneAggressiveCrashRadius` | number | 900 | how far uncontrolled drones roam to attack; ≤ 2000; always written on drone barrels | C |
| `preSpawn` | int | 0 | on a `holdsRaised` barrel: free drones emitted right after spawn; nothing on projectile spawners | C |
| `droneControllable` | bool | true | mirror of `drone.controllable`; no effect alone | C |
| `mountTurret` | int | | rides `turrets[i]` (the projectile's own list for a sub-barrel) | C |
| `mount` | int | | rides `barrels[i]` of the same array, measured from that barrel's midpoint (launcher tips) | H |
| `invisible` | bool | false | not drawn, still fires: hidden bite points, trail droppers | C |
| `color` | int | 1 (Cannon grey) | palette index; 27 = the body's colour (missile barrels) | C |
| `order` | int | 0 | draw order shared with shapes and turrets; -1 sits under the main barrel | C |
| `editor` | object | | `{"name": "…"}` (name every part), `{"group": "…"}` folder | C |

**Import budget (§7a, C: the editor's own check, exact).** The lobby refuses a tank over
**120 entities/s**, **250 alive**, **2000 room**, **64 per volley**, **96 drones** or **96
pieces**. Everything counts at once (left click, right click, auto-fire) at the tank's Reload
cap: a barrel fires every ⌈15 × 0.914^cap × `reloadMultiplier`⌉ ticks (25/s), and each shot
counts 1 + everything its projectile carries (parts, rods, guns, turrets). At cap 12 a plain
barrel costs 4.2/s, reload 0.5 costs 8.3, 0.25 costs 12.5; cap 7 about three quarters; cap 0
makes barrels cheap. Alive = per second × lifetime (unset = 3 s). A projectile's live guns fire
once per live copy (buildings living 27 s multiply). Room: a standard bullet is 1, size counts
squared (width × size; drones, traps and polygon bullets 1.4× the radius), collidable parts add
theirs. Put complex projectiles on a **Reload cap of 0**, as a player-built pack does on 47 of
60 tanks. `validate_pack.py --summary` prints all six figures.

## Body shape (§8)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `sides` | int | | polygon sides; 0, 1 and 2 draw as a circle; ≤ 18; always written | C |
| `size` | number | 25 | circumradius; ≤ 300 (≤ 150 if collidable) | C |
| `xOffset` / `yOffset` | number | 0 | position: x forward, y to the tank's right; ±800 | C |
| `angle` | number | 0 | rotation | C |
| `spinSpeed` | number | 0 | per tick (Smasher 0.1, Spike 0.17) | C |
| `star` | bool | false | 2 × sides vertices, inner radius 0.4 × size | C |
| `collidable` | bool | false | the part has its own hitbox, contact at roughly half to two thirds of its drawn radius; **only the first three per tank or projectile** | C |
| `aboveBody` | bool | false | draw over the hull (or over its turret's disc) | C |
| `mountTurret` | int | | rides a turret, offsets in the turret's frame | C |
| `mount` | int | | rides a barrel, from its midpoint | H |
| `staysVisible` | bool | false | stays drawn while the tank is faded (eyes on a stalker) | C |
| `color` | int | 0 (Border grey) | palette index | C |
| `order`, `editor` | | | as barrels | C |

## Turret (§9)

| Key | Type | Default | Meaning | |
|---|---|---|---|---|
| `xOffset` / `yOffset` | number | 0 | mount position | C |
| `angle` | number | 0 | rest direction | C |
| `arc` | number | 0 = full circle | traverse limit either side of `angle`; **0 turns all the way round**; for a fixed pivot use 0.087; a narrow arc pointing away from enemies makes a pendulum that lags turns | C |
| `range` | number | 1700 | targeting range (side turrets 2000). **0 = no auto-targeting**: with `controllable` it rests at `angle` and follows the cursor only while fire is held (hands, jaws); give it an `arc` or it wanders. With `controllable` **and** a range (a player-built pack's limbs: 250, 750, or unset) it also turns toward enemies in range while idle: a living limb (recipe 27; Limb Lab 2026-09-28). Cursor-following needs the cursor inside the wedge | C |
| `controllable` | bool | false | player aims it while firing; with a range it still tracks enemies when idle | C |
| `aboveBody` | bool | true | drawn over the hull | C |
| `baseSize` | number | 25 | disc radius (10 for a joint, 30 for an eyeball, 1 to hide) | C |
| `color` | int | 1 | disc palette index (19 White eyeball, 27 owner) | C |
| `order`, `editor` | | | as barrels | C |

Turrets always track the nearest target inside `range` and `arc`, armed or not. A turret's
weapon is a tank barrel with `mountTurret`; shapes ride it the same way, so one pivot can carry
a whole jaw. **Turrets cannot be nested** (a `mountTurret` on a turret is ignored).

**Draw order (§9a).** Ascending `order` across barrels, shapes and turrets, ties in array
order; the hull paints over all of them; then `aboveBody` shapes, `flags.aboveBody` barrels
and turrets. Hull polygons draw at 1.3 × size, squares axis-aligned. Outline = fill × 0.72.

## Palette (§10): use the editor's swatch names in recaps

| idx | name | idx | name | idx | name |
|---|---|---|---|---|---|
| 0 | Border (grey `#555555`, shape default) | 10 | Periwinkle | 20 | Charcoal |
| 1 | Cannon (`#999999`, barrel default) | 11 | Pink | 21 | Teal |
| 2 | Blue (fixed `#00B2E1`) | 13 | Mint | 22 | Indigo |
| 4 | Red **team slot** | 14 | Box (`#BBBBBB`) | 23 | Brown |
| 5 | Purple **team slot** | 16 | Orange | 24 | Crimson |
| 6 | Green **team slot** | 18 | Cyan | 25 | Forest |
| 7 | Shiny | 19 | White | 26 | Plum |
| 8 | Yellow | | | 27 | owner / team colour |
| 9 | Salmon | | | | |

3–6 follow the player's team once they have been on that team; for a colour that must stay
put use Salmon or Crimson (reds), Blue or Indigo, Mint or Forest, Plum. 3, 12, 15, 17, 28, 29
are unnamed greys.

## Vanilla ids (§11): the full table with levels and parents is `vanilla-tanks.md`

0 Tank, 1 Twin, 6 Sniper, 7 Machine Gun, 8 Tri-Angle, 9 Flank Guard (not the other way
round), 10 Destroyer, 11 Overseer, 12 Overlord, 36 Smasher, 48 Battleship, 52 Factory,
54 Skimmer, 55 Rocketeer, 58 Auto Tank, 60 Dual-Barrel, 61 Pellet Shot, 62 Shotgun,
63 Glider, 64 Firework. **Rejected by the engine**: 53 Ball, 56, 57, 59.
