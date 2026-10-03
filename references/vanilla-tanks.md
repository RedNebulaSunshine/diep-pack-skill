# Vanilla tanks: IDs, tiers and parents

For wiring `upgradesFrom` / `advancesInto` / `editor.replaces` / `hidden`. IDs are from
`references/schema/` §11 (engine-verified), levels from the stock-roster copies in
the stock-roster copy, parents from the game's upgrade tree.

**Link target** = the engine accepts this ID in a tree field. Never emit an ID marked no.

| ID | Tank | Level | Upgrades from | Link target |
|---|---|---|---|---|
| 0 | Tank | 1 | — | yes |
| 1 | Twin | 15 | Tank | yes |
| 2 | Triplet | 45 | Triple Shot | yes |
| 3 | Triple Shot | 30 | Twin | yes |
| 4 | Quad Tank | 30 | Twin, Flank Guard | yes |
| 5 | Octo Tank | 45 | Quad Tank | yes |
| 6 | Sniper | 15 | Tank | yes |
| 7 | Machine Gun | 15 | Tank | yes |
| 8 | Tri-Angle | 30 | Flank Guard | yes |
| 9 | Flank Guard | 15 | Tank | yes |
| 10 | Destroyer | 30 | Machine Gun | yes |
| 11 | Overseer | 30 | Sniper | yes |
| 12 | Overlord | 45 | Overseer | yes |
| 13 | Twin Flank | 30 | Twin, Flank Guard | yes |
| 14 | Penta Shot | 45 | Triple Shot | yes |
| 15 | Assassin | 30 | Sniper | yes |
| 16 | Arena Closer | — | not playable | **no** (not stock to the lobby) |
| 17 | Necromancer | 45 | Overseer | yes |
| 18 | Triple Twin | 45 | Twin Flank | yes |
| 19 | Hunter | 30 | Sniper | yes |
| 20 | Gunner | 30 | Machine Gun | yes |
| 21 | Stalker | 45 | Assassin | yes |
| 22 | Ranger | 45 | Assassin | yes |
| 23 | Booster | 45 | Tri-Angle | yes |
| 24 | Fighter | 45 | Tri-Angle | yes |
| 25 | Hybrid | 45 | Destroyer | yes |
| 26 | Manager | 45 | Overseer | yes |
| 27 | Mothership | — | not playable | **no** (not stock to the lobby) |
| 28 | Predator | 45 | Hunter | yes |
| 29 | Sprayer | 45 | Machine Gun (skips tier 3) | yes |
| 30 | *(removed)* | — | — | **no** |
| 31 | Trapper | 30 | Sniper | yes |
| 32 | Gunner Trapper | 45 | Gunner, Trapper | yes |
| 33 | Overtrapper | 45 | Overseer, Trapper | yes |
| 34 | Mega Trapper | 45 | Trapper | yes |
| 35 | Tri-Trapper | 45 | Trapper | yes |
| 36 | Smasher | 30 | Tank (skips tier 2) | yes |
| 37 | *(removed)* | — | — | **no** |
| 38 | Landmine | 45 | Smasher | yes |
| 39 | Auto Gunner | 45 | Gunner, Auto 3 | yes |
| 40 | Auto 5 | 45 | Quad Tank, Auto 3 | yes |
| 41 | Auto 3 | 30 | Flank Guard | yes |
| 42 | Spread Shot | 45 | Triple Shot | yes |
| 43 | Streamliner | 45 | Hunter, Gunner | yes |
| 44 | Auto Trapper | 45 | Trapper | yes |
| 45 | Destroyer Dominator | — | not playable | **no** (not stock to the lobby) |
| 46 | Gunner Dominator | — | not playable | **no** (not stock to the lobby) |
| 47 | Trapper Dominator | — | not playable | **no** (not stock to the lobby) |
| 48 | Battleship | 45 | Twin Flank, Overseer | yes |
| 49 | Annihilator | 45 | Destroyer | yes |
| 50 | Auto Smasher | 45 | Smasher | yes |
| 51 | Spike | 45 | Smasher | yes |
| 52 | Factory | 45 | Overseer | yes |
| 53 | Ball | — | internal | **no** (rejected) |
| 54 | Skimmer | 45 | Destroyer | yes |
| 55 | Rocketeer | 45 | Destroyer | yes |
| 56, 57 | *(gap)* | — | — | **no** (rejected) |
| 58 | Auto Tank | 45 | Tank | yes (probe confirmed 2026-09-26) |
| 59 | *(gap)* | — | — | **no** (absent from every human `hidden` list) |
| 60 | Dual-Barrel | 45 | ? | yes (probe confirmed 2026-09-26) |
| 61 | Pellet Shot | 45 | ? | yes (probe confirmed 2026-09-26) |
| 62 | Shotgun | 30 | Machine Gun | yes (a human pack's Machine Gun advances into it) |
| 63 | Glider | 45 | Destroyer | yes (a player-built tank upgrades from it) |
| 64 | Firework | 45 | ? | yes (a player-built tank upgrades from it) |

Notes:

- **At most 19 upgrades per tank**, stock children included (engine message `tank 0 offers
  20 upgrades, the most is 19`, 2026-09-28). Stock counts: Tank 6, Overseer 6, Destroyer 5,
  Trapper 5, Sniper, Machine Gun and Flank Guard 4. Spread a large line over several parents
  or chain it through its own tanks; the validator counts it.
- 16, 27, 45, 46 and 47 (Arena Closer, Mothership, the three Dominators) are **not stock** to the
  lobby: `hidden: [16, …]` was refused with "hidden id 16 is not a stock tank" (2026-09-29), and
  the editor's own stock roster lists the other 54 only. An older probe once accepted them as
  `advancesInto` targets; never emit them. The validator errors on them everywhere.
- 56 and 57 were probed and rejected. The six newest tanks are 58 and 60–64 (spec §11):
  found in the human packs, then confirmed in game on 2026-09-26 with one probe child per
  ID (an ID-probe pack). All six are safe link targets.
- Tier levels: tier 2 = 15, tier 3 = 30, tier 4 = 45. Official custom tier-5 tanks use 60
  (the official 10th Anniversary pack, all `upgradesFrom` a tier-4 tank, Mega
  Smasher `upgradesFrom [36]` at 45).
- `editor.replaces: N` puts the custom tank in vanilla tank N's menu slot; pair it with pack
  `hidden: [N]` or both tanks appear.
