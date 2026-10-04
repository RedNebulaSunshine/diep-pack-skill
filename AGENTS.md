# AGENTS.md

Instructions for AI coding agents (Copilot, Claude Code, others) working in this repository.

## Who publishes this repository

This repository is published by **RedNebulaSunshine** (`rednebulasunshine@gmail.com`). Every commit,
tag, release, pull request, issue and comment here must carry that identity and no other.

Before any write (`git commit`, `git push`, `gh pr`, `gh issue`, `gh release`, `gh api` with a body):

- `git config user.name` and `user.email` in this checkout must be `RedNebulaSunshine` and
  `rednebulasunshine@gmail.com`. If they are not, set them locally (`git config user.name ...`) first.
- `gh api user --jq .login` must print `RedNebulaSunshine`. If it prints anything else, do not run the
  command. Point `GH_TOKEN` at the RedNebulaSunshine account (or `gh auth switch`) and check again.
- Add no `Co-authored-by:` trailer that names any person, account or tool other than RedNebulaSunshine.
- After opening a pull request or issue, verify it: `gh pr view <n> --json author,commits`. If the author
  is not RedNebulaSunshine, stop and tell the maintainer. Do not try to fix it quietly.
- If you cannot confirm which identity a command will use, do not run it. Ask.

## Other rules

- The skill names no other player's pack, author or tank, in files or commit messages: say "a player-built
  pack" and describe tanks by what they are.
- Read `SKILL.md`, `CHANGELOG.md`, `references/` and `scripts/` before changing anything. A version bump is
  `metadata.version` in `SKILL.md` plus a `CHANGELOG.md` entry; the release workflow builds and publishes
  the zip on push to `main`.
- Run `python scripts/validate_pack.py examples/x-wing/x-wing.diep-pack --summary` after touching the
  validator or composer.
