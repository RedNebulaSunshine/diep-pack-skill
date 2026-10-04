---
name: diep-pack
description: "Design custom Diep.io content as a .diep-pack for the official sandbox editor from a plain-English description: tanks (barrels, projectiles, drones, traps, missiles, turrets, body shapes, stealth, stats, upgrade-tree placement), figurative tanks built from many parts (dragonfly, crab, starship), and themed arenas of custom shapes (food, crashers, walls, prizes, bosses, spawn zones and weights). For any character, creature, vehicle, object or theme it imagines what the subject is known for and turns that into moves this game can perform (a sword that swings and cuts, a sidekick that follows, eggs that hatch) and into shapes that belong in its world, then pitches or builds them without being told. Use whenever the user wants to create, tweak or edit a custom Diep.io tank, a small line of tanks, or the arena's shapes. Also handles 'edit PACK: CHANGE'."
license: MIT
metadata:
  version: "1.5.0"
  repository: "https://github.com/RedNebulaSunshine/diep-pack-skill"
  requires: "Python 3.8+; Pillow for PNG renders (optional)"
---

# diep-pack

Turn a description into a pack the user pastes into the diep.io sandbox editor. The
deliverable is a `.diep-pack` file (one line of JSON), a short recap, and a few things to check
in game.

**Paths.** `references/…`, `scripts/…` and `assets/…` below are relative to this skill's
directory (the folder holding this SKILL.md). Run the scripts by their absolute path from the
user's working directory: packs and renders land in `./output/` there (override with
`$DIEP_PACK_OUT`). Use `python3` where `python` is not the interpreter's name. Only the
renderer needs a third-party package (Pillow); everything else is standard library.

**Host.** Decide once, at the start, whether you are in a *terminal host* (Claude Code, Codex
and other CLIs on the user's own machine, where any path you print can be opened) or a *chat
host* (claude.ai, ChatGPT and other sandboxed chats, where the user cannot see your working
directory at all). In a chat host every file the user needs, the pack, its render, a feedback
draft, must also go through the host's own file-delivery step, whatever it is that shows them
a download or an image; a path on its own reaches no one. §5, §6 and §8 say where this matters.

## 0. Once per session: is there a newer version of the skill?

Before your first reply in a session, run `python <skill>/scripts/check_update.py`. It
checks at most once a day, sends nothing about the user, and prints one line when there is
nothing to say (`UP TO DATE`, `AHEAD`, `NOT CHECKED`, `OFF`); carry on without mentioning
it. If it prints `UPDATE`, open your reply with a few lines: the new version, its `NEW IN`
items in plain words, and what to do next, which the `HOW` line decides:

- **A git clone** (`HOW … --apply`): offer it ("Update the skill now? It takes a few seconds.").
  On a yes, run `--apply` and re-read this file before continuing, since it may have changed;
  if it says it cannot update, pass on what it printed. Never update without a yes.
- **Anything else** (a zip uploaded to claude.ai or ChatGPT, a copied folder; the script prints
  a `LINK` line): the skill cannot update itself, so do not offer to. Give the `LINK` as a
  clickable link, that exact release zip, and the one or two reinstall steps from the `HOW`
  lines for the host you are in (remove the old diep-pack skill, upload the new zip). Say that
  only that zip works, not GitHub's *Download ZIP* button, whose folder name is refused.

Then answer the request as usual, in the same reply, with the version you have. If it prints
`MOVED`, say the skill has a new home.

## 1. Load context, as much as the request needs

The references and the build library are large, and every token read is paid for again on
every later turn, so **read them by section with `scripts/ref.py`**, not as whole files:

```
python <skill>/scripts/ref.py recipes                 # a file's sections, each with its size
python <skill>/scripts/ref.py recipes intro 5 25      # the text before §1, then §5 and §25
python <skill>/scripts/ref.py figurative 7b           # a number, or a word in the heading ("dash")
python <skill>/scripts/ref.py spec 7a                 # the spec, by its § number
python <skill>/scripts/ref.py --find keepDistance     # every section that mentions a term
python <skill>/scripts/ref.py api                     # compose.py and its presets, one line per call
python <skill>/scripts/ref.py api trail jaws          # those calls in full
python <skill>/scripts/ref.py stock "Twin Flank"      # a stock tank verbatim, from the editor's own roster
```

Read a section once per session; it stays in context. Open a whole file only where this list
says so. Never read `scripts/compose.py` or `scripts/mechanics.py` whole (31k tokens): `ref.py api`
gives their docstrings, and `ref.py api <call> --source` one call's code when you need it.

Always:

1. `references/quick-reference.md`, whole (~5k tokens): every field, its default, unit and
   confidence, plus the rules a pack must obey. This is enough for most tanks. In edit mode,
   only the sections for the fields the change touches.
2. `ref.py recipes intro` (the preset table, the import budget, the stock balance
   envelope), then `ref.py recipes <n> …` for the recipes the design uses. Stock values are
   proven; invented values are guesses.
3. `references/moves.md`, whole (~3k tokens), whenever the request has a subject or a theme
   (a character, creature, vehicle, object, job, element or mood): the method that turns a
   subject into signature moves, the verb-to-mechanic catalogue, and worked pitches that set
   the bar. That is nearly every request; skip it only for a purely mechanical one ("two
   alternating Sniper barrels"), and in edit mode unless the change adds a move.

When needed:

- `references/arena.md`, whole, when the request is about the map's shapes (food,
  crashers, bosses, "the arena", "what spawns", a whole themed pack or total conversion): the
  method that turns a theme into shapes, role templates, the ring layout and spawn weights.
  For a themed tank that says nothing about the map, read only `ref.py arena 0` (offer the
  arena in one line; do not build it).
- `references/vanilla-tanks.md`, whole (small), when placing the tank in the upgrade tree
  (IDs, levels, parents, which IDs the engine rejects).
- `ref.py stock <name>` whenever a design must keep a stock tank's mechanics exactly: a
  reskin or cosmetic pack, "a Penta Shot with ears", "a Twin Flank that also …", "an X
  variant" for any stock X. It prints that tank verbatim from the sandbox editor's own roster
  export (`references/stock-tanks.diep-pack`, 54 tanks, 200–900 bytes each): every barrel
  angle, offset, delay and multiplier, drone counts, projectile fields, stat caps, help text,
  zoom and scope. Clone it and add to it; never rebuild a stock tank from recipe excerpts and
  guesses. `ref.py stock` lists the roster, `ref.py stock --using raises` the tanks that use a
  field. Never open the roster file itself (14k tokens). In a design script,
  `Pack.from_stock(name)` does the cloning (see "Stock clones and reskins" below).
- `references/figurative.md` when the request names a subject with a shape (an animal,
  vehicle, object, "looks like …", "shaped like …") or asks for more than a handful of
  decorative parts: `ref.py figurative 1 2 3b 4 5` (building blocks, the silhouette-first
  workflow, the archetype table, the build library at a glance, the motion map), then §7 and
  §7b, or the parts of them `--find` points to, when the design uses a trick player-built
  packs proved: a body that trails behind, a biting mouth, hands that follow the cursor, eyes
  that watch, faces and line art on the hull, decorated bullets, limbs that react to enemies,
  a dash, melee fists, drones that are whole characters, walking golems, placed buildings,
  projectiles drawn as webs and eggs. The worked dragonfly (§3) only if the workflow is
  unclear. Then `ref.py api` once, and `ref.py api <call>` for each call you use.
- `references/schema/`, the full spec, by section (`ref.py spec <§>`; the quick reference's
  headings carry the § numbers) when a design leans on a field the quick reference tags
  Medium or Low, when the validator reports something you do not understand, or when the
  user asks *why* a field behaves as it does. Do not re-derive or guess anything the spec
  marks Confirmed.

## 2. Interpret the request

**Start with the signature moves.** The user describes a subject; they rarely name the
mechanics, because most people do not know the format can swing a blade, spin a web, lay an
egg that hatches or place a tower. Knowing that is your job. Before any barrel, follow
`references/moves.md` §1: list the subject's recognisable traits (weapon, power, movement,
company, defence, tell), turn each into a move from its catalogue, and choose a default set
with a job for left click, right click and something automatic. A themed tank whose only
weapon is a plain gun is a failure even when it validates. What the user explicitly asked for
stays; the moves fill in what they did not know to ask for.

This is a skill, not a lookup table. The subjects named in this file and in `moves.md` only
show what the method produces; most requests will name something that appears nowhere in
this skill (a film character, a kitchen appliance, a historical figure, a mood), and each
gets the method from scratch: what is it famous for, what would a fan expect it to *do*, and
which of the game's few mechanics can perform that, however loosely. Be bold and specific:
the user should read the pitch and think "I would never have thought of that, and it is
exactly right".

Then turn the description and the moves into a design sheet before writing JSON:

- Name(s). One tank by default; a "line", "tree" or "tiers" request is a multi-tank pack.
- Hull: sides (0 circle), size, star, spin, colour.
- Barrels: count, angles (convert degrees to radians, clockwise positive, front = 0),
  offset, length, width, muzzle, delay for alternation, decorative tips.
- Projectiles: bullet / drone / trap; missile (bullet + `forceFire` sub-barrels, `color 27`),
  minion (drone + plain sub-barrels), swarm (`drone.idle: cruise`), necro (`raises` +
  `holdsRaised`, no projectiles), shotgun (`numBullets`), burst (`burst` + `firesOnDeath`),
  stationary shot (speed 0: trails, contact damage), decorated (`parts`) or armed (`turrets`),
  **or a whole drawing or character**: line art with `proj_rod` (a web, a trident), an egg
  that hatches (`egg`), a figure drone with arms, fists and a lunge (`figure_drone` +
  `summon`), a golem that walks by recoil (`walker`), a placed building (`sentry` + `place`).
  Per-shot rolls: `lifetime`/`damage`/`speed`/`size` as `[min, max]`, `projectile: [a, b]`.
- Turrets (tracking, cursor-following with `range: 0`, **living limbs** with `controllable`
  plus a range, or fixed; disc `baseSize`/`color`; shapes and rods ride them), body shapes,
  stealth, scope, stat caps, speed/zoom/knockback, help text, auto-fire (`forceFire` on a
  gun), invisible barrels, a right-click dash (`dash`), melee fists that land only within
  reach (`punch`), a sword sweep (`blade`), class-folder nodes (`folder`).
- Pack-level: `starters`, `hidden` for a total conversion (spec §1); custom arena `shapes` and
  `hiddenShapes` through `references/arena.md` (built when the request is about the map,
  offered in one line after a themed tank).
- Balance: scale `damageMultiplier` down as barrel count goes up, like the stock ring tanks.
- **Animate by default**: give every tank some movement unless the request says not to. The
  motion map in `figurative.md` §5 lists what moves: pistons (`animate`, with `forceFire` to
  paddle without a click), pendulum pivots that swing on turns, cursor pivots, eyes and brows
  that track, spinning parts, a trail. Brows, ears, tails, hands and legs should each do
  something; mount details on an existing turret (brows on the eye) when the part budget is
  tight.
- **More is better** (play-tester feedback): spend the part budget rather than save it. More
  parts, and more of them moving (pistons, pendulums, living limbs, spinning stars, tracking
  eyes and brows), make a tank look exciting and powerful. Aim for contrast (a dark layer under
  a bright one), variety in size (one big star, several small ones), points and stars rather
  than plain circles, and aggressive shapes (spikes, horns, star auras, angry brows) that
  suggest power. Small parts are mostly outline in game (fill shows only past ~15 radius), so
  make accents big enough to read. Grow the show with the tier: each upgrade should look
  visibly grander than its parent. The limit: the subject must still read. Spend the extra on
  the head and the props; keep a trail or body recognisable with ordered patterns and static
  marks (bands, dots, diamonds), not random stars, spinning shapes and particle clouds (a
  play tester: "too much variety ... they no longer look like" the subject).
- **Branch the tree**: in a multi-tier line, offer two or three upgrades at every level rather
  than one path; a single path bores players. Shared children (a tank listing two parents in
  `upgradesFrom`) keep the count manageable: a lattice of 1, 2, 3, 3, 3 tanks per tier gives
  every tank two or three choices with twelve tanks per line.
- **Part budget**: the editor keeps 32 body shapes and 32 barrels per tank and silently drops
  the rest (spec §9c); the most turrets seen is 8; and the game refuses a tank with more than
  **96 pieces in all**, projectiles' parts, sub-barrels and turrets included (a figure drone or a
  drawn shot spends the hull's budget). Plan the count in the design sheet; `save()` warns and
  the validator errors.
- **Use the format's imagination.** Drones and projectiles are not dots and limbs are not
  stickers. The design sheet lists the signature moves first (`moves.md`), each with its
  preset and button, then the guns: a spider gets living legs (`leg`) and shoots webs (`web`);
  a hen lays eggs (`egg`) and is followed by chicks (`figure_drone` + `summon`: drones are
  always out, never on a click); a brawler punches (`punch`) and dashes (`dash`); a wizard
  places a tower (`sentry`) or raises a golem (`walker`); a knight sweeps a sword (`blade`) on
  a living arm. A move marked **try** in the catalogue is offered as an experiment and named
  as a guess in the recap.

Pick the recipe(s) that match and copy their numbers as the starting point; adjust only
what the request asks for. In a compose script every recipe is a preset (`d.twin()`,
`d.spawner()`, `d.destroyer(right_click=True)`, table at the top of `recipes.md`); use them
rather than retyping numbers.

For a request that combines several systems (a figure with two different guns, a
right-click mode, drones and a turret), write the design sheet as a table with one row per
system: where it sits in the anatomy, which preset, which button (left / right / automatic),
and its phase (`delay`). Two systems on the same button fire together unless one has `delay`.

## 3. Ask once, before generating

Ask the user, in one message, for the things the description cannot settle (use the
host's structured-question tool if it has one; otherwise plain text):

- **The moves** (any request with a subject or theme): the pitch of `moves.md` §1 step 4.
  One plain line per chosen move saying what the player will see and which button does it,
  marked Recommended, then one or two alternatives. Lead with this: it is the part the user
  cares about and could not have written themselves. Where two readings differ in kind (webs
  that snag versus webs that hurt), offer both.
- **The arena** (a request about the map or a themed pack): the pitch of `arena.md` §1 step
  7, one plain line per shape (role, look, where it spawns), marked Recommended, and whether
  the vanilla shapes stay. For an arena-only request skip level and parent.
- **Level**: 15 / 30 / 45 / 60 (or a number the user gave).
- **Parent tank(s)** by name, from `vanilla-tanks.md`; multiple parents allowed.
- **Author name**: the name the editor shows on the pack. Remember it for the rest of the
  session; in edit mode keep the pack's existing author.

If the description implies a lineage ("an Overseer variant", "upgrade from Twin"), put that
inference first and mark it Recommended. For a multi-tank line ask only for the root; the
rest chain from it by custom id. Do not ask anything else unless a genuine ambiguity would
change what the tank *is*. If the user said to just build it ("surprise me", "go ahead"),
or the host cannot ask (a non-interactive run), build the recommended moves, use level 45 off
Tank, omit the author, and say so in the recap, with the alternatives offered there.

Never wire to Ball (53) or IDs 56/57/59. Shotgun, Glider and Firework are 62, 63, 64; Auto
Tank, Dual-Barrel and Pellet Shot are 58, 60, 61 (all six confirmed in game).

## 4. Build the JSON

- **Sparse like the editor.** Omit fields at default. Always write: pack `version: 2`,
  `name`, `tanks` (left out of an arena-only pack; `author` when the user gave one); tank `id`, `name`, `minLevel`,
  `body.sides`, `invisibility.gain` (0.03076923076923077) and `.lossOnHit` (0.05),
  `statsMaxLevel`; projectile `name`, `base`, `sides`; barrel `bulletType`, `projectile`;
  drone barrel `numDrones`, `droneAggressiveCrashRadius` (900 unless the recipe says otherwise).
- **IDs** 100001, 100002, … in pack order. Pack `name` = first tank's name.
- **Stock clones and reskins.** A tank that is a stock tank plus something starts from
  `ref.py stock <name>` and keeps every mechanical field as printed (the pack id, name and
  tree links are the pack's own). A cosmetic-only or reskin pack adds nothing that changes
  play: non-collidable body shapes, decorative barrels and turrets (`bulletType: "none"`,
  `projectile: -1`), parts on the projectiles; and each clone takes its stock tank's slot
  with `editor.replaces: N` plus `N` in the pack's `hidden` list, so the stock tank and its
  reskin never both appear. In a design script `pack.from_stock("Twin Flank")` returns a Tank
  with all of that loaded verbatim (`as_name=` renames it; `level=` and `parents=` are the
  pack's own) and does the `editor.replaces` and `hidden` bookkeeping; add rods, shapes,
  turrets and projectile parts on top. `save()` prints a NOTE for each field that differs from
  the stock tank in play, and `validate_pack.py <pack> --cosmetic` turns those into ERRORs: run
  it on every reskin.
- **Units**: radians; `delay` in reload periods (0.5 alternates); `lifetime` seconds;
  `spin`, `spinSpeed`, `invisibility.gain` per tick (25/s); `zoomMultiplier` < 1 = wider view.
- **Consistency**: `bulletType` equals the target projectile's `base`; decorative barrels
  are `bulletType: "none"`, `projectile: -1`; sub-barrels on a bullet need `forceFire` or
  `firesOnDeath` or they never fire; `raises` needs a `holdsRaised` barrel with
  `projectile: -1`; `editor.replaces: N` is paired with pack `hidden: [N]`; a stationary
  shot sets both `speedMultiplier` and `initialVelocityMultiplier` to 0; a barrel that
  should fire on its own carries `flags.forceFire`, and `invisible: true` if it is only a
  mechanism, not a picture.
- **Import budget** (spec §7a, the editor's own check, exact): the lobby refuses a tank over
  120 entities created per second, 250 alive, 2000 "room" (bullet areas: size counts squared),
  64 per volley, 96 drones or 96 pieces. The whole tank counts with the **Reload stat at its
  cap** and every trigger held, left click, right click and auto-fire together (with caps of
  12: 12.5/s at reload 0.25, 8.3 at 0.5, 4.2 at 1; caps of 7 cost about three quarters; a cap
  of 0 makes barrels cheap). **A shot counts as 1 + everything its projectile carries** (parts,
  sub-barrels including drawing-only rods, turrets), and a projectile's live guns count once per
  live copy, so a drawn web, a long-lived building or a figure drone multiplies the cost: give
  such tanks a Reload cap of 0 (a player-built pack does on 47 of 60 tanks). The limits are
  exact, so a tank may sit right at them. `validate_pack.py --summary` prints all six figures;
  quote them in the design sheet for anything with many auto-firing barrels, pistons, a trail,
  drawn or big projectiles or high stat caps.
- **Editor import rules** (spec §0): the editor clamps numbers to its ranges, drops parts past
  its counts, keeps only three `collidable` parts per tank and per projectile, and gives a
  projectile's barrel that fires a decorated or armed projectile a plain shot instead. The
  validator warns on each; treat those warnings as design bugs.
- **Colours** only as palette indices 0–29 (spec §10); 27 = owner colour. In recaps call
  colours by the editor's swatch names (Salmon, Crimson, Mint, Box, Charcoal …; table in the
  quick reference, `compose.C`). Never use 3–6 for a colour that must stay put: the picker
  calls them Red, Purple and Green but they are team slots that follow the player's team.
- **`order`** in creation sequence across barrels, body shapes and turrets; −1 for bases
  that sit under the main barrel.
- **Name every part.** Each barrel, body shape and turret gets a unique, human
  `editor: {"name": "…"}` ("fore wing right", "tail pivot 2", "left mandible"). The editor
  shows these in its part list, so the recap and the in-game checks refer to parts **by
  those names**, never by index or by look ("the second grey octagon"). `compose.py` does
  this automatically; hand-written JSON must too.
- **Tree**: at most 19 upgrades per tank, stock children included (Tank has 6, Overseer 6);
  the validator counts them. `upgradesFrom` with vanilla IDs or same-pack ids; `advancesInto` only when the
  user asks for it (the official pack uses `upgradesFrom` alone).
- Anything the spec tags Medium or Low that the design depends on (e.g. `keepDistance`,
  `collidable`, `revealDistance` default) gets named as a guess in the recap.

## 4b. Figurative builds: script it, render it, look at it

When the tank is meant to *look like something*, do not hand-type coordinates. Follow
`references/figurative.md`:

1. Write the design sheet as anatomy: view (top-down), size budget, a line per feature
   with the primitive it becomes (chain, strip, rods, polygons), the layer plan, two or
   three colours, and where the weapons sit in the anatomy.
2. Write `<slug>.py` in the user's working directory using `scripts/compose.py`. Start from
   the closest archetype in `assets/archetypes/` (`dragonfly` long body and wings, `crab` wide
   with claws, `spider` many jointed legs, `starship` hard-edged vehicle, `serpent` a head with
   a trailing body and a biting mouth, `croc` a full creature with jaws, eyes, paddling legs
   and a tapered tail, `president-prism` a face painted on the hull; `examples/x-wing/` a
   vehicle with converging cursor-pivot guns; table in `figurative.md` §3b). The script's
   first lines put this skill's `scripts/` folder on `sys.path` by absolute path, then
   `from compose import C, Design`. Degrees clockwise, forward = +x, y = tank's right. Build
   symmetric features once and `mirror()` them; build multi-part assemblies (a claw, a
   nacelle) inside `with d.frame(at, angle):`. Jointed limbs are `limb()`, filled irregular
   areas are `fan()`, faces are `line()` and circles with `above=True`. Draw limb roots
   first, body over them, details last; anything that must show over the hull is a shape or
   rod with `above=True`. Weapons are presets placed in the anatomy; so are a trailing body
   (`trail()`), jaws (`jaws()`), watching eyes (`eye()`) and hands (`cursor_pivot()`).
3. Run `python <slug>.py`. It writes the pack to `./output/`, validates it, prints the part
   table, any `HIDDEN` parts (entirely under the hull) and the figure's span, and renders
   `./output/renders/<slug>-<tank>.png`.
4. Read the PNG and critique it against the subject (silhouette, symmetry, hull swallowing
   parts, seams, proportions). Fix the script and rerun, at most three passes. The script
   is the source of truth; never patch the JSON by hand.

Simple weapon tanks (a few barrels, no picture to match) can still be written as JSON
directly, but render them too (step 5) before delivering.

## 5. Write, validate, render

Save as one line of compact JSON to `./output/<slug>-<version>.diep-pack` (slug = lower-case
pack name, hyphens; version per §5a); `compose.save()` does this for scripted designs. Then:

```
python <skill>/scripts/validate_pack.py output/<slug>-<version>.diep-pack --summary
python <skill>/scripts/render_pack.py output/<slug>-<version>.diep-pack
```

Fix every ERROR. Read every WARNING and either fix it or explain it in the recap. Use the
`--summary` lines to check the pack says what you meant. Open the PNG the renderer prints
(`output/renders/…png`, one per tank, `--sheet` for a contact sheet, `--svg` for an SVG
beside it) and check it matches the design sheet; the renderer reproduces the editor's own
drawing to within a pixel (verified against every stock and official tank and 326
player-built ones), except that star inner radius and `sides` 0–2 shapes are guesses. If
Pillow is missing, `--svg` still works; tell the user how to install Pillow for PNGs.

## 5a. Version every iteration (semantic versioning)

Every pack carries a version, `MAJOR.MINOR.PATCH`, and every iteration the user receives gets a
new one: never hand over two different packs under the same number.

- **Where it lives.** The editor keeps only the pack's name, author, tanks, shapes, hidden lists
  and starters on import (editor code), so the version goes in three places: the **pack name**
  (`"Sea Pack v0.3.1"`, the one place a player sees which iteration is loaded), the **file name**
  (`output/sea-pack-0.3.1.diep-pack`, so earlier iterations stay on disk to compare or roll back
  to), and a **changelog**. In a script: `Pack("Sea Pack", author, version="0.3.1")` (or
  `Design(..., version=...)`) writes both names; renders keep the unversioned name so they always
  show the latest. Hand-written JSON: put the suffix in `name` and the file name yourself.
- **The changelog** is `<design script>.changelog.md` beside the script (`sea-pack.changelog.md`
  for `sea-pack.py`), newest first, one entry per version:
  `## 0.3.1 (2026-10-02, patch)` then a bullet per change in plain words, naming tanks and
  parts. `save()` prints a `VERSION` note when the entry is missing or when it overwrites a
  version with different content (fine while iterating before delivery, never after).
- **Which number to bump**, judged by what the change means to someone who has the last version:
  - **MAJOR**: what players or an importer rely on breaks: a tank or line removed; tanks
    re-parented or their unlock levels moved; the starters or the hidden stock tanks changed; the
    arena replaced wholesale; a tank's weapons swapped for different ones (it now plays as a
    different class).
  - **MINOR**: something added or reworked that keeps the tree: a new tank, line, ability, move,
    projectile, companion or arena shape; a tank renamed or visibly redesigned; a balance pass
    across several tanks.
  - **PATCH**: tuning and fixes within what exists: numbers (damage, reload, speed, counts,
    lifetimes, spawn weights), colours, part sizes and positions, help text, a budget trim, a bug
    fix (a part that did not show, a refused import).
  - When one iteration mixes kinds, the biggest wins; reset the lower numbers (0.4.2 + MINOR = 0.5.0).
- **Start at 0.1.0.** While the user is still shaping the pack (0.y.z), a MAJOR-kind change bumps
  MINOR instead, as semantic versioning allows before 1.0. Offer **1.0.0** when the user calls the
  pack finished or wants to share it; from then on MAJOR means MAJOR.
- **Say it.** The delivery (§6) names the version and the bump with its reason
  ("0.12.0 → 0.12.1, patch: fried-egg whites"), and the recap matches the changelog entry.

## 6. Deliver

Reply with, in this order:

1. The **version** and the bump (§5a), then the pack **file**. In a terminal host: its
   absolute path on its own line, with the instruction to import it from file (or open it in
   an editor and copy from there). In a chat host: hand the `.diep-pack` over through the
   host's file-delivery step so the user gets a download, show the render the same way, and
   name the file rather than printing a path nobody can open. Then the one-line JSON in a
   `json` code block for packs under about 2 KB. Do not paste longer packs into the reply:
   terminals wrap or truncate long single-line code blocks on copy and the result fails to
   parse in the game.
2. **Recap**, a few bullets per tank: the signature moves first, each in plain words with
   its button; level and parent(s); barrels by type; projectiles and what makes them special;
   any guessed or Medium/Low-confidence fields, named. Run the check of `moves.md` §4 and
   end with one or two ideas not built, as offers ("Want R2-D2 swapped for a Force leap?"). For a
   figurative build add the render path and the part count, and name the design script.
3. **Import**: "In the sandbox editor: Import, choose the file, *add to this pack*." An
   arena-only pack (shapes, no tanks) imports only this way; *import as new pack* refuses it. Mention
   that IDs are reassigned on import, so tree links to other packs are not possible. For a
   **revised** pack the user already imported, say *import as new pack* (or delete the old
   copies first): adding it again stacks a second set of children on the same parents, and a
   tank may offer at most 19 upgrades, stock ones included (Tank already has 6).
4. **Try in game**: two or three concrete things to look at, in plain language ("hold fire
   and watch whether the rear pair alternates with the front pair"). One pack per message;
   people test one thing at a time.

## 7. Edit mode

`edit <path or pasted JSON>: <change>`: load the pack (a file, or JSON pasted in the
message), apply only the described change, keep ids, author and tree links, bump the version
(§5a; a pack without one starts at 0.1.0, or 1.0.0 if the user says it is already released),
add the changelog entry, revalidate, re-render, and deliver as in §6 with a recap of what
changed. Save a new versioned file in `./output/`; never overwrite an earlier version. If a
`<slug>.py` design script exists for the pack, edit the script (its `version=` and changelog)
and rerun it instead of the JSON.

## 8. Feed findings and discoveries back

Two things are worth sending back to the skill:

- **Findings**: the user reports in-game behaviour that confirms, contradicts or refines the
  spec, or the validator, the renderer or the build library disagrees with the game, or the user
  corrects how the skill works in a way that would help every user. Say so plainly in the recap.
- **Discoveries**: the user and you find a new way of achieving something that future users
  would want, whether functional (a new move, a new use of a field, a budget saving), aesthetic
  (a drawing, layering, colour or motion trick that reads better in game) or quality of life (a
  faster test, a useful check, a clearer question). It must be absent from the references
  (`ref.py --find` to check), carry over to other subjects, and have been seen working.

Then:

- **The skill's maintainer** (the user says they maintain it): fix it in place. Update the
  field's row in `references/schema/` (and §13 of `00-format.md`), keep the confidence tag
  honest, and fix `recipes.md` or `scripts/validate_pack.py` if they encoded the old belief.
  The spec is the single source of truth; there is no separate feedback log. Write a discovery
  into the reference it belongs to, as a method.
- **Everyone else**: encourage them, once per finding or discovery, at the end of the reply,
  to share it through the skill's GitHub repository. Name what is new and why others would
  want it, and make clear that **nothing personal is sent**: you draft an issue about the
  technique or the finding, not about them, with no names, files, paths, accounts or
  conversation; a script strips any that slip in; they see every word and submit it themselves
  on GitHub, where it appears under their own account; and pack contents go in only if they
  agree. On a yes, read `references/feedback.md` (whole, short) and follow it. On a no, drop it.

## Examples

- `a Sniper variant with two long barrels that fire alternately and a rear spawner with 3
  swarm drones`
- `a hexagonal smasher that fades when still, spikes spinning fast`
- `a two-tier line off Destroyer: a slow missile launcher at 45, then a version at 60 whose
  missiles explode into 8 bullets on right-click`
- `edit output/sniper-swarm.diep-pack: make the drones uncontrollable and double their count`
- `a tank that looks like a dragonfly, top view, whose mandibles are the guns`
  (figurative: design sheet → `dragonfly.py` from the archetype → render → critique → deliver)
- `a crab whose right claw fires a heavy shell on left click and the left claw on right
  click` (figurative + two systems on two buttons: `assets/archetypes/crab.py`)
- `a snake: a head that leaves its body behind it as it moves, jaws that open toward the
  cursor and bite, one eye that watches enemies` (`assets/archetypes/serpent.py` with
  `trail()`, `jaws()`, `eye()`)
- `an X-Wing with four wingtip lasers that converge on the cursor and a torpedo on right
  click` (`examples/x-wing/`: the script, the pack it builds, and its PNG and SVG renders)
- any bare subject: `Luke Skywalker`, `a lawnmower`, `Cleopatra`, `an octopus`, `a
  firefighter`. The user names nothing else; the skill works out the moves (`moves.md` §1) and leads
  its one question with them.
- `arena shapes for a desert pack` (arena: the theme's world as roles and rings, `arena.md`;
  the recap tables each shape's share of the spawns)
- `hide the vanilla hexagons and add a cyan replacement with 1500 health` (arena, mechanical)
- `a big spider` (imagination: eight living legs on pivots (`leg`), a web shot drawn with
  sub-barrels (`web`), a right-click dash, fangs as `punch`)
- `a hen followed by her chicks that lays eggs on right click` (`egg` laid with
  `lifetime=[12, 22.5]` and `projectile=[egg, golden]`; chicks are `figure_drone`s with a beak
  turret; the hen's head is a living limb)
