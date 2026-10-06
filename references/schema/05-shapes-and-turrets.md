## 8. BodyShape (`tanks[].bodyShapes[]`)

```json
{"sides":6,"size":57.5,"angle":1,"spinSpeed":0.1}                         // Smasher hexagon
{"sides":4,"size":20,"aboveBody":true,"order":1,"color":1}                // Tenk's grey square
{"sides":9,"size":136,"xOffset":142,"yOffset":-221,"collidable":true,"order":17,"color":26}
```

**Editor limits** (its import code, 2026-09-29, re-read 2026-10-06; the same for a projectile's
`parts` except the hitbox count): 32 shapes; `sides` at most 18; `xOffset` and `yOffset` within
−800…800; `size` at most 300; **only the first eight `collidable` shapes of a tank stay collidable**
(three before the 2026-10-06 update; still **three** on a projectile), the rest become drawing-only,
and the collidable ones are capped at size 150. A shape that rides another shape (`mountPart`) is
never collidable. `validate_pack.py` warns on each.

| Key | Type | Default | Meaning | Confidence |
|---|---|---|---|---|
| `sides` | int | — | Polygon side count; **0, 1 and 2 draw as a circle** (exports of a character's goggles, a snake's pupil, and a drawing-leftovers test export for 2; the editor: "Under 3 draws a circle"). At most 18. Always written. | Confirmed |
| `size` | number | **25** | **Circumradius** (centre to vertex): an 80 square renders with half-side 56.6. Smasher hexagon 57.5, Spike triangles 65. Omitted when 25 (40 human shapes have no `size` and every export draws them at 25). | Confirmed |
| `xOffset` | number | 0 | Position along the aim axis, forward positive. (The editor's new-part default of 55 is a UI default, not the format's.) | Confirmed |
| `yOffset` | number | 0 | Position across the aim axis, positive toward the tank's right. | Confirmed |
| `angle` | number | 0 | Rotation of the part, radians. Offsets are Cartesian, unlike barrels' polar `angle`. | Confirmed |
| `spinSpeed` | number | 0 | Rotation per tick (Smasher 0.1, Spike 0.17, Blender 0.25). | Confirmed |
| `star` | bool | false | "Drawn as a star": 2 × `sides` vertices alternating **inner radius 0.4 × size** and `size`, starting on an inner vertex at angle 0 (§9b; three human exports agree). Glitch bursts, sparkles, spiked plates. | Confirmed (drawing) |
| `collidable` | bool | false | Part has physical collision of its own; **eight per tank** (three before 2026-10-06; **Confirmed in play 2026-10-06**: eight plates on a ring all stopped shapes) **and three per projectile** at most (the editor clears the flag on every later one, and caps their size at 150); **also on a projectile's `parts`** (the lab's Web Lab, 2026-09-28: the web drew as designed and lasted about 5.5 s; shapes took damage only from its centre disc and its two collidable hook stars, never from the rods, and were not pushed back). 100+ human shapes set it (big carapaces, boss bodies, "power cells"). Confirmed 2026-09-26 (the `hitbox-test` test build): over a size-8 hull, a collidable octagon of size 120 made tanks, shapes and bullets collide well outside the hull but **inside the drawn rim**; the same octagon without the flag collided only at the tiny hull, so the hull's own hitbox scales with `body.size` and a non-collidable part is picture only. the `hitbox-rings` test build (dots at 40/60/80/100 on that octagon) put the contact edge for both shapes and bullets at the 80 ring or just inside it. That pack had 49 shapes, so under the 32-shape cap (§9c) only 7 of the 80 dots and none of the 100 dots existed in play; the reading therefore says **a collidable part collides at between half and two thirds of its drawn radius** (coarse, one reading). | Confirmed |
| `aboveBody` | bool | false | Draw over the hull (Tenk, Cyclone, Ambusher carry a small grey square on top). Without it the hull always paints over parts (§9a). On a part with `mountTurret`, over the turret's disc. | Confirmed |
| `mountTurret` | int | absent | `0`, `1`, `2` (the serpent's teeth, fangs and pupil; a skeleton's star hands) | Index into `turrets[]`: the shape rides the turret and turns with it, its offsets in the turret's frame. Drawn before the disc unless `aboveBody`. | Confirmed (drawing) |
| `mount` | int | absent | `0` (a player-built tank: a triangle on the main barrel) | Index into `barrels[]`: the shape rides that barrel, offsets measured from the barrel's **midpoint** along its axis (same rule as barrel-on-barrel, §9b). | High |
| `mountPart` | int | absent (−1) | | **Added 2026-10-06: parts ride on parts.** Index into this same `bodyShapes[]` (a projectile's `parts[]` for a part): the shape rides that shape, its `xOffset`/`yOffset` measured from the carrier's centre along the carrier's angle and its `angle` added to the carrier's, so when the carrier spins (`spinSpeed`) everything on it orbits: moons round a planet, lanterns on a wheel, a clock's hands, a chained tail of parts each riding the last. The editor's part form calls it "Rides on" and lists "What rides on it". Rules from the importer: `mount` wins, then `mountTurret`, then this; a bad index, a self-reference or a chain where the carrier already sits more than three deep is cleared to −1 ("Parts nest 4 deep at most": a root part and four riders); **a riding shape is looks only**: the importer clears its `collidable` flag, so put the hitbox on the carrier. Barrels take `mountPart` too (§7). The chain's root may itself sit on a turret or a barrel. **Confirmed in play 2026-10-06** (the lab's Editor Update Probe): three moons riding a spinning plate went round with it; they draw **under** the carrier unless `aboveBody` (they were barely visible beneath the plate), the same rule as a part on a barrel. | Confirmed (play) |
| `fixedRotation` | bool | false | | **Added 2026-10-06.** "Keeps its angle in the world instead of turning with the tank's aim, like a dominator's base." Only the **angle** is fixed: a part placed off-centre still swings round with the aim, so a dominator base or a compass needle sits at the centre. The editor's part form is now a **Rotation** choice: With the aim (the usual) / Fixed / Spins; its spin tooltip was reworded to "Turns on its own, in world space. Speed is rotation per tick; negative spins the other way, 0 is Fixed. The preview does not animate." **Confirmed in play 2026-10-06**: a fixed square under the hull and a fixed needle over it held still while the tank turned. | Confirmed (play) |
| `staysVisible` | bool | false | `true` (a player-built glitch tank: a blue circle on an invisibility-enabled tank) | The part stays drawn while the tank is faded: eyes that give a stalker away. Confirmed in play 2026-09-26: a Yellow dot stayed visible while the hull and an ordinary Cyan dot faded. | Confirmed |
| `color` | int \| string | 0 (`#555555`) | Palette index (§10), or since 2026-10-06 a hex string `#rrggbb` / `#rrggbbaa`. Vanilla smasher hexagons and Spike triangles omit it and render `#555555` in the roster SVG, so the default is index 0, the dark smasher grey. | Confirmed |
| `order` | int | 0 | Draw order (§9a). | Confirmed |
| `editor` | object | | `{"name": "…"}`, `{"group": "…"}` — label and folder in the editor's part list. | Confirmed |

## 9. Turret (`tanks[].turrets[]`)

```json
{"angle":3.1415927}                                                                   // top-mounted (Auto Trapper)
{"xOffset":40,"range":2000,"arc":1.4137,"controllable":true,"aboveBody":false}        // side-mounted (Auto 7)
{"xOffset":40,"yOffset":-20,"baseSize":10,"range":0,"angle":-0.7854,"arc":1.0472,"controllable":true,"aboveBody":false,"color":27}  // the serpent's jaw pivot
{"xOffset":15,"baseSize":30,"arc":1.5708,"color":19}                                  // the serpent's eyeball (pupil is a mounted shape)
```

| Key | Type | Default | Meaning | Confidence |
|---|---|---|---|---|
| `xOffset` / `yOffset` | number | 0 | Mount position, same axes as body shapes. Auto 7 places seven on a ring of radius 40. | Confirmed |
| `angle` | number | 0 | Rest/centre direction of the turret. The editor: "Where its arc is centred, and where it rests with nothing to shoot." | Confirmed |
| `arc` | number | full circle | Traverse limit either side of `angle`, radians (Auto 7: 1.41 ≈ 81°). Verified: a 0.35 arc held a decorative and an armed turret within ±20° of `angle`; with no arc the turret tracked freely. **`0` is the full circle**, not a locked turret: the editor says "0 lets it spin all the way round, like Auto Tank" and writes 0 when unset. For a fixed pivot use a tiny arc (0.087). **On a projectile's turret the arc is measured from the projectile's heading when it was fired**, not from its nose as it turns, so a missile steered by an arc-limited turret can be escaped by moving round it; only `arc` 0 chases all round (a player's seeker missiles, recipes §33; their play, 2026-10-05). | Confirmed |
| `range` | number | ? | Targeting range in world units (side turrets 2000; human packs 1000–2750). Default for top turrets not written. **Unset** on a `controllable` turret (a player-built spider's legs) still auto-targets, and from further than 250: Leg Range Lab (2026-09-28) put 250-range legs on one side and unset legs on the other; both twitched toward passing shapes, and the unset legs reacted to shapes further away. **Unset = 1700** (the editor's default, read from its code 2026-09-29). **`0` turns auto-targeting off**: with `controllable: true` the turret rests at `angle` and follows the cursor (within `arc`) only while the fire button is held, returning to rest on release; what the turret carries (nothing, a player gun, an auto gun) makes no difference, and a pivot with **no `arc`** wanders when released. It lets go of the cursor once the cursor leaves its wedge or passes its tip. A skeleton character's hands seem to follow always only because they rest at `angle` 0 and the hull itself faces the cursor. (Serpent jaws and the `pivot-test` test build, 2026-09-26.) Without `controllable` the turret is a fixed pivot (two held props: `range: 0, arc: 0.087`). On a missile: 2000 with a 25° arc for a seeker, 400 with an 80° arc for a proximity fuse; a full-circle chaser needs a short range or it locks on to whatever is behind the tank at launch (recipes §33). | Confirmed |
| `controllable` | bool | false | Player can aim it (side-mounted Auto 3/5 behaviour, ref §4). Auto Smasher's top turret is `{"angle": π, "controllable": true}`, confirming the default is false and independent of mount style. With `range: 0` the player's aim applies only while fire is held; the turret otherwise sits at `angle` (serpent, 2026-09-26). **With a range** (a player-built pack, 2026-09-28: 72 tanks put legs, arms, hands, plumes and capes on `controllable` turrets with `arc` 0.26–0.7 and `range` 100 / 250 / 750 or unset, never 0) the turret tracks enemies inside the range while the player is idle and follows the cursor while firing: a "living limb" (recipes §27). **Confirmed** (Limb Lab, 2026-09-28: with nothing near and no click, the living-limb arm and the range-0 arm both sat still at rest; a shape within 250 turned the living-limb arm toward it while the range-0 arm ignored it; holding left click swung both to the cursor; two legs resting backward (165 degrees, arc 15, range unset) ignored a forward cursor, which is outside their wedge). A limb follows the cursor only while the cursor is inside its wedge (rest `angle` ± `arc`), so a limb resting backward never follows a forward cursor. | Confirmed |
| `aboveBody` | bool | true | Drawn over the hull. Side turrets set false. The editor defaults it to true. | Confirmed (editor code) |
| `baseSize` | number | 25 | **Radius of the turret's disc** (human packs 1–53: 10 for a joint that should read as a pivot, 30 for an eyeball, 1 to hide it). Verified in every export. | Confirmed (drawing) |
| `color` | int \| string | 1 (`#999999`) | Palette index of the disc (§10), or a hex string since 2026-10-06: 19 White for an eyeball, 27 for a joint in the owner's colour. | Confirmed (drawing) |
| `order` | int | 0 | Draw order (§9a). | Confirmed |
| `editor` | object | | `{"name": "…"}`, `{"group": "…"}` | Confirmed |

The turret's weapon is a tank barrel with `mountTurret` = the turret's index (§7); shapes
ride it the same way (§8 `mountTurret`), so a turret can carry a whole assembly: the
creature's jaw is a bar, four teeth, a fang and three invisible bite barrels on one
`baseSize: 10` pivot. The disc is drawn by the game at `baseSize`. **Turrets always track
the nearest target within `range` and `arc`, weapon or not.** A turret carrying only a
decorative rod and no `arc` swings freely toward enemies; the same turret with `arc` 0.35
about straight back only moves when a target is inside that wedge, so most of the time it
rests at `angle`, lagging the hull's turns and settling back (three-pivot tail tests,
2026-09-26). A weapon on an arc-limited turret fires only at targets inside the wedge. **Turrets cannot be
nested**: a turret carrying `mountTurret` (or `mount`) is placed at its raw `xOffset`/`yOffset`
in the tank frame and the field is ignored (SVG export of a three-turret chain test,
2026-09-26, the SVG export of a three-turret chain test). Decorative barrels
mounted on a turret (`bulletType: none`) do turn with it. `editor: {"name": "…"}` labels the
turret in the editor's part list, exactly as for barrels (§7) and shapes (§8). Confirmed.

### 9a. Draw order

Parts are painted in ascending `order`; barrels, body shapes and turrets share the one
sequence, and ties keep array order (verified in SVG: square 1, pentagon 1, cannon 2,
triangle 3). The hull is painted after all of them regardless of value; only parts marked
above the body paint over it: shapes with `aboveBody`, barrels with `flags.aboveBody`, and
turrets unless `aboveBody: false`. The editor assigns `order` in creation sequence, so a
user pack can show values up to 70 across 70 parts (a player-built tank); it does not
renumber duplicates. Projectile sub-barrels have their own per-projectile sequence.

### 9b. Drawing rules (from the editor's SVG exports)

Reverse-engineered from the editor's SVG exports and the players' SVG exports and implemented in
`scripts/render_pack.py`, whose `--compare` mode reproduces every
polygon of the 53 stock tanks, the 19 official tanks and the **326 human-built tanks** to
within 0.3 units. All Confirmed unless marked.

| Rule | Detail |
|---|---|
| Frame | x forward, y to the tank's right (screen y-down); rotations clockwise positive. The export wraps the tank in `rotate(-45)` for display only. |
| Outline | Every part: stroke width 7.5, colour = `round(fill × 0.72)` per channel, round joins. |
| Hull circle | radius `size` (default 50), fill palette 2 (player blue) or `body.color`. |
| Hull polygon | circumradius **1.3 × `size`** (Necromancer's default 50 draws as 65; the official octagons' 44.23 draws as 57.5). Vertex at 0° except squares, whose vertices start at 45° (axis aligned). **`body.angle` is applied** (the exporter writes it as a `rotate` on the hull polygon; the earlier note that it was ignored came from a parser that dropped that transform). |
| Body shape | circumradius `size` (25 when omitted), centred at (`xOffset`, `yOffset`), rotated `angle`; same vertex rule (squares at 45°). Default fill palette 0. `sides` 0 or 1: a circle of radius `size`. |
| Star polygon | 2 × `sides` vertices: vertex k at angle `angle + k·π/sides`, radius **0.4 × size** for even k (inner) and `size` for odd k, so the points sit at odd multiples of π/sides (no 45° rule for star squares). Same for a `star` hull, at 1.3 × size. |
| Barrel | rectangle from x = `startDistance` to `startDistance + distance`, half-width 21 × `heightMultiplier` at the start and × `muzzleScale` at the end, shifted by `offset` in y, then rotated by `angle` about the hull centre. Default fill palette 1. Negative `startDistance`, widths 0.1–2.5 and tapers 0.04–7.5 all draw by the same formula. `invisible: true` barrels are not drawn at all. |
| Barrel on a barrel (`mount`) | drawn in a frame at the **midpoint** of the base barrel's axis (`startDistance + distance/2` along its angle, at its offset), rotated by the base's angle; the mounted barrel's own `startDistance` counts from there. Drawn before (under) the base barrel, or after it when the mounted barrel has `flags.aboveBody`. Auto Trapper's tip: base 60 long, tip `startDistance` 30 → tip spans 60–80. A **shape** with `mount` uses the same frame (Ritual's triangle at `xOffset` 45 on a 70-long barrel lands 80 out). |
| Part on a part (`mountPart`) | drawn in a frame at the carrier shape's **centre**, rotated by the carrier's angle, inside whatever frame the carrier itself sits in (the hull, a turret, a barrel's midpoint or another shape), four deep at most. The rider's own `order` and `aboveBody` place it in the sequence like any other part; `render_pack.py` draws it so (the editor's preview code, 2026-10-06: Confirmed (editor code), not yet checked against an SVG export). |
| Fixed rotation | a `fixedRotation` shape draws at its `angle` in the **world**: the renderer subtracts the heading it draws the tank at, so a heading-up render shows the part turned 90° from an aim-relative one. |
| Turret | frame at (`xOffset`, `yOffset`) rotated by `angle`; the barrels and shapes with `mountTurret` draw in that frame, those without `aboveBody` first, then the disc (radius `baseSize`, default 25, fill `color`, default palette 1), then the mounted parts flagged above. Within each group parts draw in ascending `order`; **ties draw shapes before barrels** (the opposite of the top-level rule; a player-built wizard's export, 2026-09-28). `aboveBody` (default true) draws the whole turret after the hull. |
| Sequence | parts under the hull (barrels without `flags.aboveBody`, plain shapes, `aboveBody: false` turrets) in ascending `order`, ties in array order; then the hull; then `aboveBody` shapes, `flags.aboveBody` barrels and turrets in ascending `order`. Mounted parts draw inside their base's slot. |
| Colour 27 | the exporter fills it with the hull's own `color` (or player blue), and play does the same: 27 is the hull's colour, the team's only when the hull is team-coloured (Confirmed 2026-09-30, §10); for team accents on a coloured figure, a team hull under a same-size cover shape. Parts **mounted on a turret** follow too: colour-27 eye dots on an auto-turret showed the team colour in play (gargoyle heads on a team hull under a cover, 2026-10-01). |
| Shape offsets | the exporter rounds shape `translate` values to integers; the game uses the real values. |

### 9c. Part limits

**Confirmed 2026-09-29 from the editor's import code** (first seen 2026-09-27, when the croc's
42 body shapes showed as "32/32 parts" with everything after the 32nd missing in play, no error):
per tank the editor keeps **32 body shapes, 32 barrels and 8 turrets**, per projectile **32
parts, 32 barrels and 8 turrets**, and **16 projectiles**; anything past that is dropped on import
without a word. A pack holds at most 512 tanks, 256 custom shapes and 512 bosses (§1b). The human packs agree: their
largest tanks sit at exactly 32 shapes and 32 barrels, and the most turrets seen is 8.
`validate_pack.py` errors past each limit; `compose.save()` warns. **Hitboxes**: 8 collidable
shapes per tank, 3 per projectile (2026-10-06; §8).

**Total pieces, confirmed 2026-09-28**: the game refuses a tank with more than **96 pieces**, counting body shapes, barrels and turrets on the tank **plus** every projectile's `parts`, `barrels` (drawing-only rods, pop and fist sub-barrels) and `turrets`. The error reads "the tank has 97 pieces across its body and projectiles; a tank may have 96" (SpongeBob: 65 on the tank + 32 on projectiles). The previous build at exactly 96 imported, and a player-built pack's largest tanks sit at exactly 96. The editor checks the same count before loading ("has N pieces; a tank may have 96", §7a). So a figure drone, a drawn web or a decorated shot spends the same budget as the hull's art. The validator errors over 96.

