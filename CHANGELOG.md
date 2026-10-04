# Changelog

Newest first. One entry per published version of the skill (`metadata.version` in
`SKILL.md`), in plain words for the people who use it: `scripts/check_update.py` shows these
lines to a user whose copy is older. Format: `## MAJOR.MINOR.PATCH (date)`, then a bullet per
change.

## 1.5.0 (2026-10-04)

- `Pack.from_stock(name)` in `compose.py` returns a Tank pre-filled from the stock roster: the
  tank's fields, body, projectiles, barrels, body shapes and turrets, verbatim and unrounded, with
  presets, rods, shapes and projectile parts added on top. It also sets `editor.replaces` and
  adds the vanilla id to the pack's `hidden` list (`replace=False` to skip; the base Tank cannot
  be hidden). `save()` prints a NOTE for every field that differs from the stock tank in play.
- `validate_pack.py` diffs every tank that carries `editor.replaces` against its stock twin and
  notes what changes play: barrel angles, offsets, delays, multipliers and width, projectile
  fields, `statsMaxLevel`, speed, zoom, hull size, collidable shapes. Decoration passes
  (`bulletType: "none"` barrels, non-collidable shapes, turrets without barrels, projectile
  parts, colours). `--cosmetic` turns the differences into errors for a reskin pack.

## 1.4.0 (2026-10-04)

- The skill now ships the sandbox editor's own export of its 54 stock tanks
  (`references/stock-tanks.diep-pack`) and serves it one tank at a time: `ref.py stock` lists
  the roster with each tank's vanilla id, level and parts, `ref.py stock "Twin Flank" 14` prints
  tanks verbatim by name or id, `ref.py stock --using raises` finds the tanks that use a field.
  A reskin, "a Penta Shot with ears" or any "stock tank plus …" design clones the real tank
  instead of rebuilding it from recipe excerpts and guesses (issues #8 and #9).
- The seven vanilla shapes as the editor itself writes them (size, health, score, contact
  damage, knockback, drift, crasher speed and radius, spawn weight and band) are now a table in
  arena.md §2 and verbatim JSON in the spec §1a. Four weights and every band were new: Alpha
  Pentagon 0.005 in the centre 10 %, Crasher 0.02 and Small Crasher 0.1 in the inner 20 %,
  Hexagon 0.004; vanilla food spawns only in the outer 80 %. `spawn_shares()` now counts the
  vanilla shapes it keeps at those weights and bands instead of three weights over the whole map.
- Reporting a finding: the draft can carry no file, so the skill no longer says "attached"; it
  tells the user to drop a file into a comment on the issue page after filing, and the reporter
  warns when a draft still claims an attachment.

## 1.3.5 (2026-10-03)

- README: on claude.ai the update check runs at the start of every chat, since nothing survives
  between chats there, and takes about a second. Second live test of the update notice.

## 1.3.4 (2026-10-03)

- The update check fetches past GitHub's five-minute file cache, so a release is seen the moment
  it is published, and every answer says when it was checked ("checked just now" or "from the
  cache, checked 40 min ago; --force checks now"), so a stale answer is never silent.

## 1.3.3 (2026-10-03)

- Tidy-up, no change in behaviour: the update script drops a variable left over from the old
  download link, and the README's tooling table says what the check does for a zip install. This
  release is also the first live test of the update notice on a zip install.

## 1.3.2 (2026-10-03)

- On a zip install (claude.ai, ChatGPT, a copied folder) the update notice now gives the exact
  release zip link and the reinstall steps (remove the old skill, upload the new zip) instead of
  offering an update it cannot perform.

## 1.3.1 (2026-10-03)

- Install without a terminal: the README walks through adding the skill to Claude (claude.ai
  and the desktop app; Claude Code on the same account gets it too) and to ChatGPT (Skills on
  work plans; a Project with the zip on personal plans), and every release now ships a ready
  `diep-pack.zip` on GitHub Releases, built automatically, with the folder name claude.ai
  accepts. The update check sends zip installs there.
- Chat hosts (issue #2): the skill now tells a terminal host from a chat host and, in a chat,
  hands the pack, its render and any feedback draft over through the host's download step
  instead of printing a path the user cannot open.

## 1.3.0 (2026-10-03)

- Pulsing light (a user's discovery, issue #1): two star shapes on one spot in two tones of one
  hue, spinning in opposite directions, read as a lantern, beacon, reactor core or heartbeat with
  no projectiles. `d.pulse(at, size)` builds it; figurative.md §5 and moves.md §2 describe it,
  with the beat-rate formula.

## 1.2.4 (2026-10-03)

- Loads on claude.ai: the description is quoted YAML with no angle brackets, and the Claude
  Code-only `argument-hint` line is gone, so uploading the zip as a skill no longer fails.

## 1.2.3 (2026-10-03)

- The skill is public: it now lives at github.com/RedNebulaSunshine/diep-pack-skill. Update
  checks and issue links point there.

## 1.2.2 (2026-10-01)

- Team colour: parts on a turret (eyes on a swivelling head) follow the team colour too, confirmed
  in play. Now in the spec.

## 1.2.1 (2026-10-01)

- Stealth: a faded tank's auto-fire keeps firing and its shots stay visible (a trail, a plume,
  exhaust), so they give away where it hides. Now in the spec and in the validator's summary.

## 1.2.0 (2026-10-01)

- Tells you when a newer version of the skill is out, what it adds, and can update itself
  (a git clone, with your OK).
- Discoveries: when you and the skill find a new trick (a move, a drawing technique, a faster
  way to test), it offers to share it with future users as a GitHub issue that you check and
  submit yourself. Nothing personal is sent.
- The repository's address lives in one place (`metadata.repository` in `SKILL.md`).

## 1.1.0 (2026-10-01)

- Uses fewer tokens: reads only the sections of its references a design needs
  (`scripts/ref.py`), and the build library's calls without its source.
- Findings from your play tests can go back to the skill: it drafts a GitHub issue, removes
  anything private, and opens the form filled in for you to check and submit.

## 1.0.0 (2026-09-30)

- First release as `diep-pack`: tanks, figurative tanks built from many parts, multi-tank
  lines and themed arenas of custom shapes, from a plain-English description; signature moves
  for any subject; a validator with the editor's own import budget; a renderer that matches
  the editor; versioned packs with changelogs.
