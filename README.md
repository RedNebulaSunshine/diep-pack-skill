# diep-pack

An [Agent Skill](https://agentskills.io) that turns a plain-English description into a custom
pack for the **diep.io sandbox editor**: tanks, and the arena shapes they fight over. Describe
a tank or a theme; the skill designs it, writes
the `.diep-pack` file, validates it against a reverse-engineered spec of the format, renders it
the way the editor draws it, looks at the render, and tells you what to try in game.

![X-Wing, rendered by the skill](examples/x-wing/x-wing.png)

> "an X-Wing with four wingtip lasers that converge on the cursor, a proton torpedo on right
> click, and an astromech that watches the nearest enemy"

The pack that prompt produced is in [`examples/x-wing/`](examples/x-wing/): the design script,
the `.diep-pack` it builds, and the PNG and SVG renders.

## What it can do

- Weapon tanks from every stock mechanic: alternating and ring cannons, snipers, destroyers,
  drones and swarms, necromancers, missiles, minions, trappers, smashers, stealth, auto
  turrets, shotguns, bursts, right-click modes, scopes.
- Figurative tanks that look like something (a dragonfly, a crab, a snake, a starship, a
  crocodile) built from up to 32 body shapes and 32 barrels, using the tricks players have
  discovered: parts that pump like pistons, pendulum tails, jaws and hands that follow the
  cursor, eyes that watch enemies, a body that trails behind the tank, faces painted on the hull.
- Themed arenas: the map's shapes replaced by the theme's own food, crashers that hunt,
  walls that never budge, rare prizes and bosses, laid out in square rings from the edge to the
  centre, with each shape's share of the spawns predicted before you import.
- Upgrade-tree placement (level and parent tanks), multi-tank lines, total conversions.
- Edit mode: change an existing pack without disturbing the rest.

## Install

The skill is a single folder in the
[Agent Skills](https://agentskills.io) format, so it works in any agent that reads `SKILL.md`.

**Claude Code**

```
git clone https://github.com/RedNebulaSunshine/diep-pack-skill ~/.claude/skills/diep-pack
```

or clone it into a project's `.claude/skills/diep-pack` to scope it to that project. Then:

```
/diep-pack a hexagonal smasher that fades when still, spikes spinning fast
```

**Claude.ai** upload a zip of this folder as a custom skill in Settings.

**Other agents (Codex, Cursor, Gemini CLI, …)** point the agent at `SKILL.md` or copy the
folder into wherever that agent looks for skills. Nothing in the skill depends on a
particular host.

**Requirements**

- Python 3.8 or newer (`python` or `python3`).
- [Pillow](https://pypi.org/project/Pillow/) for PNG renders: `pip install -r requirements.txt`.
  Without it the renderer still writes SVG.

**Updates**

Once a day at most, at the start of a session, the skill checks whether a newer version is
published and, if so, tells you what it adds ([`CHANGELOG.md`](CHANGELOG.md)) and offers to
update. A `git clone` updates itself with your OK (a fast-forward; local edits are never
touched); any other install gets download instructions. The check fetches this repository's
`SKILL.md` and `CHANGELOG.md` and sends nothing about you or your work. To turn it off, set
`DIEP_PACK_NO_UPDATE_CHECK=1`; to check by hand, run `python scripts/check_update.py --force`.

## How it works

| Piece | What it is |
|---|---|
| `SKILL.md` | The workflow the agent follows: load only the references it needs, work out the subject's signature moves, pitch them with level / parent / author in one question, build, validate, render, look, deliver. |
| `references/quick-reference.md` | Every field on one page with default, unit and confidence. |
| `references/schema/` | The full reverse-engineered spec of the `.diep-pack` format, one file per family, every field tagged Confirmed / High / Medium / Low with how it was established. Diep.io publishes no documentation for this format. |
| `references/moves.md` | From a subject to what the tank does: the method, a catalogue of verbs (swing a blade, leap, snare, summon, place…) mapped to mechanics, and worked pitches (Luke Skywalker, a hen, Thor, a pirate ship, a toaster). |
| `references/arena.md` | From a theme to the arena's shapes: the method, roles with their numbers (food, prize, hazard, wall, boss…), the ring layout and spawn weights. |
| `references/recipes.md` | How each stock mechanic is written, with the real stock tanks' numbers. |
| `references/vanilla-tanks.md` | Every vanilla tank's id, level and parents, and which ids the engine rejects. |
| `references/figurative.md` | Building a subject out of parts: primitives, the silhouette-first workflow, the motion map (what can move and how), lessons from player-built packs. |
| `scripts/validate_pack.py` | Standard-library validator: unknown keys, bad references, the editor's import limits (counts, clamps, the three-collidable rule), and the lobby's import budget, ported from the editor's own check. `--summary` prints what the pack says. |
| `scripts/render_pack.py` | Renders a pack the way the editor draws it (PNG, `--svg`, `--sheet`), verified to within a pixel against every stock tank and hundreds of player-built ones. |
| `scripts/ref.py` | Prints only the sections of the references a design needs (`ref.py recipes intro 5 25`, `ref.py spec 7a`, `ref.py --find keepDistance`) and the build library's calls without its source (`ref.py api`), so the agent loads a few thousand tokens instead of tens of thousands. |
| `scripts/check_update.py` | The once-a-day check for a newer published version: what is new, and `--apply` to fast-forward a git clone. |
| `scripts/skill_meta.py` | Reads the skill's version and repository from `SKILL.md`'s `metadata`, the one place the repository's address is written, so moving the repository is a one-line change. |
| `scripts/report_issue.py` | Turns a finding into a GitHub issue the user files themselves: strips paths, names, keys and other private details, then prints a link that opens the issue form filled in (`references/feedback.md`). |
| `scripts/compose.py`, `scripts/mechanics.py` | A build library for figurative designs: rods, chains, jointed limbs, fans, mirrors, frames, and every stock mechanic as a one-call preset. `save()` writes, validates and renders. |
| `assets/archetypes/` | Design scripts to copy from: dragonfly, crab, spider, starship, serpent, croc, a face on the hull. |
| `examples/x-wing/` | A complete worked example with its outputs. |
| `evals/evals.json` | Plain requests ("Luke Skywalker", "a hen") with what a good answer must propose unprompted: run them after changing `SKILL.md` or `moves.md`. |

Packs and renders are written to `./output/` in the directory the agent runs from
(set `DIEP_PACK_OUT` to change that).

To try the tooling without an agent:

```
python scripts/validate_pack.py examples/x-wing/x-wing.diep-pack --summary
python scripts/render_pack.py examples/x-wing/x-wing.diep-pack --svg
python examples/x-wing/x-wing.py
```

## Importing a pack

In the sandbox editor: **Import**, choose the `.diep-pack` file, **add to this pack**. Prefer
importing from a file over pasting; long pasted lines get mangled. Tank ids are reassigned on
import, so a pack cannot link into another pack's tree.

## Limits worth knowing

- 32 body shapes, 32 barrels and 8 turrets per tank; the editor drops the rest without a
  warning, and keeps only three collidable parts per tank and per projectile.
- The game refuses a tank over its import budget (120 entities a second, 250 alive, and four
  more limits); the validator carries the editor's own copy of that check.
- Turrets cannot be mounted on turrets, so a jointed chain that bends is impossible.
- A few defaults are still unmeasured; the spec's §13 lists them and the skill names any
  guess it relies on.

## Contributing

Findings from in-game tests and new techniques are the most valuable contributions. When you
tell the skill that something behaved differently in game, or the two of you find a new way of
doing something (a move, a drawing trick, a faster way to test), it offers to draft an issue for
this repository. It writes up the finding or the technique (not you or your pack), removes
anything private, and gives you a link that opens the issue already filled in. You check it and
press Submit; the skill sends nothing itself. You can also open an issue by hand with the
**Skill finding or discovery** form. Issues are read by the maintainer before anything
changes; please do not open pull requests for findings, open an issue instead.

## Licence and credits

MIT licence, see [LICENSE](LICENSE). Diep.io, its tank designs and the sandbox pack format
belong to the game's publisher; this project documents the format and generates files for
it and is not affiliated with them. The spec was built from the editor's own exports and from
in-game tests, and learned a great deal from six packs built by other players (326 tanks)
that are not redistributed here.
