# Changelog

Newest first. One entry per published version of the skill (`metadata.version` in
`SKILL.md`), in plain words for the people who use it: `scripts/check_update.py` shows these
lines to a user whose copy is older. Format: `## MAJOR.MINOR.PATCH (date)`, then a bullet per
change.

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
