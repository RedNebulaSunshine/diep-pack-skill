## 1. Pack (top level)

```json
{"version":2,"name":"My Pack","author":"Your Name","tanks":[ … ],"hidden":[4]}
```

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `version` | int | `2` | Format version. Always 2 in every export seen, including official ones. | Confirmed |
| `name` | string | `"10th Anniversary"` | Pack display name. The editor fills in a generic name when it is missing. | Confirmed (editor code) |
| `author` | string | `"diep.io"`, `"Your Name"` | Author display name. Official packs say `diep.io`; copying a stock tank into your pack stamps your name on the copy. **Optional**: one large player-built pack has none. | High |
| `tanks` | Tank[] | | The tanks. §2. Optional in an arena-only pack: the shape editor exports shapes with no `tanks` key (2026-09-29). Such a pack imports only through **Add to this pack** (it adds the shapes to the open pack); **Import as new pack** refuses it with "A pack needs a tank. Use Add to this pack instead." | Confirmed (editor code) |
| `hidden` | int[] | `[4]`, 53 ids | Vanilla tank IDs hidden from the class tree. A tank with `editor.replaces: 4` but no `hidden` showed **both** the vanilla Quad Tank and the custom one at level 30, so `hidden` is what removes the vanilla entry. A player-built total conversion hides every stock tank but Tank with no `replaces` anywhere and `starters: [100001]`, i.e. a total conversion, Confirmed 2026-09-26: importing it left a class tree with only its own tanks, so `hidden` works alone. Only vanilla IDs (below 100000) are kept. **Tank (0) cannot be hidden**: a pack hiding all 54 stock ids was refused with "the base tank cannot be hidden" (2026-09-29); hide the other 53 and put the pack's own level-1 tanks in `starters` (every player-built total conversion does), which leaves Tank unreachable. | Confirmed |
| `starters` | int[] | `[100001]`, `[0, 100209, 100211, 100214, 100219]` | The tanks a player can spawn as (vanilla 0 and/or level-1 tanks of this pack). One large pack lists Tank plus four custom level-1 tanks; a total conversion only its first tank. Confirmed 2026-09-26: after importing that conversion a fresh life spawned as its first tank. | Confirmed |
| `shapes` | CustomShape[] | | Custom arena polygons (food, crashers, bosses): §1a. Referenced by tank `raises` through their id. | High |
| `hiddenShapes` | string[] | `["hexagon"]`, all seven | Vanilla shape kinds that stop spawning: any of `square`, `triangle`, `pentagon`, `big_pentagon`, `hexagon`, `small_crasher`, `big_crasher` (the same names `raises` uses). Paired with a custom shape whose `editor.replaces` names the same kind. Confirmed 2026-09-26: `["square"]` left an arena with no squares. | Confirmed |

### 1a. Custom shape (`shapes[]`)

Seen in human packs (32 definitions); the editor has a shape editor beside the tank editor.
**Spawning confirmed in play 2026-09-26** (the `arena-test` test build): a 4-sided "Ruby" with
`spawn.densityMultiplier` 1.0 and no radius band made up roughly 40–50 % of the shapes in the
arena. The other fields are plain-named and their values sit in sensible ranges (a "Hexagon"
replacement: 6 sides, size 100, health 1500, xp 1500).

```json
{"id":"custom_shape_13","name":"Hexagon","sides":6,"size":100,"maxHealth":1500,"xpBounty":1500,
 "damageOnTouch":4,"knockbackOnTouch":10,"knockbackMultiplier":0.1,"color":"#35c5db",
 "ai":{"floatSpeed":0.05},"spawn":{"radiusMin":0.2,"densityMultiplier":0.004},"editor":{"replaces":"hexagon"}}
{"id":"custom_shape_20","name":"Red Crasher","sides":3,"size":55,"maxHealth":75,"xpBounty":60,
 "damageOnTouch":3,"knockbackOnTouch":12,"knockbackMultiplier":0.1,"color":"#B5323A",
 "ai":{"floatSpeed":0.1,"aggressiveCrashRadius":2000,"aggressiveCrashSpeed":3},
 "spawn":{"radiusMin":0.8,"densityMultiplier":0},"editor":{"disabled":true,"spawnWeight":0.1}}
```

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `id` | string | `custom_shape_1` … | Identity, `custom_shape_N`; what `raises` uses. **Positional**: the editor's export numbers the shapes `custom_shape_1` … in list order, so reordering or deleting shapes renumbers them. At most 256 shapes per pack. | Confirmed (editor code) |
| `name` | string | | Display name. | High |
| `sides` | int | `0`–`18` | Polygon sides; 0 (and 1) a circle. Editor range 0–18 (user, 2026-09-29). | Confirmed |
| `size` | number | `30`–`500` | Radius; vanilla-like squares 55, pentagons 75, alpha pentagons 200, hexagons 100. **Missing = 50** (the editor fills it in on import). | Confirmed (editor code) |
| `maxHealth`, `xpBounty` | number | `20`/`30` … `135000`/`750000` | Health and score on kill. **Missing = 10** each (the editor fills them in on import). | Confirmed (editor code) |
| `damageOnTouch`, `knockbackOnTouch` | number | `2`–`20`, `8`–`25` | Body damage dealt and knockback dealt on contact. `damageOnTouch` confirmed 2026-09-29: at 20, two touches killed a tank with Max Health and Body Damage at 7/7, so 20 is boss-grade; keep food low (2–4). `knockbackOnTouch` is "how hard it shoves what it hits" (the editor). The editor's reference: "A vanilla square does 2 damage, shoves with 8 and takes full knockback." Missing = 1 each. | Confirmed |
| `knockbackMultiplier` | number | `0`–`3` (editor max 3) | Knockback the shape receives. Confirmed 2026-09-29: 0 is immovable, neither bullets nor a ramming tank shift it (the tank bounces off and takes contact damage); 2 and 3 get pushed by a high-knockback gun, yet a stock tank's bullets barely move a shape at 2, so the effect is modest. Heavy shapes in player packs use 0.01–0.1. The editor: "A square takes 1, a Pentagon 0.5, an Alpha Pentagon 0.05." Clamped to 3 on import; missing = 1. | Confirmed |
| `color` | string | `"#FFE869"` | **Hex string**, not a palette index (the only place hex appears). Missing = `#ffe869` (square yellow). | Confirmed (editor code) |
| `ai.floatSpeed` | number | `0`–`1000` (editor) | Idle drift speed (vanilla-like 0.05; the editor's new shape uses 0.1). Confirmed 2026-09-29: at 1 the shape wanders aimlessly and visibly faster than at 0.05, without seeking the player. The editor shows it only for shapes that are not crashers (user); its help text, "How fast it wanders when nothing is chasing it", suggests a crasher also drifts at it while no tank is in range (untested). Missing = 0. | Confirmed |
| `ai.aggressiveCrashSpeed` / `ai.aggressiveCrashRadius` | number | `1`–`3.2` / `1500`–`2000` | Crasher behaviour: chase speed, and the radius at which it notices a tank (the editor: "How far off it notices a tank. The server searches this radius, so it is what a crasher costs"; at most 2000). A radius of 0 or none means not a crasher: the shape just floats. Confirmed 2026-09-29: speed 3, radius 2000 chased the player down; a shape without them only drifts. | Confirmed |
| `spawn.densityMultiplier` | number | `0` (event only), `1e-7`–`999` | The editor calls it **Spawn weight**: "How often it is picked, next to squares at 1, triangles 0.2, pentagons 0.05." A relative weight, not a count: shapes share the map's shape cap (a sandbox setting). 0 = never spawns naturally; missing = 0.01. In play, 1.0 beside the vanilla shapes made about 40–50 % of spawns (2026-09-26), as 1 / (1 + 1.25) predicts. How it combines with the spawn band: "Spawn shares" below. | Confirmed |
| `spawn.radiusMin` / `radiusMax` | number | `0`–`1` | The spawn band: the editor's two sliders read "how far out from the centre of the map it may spawn, 0% is the centre, 100% is the edge", stored as fractions. The map is rectangular (usually square), so a band is a square ring. Omitted means 0 / 1 (anywhere). Confirmed in play 2026-09-29 (`arena-zone-test`): three stacked bands (0.8–1, 0.4–0.8, 0–0.4) stayed apart and followed the square edges. **A band's share of the shapes goes with its width, not its area** (see "Spawn shares" below), so the centre crowds. | Confirmed |
| `editor.replaces` | string | `"hexagon"` | Vanilla shape kind whose place this takes (paired with `hiddenShapes`): the editor's wording is "your version spawns in its place". | High |

**The seven vanilla shapes, as the editor's own copy of each writes them** (Confirmed 2026-10-04, exported
and read; `maxHealth`/`xpBounty` missing = 10; colours omitted, that export was recoloured):

```json
{"name":"Square","sides":4,"size":55,"damageOnTouch":2,"knockbackOnTouch":8,"ai":{"floatSpeed":0.1},"spawn":{"radiusMin":0.2,"densityMultiplier":1}}
{"name":"Triangle","sides":3,"size":55,"maxHealth":30,"xpBounty":25,"damageOnTouch":2,"knockbackOnTouch":8,"ai":{"floatSpeed":0.1},"spawn":{"radiusMin":0.2,"densityMultiplier":0.2}}
{"name":"Pentagon","sides":5,"size":75,"maxHealth":100,"xpBounty":130,"damageOnTouch":3,"knockbackOnTouch":11,"knockbackMultiplier":0.5,"ai":{"floatSpeed":0.05},"spawn":{"radiusMin":0.2,"densityMultiplier":0.05}}
{"name":"Alpha Pentagon","sides":5,"size":200,"maxHealth":3000,"xpBounty":3000,"damageOnTouch":5,"knockbackOnTouch":11,"knockbackMultiplier":0.05,"ai":{"floatSpeed":0.05},"spawn":{"radiusMax":0.1,"densityMultiplier":0.005}}
{"name":"Crasher","sides":3,"size":55,"maxHealth":30,"xpBounty":25,"damageOnTouch":2,"knockbackOnTouch":12,"knockbackMultiplier":0.1,"ai":{"floatSpeed":0.1,"aggressiveCrashRadius":2000,"aggressiveCrashSpeed":2.6},"spawn":{"radiusMax":0.2,"densityMultiplier":0.02}}
{"name":"Small Crasher","sides":3,"size":35,"xpBounty":15,"damageOnTouch":2,"knockbackOnTouch":8,"knockbackMultiplier":2,"ai":{"floatSpeed":0.1,"aggressiveCrashRadius":2000,"aggressiveCrashSpeed":2.7},"spawn":{"radiusMax":0.2,"densityMultiplier":0.1}}
{"name":"Hexagon","sides":6,"size":100,"maxHealth":1500,"xpBounty":1500,"damageOnTouch":4,"knockbackOnTouch":10,"knockbackMultiplier":0.1,"ai":{"floatSpeed":0.05},"spawn":{"radiusMin":0.2,"densityMultiplier":0.004}}
```

The weights for the four the help text does not name (Alpha Pentagon 0.005, Crasher 0.02, Small Crasher 0.1,
Hexagon 0.004) and every band come from here: vanilla food spawns in 0.2–1, crashers in 0–0.2, Alpha Pentagons
in 0–0.1. `compose.VANILLA_SPAWN` carries them for `spawn_shares()`.
| `editor.disabled` | bool | `true` | Not spawned while disabled (all "(Event)" shapes carry it). Confirmed 2026-09-26: a disabled shape at density 1.0 never appeared. | Confirmed |
| `editor.spawnWeight` | number | `0.003`–`1` | **The weight a disabled shape keeps**: disabling writes `spawn.densityMultiplier: 0` and parks the real weight here, and enabling restores it. | Confirmed (editor code) |

**Shape editor ranges** (read off two exports of one shape, every value maxed and every value
at its minimum, 2026-09-29; the validator warns outside them):

| Field | Min | Max |
|---|---|---|
| `sides` | 0 (circle) | 18 |
| `size` | 5 | 500 |
| `maxHealth` | 1 | 1 000 000 |
| `xpBounty` | 0 | 10 000 000 |
| `damageOnTouch`, `knockbackOnTouch` | 0 | 1000 |
| `knockbackMultiplier` | 0 | 3 |
| `ai.aggressiveCrashSpeed` | 0 (the key is then dropped: not a crasher) | 1000 |
| `ai.aggressiveCrashRadius` | 1 | 2000 |
| `spawn.densityMultiplier` | 0 | 1000 |
| `spawn.radiusMin`, `spawn.radiusMax` | 0 (centre) | 1 (edge) |
| `ai.floatSpeed` | 0 | 1000 (shown for shapes that are not crashers) |

Keys at their default are omitted: `radiusMin` 0, `radiusMax` 1, `aggressiveCrashSpeed` 0.

**Spawn shares** (2026-09-29; the user counted 100 shapes on a 5000 × 5000 map with a 100-shape
cap, after killing every shape and letting them respawn; vanilla shapes hidden; bands 0.8–1,
0.4–0.8 and 0–0.4):

| Test | Densities | Counted | density × band width predicts |
|---|---|---|---|
| `arena-zone-test` | 1 / 1 / 1 | 17 / 46 / 37 | 20 / 40 / 40 |
| `arena-density-test` | 1.8 / 1.2 / 0.4 | 31 / 59 / 10 | 36 / 48 / 16 |

The model: **a shape's share ≈ density × band width**, not × band area. It behaves as if the game
picked a distance from the centre (evenly from 0 to 1) and a shape by weight ("how often it is
picked", the editor), and kept the pair only when the distance lies in that shape's band.
(Picking the distance first and then only among the shapes whose band holds it would make
density irrelevant for bands that do not overlap; the second count rules that out.) Fitted jointly, both
counts agree with the density scaling (p = 0.5) with band weights of about 0.18 / 0.49 / 0.34
per 0.2 / 0.4 / 0.4 of width: the middle band draws a little more than its width, the outer
band a little less. Pure width is not ruled out (p = 0.12); an equal split and a split by area
are (p = 0.001, p < 1e-8). Treat predictions as ±5 shapes in 100. For a designer:
- Density is a weight shared with every other enabled shape, vanilla ones included (square 1,
  triangle 0.2, pentagon 0.05). A shape's share of the cap is its weight × width over the sum.
- Per unit of area the centre crowds: 0–0.4 is 16 % of a square map but gets 40 % of the
  spawns at equal density. For the same count in each ring set density ∝ 1 / width; for the
  same crowding per area, density ∝ ring area / width (ring area = outer² − inner²; for the
  bands above 1.8 / 1.2 / 0.4, which in play gave 31 / 59 / 10, close to even crowding).

## 2. Tank

The smallest tank the editor writes (a Basic Tank clone):

```json
{"id":100004,"name":"My Tank","minLevel":1,"body":{"sides":0},
 "projectiles":[{"name":"Bullet","base":"bullet","sides":-1}],
 "invisibility":{"gain":0.03076923076923077,"lossOnHit":0.049999999999999996},
 "statsMaxLevel":[7,7,7,7,7,7,7,7],
 "barrels":[{"bulletType":"bullet","projectile":0}]}
```

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `id` | int | `100002`, `100067` | Tank ID. Custom IDs start at 100001 and are reassigned on "add to this pack". The official anniversary pack uses 100065–100084 (100070 missing). IDs below 100000 are vanilla (§11). Referenced by `upgradesFrom`/`advancesInto`. The editor keeps a numeric `id` from the file and exports it unchanged, but **the lobby refuses a tank id below 100000**: "tank[0]: id 12 is outside the custom range (>=100000)" (2026-09-29, the `boss-stomp-test` test build), so a pack cannot overwrite a stock tank (or the Fallen bosses built from Overlord 12 and Booster 23); the validator errors. | Confirmed |
| `name` | string | `"Apex Predator"` | Display name. Duplicates allowed. | Confirmed |
| `minLevel` | int | `1`, `15`, `30`, `45`, `60`, `120` | Level at which the tank can be chosen (tier gate; ref §2). Official tier-5 tanks use 60. The sandbox level cap is at least 120 (user reached 120 with the K cheat). The editor keeps it within 1–120. | Confirmed |
| `body` | Body | | Hull geometry and styling. §3. | Confirmed |
| `baseHealth` | number | `100000` | Base max HP. Absent = 50 (vanilla at level 1, ref §6); at most 100000. Played 2026-09-29 (the `boss-test` test build: 100000 health, `baseBodyDamage` 40, `knockbackMultiplier` 0, `speedMultiplier` 0.6, a collidable size-150 body over a size-67 hull): it worked as the numbers say, a powerful tank, but a playable one, not a diep boss (arena.md §2). | Confirmed (editor code, play) |
| `baseBodyDamage` | number | `7` (Spike), `8` (Blender) | Base body damage in the ref §6 unit where vanilla is 5 and damage = (points + base) × 4. Spike's "+2 base body damage" is exactly 7. Absent = 5; at most 10000. The editor: "Damage dealt to whatever runs into it." | Confirmed (editor code) |
| `speedMultiplier` | number | `1.1` (Smasher line), `3` | Movement speed multiplier. Absent = 1; at most 3. | Confirmed (editor code) |
| `zoomMultiplier` | number | `0.9`, `0.85`, `0.75`, `0.65` | **Inverse** of field of view. Skimmer 0.9 ↔ ref §6 FoV 111%; Predator 0.85 ↔ 117.6%. Below 1 = see more (the editor: "Lower sees more of the arena"). Absent = 1; kept within 0.5–5. | Confirmed |
| `scopeDistance` | number | `1500` (Predator) | How far the camera slides toward the aim direction while secondary fire is held. Predator's `helpText` says exactly this. Absent or 0 = no scope; at most 3000. | Confirmed |
| `knockbackMultiplier` | number | `0.2` (Mega Smasher), `10` | Multiplier on knockback the tank **receives** (the editor: "How hard a hit pushes the tank. 0 never budges"): a high value flung the tester much further when ramming a pentagon. **At most 3**: the editor clamps it on import (a 10 in an old test is now 3). Mega Smasher's 0.2 is knockback resistance. Per-barrel `knockbackMultiplier` (§7) covers knockback dealt. | Confirmed |
| `helpText` | string | `"Right click to fire your front barrel"` | Class hint shown to the player, **centred at the top of the screen** while playing the tank (2026-09-26); three official tanks carry one, each describing a secondary-fire trick. **At most 80 characters**; the editor cuts the rest. | Confirmed |
| `raises` | string[] | `["square"]`, `["square","custom_shape_4","custom_shape_12"]` | Polygon kinds that become drones when killed — the Necromancer mechanic (ref §3). Vanilla Necromancer and Resurrector list only `square`; the extreme example lists all seven: `square`, `triangle`, `pentagon`, `big_pentagon` (Alpha Pentagon), `hexagon`, `small_crasher`, `big_crasher`. A custom shape's `id` (§1a) is accepted too (two player-built tanks do). Requires a spawner barrel with `flags.holdsRaised`. | High |
| `projectiles` | Projectile[] | | Projectile definitions, referenced by index from barrels. §5. **Optional**: Smasher, Landmine, Spike, Necromancer have none. **At most 16.** | Confirmed |
| `invisibility` | Invisibility | | Fading rules. Always written. §4. | Confirmed |
| `statsMaxLevel` | int[8] | `[7,7,7,7,7,7,7,7]`, `[10,0,0,0,0,10,10,10]`, `[12,0,0,0,0,12,12,12]` | Per-stat point caps. The Reload cap (index 1) also sets the rate the import check assumes for every barrel (§7a): caps of 12 make a tank fire 1.5× faster on paper than caps of 7. **Index order is the reverse of the in-game key order**: 0 Movement Speed, 1 Reload, 2 Bullet Damage, 3 Bullet Penetration, 4 Bullet Speed, 5 Body Damage, 6 Max Health, 7 Health Regen. `0` removes the stat from the panel. Vanilla 7, Smasher line 10, official Blender 12, extreme example 12. Verified with `[7,7,7,7,0,0,0,10]`: Health Regen capped at 10, Bullet Speed / Body Damage / Max Health disabled. **Each cap 0–12**: the editor rounds and clamps. | Confirmed |
| `upgradesFrom` | int[] | `[0]`, `[13,2]`, `[1,9]` | Parent tank IDs in the class tree (vanilla or custom). **A tank may offer at most 19 upgrades**, stock children included: adding a seven-tank pack wired to Tank (0) a second time on top of Tank's 6 stock children was refused with `tank 0 offers 20 upgrades, the most is 19` (2026-09-28). "Add to this pack" appends copies, so re-importing a revised pack into the pack that holds the old one stacks its children; import it as a new pack instead. Confirmed. The editor has a dedicated "ladder" screen for this; official tanks carry the field, and the copy function strips it. **The engine validates IDs on import**: a pack referencing ID 56 was refused with `tank 100002 advancesInto unknown id 56`. Verified in game: a custom tank with `upgradesFrom: [6]`, `minLevel: 30` and no `advancesInto` anywhere was offered as an upgrade from Sniper at level 30. A two-tank pack whose second tank had `upgradesFrom: [100001]` (the first tank's id in the same pack) imported and worked, so in-pack custom links survive import. | Confirmed |
| `advancesInto` | int[] | `[5,40]` | Child tank IDs, the mirror of `upgradesFrom`; the editor writes both. | Confirmed (editor code) |
| `editor` | object | `{"replaces":4}`, `{"disabled":true}` | Editor metadata. `replaces` = vanilla ID whose slot this tank takes in the menu. On its own it does **not** hide the vanilla tank (both appeared); pair it with pack `hidden`. `disabled: true` keeps the tank out of the tree (a player-built pack's four level-120 admin tanks). A player-built pack also writes `editor.advancesInto` / `editor.upgradesFrom` (int[]) on six tanks: the editor's own note of a link, separate from the tank-level fields that the engine reads (one spider's `editor.advancesInto: [100082]` names a different tank from the three its real `advancesInto` lists). **Read from the editor's export code** (2026-09-29): a disabled tank is written with empty `upgradesFrom` / `advancesInto` ("outside the tree", "nobody can upgrade into them"), and any link to a disabled or missing pack tank is moved out of the real field into `editor.upgradesFrom` / `editor.advancesInto`, so it comes back when that tank is enabled. **`replaces` does not reach the server's bosses** (2026-09-29, the `fallen-boss-test` test build): with Overlord (12) and Booster (23) replaced and hidden, the admin panel's Fallen Overlord and Fallen Booster spawned as the stock tanks, and the stand-ins imported as 100001 and 100002; the export writes `replaces` only under `editor`, so it is a tree slot, nothing more. | Confirmed (editor code; bosses in play) |
| `barrels` | Barrel[] | | Weapons and decorative barrels. §7. **Optional** (smashers have none). **At most 32** (§9c). | Confirmed |
| `bodyShapes` | BodyShape[] | | Polygons attached to the hull. §8. **At most 32**; the editor drops the rest (§9c). | Confirmed |
| `turrets` | Turret[] | | Auto-turret mounts. §9. **At most 8** (§9c). | Confirmed |

