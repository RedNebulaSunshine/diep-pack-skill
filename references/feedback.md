# Feedback: findings and discoveries for the skill's repository

The skill improves through what its users find, in two ways:

- **Findings**: the skill was wrong or incomplete. The spec in `references/schema/` was built from
  the editor's code and from in-game tests, and any play test can confirm or overturn part of it.
- **Discoveries**: the user and the skill found a new way of doing something, functional,
  aesthetic, quality of life or otherwise, that future users would want.

This file turns either one into a GitHub issue on the skill's repository (`metadata.repository`
in `SKILL.md`). **The skill never posts anything.** It drafts the issue, strips what is private,
and gives the user a link that opens GitHub's form already filled in. The user reads it and
submits it, or does not. The maintainer reads every issue before anything changes.

## 1. When to offer

Offer a report once per finding or discovery, at the end of the reply that delivers or recaps.
Never offer mid-design, never twice for the same thing, never as a nag.

**Findings**, when:

- in-game behaviour contradicts, refines or confirms something the skill says: a field, a
  default, a limit, a recipe's numbers, a Medium or Low guess now settled either way;
- the validator passed a pack the editor or the lobby refused, or failed one they accept;
- a render does not match what the editor draws;
- a build-library call (`ref.py api`) fails, or does something its docstring does not say;
- the user corrects how the skill works in a way that would help every user (how it pitches,
  what it asks, a rule of taste confirmed by play testers), not a preference about one pack.

**Discoveries**, when the two of you found something the skill did not know and others would
want:

- *functional*: a new move or mechanic, a new use of a field, a cheaper way through the import
  budget, presets combined so they do something none does alone;
- *aesthetic*: a way of drawing that reads better in game, such as a pattern, a layering or
  outline trick, a colour scheme that holds up with team colours, or a motion that sells the
  subject;
- *quality of life*: a faster way to test, a check that caught a mistake, a clearer question or
  recap, a helper that saved repetitive work;
- anything else that made the result better and would carry over to other designs.

Before offering a discovery, run `ref.py --find <its key field or word>` to be sure the
references do not already have it. It must carry over: a method that works for other
subjects, not this one subject's look. Offer it once the user has seen it work, in game or in
the render, and say how far it has been tested.

Not for: a taste call about one pack, a bug in the game itself that the skill cannot change,
a question, or anything the user asked to keep private.

### The offer: encourage it, and say plainly what is sent

Make it one or two lines, warm and specific. Name what is new and why others would want it.
For example, for a discovery: "That (technique) is new; the skill does not know it yet. Want
to share it so future users get it too? I'd draft a GitHub issue about the technique, not
about you or your pack. You'd see every word, and you'd submit it yourself."

When the user hesitates or asks what is shared, reassure them accurately and do not
overclaim:

- Nothing is sent by the skill. GitHub opens with the issue filled in, and the user reads it,
  edits it and submits it, or closes the tab.
- The issue describes the finding or the technique, not the user. It contains no names,
  author name, files, paths, accounts, keys or conversation. A script removes any of those that
  slip in as a second check, and lists what it removed.
- Pack contents go in only if the user says yes, and then only the excerpt that shows the
  point.
- The issue is public, and it appears under the user's own GitHub account, like any issue
  they file.

If the user declines, drop it and do not offer again for that finding or discovery.

**The maintainer is the exception.** If the user maintains this skill (they say so), fix it
in place as `SKILL.md` §8 describes instead of filing an issue. Record a discovery where it
belongs: a mechanic with its numbers in `recipes.md` (and a preset in `mechanics.py` if it will
be reused), a look in `figurative.md`, a verb-to-move in `moves.md` §2, a workflow step in
`SKILL.md`. Write it as a method, keeping the subject out.

## 2. Write the draft

Write `./output/feedback/<slug>.json` (slug from the title, lower case, hyphens). Write it
for a maintainer, or a maintainer's agent, who has not seen this conversation: everything it
needs to make the change goes in the issue.

| Key | Required | Finding | Discovery |
|---|---|---|---|
| `title` | yes | The fact: "`<field or rule>`: <what the game does>, not <what the skill says>" | "New: <what it achieves> by <how>" |
| `kind` | yes | `spec`, `validator`, `renderer`, `build-library`, `missing-move`, `skill-behaviour` or `other` | `discovery` |
| `area` | | The file and section: `references/schema/04-barrels.md §7a`, `scripts/validate_pack.py` | Where it would belong: `recipes.md` (new section), `figurative.md §5`, `moves.md §2` |
| `believed` | yes | What the skill says or did, quoted: the row, the number, the sentence | What the skill did or knew before: the limitation it works around, or "not in the references" |
| `observed` | yes | What the game, the editor or the user saw, with the numbers | The technique: what it achieves, how it is built (fields, presets, numbers, order), why it works |
| `tested` | | How: the steps, the date, once or repeated | Where it was seen working (render, in game) and how often |
| `suggestion` | | The change, as text that could be pasted into the named section, with the confidence tag it earns | The text to add, in that file's style, and a preset signature if it deserves one |
| `confidence` | | `Confirmed in game`, `likely` or `guess` | the same |
| `pack` | | Only if the user agrees: the smallest excerpt that shows it, not the whole pack | Only if the user agrees: the parts that make the trick |
| `agent` | | The host and model you are running as, e.g. "Claude Code (Opus 5.5)" | the same |

One finding or discovery per issue. Content rules, whatever the sanitiser catches:

- **No people.** Do not name the user, their author name, other players, or another player's
  pack or tank: write "a player-built pack". A user who wants credit can add it on GitHub.
- **The method, not the subject.** Describe a discovery so it works for anything ("a brim
  drawn as a ring of short rods above the hull"), not as this pack's character or theme.
- **No conversation.** No transcript, no quotes of the user beyond the behaviour they reported.
- **No machine.** No paths, accounts, keys or system details; the skill version and commit are
  added for you.

## 3. Sanitise and build the link

```
python <skill>/scripts/report_issue.py output/feedback/<slug>.json --redact "<author name>" --redact "<any other name from the session>"
```

Pass every person's name and every player-built pack or tank name that came up in the session
with `--redact`. The script also removes paths, user and machine names, e-mail addresses, keys
and tokens, IP addresses, @-handles (which would notify strangers on GitHub) and pack
`author` fields. It saves the sanitised body as `<slug>.md` beside the draft, and prints, in
order: what it removed, the body, a search link for duplicates, the new-issue link, the
`<slug>.link.html` page and a `gh` command.

Read the body it prints. If a redaction broke the meaning, rephrase the draft and rerun; never
put removed text back by hand. If the link was shortened to fit, say so: the user can paste
the rest from the saved `.md`.

## 4. Hand it to the user

Show the issue's title, a two- or three-line summary of the body and what the script removed
(or "nothing private was found"), and say: "This opens GitHub with the issue filled in. Check
it, edit anything, tick the privacy box and submit. Nothing has been sent." The user must be
signed in to GitHub.

The link is long (often 1–7 KB), and **a terminal wraps it and breaks it**, so in a terminal
host never paste the raw link. Ask "Open it in your browser?" and on a yes rerun the
script with `--open`; if it says no browser could be opened, give the path of the
`<slug>.link.html` page it saved (a button that holds the link). In a chat host that
renders markdown, give it as a link instead: `[Open the pre-filled issue](<link>)`.

Only if the user explicitly asks you to file it for them, and `gh` is installed and signed
in (`gh auth status`), run the printed `gh issue create` command: it posts under **their**
account, so get a yes for this exact issue first. Never post without that yes, and never post
an issue the user has not seen.

The repository can be overridden with `DIEP_PACK_REPO=owner/name` (a fork), and
`--plain` sends the whole body as one text field for a repository without the issue form.
