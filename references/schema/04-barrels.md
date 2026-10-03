## 7. Barrel (`tanks[].barrels[]` and `projectiles[].barrels[]`)

Same schema in both places. Minimal barrel: `{"bulletType":"bullet","projectile":0}`, a
forward default cannon. **Editor limits** (read from its import code, 2026-09-29): 32 barrels per
tank and per projectile; each number below marked "at most" is clamped to that on import
(`validate_pack.py` warns). Negative values pass except where a range is given.

| Key | Type | Default | Examples | Meaning | Confidence |
|---|---|---|---|---|---|
| `angle` | number | 0 | `±π/2`, `2.618` | Direction, radians clockwise from aim. | Confirmed |
| `offset` | number | 0 | Twin `±26`, Battleship `±20`, minions `±16` | Sideways displacement of the barrel from the aim axis. | Confirmed |
| `distance` | number | 95 | `20`–`135`, Stalker 120, sniper 110, spawner 70 | Barrel **length** (editor "Length"). **Clamped to −500…500** on import (a 600 rod exported as 500, 2026-09-26), like `offset` and `startDistance`. 20 sinks into the hull. | Confirmed |
| `startDistance` | number | 0 | Hitman 15, trapper tip 30, `500`, `-190` | Editor "Gap": where the barrel starts, measured from the hull centre. Independent of length; bullets spawn at the muzzle wherever it is. **Negative values are common in human packs** (a rod crossing the hull centre, or a line drawn across a face) and draw exactly as expected. | Confirmed |
| `heightMultiplier` | number | 1 | `0.5`–`2.3`; human packs `0.1`–`2.5` | Width multiplier on the default 42, **at most 2.5**. 0.1 (4 units) is a hairline: outline only. It also scales the bullet (§7a room: radius 21 × this × `bulletSizeMultiplier`). | Confirmed |
| `muzzleScale` | number | 1 | `1.75` (spawners, machine guns), `0.5714` (sniper tips), `1.6667`; human packs `0.04`–`7.5` | Muzzle width ÷ base width: >1 flares, <1 tapers. Near 0 draws a needle point; 7.5 a wide fan. Both verified in exports. | Confirmed |
| `bulletType` | enum | — | `bullet` \| `drone` \| `trap` \| `none` | Weapon class of the barrel, independent of the projectile's `base`. A deliberate mismatch (`drone` barrel firing a `bullet` base, `bullet` barrel firing a `trap` base) imports, fires the **projectile's** base behaviour, and re-exports unchanged; the barrel keeps its own class semantics (the `drone` barrel still exported `numDrones` and `droneAggressiveCrashRadius`). Stock tanks always keep the two in agreement. `none` with `projectile: -1` is a purely decorative barrel (deployer bases, launcher tips). Necromancer spawners use `drone` with `-1` and `holdsRaised`. Always written. | Confirmed |
| `projectile` | int \| int[] | — | `0`, `-1`, `[0,1,2,3,4]` | Index(es) into `projectiles[]`; `-1` = none. The editor's "Projectiles" checklist: one enabled → int, several → array, none → −1. With an array **each shot picks one at random**; official Automator uses this to spawn five minion types. Always written. | Confirmed |
| `damageMultiplier` | number \| [min,max] | 1 | `0.15`–`3`; player-built `[0.5, 1.5]` | Projectile damage, **at most 20** (the editor's slider runs 0–20). A two-element range rolls a value per shot, like `speedMultiplier`: the editor reads `[min, max]` on every multiplier it offers a range for (damage, penetration, speed, size, knockback, launch speed, lifetime). | Confirmed |
| `penetrationMultiplier` | number \| [min,max] | 1 | `0.2`–`5`; player-built `[3, 5]` | Projectile health (ref §6 "penetration"), **at most 20**. Range form as for `damageMultiplier`. | Confirmed (editor code) |
| `speedMultiplier` | number \| [min,max] | 1 | `0.2`–`2`; Pellet Shot `[1.08, 1.32]`; `0` | Projectile speed, **at most 3**. **May be a two-element range**, in which case each bullet rolls a value in it (Pellet Shot's uneven pellet cloud). **`0` with `initialVelocityMultiplier: 0` makes a stationary shot** that stays where it was fired: a player-built snake drops one behind itself every quarter reload and, as the tank moves, they form the trailing body in its in-play screenshot. | Confirmed (0: seen in play in that screenshot) |
| `initialVelocityMultiplier` | number \| [min,max] | 1 | Rocketeer `1.2`, Shotgun `1.5`, Pellet Shot `[0.75, 2.25]`, `0` | Launch speed relative to cruise speed; Rocketeer fires fast (1.2) then cruises slow (0.2) until its thruster kicks in. Range form as above. `0` = no launch speed (see `speedMultiplier`). **At most 3**; the editor calls it "launch". | Confirmed (editor code) |
| `numBullets` | int | 1 | Shotgun, Dual-Barrel `4`; Pellet Shot `10` | Projectiles per shot from this barrel, **1–10**. The editor: "Fired together, each with its own spread. Shotgun fires 4." | Confirmed (editor code) |
| `bulletSizeMultiplier` | number \| [min,max] | 1 | `0.43`–`1.5`; `2.3`; `[0.6, 1.5]` | Projectile radius, **at most 3** (slider 0.2–3). A range rolls each shot's size (two human tanks). **2026-09-28** (Builder Lab): a 1.5 bolt from a 2.6 ballista's turret gun came out almost the ballista's size, which fits "parent × this ÷ 2" (1.95) better than an absolute 1.5. On a projectile's sub-barrel the number was first read as the **same absolute scale**, not relative to the parent: under a 2.0 stationary segment, end pieces of 0.5 / 1.0 / 2.0 measured about ¼ / ½ / 1.2× the segment (the `taper-size-test` test build, 2026-09-26). **Revised 2026-09-27** (croc tail screenshot): that test's parent was 2.0, which cannot tell "absolute" from "relative, half the parent per unit"; under a 1.5 parent a 1.15 child came out about half the parent, not 0.77, so **a sub-barrel's bullet radius = parent radius × this ÷ 2** (Skimmer's side shots are half its missile). Use 1.6 for an 0.8 step. Polygon bullets (`sides` ≥ 3) draw at about 1.3× the round radius, like polygon hulls: a 1.5 octagon segment outsized a 44-radius head. | Confirmed; ÷ 2 rule Medium |
| `reloadMultiplier` | number | 1 | `0.2`–`12` | Reload time multiplier (higher = slower), **at most 20** (slider 0.1–20). Destroyer-class 4, spawners 3–6, Boss 12. **Import budget**: a barrel fires every ⌈15 × 0.914^ReloadCap × this⌉ ticks and the tank may create at most 120 entities a second and keep 250 alive (§7a). | Confirmed |
| `delay` | number | 0 | `0.5`, `0.2`/`0.4`, `0.01`, Rocketeer `7` | Firing phase in units of this barrel's reload period: 0.5 alternates Twin/Octo (verified in game on a custom two-barrel tank), 0.2/0.4 stagger Predator's burst, 7 makes the rocket wait seven short reloads before thrusting. 0.01 on auto-turret barrels. **At most 10.** The editor: "Past 1 it sits out whole cycles before its first shot, which is how a rocket coasts before its thruster lights." | Confirmed |
| `spreadMultiplier` | number | 1 | `0` (Hitman), `0.1`, `0.3`, `3` | Shot scatter (ref §6 hidden stats), **at most 20**. `0` = perfectly straight. | High |
| `lifetime` | number \| [min,max] | base default (bullets ≈ 3 s) | traps `24`, `9.6`; drones `4.2`; missile `3.9`; sub-bullets `0.9`, `0.75`; player-built `[12, 22.5]` | Projectile lifetime in **seconds**, **at most 30**. Unset, the budget counts 3 s whatever the base (§7a). Trap 24 and swarm 4.2 match ref §5; a 3.9 missile lived ≈4 s in test. A two-element range rolls each shot's lifetime (17 tanks of a player-built pack: eggs that hatch at different times, fire breath of uneven reach). Range confirmed in play (the lab's Egg Lab, 2026-09-28: a layer with projectile [egg, golden egg] and lifetime [12, 22.5] dropped a golden egg about every other time, the eggs hatched at clearly different times, and each burst's yolk and white hurt and shoved nearby shapes). | Confirmed |
| `recoilMultiplier` | number | 1 | `0`, `0.3`, `3`, `6`, `17` | Recoil on the owner (or on the carrying projectile: missile thrust), **at most 20**. | Confirmed |
| `knockbackMultiplier` | number | 1 | `0.05`–`1.2` | Knockback the projectile deals on hit, **at most 20**. | High |
| `numDrones` | int | — | `2`, `6`, `11`, `24` | Max live drones for this spawner, **at most 24** (a drone barrel without it gets 24). Overlord 4 × 2 = 8, Necromancer 2 × 11 = 22 (ref §5). Written on every drone barrel. A tank may have 96 drones in all (§7a). | Confirmed |
| `droneAggressiveCrashRadius` | number | 900 | `900`, Factory `1200`, Battleship `1600` | Written on every drone barrel; the editor fills in 900 when it is missing and clamps it to **at most 2000**. How far from the owner uncontrolled drones will range to attack: in test, drones with 2000 roamed much further out than drones with 50. | Confirmed |
| `preSpawn` | int | 0 | Resurrector `2` | Drones present the instant the tank spawns (verified: Resurrector appears with two). **But** `preSpawn: 8` with `numDrones: 8` and `reloadMultiplier: 6` did not: the drones appeared one by one at the reload rate (2026-09-26). Either there is a cap, or the reload gates it; untested which. **2026-09-26** (the `prespawn-test` test build): on ordinary projectile-drone spawners `preSpawn` 2, 3 and 8 (reload 1 and 6) all did nothing: no drone was out at spawn and they trickled in at the reload rate. Resolved with the `prespawn-necro-test` test build: **on a `holdsRaised` (Necromancer-style) barrel, `preSpawn` N makes that barrel emit N free drones on its own right after the tank spawns**, in quick succession rather than pre-placed (2 per raiser stopped at 4 squares with nothing killed; 8 per raiser gave well over ten). On projectile-drone spawners it does nothing. The editor also drops `preSpawn` and `holdsRaised` from a projectile's barrels, and keeps `preSpawn` only on a `holdsRaised` barrel, at most `numDrones`. | Confirmed |
| `droneControllable` | bool | true | Hybrid, Overtrapper `false` | Barrel-level copy of the projectile's `drone.controllable`. Stock tanks set both. **On its own it does nothing** (2026-09-26, the `controllable-test` test build): `false` here with `drone.controllable: true` gave ordinary steerable Overlord drones, while `true` here with `drone.controllable: false` gave fully AI drones. The projectile field is the one the engine reads; write both to look stock. | Confirmed (no effect alone) |
| `mountTurret` | int | absent = hull | `0`–`6` | Index into `turrets[]` (the tank's for a tank barrel, the **projectile's** for a sub-barrel, §5b); barrel rides the turret's rotating head. On a `range: 0` `controllable` pivot a `firesOnSecondary` barrel did not fire at all (SpongeBob, 2026-09-28; §6 `firesOnSecondary`). | Confirmed |
| `mount` | int | absent | `0`, `2`, `4` | Index into **this same barrel array**: the barrel is attached to another barrel and follows it. Used for launcher tips (`distance` 20, `startDistance` 30, `muzzleScale` 1.75, `bulletType: none`) mounted on each trap launcher of Auto Trapper and Defender's Son. A `mount`ed barrel counts toward the import budget only with `forceFire` or when its parent sits on a turret (§7a). | High |
| `invisible` | bool | false | `true` (the serpent's teeth and tail dropper; 75 barrels in one player-built pack) | The barrel is **not drawn** but still fires. Absent from every export's SVG. The human packs' way to add damage points, trails, beams and hidden auto-fire without changing the picture. | Confirmed (drawing); High (fires: the serpent's tail is made this way) |
| `color` | int | grey (1) | missile sub-barrels `27` | Palette index for the barrel body (§10); 27 draws in the body's colour (the team colour when the body is 27 too), which is why missile barrels are tank-coloured (ref §5). | Confirmed (editor code) |
| `order` | int | 0 | `-1`, `1`, up to `48` | Draw order (§9a). Negative allowed; deployer bases use −1 to sit beneath the main barrel. | Confirmed |
| `flags` | object | | §6 (`forceFire`, `holdsRaised`, `firesOnSecondary`, `firesOnDeath`, `aboveBody`) | | |
| `editor` | object | | `{"name": "fore wing right"}`, `{"group": "Secondary", "name": "Barrel 3"}` | Part label shown in the editor's part list, as on body shapes (§8). Native exports only carry it on shapes, but the editor shows it on barrels and turrets too (verified 2026-09-26 with a pack naming every part). `group` is a folder name in that list (one player-built pack sorts barrels into "Main" and "Secondary"). Generators should name every part. | Confirmed; `group` High |

### 7a. The import budget: what the lobby refuses

**Confirmed 2026-09-29 from the editor's own code.** The sandbox editor carries its own copy of
the lobby's check and shows it before you load a pack ("Over budget, the lobby would refuse
it"). `validate_pack.py` ports it line for line, and the port reproduces every refusal on record
exactly:

| Tank | Message from the game | Port |
|---|---|---|
| croc, build 1 (Reload cap 12) | `fires too much: 196/120 per second, 71/250 in the air` | 195.8, 70.8 |
| croc, build 2 | `fires too much: 121/120 per second, 66/250 in the air` | 120.8, 65.8 |
| Web Lab (24 drawing-only rods on its web) | `fires too much: 84/120 per second, 437/250 in the air` | 84.4, 437.1 |
| Builder Lab (buildings with turret guns) | `fires too much: 132/120 per second, 112/250 in the air` | 132.4, 112.0 |

Every other tank on file comes out under every limit, and the largest player-built tanks sit
right at them (119.9/s, 250.0 in the air, 64 per volley, 96 pieces, 96 drones), so their builders
designed against these very numbers. There is no margin to leave.

**Six limits.** The lobby refuses the first one a tank passes, checked in this order:

| Limit | Message | What counts |
|---|---|---|
| 96 drones | `has N drones; a tank may have 96` | live drones: `numDrones` per drone barrel, × each carrier alive when drones carry drone barrels |
| 96 pieces | `has N pieces; a tank may have 96` | shapes + barrels + turrets on the tank and on every projectile (§9c) |
| 64 per volley | `puts N entities out per volley; a tank may put out 64` | one pull of every trigger: each firing barrel's `numBullets` × (1 + the pieces of its biggest projectile), plus the `numBullets` of every firing sub-barrel on every projectile |
| 120 per second | `fires too much: R/120 per second, A/250 in the air` | entities created per second (below) |
| 250 in the air | (same message) | of those, alive at once |
| 2000 room | `takes too much room: N/2000 bullet-areas in the air` | collider area of everything alive, a standard bullet = 1 |

**How it is counted.** The whole tank, the Reload stat at its cap, every trigger held: left
click, right click and auto-fire all at once.

- **Reload.** A barrel fires every ⌈15 × 0.914^cap × `reloadMultiplier`⌉ ticks (at least 1),
  cap = `statsMaxLevel[1]`, 25 ticks a second. At reload 1 that is 3.1/s at cap 7, 4.2/s at
  cap 12, 1.7/s at cap 0; whole ticks make very short reloads cheaper than proportional (cap 12:
  reload 0.25 and 0.5 cost 12.5 and 8.3). **Lowering the Reload cap is the cheap way to buy
  budget**: a large player-built pack sets it to 0 on 47 of its 60 playable tanks.
- **What a shot costs.** Each shot counts `numBullets` × (1 + the projectile's pieces:
  parts + barrels + turrets, drawing-only rods and cosmetic parts included). A web with 24 rods
  is 25 per shot. A barrel that picks at random (`projectile: [a, b]`) counts at its costliest
  option.
- **In the air** = per second × lifetime. An unset `lifetime` counts **3 s**, even on traps
  (their in-game default is 24 s, but the budget does not see it). A `[min, max]` lifetime
  counts its max.
- **Sub-barrels.** A barrel on a projectile adds its own shots **once per live copy** of the
  projectile, only if it actually fires: on a drone, always; on a bullet or trap, only with
  `forceFire` or when it sits on one of the projectile's turrets (§5). A `firesOnDeath` one fires
  once per shot, and only if the projectile has a `burst` trigger set. Chains are followed to
  eight levels.
- **Drones** do not count per second or in the air; they count against the 96-drone limit and
  the room, `numDrones` each.
- **Room.** A round bullet's radius is 21 × `heightMultiplier` × `bulletSizeMultiplier` (its
  max when a range); drones, traps and polygon (`sides` ≥ 3) bullets are 42 × 0.707 × the same.
  Room per live shot = (radius ÷ 21)², so a 2× shot costs 4 and a 3× shot 9, and each of up to
  three collidable parts adds (part size × radius ÷ 50 ÷ 21)². Cosmetic parts are free.
- **Tank barrels.** Every hull barrel counts. A barrel mounted on another barrel (`mount`) counts
  only with `forceFire` or when its parent sits on a turret.

`validate_pack.py` reports each limit as an ERROR, worded as the game words it, and
`--summary` prints all six figures for every tank; `compose.save()` shows them on every build.
