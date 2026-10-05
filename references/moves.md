# Signature moves: from a subject to what the tank *does*

A user who asks for "Luke Skywalker" is asking for a lightsaber, a leap and the Force, not for
a white circle with a gun. They will rarely name the mechanics: most users do not know the
format can swing a blade, spin a web or place a tower. **Your job is to know it for them.**
This file is the method, a catalogue organised by what a subject does, and worked pitches.
Presets are in `scripts/mechanics.py`; numbers and proofs are in `recipes.md` and
`figurative.md` §5.

## 1. The method (every request with a subject or a theme)

A subject is anything with an identity: a character, creature, vehicle, object, job,
element or mood ("Luke Skywalker", "a hen", "a pirate ship", "a toaster", "an ice tank",
"something spooky"). Only a request that is purely mechanical ("a Sniper with two alternating
barrels") skips this, and even then offer one idea in the recap.

1. **Brainstorm what makes the subject recognisable**, wide first: eight or more things a
   fan would name (famous items, powers, scenes, sidekicks, habits, catchphrases, weaknesses,
   where it lives), then keep the three to six that could become something the player sees or
   does. Think like a fan, not an engineer. You know the subject; use that knowledge fully.
   Headings that help:
   - *Weapon*: what it fights with (lightsaber, hammer, claws, stinger, cannons).
   - *Power*: what it can do that others cannot (the Force, lightning, webs, invisibility).
   - *Movement*: how it gets around (leaps, flies, slithers, charges, walks on legs).
   - *Company*: who is with it (droids, chicks, a crew, minions, a pet).
   - *Defence*: how it survives (shield, shell, armour, speed, hiding).
   - *Tell*: the one detail that makes a fan grin (R2-D2's dome, the hen's cluck, a
     pirate flag, a toaster's pop).
2. **Turn each trait into a move** with the catalogue in §2. Pick by what the player will
   see and feel, not by the nearest stock tank. Most traits will have no row of their own (a
   camera's flash, a firefighter's hose, a magnet's pull): describe the effect as the player
   would see it (something that flies from a point, stays on the ground, follows, bursts,
   shoves, circles, swings, fades) and build it from the rows that make that picture. A flash
   is a wide burst of short-lived White specks; a hose is a fast spray from a nozzle on a
   cursor pivot; a magnet's pull, which the game cannot do, becomes scrap that orbits the tank
   and hits what it touches. A trait with no honest substitute is drawn only; say so.
3. **Choose the default set**, one move per input so the tank is playable:
   - **left click**: the main attack (usually the signature weapon), always a shot the
     player can see leave the tank. Hidden hits (`punch()`, contact damage) are *automatic*
     moves, not a left-click weapon: a tester whose left click produced nothing visible
     reported the tank as not firing at all, and read nothing else in the recap;
   - **right click**: the signature power or movement (a dash, a burst, a place, a push);
   - **automatic**: something alive without a click (companions, living limbs, a trail,
     an aura, an eye that watches);
   - **the look**: the tell, drawn; whether it moves is offered, not assumed (SKILL.md §2,
     "Motion is a question").
   Keep one or two good ideas in reserve as alternatives. Check the part budget (32 shapes,
   32 barrels, 8 turrets, 96 pieces with the projectiles' parts) and the fire budget (Reload cap 0 for drawn projectiles, buildings
   and figure drones) before promising.
4. **Pitch it** (SKILL.md §3): name each chosen move in one plain line ("Lightsaber: a glowing
   blade that swings toward your cursor and cuts on left click"), then the alternatives in
   one line each. The user can say "go" or swap a move. When the user has said to just build
   it, or cannot be asked, build the default set and nothing beyond it (no motion or
   decoration the set does not need), and put the alternatives in the recap as offers.
5. **Check before delivering** (§4 below).

Prefer the surprising, true move to the safe one. "A hen that shoots bullets" is a failure
even if it validates; "a hen that lays eggs which hatch into chicks, followed by two chicks
that peck" is what the user hoped for without knowing to ask.

## 2. Catalogue: verbs to moves

Status: **C** confirmed in play, **H** high (follows from confirmed rules), **try** an
untested idea (offer it as an experiment and name it as a guess in the recap).

| The subject… | Move | Mechanism (preset) | Status |
|---|---|---|---|
| **swings a blade** (sword, lightsaber, axe, scythe) | a blade that swings to the cursor and cuts on click | a long rod on a `cursor_pivot` (or `living_limb` so it also twitches at enemies) carrying `blade(turret=i)`: a line of invisible hits along the rod; owner colour or a bright swatch for a glowing blade | H (blade), C (pivot) |
| … and the blade itself should hurt on contact | a blade that damages whatever it touches, with no click | the same rod plus up to three small `collidable` shapes along it on the pivot (the editor keeps three collidable parts per tank); collidable parts have their own hitbox (C), but whether a turret-mounted part deals the tank's body damage is untested | try |
| **punches, bites, claws, stings** within reach | hits that land only when something is close | `punch()` (hidden auto-turret, front cone); a mouth: `jaws()` + `contact_damage()` | C |
| **leaps, pounces, charges, jumps** | a burst of speed on right click | `dash()` (backward recoil barrel, harmless shot) | C |
| **pushes** (the Force, a gust, a shockwave) | a right-click blast that shoves | a wide `shotgun()` of short-lived, low-damage, high-`knockbackMultiplier` pellets on right click, or a `firework_launcher()` burst | H (knockback dealt) |
| **throws something recognisable** (trident, hammer, shuriken, boulder) | the thrown thing is drawn, not a dot | a projectile with `proj_rod()` rods or `parts`; spin it; collidable parts where it should hit | C |
| **snares** (web, net, lasso) | a web that flies and catches | `web(hooks=N)` | C |
| **lays, plants, drops** (eggs, mines, seeds, bombs) | things left behind that hatch or burst | `egg()` (rolled hatch time, `projectile: [egg, golden]`), `trap_launcher()`, `burst` + `firesOnDeath` | C |
| **spills, splashes, leaves a puddle** (potion, acid, slime, oil) | a thrown flask that bursts into a puddle that stays and hurts whatever crosses it | a bullet with `burst` onDestroyed + onExpire and 6-10 `firesOnDeath` sub-barrels in a ring firing plain blobs with `speedMultiplier` 0, `initialVelocityMultiplier` [0.15, 0.55] (they slide out and stop), `penetrationMultiplier` 3, lifetime 3-6 s; right click, reload 5-6. Each blob counts twice in the import budget (as a piece of the shot and when it spawns) | C (2026-09-29: the blobs stayed and wore shapes down; 1.5-2.6 s felt too short, 3-6 s asked for) |
| **explodes, scatters, splits** (grenade, firework, cluster) | a shot that bursts into many | `firework_launcher()`, `burst` on death or on right click | C |
| **breathes, sprays** (fire, frost, water, poison) | a short cone of fast, short-lived shots | `shotgun()` or `machine_gun()` with low `lifetime`, spread, matching colours and star or circle pellets | C |
| **fires a beam or laser** | long fast bolts, maybe converging on the cursor | `sniper()`/`hitman()`; lasers on `cursor_pivot`s that converge (the X-Wing) | C |
| **fires a rocket** | a rocket with a thruster, or a shot the player steers | `missile_launcher()` (Skimmer, Rocketeer, Glider); `missile(seeker=False)`; controllable drones steer to the cursor | C |
| **fires a heat-seeking missile** (homes, locks on, chases; a hornet, a guided arrow) | a missile that turns toward the nearest target and runs it down | `missile()` on any gun, or `missile_launcher(thrusters="seeker")`: an auto turret under the bullet with the recoil engine mounted backward on it; `arc=0` to chase (with a short range), otherwise a steering wedge measured from the launch direction (recipes §33) | C (a player's pack) |
| **bursts near the target** (flak, a proximity mine that flies) | a missile that explodes into fragments by itself when something comes close | `missile(warhead=10, proximity=True)`: the warhead is an auto gun on a second, tighter turret with a long reload; `warhead=10` alone bursts on hit, expiry or right click | C (a player's pack) |
| **fires a salvo that fans out** (cluster rockets, a volley of darts, a MIRV) | several missiles at once that split a moment after launch and each burst | `mjrv_launcher()`: drone missiles with sideways recoil splitters; the player holds left click | C (a player's pack) |
| **has companions** (droids, chicks, crew, a twin, a pet) | characters that follow and fight on their own | `figure_drone()` + `summon()` (always out, not a click) | C |
| **commands an army or swarm** (bees, minions, bats, zombies) | many small followers | `swarm_spawner()`, `minion_factory()`, `necromancer()` | C |
| **builds or places** (tower, turret, totem, campfire, flag) | a structure that stays and acts | `sentry()` + `place()` | C |
| **raises a guardian** (golem, scarecrow, robot) | a figure that walks and fights | `walker()`; `wander=False` for a guard that waits and hunts | C |
| **shields, blocks, hides in a shell** | a plate that stops shots | a `collidable` shape (collides with bullets, C) on a `cursor_pivot` so it faces the cursor, or a collidable carapace; a smasher build | C (collision), try (a turret-mounted shield) |
| **vanishes, sneaks, cloaks** | fades when still | `stealth()` | C |
| **rams, stomps, is huge** | the body is the weapon | `smasher()`, body damage caps, a big collidable carapace | C |
| **watches** (an eye, a scanner, a lighthouse) | a part that turns toward danger | `eye()`, a tracking turret | C |
| **has legs, arms, a tail, a cape, hair** | limbs that feel alive | `leg()`, `living_limb()`, `pendulum()` | C |
| **flaps, paddles, pumps, pedals** | parts that pump as it fires or moves | `animate()` (`forceFire` to move without a click) | C |
| **slithers, streaks, leaves a trail** (snake, comet, slime, footprints) | a body or trail that follows its path | `trail()` | C |
| **spins** (saw, drill, wheel, propeller, planet) | a part that turns forever | `spinSpeed` on a shape or the hull | C |
| **glows, sparkles, is magic** | an aura of specks or orbiting motes; or a light that pulses | a sparkler (auto-firing spinning star specks), uncontrolled orbiting drones; for a pulse with no projectiles, `pulse()`: two counter-rotating star shapes on one spot (figurative.md §5) | C; pulse likely |
| **sees far** (sniper, lookout, telescope) | a wider view or a scope | `sniper()` zoom, `scope()` | C |
| **grows up, powers up, transforms** | the story as an upgrade line | a multi-tank line (padawan → knight → master) | C |

**What the format cannot do** (offer the nearest substitute): heal, slow, freeze, stun or
poison over time (no status effects: use colour and a spray); pull toward you; a
projectile that returns to its owner; a chain of joints that bend one after another
(`figurative.md` §5); writing words. Never promise these.

## 3. Worked pitches

These show the *shape* of a good pitch: the moves chosen, then the alternatives. They are not
a list to match against. A subject that is not here (nearly all of them) gets the method of §1,
and one that is here still gets a fresh look at what this user asked for.

**Luke Skywalker** (traits: lightsaber, the Force, the jump, R2-D2, the X-Wing, the pilot's
jacket).
- Lightsaber (left click): a Blue (or Mint, for the green saber) glowing blade on a cursor pivot that swings where you
  aim and cuts along its whole length (`cursor_pivot` + rod + `blade`).
- Force push (right click): a wide, harmless-looking wave that shoves everything back
  (knockback shotgun).
- Force leap (alternative right click): `dash()`.
- R2-D2 (automatic): a little dome droid that follows and zaps shapes (`figure_drone` +
  `summon`).
- Look: a hull in the pilot's colours with a hand holding the hilt.
- Alternatives: the saber also hurts on touch, no click (collidable, an experiment); an
  X-Wing upgrade at the next tier; Obi-Wan as the companion instead of R2-D2.

**Spider-Man**: web shot (`web`, left), web-swing leap (`dash`, right), spider sense (an
`eye` or antenna that turns toward danger), living legs if he is drawn as a spider. Alt: a web
trap left behind (`trap_launcher` drawn as a web).

**A hen**: lays eggs that hatch at random times, one in two golden (`egg`, right click);
followed by two chicks that peck (`figure_drone` + `summon`); pecks within reach (`punch`); a
head on a living limb that bobs toward food; wings that flap when she fires (`animate`).

**Thor**: Mjolnir thrown as a drawn hammer (`proj_rod`/`parts`, left); lightning burst
around him (`firework_launcher`, right); a flowing cape (`pendulum`); a shockwave stomp as an
alternative right click (knockback shotgun). Cannot: the hammer coming back to him (say so,
offer a spinning hammer on a cursor pivot as the melee alternative).

**A pirate ship**: broadside cannons on both sides (`cannon_ring` or `spread`, left); a
cannonball that bursts into grapeshot (`burst`, right); a Jolly Roger flag and sails that
swing on turns (`pendulum`); a wake behind it (`trail`); a crew of little pirates or a parrot
(`figure_drone`). Alt: drop a powder keg that explodes (`trap_launcher` + `burst`).

**A toaster** (an object, played for laughs): pops toast straight up as the shot (a drawn
slice, `parts`); a lever on a pivot that pumps as it fires (`animate`); crumbs as a trail
(`trail`); right click fires a whole burnt loaf that bursts into crumbs (`burst`).

**An ice tank** (a theme, not a subject): frost-breath spray (short `shotgun`, White and Cyan
star pellets), an icicle wall placed on right click (`sentry` with collidable spikes),
spinning snowflake body shapes, a sparkle aura. Cannot: slowing enemies; say so.

## 4. Check before delivering

- Every trait in the list is either built, offered as an alternative, or named as impossible.
- The tank does at least one thing a stock tank cannot, and every input has a job: left
  click, right click, and something automatic.
- A fan would recognise it with the colours turned off, by what it does.
- The recap names each move in plain words and ends with the one or two alternatives not
  built ("Want R2-D2 swapped for a Force leap? Say so").
