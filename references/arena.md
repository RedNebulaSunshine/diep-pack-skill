# Arena: filling the map with shapes that belong to the theme

A pack can replace the arena's polygons with its own: food the players shoot for score,
hazards that hunt them, obstacles that do not budge, rare prizes and bosses, each with its own
outline, colour, stats and place on the map. A user who asks for "a pirate pack" or "an arena
for my robot tanks" wants to shoot barrels and treasure chests, not yellow squares. They will
rarely name the fields; **your job is to imagine what the theme's world is full of and turn it
into shapes the game can spawn.** This file is the method, the role templates, the map layout
and the checks. Field facts are in `schema/01-pack-and-tank.md` §1a; the helpers are
`Pack.custom_shape()`, `Pack.spawn_shares()` and `ring_density()` in `scripts/compose.py`.

## 0. When to use it

- The request is about the map: "shapes", "food", "the arena", "crashers", "bosses", "what
  spawns", "a whole <theme> pack / world / total conversion". Build it.
- A themed tank request that says nothing about the map: do not build shapes (they change the
  arena for everyone in the lobby). End the recap with a one-line offer that names two or
  three of the shapes you would make ("Want the arena to match? Doubloons at the edge, powder
  kegs that chase, a kraken in the middle.").
- A pack of several tanks with a shared theme: offer the arena in the one question of SKILL.md
  §3, as its own line.

## 1. The method (any theme)

1. **Brainstorm the theme's world**, wide first: eight or more things that lie around in it,
   live in it or threaten it, as a fan would name them. Headings that help:
   - *Common stuff*: what is everywhere and cheap (leaves, coins, scrap, snowballs, bones).
   - *Valuables*: what is rare and worth chasing (gems, relics, golden versions).
   - *Dangers*: what attacks or hurts (pests, guards, monsters, hazards that sting on touch).
   - *Terrain*: what is solid and in the way (rocks, walls, crates, pillars, wrecks).
   - *Landmarks*: the one huge thing at the heart of it (a nest, a hoard, a monument, a boss).
   - *Geography*: where things live, from the outskirts to the heart (shore → shallows → deep;
     meadow → forest → cave; orbit → belt → core).
2. **Give each kept idea a role** from §2 and start from that role's numbers. Five to eight
   shapes is a rich arena; three is enough for a small one. Every arena needs at least one
   food a level-1 tank can kill in a few shots, and most of the spawns should be food.
3. **Lay out the map in rings** (§3): the geography becomes square bands from the edge (1) to
   the centre (0). The diep convention, and a good default: cheap food in the outskirts,
   richer food further in, and the danger and the jackpot at the heart (the vanilla pentagon
   nest, where crashers live). A theme may invert it (a prison yard's walls on the rim) when that is
   what the fan expects.
4. **Draw each shape** so it reads at a glance: `sides` (0 is a circle, up to 18), `size`, and
   a hex `color` that says what it is (§4). A shape is one filled polygon, nothing more: the
   name, colour, outline and size must carry the idea.
5. **Set the weights** (§3) and read the predicted shares `save()` prints. Adjust until the
   mix matches the plan: mostly food, a sprinkle of prizes, hazards noticeable but not a swarm,
   a boss rare enough to be an event.
6. **Decide what happens to the vanilla shapes**: hide them all for a full conversion
   (`hidden_shapes = VANILLA_SHAPES`), replace one kind with a themed version
   (`replaces="pentagon"` plus that kind in `hidden_shapes`), or leave them and add a few
   themed extras (the vanilla weights then share the map, §3).
7. **Pitch it** (SKILL.md §3): one line per shape, "Doubloon: small gold circle, common at the
   edge, 25 score", marked Recommended, with one or two alternatives. The user can say "go" or
   swap a shape.

Prefer the surprising, true idea to the safe one. "Squares, but brown" is a failure even if it
validates; "barnacle-crusted crates you can't push, gulls that dive at you near the shore, a
treasure chest worth a level in the middle" is what the user hoped for.

## 2. Roles and their numbers

The vanilla reference, from the editor's help text (Confirmed, editor code): a square does 2
contact damage, shoves with 8, takes knockback 1 and spawns at weight 1; triangles weigh 0.2,
pentagons 0.05; a pentagon takes knockback 0.5 and an alpha pentagon 0.05. Health and score are
diep's long-standing values (Medium): square 10 / 10, triangle 30 / 25, pentagon 100 / 130,
alpha pentagon 3000 / 3000, sizes about 55 / 55 / 75 / 200. Score roughly tracks health; a
tank needs about 23 500 score for level 45 (Medium), so what an arena pays sets how fast players
climb.

| Role | Look | `size` | `maxHealth` / `xpBounty` | touch dmg / shove | knockback taken | movement | weight, band |
|---|---|---|---|---|---|---|---|
| **Food** (common stuff) | small, simple, bright | 30–60 | 10–30 / 10–25 | 2 / 8 | 1 | drift 0.05–0.1 | 0.2–1, outskirts or anywhere |
| **Rich food** | medium, more sides | 55–80 | 60–150 / 60–150 | 2–3 / 8–10 | 0.5 | drift 0.05 | 0.05–0.2, middle ring |
| **Prize** (valuables) | small, vivid, rare | 25–60 | 50–500 / 1000–10 000 | 2–4 / 8 | 0.5–1 | drift 0.1–0.2 (it slips away) | 0.001–0.01, heart |
| **Hazard** (dangers that hunt) | sharp: 3 sides, dark or hot colour | 30–55 | 20–75 / 15–60 | 3–6 / 12 | 0.1–1 | crasher: speed 2.6–3.2, radius 1500–2000 | 0.02–0.2, where the danger lives |
| **Swarm** (pests) | tiny, many | 15–30 | 5–25 / 5–20 | 1–3 / 6 | 1–2 | crasher: speed 3–4, radius 1000–1500 | 0.1–0.5, one band |
| **Sting** (dangers that don't move) | spiky look (many sides, dark) | 30–60 | 50–200 / 30–100 | 6–12 / 16 | 0 | drift 0 | 0.02–0.1 |
| **Terrain** (in the way) | big, dull, heavy | 80–200 | 250–2500 / 0–50 | 0–2 / 16 | 0 (never budges) | drift 0 | 0.05–0.3 |
| **Boss** (landmark) | huge, many sides | 150–400 | 3000–100 000 / 3000–150 000 | 8–20 / 18–25 | 0.01–0.05 | drift 0.04, or a slow crasher (speed 1–1.5) | 1e-5–0.005, centre |
| **Event** (for later) | any | any | any | any | any | any | `disabled=True`: the user switches it on in the editor |

Confirmed in play (2026-09-29): 20 contact damage killed a tank with Max Health and Body Damage
at 7/7 in two touches, so 20 is boss-grade and food stays at 2–4; knockback taken 0 makes a
shape a wall (bullets and rams do not move it, and a ramming tank bounces off and takes its
contact damage); a crasher with speed 3 and radius 2000 runs a player down; drift 1 wanders
visibly fast. Chase radius is what makes a shape a crasher and what it costs the server ("the
server searches this radius"): keep crashers to a modest share and the radius at 2000 or less.

**A pack cannot make a real diep boss** (Confirmed 2026-09-29, editor code and play). Diep's
bosses are AI tanks the server spawns on its own timer or from the admin panel (Guardian, Summoner,
Defender, Fallen Booster, Fallen Overlord, a fixed list by name); nobody can pick or upgrade into
one, and *Boss Control* lets a player take one over. The pack format has no bosses, and a Fallen
boss stays stock even when the pack replaces and hides its tank, and the lobby refuses a pack tank
that claims a stock id ("outside the custom range (>=100000)"). Bots are no way round it either
(2026-09-29, the `bot-boss-test` test build): the admin's bots (`spawn_bot`, at most 8) level
through the tree on their own and no admin action gives one a tank; with a pack tank as Tank's only
upgrade, about 2 bots in 12 took it. The admin command `ban_tank <id>` works on **stock** ids: it
stops bots and non-admin players alike (the user, 2026-09-29), so it cannot make a bot-only tank.
On a **pack** id (100000 and up) it does nothing to anyone (bots and a player were still offered
the tank from level 15 to 120): a bug the user reported to the game's developers. Once fixed,
`ban_tank` on a boss-grade pack tank should keep it from players and bots while an admin can still
take it by Switch Tank (untested: admins look exempt). So a pack's boss is one of two
things, and the pitch says which: a **boss shape** (this row: huge, rare, one polygon, since a
shape carries no parts), or a **boss-grade tank** someone plays (`baseHealth` up to 100000, heavy
`baseBodyDamage`, `knockbackMultiplier` 0, a collidable body up to size 150, the whole figure
toolkit), reached from the tree or by the sandbox's Switch Tank, never spawned by the server.

Score keeps the arena honest: score/health near 1 for food, well above 1 for prizes (the
reward for finding one), below 1 for terrain and stings (they cost more than they pay).
Contact damage is how a theme says "don't touch": give it to what the fan would fear touching.

## 3. The map: rings, weights and shares

- The map is rectangular (usually square). A shape's band, `radius_min` to `radius_max`, is a
  fraction of the way from the centre (0) to the edge (1), and it is a **square ring**, not a
  circle (Confirmed in play: three stacked bands stayed apart and followed the map's edges).
- **Weight is a share, not a count.** The map's shape cap is a sandbox setting outside the
  pack; every enabled shape, vanilla ones included, shares it. A shape's share goes with
  **weight × band width** (two counts in play; spec §1a "Spawn shares"). `save()` prints the
  predicted share of every shape and its crowding per area; `pack.spawn_shares()` returns them.
- **The centre crowds.** 0–0.4 is 16 % of a square map but gets 40 % of the spawns at equal
  weight. To crowd a band like the rest of the map, use `ring_density(inner, outer, crowd)`,
  which is `crowd × (inner + outer)`: 1.8 / 1.2 / 0.4 for bands 0.8–1 / 0.4–0.8 / 0–0.4 came
  out close to even in play. A deliberately packed heart (a nest) just keeps equal weights.
- Stacked bands are the arena's geography. Three to four rings read clearly; a shape can also
  span several rings (a food that is everywhere, `radius_min` 0 and `radius_max` 1).
- Leave no band empty of food, or that part of the map is dead. Bands may overlap (a hazard
  in the same ring as the food it guards); overlap is untested but the share model still
  gives the expected mix.

## 4. Colour and outline

- Colours are hex strings (the only place hex is used). Pick one family per role so the
  arena reads at a glance: food in the theme's warm or natural colours, prizes bright and
  saturated (gold `#FFD700`, gem green `#00E16E`, cyan `#35C5DB`), hazards dark or hot
  (crimson `#B5323A`, purple `#7B4FA8`), terrain dull (greys `#8C8C8C`, browns `#A9724A`).
- Players already read vanilla colours: yellow square `#FFE869`, salmon triangle `#FC7677`,
  periwinkle pentagon `#768DFC`, pink crasher `#F177DD`. Reuse one only for a shape that plays
  that part (a themed replacement for squares can stay yellowish); otherwise stay clear.
- Outline by role: food simple (3–6 sides or a circle), prizes many-sided or round (a coin
  is a circle, a gem 6–8 sides), hazards 3 sides (the crasher convention), terrain 5–8 sides and
  big, a boss 8–18 sides and huge. `sides` 0–2 all draw a circle.

## 5. Build

In a compose script (SKILL.md §4b paths):

```python
from compose import Pack, VANILLA_SHAPES, ring_density

p = Pack("Sea Pack")                                          # author: ask (SKILL.md §3)
p.hidden_shapes = list(VANILLA_SHAPES)                       # a full conversion
p.custom_shape("Plankton", sides=0, size=30, health=10, xp=10, color="#9FE3C1",
               float_speed=0.1, radius_min=0.7, density=ring_density(0.7, 1))
p.custom_shape("Fish", sides=5, size=60, health=100, xp=110, color="#FF9F43",
               knockback=0.5, float_speed=0.3, radius_max=0.7, density=0.4)
p.custom_shape("Reef Rock", sides=7, size=120, health=1500, xp=20, color="#8C8C8C",
               touch_damage=2, touch_knockback=16, knockback=0, float_speed=0,
               radius_min=0.3, radius_max=0.8, density=0.08)
p.custom_shape("Shark", sides=3, size=50, health=60, xp=60, color="#4A5A6A",
               touch_damage=5, touch_knockback=12, knockback=0.3,
               crash_speed=3, crash_radius=1800, radius_max=0.4, density=0.1)
p.custom_shape("Pearl", sides=0, size=28, health=80, xp=4000, color="#F4F1E8",
               float_speed=0.2, knockback=0.8, radius_max=0.2, density=0.004)
p.save()
```

- `custom_shape` returns the shape's id, which a Necromancer-style tank of the same pack can
  put in `raises` to turn that shape into its drones: offer it when the pack has such a tank.
- A pack with no tanks is an **arena-only pack**. It imports only with **Add to this pack**
  (the shapes join the pack the user has open); **Import as new pack** refuses it ("A pack
  needs a tank"). A themed pack with tanks imports either way.
- Ids are positional (`custom_shape_1` … in list order): add shapes at the end when editing,
  or re-point any `raises` that named them.
- `disabled=True` keeps a shape in the pack without spawning it (the editor parks its weight
  in `editor.spawnWeight`): use it for event shapes the user switches on later.

## 6. Deliver and check

In the recap, a table of the shapes: name, role, look, band, share of spawns (from `save()`),
health / score, and what it does on touch. Then:

- **Import**: arena-only packs with Add to this pack; the map's shape cap is a sandbox setting,
  and the shares are of whatever cap the lobby uses.
- **Try in game**, two or three things: do the rings read from the edge to the centre; can a
  new tank farm the outskirts safely; does the hazard feel dangerous without swarming; is the
  prize rare enough to feel like a find.
- Checks before delivering: most of the spawns are food; the outskirts have food a level-1
  tank can kill; no band is empty; crashers are a modest share with radius at most 2000;
  anything at 20+ contact damage is rare and meant as a boss; score/health follows §2; every
  shape reads as the theme from its name, colour and outline alone; values stay inside the
  editor's ranges (the validator warns).
- End with one or two ideas not built, as offers (an event boss left disabled, a Necromancer
  tank that raises the theme's food).
