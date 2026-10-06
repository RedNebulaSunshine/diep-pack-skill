# `.diep-pack` format: how to read this spec

Diep.io publishes no documentation for its sandbox pack format. This spec was reverse-engineered
from the editor's own exports (every stock tank copied out of the game, the official 10th
Anniversary pack, user exports that push fields to extremes, the editor's SVG exports for exact
geometry) and from in-game tests that changed one thing at a time. **Since 2026-09-29 it is
also checked against the editor's own code**, which the game serves as one readable script: its
import normaliser (every default, clamp and count limit below), its export writer, its copy of
the lobby's import budget (§7a, which reproduces every refusal on record exactly) and its help
text for each field. `tools/editor_probe.py` in the builder repository re-reads it after a game
update and reports what changed. Six large packs built by other
players (326 tanks) were studied for what the editor can do beyond the stock tanks; they are not
redistributed here, but what they taught is recorded field by field.

The spec is split by family. Read the family a design touches:

| File | Covers |
|---|---|
| `01-pack-and-tank.md` | pack envelope, `hidden`, `starters`, custom arena `shapes` and their spawn budget (§1a), custom **bosses** and the boss rotation (§1b); tank fields, stat caps, tree links |
| `02-body-and-invisibility.md` | hull polygon and stealth |
| `03-projectiles.md` | bullets, drones, traps, `burst`, drone settings, decorated and armed projectiles, barrel flags |
| `04-barrels.md` | every barrel field, and the fire-rate import limit (§7a) |
| `05-shapes-and-turrets.md` | body shapes (including parts that ride parts and fixed rotation), turrets, draw order, the drawing rules, the 32-part limit |
| `06-palette-and-ids.md` | colour palette with the editor's swatch names, exact hex colours with opacity; vanilla tank IDs |

**Checked against the editor's code of 2026-10-06** (bundle `index-67ee240f.js`, the update that
added custom bosses, exact colours, parts riding on parts, fixed rotation, eight hitboxes per tank
and a shape spawn budget). Everything from that update is tagged **Confirmed (editor code)** until
played; the open play questions are in §13 item 22.

Section numbers (§1 to §13) are kept from the original single document so cross-references in
the recipes, the scripts and the validator still resolve. `references/quick-reference.md` condenses
all of it to one table per family for everyday use.

## 0. Conventions

### Confidence tags

Observed type, presence and example values are facts about the files. Each *Meaning* entry
carries one tag:

- **Confirmed** — verified in game or in the editor UI in play-testing, or unambiguous from an official tank.
  **Confirmed (editor code)** — read from the editor's own code (its defaults, limits and help
  text); what the game then does with the value may still rest on a play test.
- **High** — pinned down by the data or by an exact match to a documented concept.
- **Medium (inferred)** — name and values point strongly one way; alternatives not ruled out.
- **Low (inferred — unverified)** — a plausible guess. Listed again in §13.

### Format conventions

- Plain UTF-8 JSON, single line. Extension `.diep-pack`; `.json` content is identical.
- **Import.** The editor imports a whole pack from a file or from pasted text (prefer the
  file: one 4.7 KB pack was rejected as invalid when pasted yet imported fine from a file
  with byte-identical content), with two
  modes: "add to this pack", which appends the tanks and **reassigns their `id`s**, and
  "import as new pack". Tank IDs therefore never need to be unique across packs. The
  editor also copies any stock tank into a pack and exports any tank, or the whole roster,
  as SVG.
- **What import does to a pack** (the editor's code, 2026-09-29). Every pack passes through
  one normaliser before the editor shows it, and what the lobby receives is the editor's own
  re-export of the result. It **drops** what is past a count limit (512 tanks, 256 custom
  shapes, 16 projectiles; per tank and per projectile 32 barrels, 32 shapes or parts, 8
  turrets, §9c; 512 bosses, §1b), **clamps** numbers to the ranges given with each field (barrel length,
  offset and gap ±500, width 2.5, reload 20, bullet size 3, lifetime 30 s, 24 drones, hull
  size 67, 18 sides, stat caps 12, and so on), **fills in** its default for a missing field,
  keeps only the first **eight** `collidable` parts of each tank (three before 2026-10-06) and
  three of each projectile, clears a `mountPart` that points at nothing, at itself or more than four
  deep (§8), and silently
  rewires what cannot work (a projectile's barrel that fires a projectile carrying pieces gets
  a plain default shot, §5). Nothing warns; `validate_pack.py` reports each case instead.
  Unknown keys pass through untouched (that is how the stock bosses' `forcedBulletColor`,
  `droneSides` and `minDamageMultiplier` survive a round trip, §7 and §1b), and so do the legacy keys of old stock data
  (`addFinalAngle`, `bulletTimeLeftMultiplier`, `flags.largeRectSide` and the like), which it
  converts. The lobby refuses a pack whose export passes **900 KB** (the pack screen shows
  "This pack is N KB; the lobby takes 900 KB"), and since 2026-10-06 a pack whose spawning shapes
  pass the **shape budget** (§1a: "Shapes take too much room" / "<name> crowds its spawn ring").
- **Angles are radians**, positive = clockwise on screen when facing the aim direction.
  Negative values and values above π both appear; nothing is normalised.
- **Time units.** `lifetime` is seconds. `spinSpeed`, `spin` and `invisibility.gain` are
  per tick (25 ticks/s): `spinSpeed: 0.0628` turned a hull once in 4.0 s. `delay` is in
  the barrel's own reload periods.
- **Distance units** are the game's world units at level 1: default hull radius 50,
  default barrel 95 long and 42 wide.
- **Numbers.** The game stores float32; copied vanilla data comes out as float32 rounded
  into a double (`0.699999988079071`), user-entered data as clean doubles. Ints and floats
  are interchangeable. Writers may emit clean decimals.
- **Sparse export.** Fields at their default are omitted, except a few that are always
  written (§12). Absence in every sample is therefore not proof that a field does not exist;
  the vanilla copies are the only near-complete field inventory.
- The editor's preview and SVG export rotate the tank by −45°; ignore that when reading SVGs.


## 12. What the editor always writes vs. omits

**Always written:** pack `version`, `name`, `tanks`; tank `id`, `name`, `minLevel`,
`body.sides`, `invisibility.gain`, `invisibility.lossOnHit`, `statsMaxLevel`; projectile
`name`, `base`, `sides`; barrel `bulletType`, `projectile`; drone barrel `numDrones`,
`droneAggressiveCrashRadius`; body shape `sides`; boss record `id`, `tank`, `name` (§1b: the
game's own export of its six bosses writes only those and the numbers that differ from the
defaults). Official exports additionally always
write `invisibility.lossOnAttack` and `lossOnMovement`. Pack `author` and shape `size` (25)
are omitted by some human exports, so neither is required.

**Omitted at default:** everything else, including `projectiles` and `barrels` when empty.
The editor's writer (read 2026-09-29) drops every field equal to the default the game engine
reports for it, except `id`, `version`, `name`, `base`, `bulletType`, `sides` and `projectile`,
which it always keeps; that is why the list above mixes format rules with engine defaults.
A generator that omits defaults the same way produces files indistinguishable from native
exports; one that writes defaults explicitly is also accepted (the game-authored Auto 7
writes `aboveBody: false`).


## 13. Remaining open questions

22. *(found 2026-10-06, the editor update; read from the editor's code and the game's own export of
   its bosses; first probe played the same day)* **The editor update of 2026-10-06.** Resolved in play
   (the lab's Editor Update Probe 0.1.0): **27 parts on a hex hull show the team colour**, see-through
   with a grey outline while no team is assigned (§10); **riding parts orbit** with their spinning
   carrier and draw under it unless `aboveBody` (§8); a **fixedRotation** part holds still while the
   tank turns (§8); all **eight collidable** parts collide (§8); a drone barrel's **projectile list**
   hatches a mix (§7); a projectile's own `color` beats `forcedBulletColor` (§7); `spawn_boss <name>`
   spawns a custom boss (§1b); probe 0.2.0 added that a hex colour's **alpha draws translucent** in
   play, over the hull and over arena shapes (§10), and that a **barrel riding a part turns with it
   and fires** (§7, §8; the editor's tooltip "Looks only; it fires nothing" is wrong). Still open: the
   **simple** and **bot** brains with custom guns; a boss from a **stock tank** at scale 4; the
   rotation sentence after loading; what `minDamageMultiplier` changes (probe 0.3.0: three identical
   one-gun boss tanks at 1 / absent / 6) and what `ai.directionChangeSpeed` does.

Resolved: Q1–9, Q11–19, Q21–26 of the original list, plus `preSpawn`, `burst`,
`firesOnDeath`, `numBullets`, range-valued multipliers and `droneControllable` found along
the way. The human packs (2026-09-26) settled the drawing unknowns (star inner radius 0.4,
`sides` 0/1 circles, `body.angle` applied, negative `startDistance`, widths 0.1–2.5, tapers
0.04–7.5, 70 parts), fixed Shotgun/Glider/Firework at 62/63/64 and added the fields in §1a,
§5b, §6 `aboveBody`, §7 `invisible`, §8 `star`/`mountTurret`/`mount`/`staysVisible`, §9
`baseSize`/`color`. Still open, with the cheapest check:

1. *(resolved 2026-09-26)* `hidden` alone empties the class tree and `starters` picks the
   spawn tank: importing a total-conversion pack left only its tanks and a new life began as its first tank.
2. *(resolved 2026-09-26)* 58, 60, 61 are Auto Tank, Dual-Barrel, Pellet Shot: the
   an ID-probe pack probes appeared under those classes.
3. *(resolved 2026-09-26)* `drone.keepDistanceMin/Max` is measured from the target (§5).
4. *(resolved 2026-09-26)* the projectile's `drone.controllable` wins; the barrel's `droneControllable` has no effect alone (§5, §7).
5. *(resolved 2026-09-29 from the editor's code)* `revealDistance` defaults to 0 (never
   reveals), a turret's `range` to 1700 and `arc` to 0, which is the full circle. The in-game
   default `lifetime` per base is the engine's (traps 24 s), but the import budget counts an
   unset lifetime as 3 s. Still open: the exact contact radius of a `collidable` part (§8:
   about two thirds of the drawn radius, one coarse reading with a 32-shape-capped rings pack;
   the `hitbox-rings` test build now fits the cap and could pin the ratio).
6. *(resolved 2026-09-26)* `helpText` is shown centred at the top of the screen.
7. *(resolved 2026-09-26)* `preSpawn` is per `holdsRaised` barrel: N free drones emitted
   right after spawn; no effect on projectile-drone spawners (§7).
8. **Human-pack semantics never watched here** — (resolved 2026-09-26: `range: 0` +
   `controllable` follows the cursor while fire is held and rests otherwise, §9; the trail
   and its taper, §6; a projectile's turret gun fires in flight on its own, §5b; `hidden`
   alone and `starters`, §1; `drone.repel: false`, §5; `staysVisible`, §8; custom `shapes`
   spawn at a share set by `densityMultiplier`, §1a; `hiddenShapes` and `editor.disabled`,
   §1/§1a; `collidable` gives a part its own collision and a size-8 hull shrinks the hull's
   hitbox to a dot, §8; a `firesOnDeath` sub-barrel's `bulletSizeMultiplier` gives a bullet
   of half the parent's radius per unit (2.0 segment: 0.5 / 1.0 / 2.0 gave ¼ / ½ / 1.2×; 1.5
   segment: 1.15 gave about ½, 2026-09-27), §7 `bulletSizeMultiplier`).
19. *(resolved 2026-10-01)* **Shots of a faded tank** (§4): with `lossOnAttack: 0` a stealth carrier stayed faded while a `forceFire` trail dropper kept firing, and the dropped shots stayed fully visible, so any auto-fire marks where a faded tank lies.
20. *(resolved 2026-10-01)* **Colour 27 on a turret's parts** (§10): shapes mounted on an auto-turret at colour 27 show the team colour when the hull is team-coloured under a cover shape, like parts on the hull (gargoyle heads with team-coloured eye dots, play test).
21. *(found 2026-10-05, a player's write-up and sample pack, confirmed in their play; not yet replayed here)* **Guided missiles** (§5b, §7, §9, recipes §33): a rear `forceFire` recoil engine mounted on a projectile's tracking turret steers the missile; the turret's arc is measured from the launch heading, so only arc 0 chases; a long-reload turret gun on a second turret is a proximity fuse; `numBullets`, spread and recoil act on drone barrels although the editor's form hides them (its import and export carry them: read in its code). Open: what `numDrones` 2 does when a tube fires 6 drones per shot (the pack does); whether a warhead mounted on the seeker turret itself can work (the player says not, as of 2026-10-05); whether `firesOnDeath` on a turret gun fires at death as well.
18. *(resolved 2026-09-28)* **Total pieces** (§9c): at most 96 shapes + barrels + turrets per tank, its projectiles' parts, sub-barrels and turrets included (SpongeBob refused at 97; a player-built pack tops out at 96).
17. *(found 2026-09-28)* **Right click on a cursor pivot** (§6 `firesOnSecondary`, §7 `mountTurret`): a `firesOnSecondary` barrel riding a `range: 0` `controllable` turret never fired (SpongeBob's Krabby Patty); the same pivot's left-click gun fires. Whether it is the pivot kind or any turret, and whether right click moves such a pivot at all, is open: one tank with a right-click gun on a tracking turret answers the first.
16. *(resolved 2026-09-28)* **Living limbs** (§9, recipes §27): a `controllable` turret with a `range` of 250 tracks shapes in range while idle and the cursor while firing (Limb Lab); the cursor only inside its wedge. An **unset** range also tracks shapes, from further than 250 (Leg Range Lab: unset legs twitched at shapes the 250-range legs ignored); the editor's code gives its reach: 1700. Sideways legs never saw the cursor, which is always ahead of the hull and outside their wedge.
15. *(resolved 2026-09-28)* **Figure drones** (§5b, recipes §29): a drone's `controllable` turrets track shapes, not the owner's cursor; its `forceFire` recoil barrel makes it lunge on its own toward targets; its spawner fills to `numDrones` from spawn whatever the button flags (Summon Lab).
14. *(resolved 2026-09-28)* **Recoil walk** (recipes §30): an auto-firing backward recoil barrel on a trap's turret walks it forward, veering toward shapes in the turret's cone, until it expires or leaves the map; a placed bullet's turret gun shoots on its own (Builder Lab). A walk barrel without `forceFire` on a full-circle turret (`walker(wander=False)`) waits: the golem sits until a shape comes within range, walks to it and kills it, moves on to the next, and sits again (Golem Wait Lab).
13. *(resolved 2026-09-28 for `lifetime` and `projectile: [a, b]`)* **Range rolls and choices** (§7, recipes §31): Egg Lab's eggs hatched at different times and one in two was golden. `damageMultiplier`, `penetrationMultiplier` and `knockbackMultiplier` ranges import and are assumed to roll the same way (High).
12. *(resolved 2026-09-29 from the editor's code)* **Spawn depth** (§5): a projectile's barrel may only fire a projectile that carries no barrels, parts or turrets; otherwise the editor swaps in a plain default shot. So a spawned shot keeps its own colour and `sides` (the bolts) but can never carry parts or fire again (the croc's round second stage). Confirmed in play 2026-09-29: SpongeBob's shine-carrying little bubbles came out plain and in the body's Yellow. Earlier notes: bolts fired by a placed bullet's turret gun kept their own colour and seven `sides` (Builder Lab), unlike the croc's round second-stage pieces; `parts` on such a shot are still unseen. Original question: does a bullet spawned by a projectile's sub-barrel keep its colour, `sides` and `parts`, and is it really unable to fire its own sub-barrels? A two-tank pack (one stage-2 with a loud colour and a part; one with a stage-3) answers both.
11. *(resolved 2026-09-29 from the editor's code)* **Turret cap** (§9c): 8 per tank and per projectile, and 32 sub-barrels and 32 parts per projectile. Earlier notes: 8 is the most seen (a player-built pack's two biggest spiders, eight leg pivots, 2026-09-28; 7 before that); a 9- or 10-turret probe would settle it. Sub-barrel count per projectile also unmeasured. **Caveat from the cap**: the `hitbox-rings` test build carried 49 body shapes, so only its first 32 dots (in creation order) were ever drawn in play; the "contact at about two thirds of the drawn radius" reading in §8 `collidable` stands on those dots and deserves a re-run under 32 shapes.
10. *(resolved 2026-09-29 from the editor's code)* **The import budget** (§7a) is now the editor's own formula, which reproduces all four refusals exactly. Earlier fitted model, for the record: period max(15 × reload × 0.9165^ReloadCap, 1.9) ticks per firing barrel, fitted to two rejections (196 and 121 per second at cap 12) and the extreme export passing. Cheapest check: a pack of tanks with N plain barrels at caps 12, 7 and 0 (25, 39 and 72 barrels sit at about 120) tells whether the cap really moves the line; a tank with 10 barrels at reload 0.1 versus 0.3 (both 13/s under the floor) tests the floor; how in-flight is counted (long-lived bullets) is open. **Refit 2026-09-28** on two technique-lab refusals (§7a): a shot counts as 1 + its sub-barrels, drawing-only included; live sub-barrels count per live copy of their parent; drones by `numDrones`. An off-turret `forceFire` sub-barrel (a missile's thruster) counts at most once, not per live copy: a large player-built pack re-imported with such a missile tank in it (2026-09-28), which that reading put at 136/s.
9. *(resolved 2026-09-26)* Drawing leftovers: `sides: 2` is a circle; barrels over 500 are
   clamped to 500 (a drawing-leftovers test export); projectile `parts` are drawn in
   play, under the disc unless `aboveBody`, in a frame scaled to the projectile (§5b; the
   exact scale is inferred, not measured).

