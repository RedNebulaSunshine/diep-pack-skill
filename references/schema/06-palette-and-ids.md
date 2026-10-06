## 10. Colour palette

`color` fields on body, body shapes, barrels, turret discs and projectiles are indices into the
game's palette (the one `net_replace_color` edits, ref §7) **or, since the editor update of
2026-10-06, an exact colour as a hex string** (below). Hex values measured from the editor's
SVG export; **names are the editor's own swatch names** (hover text in the per-part colour
picker, read off 2026-09-26), which is what to call colours when talking to the user.

**Exact colours (Confirmed (editor code) 2026-10-06).** Every `color` field accepts a string
`#rrggbb` or `#rrggbbaa` (case-insensitive; the editor stores it lower-cased) as well as an index
0–27; anything else falls back to the field's default (27 for the body and projectiles, 0 for
shapes, 1 for barrels and turrets). The picker gained **Custom color**, **Edit color**, a **Hex**
box and an **Opacity** slider (the `aa` pair), and remembers the last 22 custom colours per browser
(local storage, not in the pack). Exports write the value as stored, so a pack may carry hex
strings anywhere a colour goes, and a custom arena shape's `color` must now be a *valid* hex string
(else `#ffe869`). **A 27 part on a hex-coloured hull shows the team colour**, not the hull's hex (Confirmed in play
2026-10-06: an orange hex hull with a 27 square showed a blue, red or other team square once a team
was assigned; with no team assigned the square drew see-through with a grey outline). The editor's
preview resolves 27 to the hull string, so it misleads here. This makes a hex hull the **simple way
to team-tint a coloured figure**: paint the hull its exact colour and set the accents to 27, no cover
shape needed. **The alpha byte draws the part translucent** (Confirmed in play 2026-10-06: a half-opaque triangle
over the hull and a 35 % white hexagon beside it both showed the hull, and arena shapes, through them).
So a ghost, glass, smoke, water or a shadow is now a one-field effect; keep the alpha above about 0x40
or the outline is all that reads. `validate_pack.py` accepts both forms;
`compose.C.rgb()`, `C.rgba()` and `C.alpha(C.cyan, 0.5)` write them. Prefer the palette where a
swatch is close: players read the stock colours (yellow food, pink crashers, grey barrels), and a
palette hull keeps the team-colour recipe below simple.

| idx | editor name | hex | idx | editor name | hex | idx | editor name | hex |
|---|---|---|---|---|---|---|---|---|
| 0 | Border (grey) | `#555555` | 10 | Periwinkle | `#768DFC` pentagon | 20 | Charcoal | `#3D3D3D` |
| 1 | Cannon | `#999999` | 11 | Pink | `#F177DD` crasher | 21 | Teal | `#12A5A5` |
| 2 | Blue | `#00B2E1` fixed | 12 | *(not offered)* | `#999999` | 22 | Indigo | `#4A57C8` |
| 3 | *(not offered)* | **blue team slot**, grey in editor | 13 | Mint | `#43FF91` (picker says `#4FFF91`) | 23 | Brown | `#A9724A` |
| 4 | Red | `#F14E54` **red team slot** | 14 | Box | `#BBBBBB` | 24 | Crimson | `#B5323A` |
| 5 | Purple | `#BF7FF5` **purple team slot** | 15 | *(not offered)* | `#999999` | 25 | Forest | `#2E9E5B` |
| 6 | Green | `#00E16E` **green team slot** | 16 | Orange | `#FCC376` | 26 | Plum | `#7B4FA8` |
| 7 | Shiny | `#8AFF69` | 17 | **Fallen** | `#C0C0C0` (offered since 2026-10-06; the Fallen bosses' grey) | 27 | "same color as the body" | **the hull's colour; the team's when the hull is team-coloured** |
| 8 | Yellow | `#FFE869` square | 18 | Cyan | `#35C5DB` | 28 | *(not offered)* | `#999999` |
| 9 | Salmon | `#FC7677` triangle | 19 | White | `#FFFFFF` | 29 | *(not offered)* | `#999999` |

The picker lists its 24 swatches in this order: White, Box, Cannon, Border (grey),
Charcoal, Red, Crimson, Salmon, Orange, Brown, Yellow, Shiny, Green, Mint, Forest, Cyan,
Teal, Blue, Indigo, Periwinkle, Purple, Plum, Pink, and since 2026-10-06 **Fallen** (17,
`#C0C0C0`, the hull colour of the game's Fallen Booster and Fallen Overlord boss tanks), then
Custom color. The five indices it does not offer (3, 12, 15, 28, 29) are the `#999999` slots;
"Cannon" writes 1, the index every stock barrel
uses (Confirmed 2026-09-29 from the editor's swatch table, which maps each name above to the
index in this table; an index it does not know draws `#999999`). 27 is
used by every official missile barrel and renders as the hull's colour, the team's on a
team-coloured hull; treat it as "same color as the body".

**In the live game 3–6 are the four team slots and are dynamic** (Confirmed 2026-09-26, a
grey-hulled test tank with octagons coloured 2, 3, 4, 5, 6, 27, 9, 24, swapping teams in
sandbox): each slot shows its own team's colour at first and, once the player has been on
that team, follows the player's current team from then on. Spawned blue: 2 and 3 blue; swap
to red: 3, 4 and 27 red; to purple: 3, 4, 5, 27 purple; to green: 3–6 and 27 green; back to
blue: 2–6 and 27 blue; thereafter 3–6 and 27 always match the team. Spawned purple the same
pattern started from 5. Index 2 stayed `#00B2E1` throughout except when the player was blue,
so it is a fixed blue; 9 and 24 never changed. The editor's hex values for 3–6 are therefore
only what the editor draws. For a colour that must stay put use 9 or 24 (reds), 2 or 22
(blues), 13 or 25 (greens), 26 (purple); `validate_pack.py` warns on 3–6.
The editor's per-part colour picker (found 2026-09-26) is the named list above plus the
"same color as the body" checkbox, which writes 27 and greys out the list. A part with
`color: 3` shows blue in the editor with nothing selected. **27 on a part takes the hull's colour**
(Confirmed in play 2026-09-30, a 19-tank pack; an early 2026-09-26 note that read it as the team
colour on a Box hull was wrong): on a hull painted a fixed colour, parts set to "same color as the
body" show that fixed colour. The editor's labels say the same: parts read "Same color as the
body", a projectile's colour switch "The team color, as each player sees it". **The recipe for team
accents on a coloured figure** (Confirmed 2026-09-30): leave the hull team-coloured (no `color`)
and cover it exactly with a same-size `aboveBody` shape in the figure's colour (polygon hulls draw
at 1.3 x size, shapes do not), drawn before the face details; parts at 27 then follow the team, and
shots with no `color` are team-coloured. A shot drawn in a fixed colour does the same on its own
scale: team disc (no `color`), a size-50 `aboveBody` part in the fixed colour over it, and small
27 parts (eyes, bubbles, a shine) as the team's highlight. A shot's line parts (`proj_rod`) and
shapes share one draw `order`, ties drawing the lines first, so a 27 rod over a covering part needs
a higher `order` (a cat's collar, 2026-09-30). Note that the picker calls the team slots simply
"Red", "Purple" and "Green": a user who picks "Red" in the editor gets a part that follows
their team after swaps, and the fixed reds are Salmon and Crimson.

## 11. Vanilla tank IDs

Corrected from the first draft using official data: every `upgradesFrom` in the anniversary
pack names a sensible parent under this table (Automator ← 52 Factory, Cyclone ← 54
Skimmer, Hitman ← 22 Ranger, Triple Flank ← 13 Twin Flank + 2 Triplet, …), and the editor's
stock-roster SVG lists tanks in exactly this order with the non-playable IDs skipped.
**8 is Tri-Angle and 9 is Flank Guard** (Striker, a Tri-Angle derivative, upgrades from 8;
a tester's Quad Tank from `[1, 9]` = Twin + Flank Guard).

| ID | Tank | ID | Tank | ID | Tank |
|---|---|---|---|---|---|
| 0 | Tank | 19 | Hunter | 38 | Landmine |
| 1 | Twin | 20 | Gunner | 39 | Auto Gunner |
| 2 | Triplet | 21 | Stalker | 40 | Auto 5 |
| 3 | Triple Shot | 22 | Ranger | 41 | Auto 3 |
| 4 | Quad Tank | 23 | Booster | 42 | Spread Shot |
| 5 | Octo Tank | 24 | Fighter | 43 | Streamliner |
| 6 | Sniper | 25 | Hybrid | 44 | Auto Trapper |
| 7 | Machine Gun | 26 | Manager | 45 | Destroyer Dominator* |
| 8 | Tri-Angle | 27 | Mothership* | 46 | Gunner Dominator* |
| 9 | Flank Guard | 28 | Predator | 47 | Trapper Dominator* |
| 10 | Destroyer | 29 | Sprayer | 48 | Battleship |
| 11 | Overseer | 30 | *(removed)* | 49 | Annihilator |
| 12 | Overlord | 31 | Trapper | 50 | Auto Smasher |
| 13 | Twin Flank | 32 | Gunner Trapper | 51 | Spike |
| 14 | Penta Shot | 33 | Overtrapper | 52 | Factory |
| 15 | Assassin | 34 | Mega Trapper | 53 | Ball* |
| 16 | Arena Closer* | 35 | Tri-Trapper | 54 | Skimmer |
| 17 | Necromancer | 36 | Smasher | 55 | Rocketeer |
| 18 | Triple Twin | 37 | *(removed)* | 58 | Auto Tank |
| | | | | 59 | *(gap)* |
| | | | | 60 | Dual-Barrel |
| | | | | 61 | Pellet Shot |
| | | | | 62 | Shotgun |
| | | | | 63 | Glider |
| | | | | 64 | Firework |

\* Not in the playable roster, and **not stock to the lobby**: `hidden: [16, …]` was refused,
"hidden id 16 is not a stock tank" (2026-09-29), and the editor's stock roster (54 tanks) leaves
all five out; never emit them. Older import probes showed the engine **accepting 16, 27, 45, 46, 47**
as `advancesInto` targets and **rejects 53** ("unknown id 53"), so Ball is not addressable
even if it exists internally. **56 and 57 are rejected** as unknown. The six newest stock
tanks are **58 and 60–64** (human packs, 2026-09-26): one total conversion hides every stock tank and
its `hidden` list is exactly the table above plus 58, 60, 61, 62, 63, 64 (no 59); a large
player-built pack has one tank `upgradesFrom [63]`, another `upgradesFrom [64]`, and its
Machine Gun replacement `advancesInto [62]` (Shotgun is Machine Gun's level-30 child), which
anchors 62–64 by name. **All six confirmed in game 2026-09-26** (an ID-probe pack:
six level-60 probes, one `upgradesFrom` each, appeared under Auto Tank, Dual-Barrel, Pellet
Shot, Shotgun, Glider and Firework respectively). Copying a stock tank into a pack does **not** preserve its
vanilla ID; it receives the next custom ID, so the copies cannot reveal them. Import errors
take the form `tank <id> advancesInto unknown id <n>` and abort the whole import.

