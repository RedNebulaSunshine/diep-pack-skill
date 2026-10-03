## 3. Body (`tanks[].body`)

```json
{"sides":8,"angle":0.39269908169872414,"size":44.23077}      // Automator, Resurrector
{"sides":18,"star":true,"angle":3.141592653589793,"size":67,"color":22}
```

| Key | Type | Example | Meaning | Confidence |
|---|---|---|---|---|
| `sides` | int | `0`, `4`, `8`, `18` | Hull polygon sides; 0 = circle (so are 1 and 2). Necromancer and Factory are 4. At most 18. Always written. | Confirmed |
| `star` | bool | `true` | The editor's "Drawn as a star" checkbox: alternating inner/outer vertices. | Confirmed |
| `angle` | number | `π/8` | Fixed rotation of the hull polygon (radians). Official octagons use π/8 so a flat side faces forward. The editor: "Turns the polygon on the body. Aim and barrels stay where they are." | Confirmed (editor code) |
| `size` | number | `44.23`, `67`, `5` | Hull radius. Default 50 (measured in SVG). Official octagon bodies use 44.23 so their area matches a circle of 50. Human packs go down to 5 and 8 to make the hull vanish behind custom parts (the whole figure is then decoration; the hitbox shrinks with it, §8 `collidable`). **At most 67**; the editor: "Radius at level 1. The whole tank grows as it levels, so a maxed one is about half again this." | Confirmed |
| `color` | int | `22` | Palette index (§10). Absent = 27, the team colour (the editor: "Blue to its owner and red to everyone else, or the team's color in team modes"). | Confirmed (editor code) |
| `spinSpeed` | number | `0.01` (Auto tanks), `0.5` | Continuous hull rotation, radians per tick. 0.0628 gave one turn per 4.0 s. Clamped to −0.5…0.5. | Confirmed |

## 4. Invisibility (`tanks[].invisibility`)

Always present. Official exports write all four rates; user exports drop `lossOnAttack` and
`lossOnMovement` when at default and drop `enabled` when false.

| Key | Type | Default | Examples | Meaning | Confidence |
|---|---|---|---|---|---|
| `enabled` | bool | false | Stalker, Landmine, Boss, Ambusher | Tank fades when the conditions below allow. | Confirmed |
| `gain` | number | 0.030769… (= 2/65) | Landmine 0.004, Ambusher 0.003, extreme 1/1500 | Opacity lost per tick while eligible. The editor shows it as **"Time to vanish"** in seconds, gain = 1 ÷ (25 × seconds), 0.1–60 s: "Seconds from fully visible to gone while idle. Moving or firing shows it again." Default 1.3 s (Stalker/Manager); Landmine 10 s. | Confirmed (editor code) |
| `lossOnHit` | number | 0.05 | extreme `0` | Opacity regained per hit taken. The editor shows it as **"Hits to reveal"**, the hits from fully hidden until it shows faintly: lossOnHit = 0.3 ÷ (hits − 1), so the default 0.05 is 7 hits and `0` is never. | Confirmed (editor code) |
| `lossOnAttack` | number | 0.23 | Landmine, Boss `0` | Opacity regained per shot fired. `0` = firing does not reveal (Boss, a Manager derivative); confirmed in play for a `forceFire` trail dropper: the tank faded while it kept firing. Its shots stay visible (below). | Confirmed (with `0`) |
| `lossOnMovement` | number | 0.08 | Landmine, Ambusher 0.16 | Opacity regained per tick while moving. | High |
| `revealDistance` | number | ? | Stalker 450, Landmine 650, Ambusher 1650 | Range within which enemies still see the faded tank, faintly (the editor: "Enemies this close see it faintly. 0 never reveals."). Default 0; at most 3000. | Confirmed (editor code) |


**Projectiles do not fade with their tank** (Confirmed in play 2026-10-01: a stealth carrier with
`lossOnAttack: 0` and an auto-firing trail dropper). The tank faded while still and its
`forceFire` barrels kept firing, but the shots stayed fully visible, so a trail, an exhaust plume
or any auto-fire marks where a faded tank lies. Use it on purpose (a ghost ship hiding in its own
fog bank) or keep auto-fire off stealth tanks.
