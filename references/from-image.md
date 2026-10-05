# From a picture

Read this when the request includes a picture or names one: a sketch of a tank, a drawing of
a subject, a photo or artwork, a screenshot of a tank in the editor or in game. Nothing here
replaces the rest of the skill; it says how to turn what you see into the design sheet of
SKILL.md §2, which then proceeds as usual (the one question of §3, build, render, deliver).
You read images natively, so there is no script for this: look at the picture, write down
what it says, and treat the result as the user's description.

Load it by section with `ref.py image <§>` like the other references.

## 1. Look at the picture first, and decide what kind it is

Open the image before anything else (in a terminal host, read the file at the path the user
gave with the image-capable file reader; in a chat host it is already in front of you). Then
decide which of these it is; most hand-drawn requests are the first two at once:

| Kind | What it is for you | Example |
|---|---|---|
| **A sketch of the tank**: a body with barrels and parts drawn where the user wants them | A drawn design sheet. The geometry is the request: reproduce it. | a circle with one slanted barrel and a square shot in front of it |
| **A drawing of a subject** that is not drawn as a tank | A description in picture form. The look comes from the drawing; what it *does* comes from `moves.md` §1, offered, not built (§3). | a flying saucer with a pilot and landing legs |
| **A photo or artwork** of a real thing | A reference for the look (silhouette, proportions, colours). Moves offered as above. | a photo of a stag beetle; a film still |
| **A screenshot** of a tank in the editor or in game | Edit mode (SKILL.md §7). Ask for the pack file if they have it; otherwise rebuild what you see and say so. | the editor's preview of a Twin with wings |
| **A diagram** with no drawing: boxes, labels, a list | A description; read the text and carry on with §2 of SKILL.md. | "L1: Tank → L2: Twin + ears" |

Ignore what is not the drawing: the paper's edge, punch holes, shadows, a hand in the shot,
the table. If the image is too small or blurred to read, say which part you cannot make out
and give your best reading rather than stopping; the user can correct it in one line.

## 2. Transcribe every note before designing anything

Users annotate drawings with arrows: the words sit at the **tail** of the arrow and the
**head** touches the part the words are about. Before the design sheet, write out every
note as a list, one line each:

```
"Square Projectiles Yellow"  → the square drawn ahead of the barrel  → the shot: 4 sides, Yellow
"TANK BODY Red"              → the circle                           → hull colour Salmon (C.red)
"BARREL"                     → the rectangle on the right            → a gun, not a decoration
```

Rules of reading, from what people actually draw:

- **Text with no arrow** is about the whole tank or *is* the request ("Gimme a UFO", "level
  45", "make it scary"). Treat it as the words of the message.
- **Crossed-out text** is withdrawn; the word beside it is the replacement ("~~Turret~~ Barrel"
  means a barrel). Do not build the struck one.
- **A curved arrow around a part** means it spins or swings, not that it is pointed at.
- **Handwriting is approximate.** Give the most sensible reading ("Flapy Wing" is a wing that
  flaps) and mark the ones you are unsure of with a question mark in the list.
- **A note you cannot place** (the arrow ends in space, two parts are equally close) goes in
  the list as "unplaced", with your best guess. Never silently drop a note: each one is
  something the user bothered to write.
- **Several arrows from one note** apply it to each part they reach.

Then read the list back. In the one question of SKILL.md §3, before anything else, give the
list as "What I read from your drawing", one short line per note, so a misread arrow or word
is caught before a build rather than after. When the host cannot ask (a non-interactive run)
or the user said to just build it, put the same list in the recap instead (§5 below).

## 3. The drawing is the whole build; everything else is an offer

Someone who draws a tank has already decided what it is. The first build contains exactly
what the drawing and its notes show: those parts, those guns, those colours, and the motion
the notes ask for ("wings flap", "eyes follow", a curved arrow). Nothing else goes in.

The skill asks before it embellishes any request (SKILL.md §2 "Motion is a question", §3
"Motion and extras"); a drawing leaves even less to decide, because the paper already answers
most of the question: what is there, what moves, how much detail. Play testers reviewing
drawn tanks said the same thing about every unrequested addition, a team-coloured mark on a
shot, a hop on right click, eggs that hatch, legs that swing, a warp jump: good idea, but ask
first. However good the addition, it reads as not listening, and the first test of a drawn
tank is whether it matches the paper.

So the moves method still runs (a UFO is still known for abduction and a death ray), and its
output goes into the one question as **offers**, each marked "not on your drawing", none of
them built until the user says yes. The view (§4) is a question too, not a decision, and so
is the **style**: "true to your drawing (Recommended), or re-imagined as a cleaner, more
anatomically correct <subject>?" Someone who drew a lopsided chicken may want exactly that
chicken, or may have drawn the idea and want you to draw it well; only they know, and the
maintainer asked for this choice by name. A picture does not make the request less
interactive: read, ask, build, then edit in the usual loop (SKILL.md §7). Two cases need
one addition even so:

- **A drawing with no weapon at all** (a saucer, an animal with no gun). A tank must be able
  to fire, so propose the single most obvious weapon for the subject, mark it as the one thing
  you are adding, and ask. Non-interactive: build that one weapon, nothing else.
- **A rule that forces a visible change**: the team colour must show on the tank and its shots
  (figurative.md §1), a figure needs a hitbox. Say what the rule needs, offer two ways to meet
  it (a small team mark on each shot, or a team ring on the hull; a collidable plate under the
  body) and let them pick. Non-interactive: meet the rule in the least visible way and say so.

When the host cannot ask: build the drawing, apply the two cases above, and put every other
idea under "Not built, on offer" in the recap, one line each. That is the whole fallback; do
not promote a recommended move to "built" just because nobody could answer.

Each note is a requirement and wins over anything you would have inferred. Translate by the
kind of word:

| The note says | It becomes |
|---|---|
| a colour ("red", "yellow body", "orange beak") | the nearest palette name (`compose.C`, figurative.md §1): Red → Salmon (`C.red`, 9) or Crimson for a dark red, Yellow → Yellow, Orange → Orange, Green → Mint, Blue → Blue, Black → Charcoal, White → White, Grey → Cannon. Say which you picked. A coloured hull is a team hull under a same-size `above=True` cover, so the team still shows |
| a shape word on a shot ("square projectiles", "spiky bullets") | the projectile's `sides` / `star` (4 sides; a star for spiky), with its colour if given |
| a movement verb ("eyes follow", "wings flap", "legs wiggle", "rotate", "spins", "bounces") | the matching entry of the motion map (figurative.md §5): follow → `eye()` or a tracking turret; flap / wiggle / paddle → `animate()` on a pendulum pivot or piston, with `forceFire` so it moves without a click; rotate / spin on a part → `spinSpeed`; on a projectile → `spin`. Only the parts the notes name move |
| a part name ("barrel", "cannon", "turret", "spawner") | that mechanic, with the stock numbers from `recipes.md`, placed where it is drawn |
| a weapon or power in plain words ("shoots lasers", "tractor beam", "lays eggs") | a move from the catalogue of `moves.md` §2, on the button the note names or the one you choose |
| a number ("level 30", "3 drones", "fast") | the field it names; "fast" and "slow" are relative to the stock tank you start from |
| a feeling ("scary", "cute", "chunky") | a styling choice you make and name in the recap |

## 4. Geometry: what the drawing settles and how to read it

**Front.** The tank faces its aim, and the renderer draws that as *up*. In the drawing, the
front is, in order: an arrow or word that marks it; the direction the main barrel points; the
direction the subject faces (a beak, a nose, a windscreen); otherwise up. Rotate the whole
drawing in your head so that direction is forward (+x in a compose script), and say in the
read-back which you chose ("front = where the barrel points, up-right in the drawing").

**View.** The game is top-down, but a tank is a flat picture that turns with the aim, so a
side-view drawing (a bird in profile, a saucer seen edge-on with its legs) can be reproduced
as drawn: it reads as that creature facing its aim, and a face painted on a hull works the
same way (the `president-prism` archetype). Users who drew a profile and got an overhead
tank were surprised, even when it looked good, so **ask**: "as drawn (profile), or seen from
above?" with as-drawn first. figurative.md §2 step 1 asks for a top-down proxy only when
*you* choose the view for a named subject. Non-interactive: as drawn.

**Scale.** The body they drew is the hull: radius 50 in tank units. Measure everything else
against it by eye: a barrel one and a half bodies long is `length` 150; a wing root at the
body's rim sits at radius 50. Angles to the nearest 15° are plenty. Place parts as fractions
of the hull radius, not in pixels, and never promise pixel accuracy: the sketch is a plan,
not a blueprint. Keep the drawn proportions of small things too: a shot's points, a beak, a
foot. Testers notice when a spindle's tips come out thinner at the base than on paper.

**Layering: what the drawing shows on top is drawn last.** A wing, a plate or a face drawn
*over* the body is an `above=True` part created *after* the body cover and the parts it
overlaps (compose draws in creation order, so an above-hull wing created before the Yellow
body cover still ends up under the cover). A leg or tail drawn *behind* the body goes under
it and is drawn first. Check this in the render: if a part the drawing shows on top has its
root swallowed, move its creation later.

**Symmetry.** A hand-drawn wobble is not design intent. If a feature is roughly mirrored
(two legs, two eyes, two engines), build it once and `mirror()` it; if one barrel is a little
off-centre, centre it unless a note says otherwise. Keep genuine asymmetry (a single wing,
one claw bigger than the other).

**Features to primitives.** Map each drawn feature with the table in figurative.md §2 step 3
(a wing is a `strip` or `fan`, legs are rods or a `limb`, a crest is a `ring` of triangles,
eyes are `eye()` when a note says they look). A shape drawn *in front of* a barrel is the
shot it fires: copy its outline onto the projectile (`sides`, `star`, `parts`, `spin`) at the
drawn proportions. Count the parts against the budget (32 shapes, 32 barrels, 96 pieces:
SKILL.md §2) while listing them; a detailed drawing spends most of it.

**Shots look like their fields, not like their names.** A bullet is a disc as wide as its
barrel (`heightMultiplier` and `bulletSizeMultiplier` scale it); the Sniper preset makes it
*bigger* and faster, not thin. A "ray", "needle" or "laser" only looks like one if you draw
it (`proj_rod`s on the projectile, or `sides`); otherwise it is a ball, and the recap must
call it a ball with its speed and rate in plain words. A tester who was promised "thin, fast
bolts" and saw round, slow ones lost trust in the whole recap.

**What the format cannot draw**, and the honest substitute: an ellipse (a chain of circles
or an octagon stretched by two overlapping polygons), a free curve (a `chain` or `polyline`),
a gradient (two shades), transparency (none), text (none; a mouth or a scar is a `line`).
Name every substitute in the recap so the user knows what to expect in game.

## 5. Build, then compare the render to the drawing

Build as in SKILL.md §4b (a figurative sketch) or §4 (a plain weapon sketch; still render
it). In the critique step (§4b step 4), put the render beside the drawing with the same
front direction and go through the note list: is each note visible in the render? Is every
drawn feature present, in the place it was drawn, at about the drawn proportion, on the
layer the drawing shows? Does the silhouette match at thumbnail size? Is there anything in
the render that is not on the paper? Fix the script for anything that fails, at most three
passes. This is a stronger check than critiquing against your own idea of the subject,
because the user has already told you exactly what they expect to see.

In the recap (SKILL.md §6) add, for a request with a picture:

- **From your drawing**: the note list again, one line each, now saying how each was met
  (`"Eyes Follow" → two eye() turrets on the head, pupils track enemies`), with any you could
  not meet marked and explained.
- Your reading of the front and the view, in one line, with the other view as an offer.
- **Rules applied**: anything the format or the team-colour rule made you add or change, and
  the alternative way to meet it.
- Any substitute for something the format cannot draw (§4 above).
- **Not built, on offer**: every move or flourish the subject suggests, one line each with
  its button, so the user can pick with a word. This list is where the imagination goes.

## 6. Help the user draw well, when asked or when a drawing was hard to read

A short list you can give (also in the README under *Draw it instead*): one tank per
drawing; the body as a circle and barrels as rectangles pointing the way they fire; one
arrow from each note to the part it is about, words at the arrow's tail; colours and
movement words are welcome ("eyes follow", "wings flap", "spins"); mark the front if no
barrel shows it; draw what should move, and say how; photograph the page flat, in good
light, with nothing else on it. Say it only once, and only when it would have helped.
