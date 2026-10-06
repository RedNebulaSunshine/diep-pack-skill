## 5. Projectile (`tanks[].projectiles[]`)

Definitions indexed by position; a barrel fires the definition(s) its `projectile` field
lists. Definitions may be shared or unused. **Editor limits** (its import code, 2026-09-29,
unchanged by the 2026-10-06 update): 16
projectiles per tank; per projectile 32 barrels, 32 parts (of which at most 3 collidable, those
at most size 150, the rest 300; a tank keeps 8 since 2026-10-06, a projectile still 3) and 8 turrets.
Everything a projectile carries counts toward the tank's 96 pieces and multiplies its shot cost (§7a).
A projectile's `parts` and sub-barrels take `mountPart` and `fixedRotation` like a tank's (§8).

```json
{"name":"Missile","base":"bullet","sides":-1,"spin":0.1,"spinFlipsOnSecondary":true,
 "barrels":[{"flags":{"forceFire":true},"distance":70,"heightMultiplier":0.9,"bulletType":"bullet",
             "projectile":1,"damageMultiplier":0.6,"penetrationMultiplier":0.4,"speedMultiplier":0.63,
             "reloadMultiplier":0.35,"lifetime":0.9,"delay":0.5,"color":27}, …]}
{"name":"Minion (Twin)","base":"drone","sides":0,"drone":{"keepDistanceMin":300,"keepDistanceMax":800},
 "barrels":[{"offset":-26,"bulletType":"bullet","projectile":5, …},{"offset":26, …,"delay":0.5}]}
```

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `name` | string | `"Minion (Sniper)"`, `""` | Editor label. Always written. | Confirmed |
| `base` | enum | `bullet` \| `drone` \| `trap` | The editor's "based on" dropdown has exactly these three. Missiles are bullets with forceFire sub-barrels; minions are drones with ordinary sub-barrels. | Confirmed |
| `sides` | int | `-1`, `0`, `4`, `18` | `-1` = the editor's "As usual" shape for the base (round bullet, triangle drone, star trap). Otherwise "Its own": polygon side count, `0` = circle (Factory minions), **at most 18**. The editor: "Under 3 draws a circle: the engine draws an arc, not a polygon with a lot of sides." Always written. | Confirmed |
| `star` | bool | `true` | "Drawn as a star" for an "Its own" shape. | Confirmed |
| `spin` | number | `0.1` (missiles), `-0.5` | Rotation per tick; sign = direction; **clamped to −0.5…0.5**. | Confirmed (editor code) |
| `spinFlipsOnSecondary` | bool | `true` | Spin reverses while secondary fire is held — the Skimmer rule (ref §5). Official Skimmer and Cyclone carry it. | Confirmed |
| `color` | int \| string | `22`, `25`, `"#b5323a"` | Palette index (§10), or since 2026-10-06 a hex string `#rrggbb` / `#rrggbbaa`. Absent = team colour. Verified on drones: `color: 25` drones are forest green in game (2026-09-26). A barrel's `forcedBulletColor` with `flags.forceBulletColor` (§7, the stock bosses) is the other way to colour a shot; which wins is a play question. | Confirmed |
| `burst` | object | `{"onSecondary":true,"onDestroyed":true,"onExpire":true}` | Editor section "Burst" with three checkboxes: `onSecondary` "Right click sets it off", `onDestroyed` "Getting destroyed sets it off", `onExpire` "Running out of time sets it off". "Setting off" **ends the projectile**; what happens then is decided by its sub-barrels: those flagged `firesOnDeath` (§6) fire once as it dies. Stock Firework ("Right click to explode your bullets") is a hexagonal shell with `burst.onSecondary` and 24 hidden `firesOnDeath` sub-barrels. In tests without `firesOnDeath` the projectile simply vanished on right-click, which matches. The reverse holds too: with no trigger set the editor says "Off: it just dies. Turn one on and guns on it can fire when it does", and its budget counts a `firesOnDeath` gun only when a trigger is set. A payload that must go off by itself near a target is not a burst at all but a turret gun with a long reload (recipes §33); `burst` then only ends the projectile early. | Confirmed |
| `barrels` | Barrel[] | | Barrels carried by the projectile (§7). Their `projectile` indexes the **tank's** `projectiles[]`. Firing is governed by flags (§6): `forceFire` fires continuously (missiles), `firesOnDeath` fires once when the projectile dies (Firework), no flag fires on the owner's fire command (Factory minions; on a plain bullet this never fired in test) **unless the sub-barrel is on one of the projectile's `turrets`**: then it is an auto-turret gun and fires at targets on its own, with or without `forceFire`, until the projectile dies (Sentry test, 2026-09-26). **A projectile's barrel may fire only a projectile that carries nothing** (no barrels, parts or turrets) and is not the projectile itself; otherwise the editor swaps in a plain default shot of the barrel's type on import (round, in the owner's colour, nothing on it). Read from the editor's import code 2026-09-29, and it explains both earlier sightings: a projectile referencing itself came out as a default round bullet, and a croc-tail chain (2026-09-27) spawned one plain round stage without its `parts` and never a third. **Confirmed in play 2026-09-29** (SpongeBob): a Cyan bubble whose six `firesOnDeath` barrels fired a Cyan "Little bubble" carrying a White shine part popped into six **Yellow** bubbles (the body's colour) with no shine. Give a spawned shot no parts and it keeps its own colour and `sides` (confirmed the same day: without the shine the little bubbles came out Cyan). So chains are one level deep, and the spawned shot is a plain one. For a graded taper fire one tank barrel per stage with growing lifetimes (`d.trail(stages=…)`). A sub-barrel's `mountTurret` indexes the **projectile's** own `turrets[]` (§5b). | Confirmed |
| `drone` | object | see §5a | Drone-only behaviour. | Confirmed |
| `parts` | BodyShape[] | see §5b | Decorative polygons drawn on the projectile, same schema as `bodyShapes` (§8). Drawn in play and turning with the projectile (2026-09-26, the `shot-parts-test` test build); drawn **under** the projectile's disc unless `aboveBody`, and in a frame **scaled to the projectile**: a triangle 45 ahead on a 1.2 bullet showed as a tiny nose at the rim and dots at 40 were hidden under the disc, so the projectile's own radius seems to count as 50, like a hull (Medium: inferred from one test; human packs use part sizes 20–75 with `aboveBody`, which fits). | Confirmed (drawn); scale Medium |
| `turrets` | Turret[] | see §5b | Auto-turrets carried by the projectile, same schema as §9; at most 8. **A recoil engine on one steers the projectile**: a rear `forceFire` sub-barrel with `mountTurret` 0 on a turret that tracks targets pushes the missile toward them (a heat-seeking missile), and a gun with a long reload on a second, short-range turret fires by itself when something comes close (a proximity fuse); draw them under the bullet (`aboveBody: false`). The arc is measured from the launch heading (§9). A player's write-up and pack, confirmed in their play (2026-10-05); recipes §33. | High |

### 5a. Drone settings (`projectiles[].drone`)

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `idle` | enum | absent \| `"hover"` \| `"cruise"` | Editor "Drone style": `hover` (the default, so usually absent) = "Standard (Overlord)", `cruise` = "Swarm (Battleship)". Only these two exist. | Confirmed |
| `controllable` | bool | `false` | `false` = AI-only drones the player cannot steer (Battleship's second spawner pair, Hybrid's and Overtrapper's auto drones, ref §5). Default true. Stock Hybrid sets this **and** the barrel-level `droneControllable: false` (§7); Battleship sets only this one. **This is the switch the engine reads**: alone it made drones fully AI, while the barrel switch alone changed nothing (the `controllable-test` test build, 2026-09-26). | Confirmed |
| `keepDistanceMin` / `keepDistanceMax` | number | `300` / `800` (all Factory minions) | Distance band the drone holds **from its target**. Confirmed 2026-09-26 (the `keep-distance-test` test build, band 300–400 on plain drones): at rest with no target they nuzzle the owner; sent at a far shape they fly to it and circle it at a distance, never touching it, where stock Overlord drones ram. So any drone can be made to stand off like a Factory minion. Each **at most 2000**. | Confirmed |
| `repel` | bool | `false` (three human drones: a one-off "familiar", two character companions) | Whether right-click repels the drone; `false` = the player cannot push it away. Default true. Confirmed in play 2026-09-26: four Overlord-style drones with `repel: false` did not scatter on right click. | Confirmed |

### 5b. Decoration and turrets on projectiles (`projectiles[].parts`, `projectiles[].turrets`)

Human packs decorate bullets, drones and traps the way tanks are decorated, and even arm
them. `parts[]` uses exactly the body-shape schema (§8: `sides`, `size`, `xOffset`,
`yOffset`, `angle`, `spinSpeed`, `star`, `color`, `aboveBody`, `collidable`, `order`,
`mountTurret`, `editor`), in the projectile's own frame (x = its heading). `turrets[]` uses
the turret schema (§9, including `baseSize`, `range`, `arc`, `angle`, `controllable`,
`color`); a sub-barrel or part with `mountTurret` rides one of **these** turrets.

```json
// A player-built tank (level 15 off Tank): a bullet carrying an auto-turret and gun
{"name":"Bullet","base":"bullet","sides":-1,"turrets":[{}],
 "barrels":[{"distance":55,"heightMultiplier":0.7,"mountTurret":0,"bulletType":"bullet","projectile":1,
             "damageMultiplier":0.3,"penetrationMultiplier":0.5,"speedMultiplier":1.2,"reloadMultiplier":3,"recoilMultiplier":0.3}]}
// A player-built "portal": a triangular shell with a second triangle riding on it
{"name":"Spike","base":"bullet","sides":3,"color":16,"parts":[{"sides":3,"size":55,"xOffset":2.7,"yOffset":54,"color":16}]}
// A player-built glitch tank: a 7-point star bullet with an eye drawn on it
{"name":"","base":"bullet","sides":7,"star":true,"parts":[{"sides":0,"size":12,"aboveBody":true,"color":4},{"sides":0,"size":8,"aboveBody":true,"order":1,"color":20}]}
```

Structure is High (59 projectiles with `parts`, 43 with `turrets` across the packs).
**Confirmed in play 2026-09-26** (the `sentry-test` test build): the turret is drawn on the
bullet, and its gun fires at shapes and enemies on its own until the bullet expires, whether
the gun is unflagged (the human way) or `forceFire`; the player's fire button plays no part.
The editor's SVG export does not draw projectiles, so `parts` geometry is unverified by
`render_pack.py`. In play (2026-09-26) parts are drawn and turn with the projectile; they
sit under its disc unless `aboveBody`, and their coordinates appear to be in a frame where
the projectile's radius counts as 50 (a part 45 ahead of a 1.2 bullet was a tiny nose at the
rim). Design them as if decorating a hull, and use `aboveBody` for anything inside radius 50.

**A player-built pack (2026-09-28) goes much further** (recipes §28–30). Of its projectiles, 57 carry
*drawing-only* sub-barrels (`bulletType: "none"`, `projectile: -1`, `flags.aboveBody`): a web of
eight spokes and sixteen chords on a trap, a trident's shaft and tines, a chick's beak, a
golem's arms; `render_pack.py --projectiles` draws them as pseudo-tanks (disc = hull of radius
50). Twenty-two drones are whole characters: `parts` (one warrior's twin reuses his
own 24 shapes), `controllable` limb turrets with `arc` and `range` 750, a hidden auto-turret
(`range` 650, `aboveBody: false`) carrying invisible stationary "fist" barrels, and a rear
recoil barrel flagged `forceFire` + `firesOnSecondary` so the drone lunges on its own. A trap
carrying an enemy-tracking turret whose backward recoil barrel (`mountTurret`, recoil 4.6,
reload 0.3) fires at the target is pushed toward it: a walker. A bullet placed with
`speedMultiplier` 0 and `lifetime` 27 carrying auto-turrets is a building. All of this imports
and re-exports (High). **Confirmed in play** for the web (the lab's Web Lab, 2026-09-28: the web drew as designed and lasted about 5.5 s; shapes took damage only from its centre disc and its two collidable hook stars, never from the rods, and were not pushed back): drawing-only
sub-barrels draw on the projectile and never collide; its `collidable` parts do. **Figure drones confirmed in play** (the lab's Summon Lab, 2026-09-28: both twins appeared on their own as soon as the tank spawned, one shortly after the other, never more than two, with no click; they hunted shapes, boosted themselves toward them with their own recoil barrel and punched; their controllable arms ignored the owner's cursor and moved on their own, turning toward shapes): a drone's `controllable` turret
does not follow the owner's cursor, and a drone spawner fills up to `numDrones` on its own
whatever its button flags. **Walkers and buildings confirmed in play** (the lab's Builder Lab, 2026-09-28: both buildings lasted about 27 s. The ballista stayed put and its turret gun shot bolts at nearby shapes on its own, but its arrow picture, drawn on the ballista's body, never turned, so the bolts seemed to leave from any side. The bolts kept their own colour and seven sides, and at size 1.5 off a 2.6 ballista they came out almost as big as the ballista. The golem walked forward on its own, meandering a little and punching shapes on its way, until it left the map: its auto-firing walk barrel pushes it even with no target, and the turret only bends the path inside its 75-degree cone).
Rods and parts on a projectile's turret (`mountTurret`) turn with it; on the projectile itself
they do not.

## 6. Barrel flags (`barrels[].flags`)

| Key | Seen on | Meaning | Confidence |
|---|---|---|---|
| `forceFire` | every spawner; every missile sub-barrel | Barrel fires continuously without player input. Drones spawn on their own; missiles thrust and spray. Required for a sub-barrel on a bullet to fire *in flight* (`firesOnDeath` fires without it). Combined with `firesOnDeath` (the serpent's tail) the sub-barrel fires throughout the parent's life *and* at its death: in play the end pieces then shimmer out from under the living segments (serpent A, 2026-09-26). | Confirmed |
| `holdsRaised` | Necromancer, Resurrector spawners | The spawner's drone slots are filled by raised polygons (`raises`) instead of spawned projectiles; such barrels have `projectile: -1`. The editor: "Shapes it kills rise as its drones and fill a barrel that fires 'Raised shapes': its slots, plus one per Reload stat point (what Necromancer calls Drone Count). Such a barrel can also spawn a few of its own" (`preSpawn`, §7). Dropped from a projectile's barrels. | Confirmed (editor code) |
| `firesOnSecondary` | Striker front barrel; Dual-Barrel's right-hand group | Barrel fires on right-click instead of left-click ("Right click to fire your front barrel", "Right click to shoot your other barrel"). **Not on a cursor pivot**: a Destroyer barrel with `firesOnSecondary` mounted on a `range: 0` `controllable` turret never fired on right click (SpongeBob, 2026-09-28), while a left-click barrel on the same kind of pivot fires; put a right-click weapon on the hull (invisible, where the held item rests): that fired the patty on right click (confirmed the same day). | Confirmed |
| `firesOnDeath` | Firework shell sub-barrels | Sub-barrel on a projectile fires once when that projectile dies, whether by `burst`, damage or expiry. Firework's 24 such barrels have `distance: 0` so they are invisible until they fire. Expiry confirmed in play 2026-09-26: `burst.onExpire` plus this flag alone spawned the serpent's tail end pieces (serpent B). | Confirmed |
| `aboveBody` | human packs only (280 barrels) | **Draw this barrel over the hull** (the flag lives under `flags`, unlike the shape field). Used for line art: hair-thin barrels (`heightMultiplier` 0.1–0.15) drawn as mouths, brows and seams on a face, wings as fans of dark rods over the body, or a mounted rod that must show over its turret disc. Drawing verified against every export (§9a); the editor's preview splits barrels the same way ("The body splits what draws over it from what draws under it"). | Confirmed |

`forceFire` on a **tank-level** bullet barrel (not a spawner) makes an auto-firing gun: the
creature's teeth and tail dropper fire continuously without a click (human packs, 105 + 269
such barrels). Combined with `invisible` and a stationary shot (§7) it becomes a damage
field or a trail.
