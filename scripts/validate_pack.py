#!/usr/bin/env python3
"""Validate a .diep-pack file against references/schema/.

Usage:  python validate_pack.py <file.diep-pack> [--summary] [--cosmetic] [--twin ID=STOCK ...]

Exit status 1 if any ERROR is found; WARNINGs never fail the run. Standard library only.
Every allowlist and rule below is taken from references/schema/; when the spec
changes, change this file to match (section numbers are cited inline).

A tank with editor.replaces N stands in for stock tank N, so each run diffs it against that
stock tank (references/stock-tanks.diep-pack) and prints a NOTE listing what changes play
(barrel angles, offsets, delays, multipliers and width, projectile fields, statsMaxLevel,
speed, zoom, hull size, collidable shapes; "field: stock -> pack"). Decoration passes:
bulletType none barrels, non-collidable shapes, turrets without barrels, projectile parts,
colours, draw order, tree links (upgradesFrom, advancesInto). --cosmetic is for a reskin:
every such difference is an ERROR, and so is a pack with nothing to compare. A reskinned
starter that clones the base Tank has no editor.replaces (Tank cannot be hidden); name its
twin with --twin 100001=Tank (the pack tank id, then a stock name or vanilla id).
"""
import importlib.util
import json
import math
import os
import sys

# --- allowlists (spec §1-§9) ------------------------------------------------------------

PACK_KEYS = {"version", "name", "author", "tanks", "hidden", "shapes", "hiddenShapes", "starters"}
TANK_KEYS = {
    "id", "name", "minLevel", "body", "baseHealth", "baseBodyDamage", "speedMultiplier",
    "zoomMultiplier", "scopeDistance", "knockbackMultiplier", "helpText", "raises",
    "projectiles", "invisibility", "statsMaxLevel", "upgradesFrom", "advancesInto", "editor",
    "barrels", "bodyShapes", "turrets",
}
BODY_KEYS = {"sides", "star", "angle", "size", "color", "spinSpeed"}
INVIS_KEYS = {"enabled", "gain", "lossOnHit", "lossOnAttack", "lossOnMovement", "revealDistance"}
PROJ_KEYS = {"name", "base", "sides", "star", "spin", "spinFlipsOnSecondary", "color", "burst",
             "barrels", "drone", "parts", "turrets"}
DRONE_KEYS = {"idle", "controllable", "keepDistanceMin", "keepDistanceMax", "repel"}
BURST_KEYS = {"onSecondary", "onDestroyed", "onExpire"}
FLAG_KEYS = {"forceFire", "holdsRaised", "firesOnSecondary", "firesOnDeath", "aboveBody"}
BARREL_KEYS = {
    "angle", "offset", "distance", "startDistance", "heightMultiplier", "muzzleScale",
    "bulletType", "projectile", "damageMultiplier", "penetrationMultiplier", "speedMultiplier",
    "initialVelocityMultiplier", "numBullets", "bulletSizeMultiplier", "reloadMultiplier", "delay",
    "spreadMultiplier", "lifetime", "recoilMultiplier", "knockbackMultiplier", "numDrones",
    "droneAggressiveCrashRadius", "preSpawn", "droneControllable", "mountTurret", "mount", "color",
    "order", "flags", "editor", "invisible",
}
SHAPE_KEYS = {"sides", "size", "xOffset", "yOffset", "angle", "spinSpeed", "collidable", "aboveBody",
              "color", "order", "editor", "star", "mountTurret", "mount", "staysVisible"}
TURRET_KEYS = {"xOffset", "yOffset", "angle", "arc", "range", "controllable", "aboveBody", "order", "editor",
               "baseSize", "color"}
TANK_EDITOR_KEYS = {"replaces", "disabled", "advancesInto", "upgradesFrom"}   # the last two: a player-built pack's editor-only tree notes
PART_EDITOR_KEYS = {"name", "group"}
CUSTOM_SHAPE_KEYS = {"id", "name", "sides", "size", "maxHealth", "xpBounty", "damageOnTouch", "knockbackOnTouch",
                     "knockbackMultiplier", "color", "ai", "spawn", "editor"}
CUSTOM_SHAPE_AI_KEYS = {"floatSpeed", "aggressiveCrashSpeed", "aggressiveCrashRadius"}
CUSTOM_SHAPE_SPAWN_KEYS = {"densityMultiplier", "radiusMin", "radiusMax"}
# the shape editor's slider ranges, read off a shape exported with every value maxed and one with
# every value at its minimum (2026-09-29); unlisted minima are 0
SHAPE_EDITOR_MAX = {"sides": 18, "size": 500, "maxHealth": 1e6, "xpBounty": 1e7, "damageOnTouch": 1000,
                    "knockbackOnTouch": 1000, "knockbackMultiplier": 3, "aggressiveCrashSpeed": 1000,
                    "aggressiveCrashRadius": 2000, "densityMultiplier": 1000, "floatSpeed": 1000}
SHAPE_EDITOR_MIN = {"size": 5, "maxHealth": 1, "aggressiveCrashRadius": 1}
CUSTOM_SHAPE_EDITOR_KEYS = {"replaces", "disabled", "spawnWeight"}
SHAPE_DEFAULT_SIZE = 25   # a body shape / part without `size` draws at 25 (spec §8)

BASES = {"bullet", "drone", "trap"}
BULLET_TYPES = {"bullet", "drone", "trap", "none"}
IDLE_MODES = {"hover", "cruise"}   # hover is the default the editor writes
RAISABLE = {"square", "triangle", "pentagon", "big_pentagon", "hexagon", "small_crasher", "big_crasher"}
PALETTE_SIZE = 30  # indices 0-29, spec §10

# Spec §11: vanilla IDs the engine accepts as tree targets. 30, 37 and 59 are gaps,
# 53 (Ball), 56 and 57 are rejected on import. 16/27/45/46/47 (Arena Closer, Mothership, the three
# Dominators) are named here for summaries but are NOT stock to the lobby: the editor's own roster
# has the other 54, and the lobby refused `hidden: [16, ...]` ("hidden id 16 is not a stock tank",
# 2026-09-29), so STOCK_IDS is what a pack may reference.
# 58 and 60-64 are the six newest stock tanks (Auto Tank, Dual-Barrel, Pellet Shot, Shotgun,
# Glider, Firework): found in the human packs, confirmed in game 2026-09-26 by probe children.
VANILLA_NAMES = {
    0: "Tank", 1: "Twin", 2: "Triplet", 3: "Triple Shot", 4: "Quad Tank", 5: "Octo Tank",
    6: "Sniper", 7: "Machine Gun", 8: "Tri-Angle", 9: "Flank Guard", 10: "Destroyer",
    11: "Overseer", 12: "Overlord", 13: "Twin Flank", 14: "Penta Shot", 15: "Assassin",
    16: "Arena Closer", 17: "Necromancer", 18: "Triple Twin", 19: "Hunter", 20: "Gunner",
    21: "Stalker", 22: "Ranger", 23: "Booster", 24: "Fighter", 25: "Hybrid", 26: "Manager",
    27: "Mothership", 28: "Predator", 29: "Sprayer", 31: "Trapper", 32: "Gunner Trapper",
    33: "Overtrapper", 34: "Mega Trapper", 35: "Tri-Trapper", 36: "Smasher", 38: "Landmine",
    39: "Auto Gunner", 40: "Auto 5", 41: "Auto 3", 42: "Spread Shot", 43: "Streamliner",
    44: "Auto Trapper", 45: "Destroyer Dominator", 46: "Gunner Dominator", 47: "Trapper Dominator",
    48: "Battleship", 49: "Annihilator", 50: "Auto Smasher", 51: "Spike", 52: "Factory",
    54: "Skimmer", 55: "Rocketeer", 58: "Auto Tank", 60: "Dual-Barrel", 61: "Pellet Shot",
    62: "Shotgun", 63: "Glider", 64: "Firework",
}
VANILLA_IDS = set(VANILLA_NAMES)
SPECIAL_IDS = {16, 27, 45, 46, 47}
STOCK_IDS = VANILLA_IDS - SPECIAL_IDS      # the editor's stock roster, 54 tanks

# Stock upgrade tree (references/vanilla-tanks.md): child -> parents. Used for the upgrade limit.
VANILLA_PARENTS = {1: (0,), 6: (0,), 7: (0,), 9: (0,), 36: (0,), 58: (0,),
                   3: (1,), 4: (1, 9), 13: (1, 9), 2: (3,), 14: (3,), 42: (3,), 5: (4,), 40: (4, 41),
                   11: (6,), 15: (6,), 19: (6,), 31: (6,), 10: (7,), 20: (7,), 29: (7,), 62: (7,),
                   23: (8,), 24: (8,), 8: (9,), 41: (9,), 25: (10,), 49: (10,), 54: (10,), 55: (10,), 63: (10,),
                   12: (11,), 17: (11,), 26: (11,), 33: (11, 31), 48: (11, 13), 52: (11,), 18: (13,),
                   21: (15,), 22: (15,), 28: (19,), 43: (19, 20), 32: (20, 31), 39: (20, 41),
                   34: (31,), 35: (31,), 44: (31,), 38: (36,), 50: (36,), 51: (36,)}
# "tank 0 offers 20 upgrades, the most is 19" (2026-09-28): Tank's 6 stock children plus two
# imports of a 7-tank pack wired to it; the engine aborts the import.
MAX_UPGRADES = 19

TWO_PI = 2 * math.pi


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def check_keys(rep, where, obj, allowed):
    if not isinstance(obj, dict):
        rep.error(where, f"expected an object, got {type(obj).__name__}")
        return False
    for k in obj:
        if k not in allowed:
            rep.error(where, f"unknown key '{k}' (not in references/schema/)")
    return True


TEAM_SLOTS = {3: "blue", 4: "red", 5: "purple", 6: "green"}


def check_color(rep, where, obj):
    if "color" in obj:
        c = obj["color"]
        if c in TEAM_SLOTS:
            rep.warn(where, f"color {c} is the {TEAM_SLOTS[c]} team slot: in game it shows a team colour and follows "
                            "the player's team after swaps (spec section 10); use 9/24 for red, 2/22 blue, 13/25 green, 26 purple")
        if not is_int(c) or not (0 <= c < PALETTE_SIZE):
            rep.error(where, f"color must be a palette index 0-{PALETTE_SIZE - 1}, got {c!r}")


def check_num_or_range(rep, where, obj, key):
    if key not in obj:
        return
    v = obj[key]
    if is_num(v):
        return
    if isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v):
        return
    rep.error(where, f"{key} must be a number or a [min, max] pair, got {v!r}")


def projectile_indices(v):
    """Return the list of indices a barrel's `projectile` field names (spec §7)."""
    if is_int(v):
        return [v]
    if isinstance(v, list) and v and all(is_int(x) for x in v):
        return list(v)
    return None


def check_barrel(rep, where, b, tank, n_projectiles, siblings, is_sub, sub_base=None, n_turrets=0):
    """Validate one barrel. `siblings` is the array it lives in (for `mount`),
    `is_sub` says whether it sits on a projectile, `sub_base` that projectile's base,
    `n_turrets` how many turrets its owner (tank or projectile) has for `mountTurret`."""
    if not check_keys(rep, where, b, BARREL_KEYS):
        return
    bt = b.get("bulletType")
    if bt not in BULLET_TYPES:
        rep.error(where, f"bulletType must be one of {sorted(BULLET_TYPES)}, got {bt!r}")
    if "projectile" not in b:
        rep.error(where, "projectile is required (int index or list of indices, -1 for none)")
        idx = None
    else:
        idx = projectile_indices(b["projectile"])
        if idx is None:
            rep.error(where, f"projectile must be an int or a non-empty list of ints, got {b['projectile']!r}")
    targets = []
    if idx is not None:
        for i in idx:
            if i == -1:
                if len(idx) > 1:
                    rep.error(where, "-1 cannot appear inside a projectile list")
            elif not (0 <= i < n_projectiles):
                rep.error(where, f"projectile index {i} out of range (tank has {n_projectiles} projectiles)")
            else:
                targets.append(i)
        if bt == "none" and targets:
            rep.error(where, "bulletType 'none' must use projectile -1 (decorative barrel)")
        for i in targets:
            base = tank["projectiles"][i].get("base")
            if bt in BASES and base in BASES and bt != base:
                rep.error(where, f"bulletType '{bt}' but projectiles[{i}].base is '{base}'; "
                                 "the spec (section 7) says keep them equal like every stock tank")
    if bt == "drone":
        if not is_int(b.get("numDrones")):
            rep.error(where, "drone barrels must carry an int numDrones (spec section 7, always written)")
        if "droneAggressiveCrashRadius" not in b:
            rep.warn(where, "drone barrel without droneAggressiveCrashRadius (engine assumes 900; "
                            "the editor always writes it)")
    elif "numDrones" in b or "droneAggressiveCrashRadius" in b or "preSpawn" in b:
        rep.warn(where, f"drone-only fields on a '{bt}' barrel")
    flags = b.get("flags", {})
    if "flags" in b:
        check_keys(rep, where + ".flags", flags, FLAG_KEYS)
        for k, v in flags.items():
            if not isinstance(v, bool):
                rep.error(where + ".flags", f"{k} must be a boolean")
    if flags.get("holdsRaised") and idx != [-1]:
        rep.warn(where, "holdsRaised barrels use projectile -1 in every stock tank (slots hold raised polygons)")
    if "mountTurret" in b:
        mt = b["mountTurret"]
        owner = "projectile" if is_sub else "tank"
        if not is_int(mt) or not (0 <= mt < n_turrets):
            rep.error(where, f"mountTurret {mt!r} out of range (the {owner} has {n_turrets} turrets)")
    if "mount" in b:
        m = b["mount"]
        if not is_int(m) or not (0 <= m < len(siblings)):
            rep.error(where, f"mount {m!r} out of range (array has {len(siblings)} barrels)")
        elif siblings[m] is b:
            rep.error(where, "mount refers to the barrel itself")
    for key in ("angle", "offset", "distance", "startDistance", "heightMultiplier", "muzzleScale",
                "reloadMultiplier", "delay", "spreadMultiplier", "recoilMultiplier",
                "droneAggressiveCrashRadius"):
        if key in b and not is_num(b[key]):
            rep.error(where, f"{key} must be a number, got {b[key]!r}")
    for key in ("numBullets", "numDrones", "preSpawn", "order"):
        if key in b and not is_int(b[key]):
            rep.error(where, f"{key} must be an int, got {b[key]!r}")
    for key in ("droneControllable", "invisible"):
        if key in b and not isinstance(b[key], bool):
            rep.error(where, f"{key} must be a boolean")
    if "editor" in b and isinstance(b["editor"], dict):
        check_keys(rep, where + ".editor", b["editor"], PART_EDITOR_KEYS)
    # [min, max] pairs roll a value per shot (spec section 7; a player-built pack uses ranges on the last
    # three as well: 17 tanks with lifetime ranges, 8 damage, 2 penetration)
    for key in ("speedMultiplier", "initialVelocityMultiplier", "bulletSizeMultiplier",
                "lifetime", "damageMultiplier", "penetrationMultiplier", "knockbackMultiplier"):
        check_num_or_range(rep, where, b, key)
    check_color(rep, where, b)
    if b.get("invisible") and bt == "none":
        rep.warn(where, "an invisible decorative barrel does nothing at all")

    # design warnings
    a = b.get("angle", 0)
    if is_num(a) and abs(a) > TWO_PI:
        rep.warn(where, f"angle {a} is larger than 2*pi; angles are radians, did you write degrees?")
    d = b.get("distance", 95)
    if is_num(d) and d < 20 and bt != "none" and not flags.get("firesOnDeath") and not b.get("invisible") \
            and not flags.get("aboveBody"):
        rep.warn(where, f"distance {d} sinks the barrel into the hull (default 95; 20 is already flush)")
    if is_sub and sub_base == "bullet" and not (flags.get("forceFire") or flags.get("firesOnDeath")) \
            and bt != "none" and "mountTurret" not in b:
        rep.warn(where, "sub-barrel on a bullet-base projectile with neither forceFire nor firesOnDeath "
                        "never fires unless it is on one of the projectile's turrets (spec section 5)")
    if "reloadMultiplier" in b and is_num(b["reloadMultiplier"]) and b["reloadMultiplier"] <= 0:
        rep.error(where, "reloadMultiplier must be positive")


def check_shape(rep, sw, s, n_turrets, n_barrels, what="body shape"):
    """One body shape (tank) or part (projectile): same schema (spec §8)."""
    if not check_keys(rep, sw, s, SHAPE_KEYS):
        return
    if not is_int(s.get("sides")) or s["sides"] < 0:
        rep.error(sw, "sides must be an int >= 0 (always written)")
    if "size" in s and not is_num(s["size"]):
        rep.error(sw, "size (circumradius) must be a number")
    for key in ("xOffset", "yOffset", "angle", "spinSpeed"):
        if key in s and not is_num(s[key]):
            rep.error(sw, f"{key} must be a number")
    for key in ("collidable", "aboveBody", "star", "staysVisible"):
        if key in s and not isinstance(s[key], bool):
            rep.error(sw, f"{key} must be a boolean")
    if "order" in s and not is_int(s["order"]):
        rep.error(sw, "order must be an int")
    if "editor" in s and isinstance(s["editor"], dict):
        check_keys(rep, sw + ".editor", s["editor"], PART_EDITOR_KEYS)
    check_color(rep, sw, s)
    if "mountTurret" in s:
        mt = s["mountTurret"]
        if not is_int(mt) or not (0 <= mt < n_turrets):
            rep.error(sw, f"mountTurret {mt!r} out of range ({n_turrets} turrets)")
    if "mount" in s:
        m = s["mount"]
        if not is_int(m) or not (0 <= m < n_barrels):
            rep.error(sw, f"mount {m!r} out of range ({n_barrels} barrels)")
    if "mountTurret" in s and "mount" in s:
        rep.error(sw, "a part cannot carry both mount and mountTurret")


def check_turret(rep, uw, u):
    if not check_keys(rep, uw, u, TURRET_KEYS):
        return
    for key in ("xOffset", "yOffset", "angle", "arc", "range", "baseSize"):
        if key in u and not is_num(u[key]):
            rep.error(uw, f"{key} must be a number")
    for key in ("controllable", "aboveBody"):
        if key in u and not isinstance(u[key], bool):
            rep.error(uw, f"{key} must be a boolean")
    if "order" in u and not is_int(u["order"]):
        rep.error(uw, "order must be an int")
    if "editor" in u and isinstance(u["editor"], dict):
        check_keys(rep, uw + ".editor", u["editor"], PART_EDITOR_KEYS)
    check_color(rep, uw, u)
    if "mountTurret" in u or "mount" in u:
        rep.error(uw, "turrets cannot be mounted on anything (mountTurret on a turret is ignored)")


def check_tank(rep, ti, t, pack_ids, hidden, shape_ids=()):
    where = f"tanks[{ti}]"
    if not check_keys(rep, where, t, TANK_KEYS):
        return
    name = t.get("name")
    if not isinstance(name, str):
        rep.error(where, "name must be a string")
    else:
        where = f"tanks[{ti}] '{name}'"
    if not is_int(t.get("id")):
        rep.error(where, "id must be an int")
    elif t["id"] < 100000:
        # the lobby refuses it: "tank[0]: id 12 is outside the custom range (>=100000)" (2026-09-29)
        rep.error(where, f"id {t['id']} is outside the custom range (>= 100000): a pack cannot "
                         "overwrite a stock tank; use editor.replaces + hidden for its tree slot")
    ml = t.get("minLevel")
    if not is_int(ml) or ml < 1:
        rep.error(where, f"minLevel must be an int >= 1, got {ml!r}")
    elif ml > 60:
        rep.warn(where, f"minLevel {ml} is above the highest official tier (60); reachable in sandbox only")

    body = t.get("body")
    if body is None:
        rep.error(where, "body is required (at least {\"sides\": 0})")
    elif check_keys(rep, where + ".body", body, BODY_KEYS):
        if not is_int(body.get("sides")) or body["sides"] < 0:
            rep.error(where + ".body", "sides must be an int >= 0 (0 = circle), always written")
        check_color(rep, where + ".body", body)
        if is_num(body.get("spinSpeed", 0)) and abs(body.get("spinSpeed", 0)) > 1:
            rep.warn(where + ".body", f"spinSpeed {body.get('spinSpeed')} rad/tick is very fast (0.0628 = one turn per 4 s)")

    inv = t.get("invisibility")
    if inv is None:
        rep.error(where, "invisibility is required (the editor always writes gain and lossOnHit)")
    elif check_keys(rep, where + ".invisibility", inv, INVIS_KEYS):
        for k in ("gain", "lossOnHit"):
            if not is_num(inv.get(k)):
                rep.error(where + ".invisibility", f"{k} must be present and numeric (always written)")
        if "enabled" in inv and not isinstance(inv["enabled"], bool):
            rep.error(where + ".invisibility", "enabled must be a boolean")

    sml = t.get("statsMaxLevel")
    if not (isinstance(sml, list) and len(sml) == 8 and all(is_int(x) and x >= 0 for x in sml)):
        rep.error(where, f"statsMaxLevel must be exactly 8 ints >= 0, got {sml!r}")

    for key in ("baseHealth", "baseBodyDamage", "speedMultiplier", "zoomMultiplier", "scopeDistance",
                "knockbackMultiplier"):
        if key in t and not is_num(t[key]):
            rep.error(where, f"{key} must be a number")
    if "helpText" in t and not isinstance(t["helpText"], str):
        rep.error(where, "helpText must be a string")

    raises = t.get("raises")
    if raises is not None:
        if not isinstance(raises, list) or not all(isinstance(r, str) for r in raises):
            rep.error(where, "raises must be a list of polygon names")
        else:
            for r in raises:
                if r not in RAISABLE and r not in shape_ids:
                    rep.error(where, f"raises entry {r!r} is not one of {sorted(RAISABLE)} or a custom shape id in this pack")

    # projectiles
    projs = t.get("projectiles", [])
    if not isinstance(projs, list):
        rep.error(where, "projectiles must be a list")
        projs = []
    t["projectiles"] = projs  # so barrel checks can index it
    for pi, p in enumerate(projs):
        pw = f"{where}.projectiles[{pi}]"
        if not check_keys(rep, pw, p, PROJ_KEYS):
            continue
        if not isinstance(p.get("name"), str):
            rep.error(pw, "name must be a string (always written)")
        if p.get("base") not in BASES:
            rep.error(pw, f"base must be one of {sorted(BASES)}, got {p.get('base')!r}")
        if not is_int(p.get("sides")) or p["sides"] < -1:
            rep.error(pw, "sides must be an int >= -1 (-1 = the base's usual shape), always written")
        for key in ("spin",):
            if key in p and not is_num(p[key]):
                rep.error(pw, f"{key} must be a number")
        if is_num(p.get("spin", 0)) and abs(p.get("spin", 0)) > 1:
            rep.warn(pw, f"spin {p['spin']} rad/tick is very fast (stock missiles use 0.1)")
        for key in ("star", "spinFlipsOnSecondary"):
            if key in p and not isinstance(p[key], bool):
                rep.error(pw, f"{key} must be a boolean")
        check_color(rep, pw, p)
        if "burst" in p:
            if check_keys(rep, pw + ".burst", p["burst"], BURST_KEYS):
                for k, v in p["burst"].items():
                    if not isinstance(v, bool):
                        rep.error(pw + ".burst", f"{k} must be a boolean")
                if not any(bb.get("flags", {}).get("firesOnDeath") for bb in p.get("barrels", [])
                           if isinstance(bb, dict)):
                    rep.warn(pw, "burst is set but no sub-barrel has firesOnDeath, so setting it off "
                                 "just ends the projectile with no explosion")
        if "drone" in p:
            if check_keys(rep, pw + ".drone", p["drone"], DRONE_KEYS):
                dr = p["drone"]
                if "idle" in dr and dr["idle"] not in IDLE_MODES:
                    rep.error(pw + ".drone", f"idle must be absent (standard) or one of {sorted(IDLE_MODES)}")
                for k in ("controllable", "repel"):
                    if k in dr and not isinstance(dr[k], bool):
                        rep.error(pw + ".drone", f"{k} must be a boolean")
                for k in ("keepDistanceMin", "keepDistanceMax"):
                    if k in dr and not is_num(dr[k]):
                        rep.error(pw + ".drone", f"{k} must be a number")
            if p.get("base") != "drone":
                rep.warn(pw, "drone settings on a non-drone base are ignored")
        # decoration and turrets carried by the projectile (spec §5b)
        p_turrets = p.get("turrets", [])
        if "turrets" in p:
            if not isinstance(p_turrets, list):
                rep.error(pw, "turrets must be a list")
                p_turrets = []
            for ui, u in enumerate(p_turrets):
                check_turret(rep, f"{pw}.turrets[{ui}]", u)
        subs = p.get("barrels", [])
        if "barrels" in p:
            if not isinstance(subs, list):
                rep.error(pw, "barrels must be a list")
                subs = []
            for bi, b in enumerate(subs):
                check_barrel(rep, f"{pw}.barrels[{bi}]", b, t, len(projs), subs, True, p.get("base"), len(p_turrets))
        parts = p.get("parts", [])
        if "parts" in p:
            if not isinstance(parts, list):
                rep.error(pw, "parts must be a list")
                parts = []
            for si, s in enumerate(parts):
                check_shape(rep, f"{pw}.parts[{si}]", s, len(p_turrets), len(subs), "part")
        if p_turrets:
            mounted = {b.get("mountTurret") for b in subs + parts if isinstance(b, dict) and "mountTurret" in b}
            for ui in range(len(p_turrets)):
                if ui not in mounted:
                    rep.warn(pw, f"turrets[{ui}] has nothing mounted on it; it will be an empty dome on the projectile")

    # barrels
    barrels = t.get("barrels", [])
    if "barrels" in t and not isinstance(barrels, list):
        rep.error(where, "barrels must be a list")
        barrels = []
    turrets = t.get("turrets", [])
    if "turrets" in t and not isinstance(turrets, list):
        rep.error(where, "turrets must be a list")
        turrets = []
    for bi, b in enumerate(barrels):
        check_barrel(rep, f"{where}.barrels[{bi}]", b, t, len(projs), barrels, False, None, len(turrets))

    # body shapes
    shapes = t.get("bodyShapes", [])
    if "bodyShapes" in t and not isinstance(shapes, list):
        rep.error(where, "bodyShapes must be a list")
        shapes = []
    for si, s in enumerate(shapes):
        check_shape(rep, f"{where}.bodyShapes[{si}]", s, len(turrets), len(barrels))

    # turrets
    for ui, u in enumerate(turrets):
        check_turret(rep, f"{where}.turrets[{ui}]", u)
    mounted = {b.get("mountTurret") for b in barrels + shapes if isinstance(b, dict) and "mountTurret" in b}
    for ui in range(len(turrets)):
        if ui not in mounted:
            rep.warn(where, f"turrets[{ui}] has nothing mounted on it (no barrel or shape with mountTurret {ui}); "
                            "it will be a bare disc")

    # tree links
    for key in ("upgradesFrom", "advancesInto"):
        ids = t.get(key)
        if ids is None:
            continue
        if not isinstance(ids, list) or not all(is_int(x) for x in ids):
            rep.error(where, f"{key} must be a list of ints")
            continue
        for x in ids:
            if x not in STOCK_IDS and x not in pack_ids:
                rep.error(where, f"{key} references id {x}, which is neither a known vanilla ID (spec section 11) "
                                 "nor a tank in this pack; the engine aborts the import on unknown ids")
            elif x == t.get("id"):
                rep.error(where, f"{key} references the tank itself")
    if "editor" in t:
        if check_keys(rep, where + ".editor", t["editor"], TANK_EDITOR_KEYS):
            r = t["editor"].get("replaces")
            if r is not None:
                if not is_int(r) or r not in STOCK_IDS:
                    rep.error(where + ".editor", f"replaces must be a known vanilla ID, got {r!r}")
                elif r not in hidden:
                    rep.warn(where + ".editor", f"replaces {r} ({VANILLA_NAMES.get(r)}) without pack hidden [{r}]: "
                                                "both the vanilla tank and this one will show (spec section 1)")
            if "disabled" in t["editor"] and not isinstance(t["editor"]["disabled"], bool):
                rep.error(where + ".editor", "disabled must be a boolean")

    # holistic warnings
    has_raises = bool(raises)
    has_holds = any(isinstance(b, dict) and b.get("flags", {}).get("holdsRaised") for b in barrels)
    if has_raises and not has_holds:
        rep.warn(where, "raises is set but no barrel has flags.holdsRaised; nothing will hold the raised polygons")
    if has_holds and not has_raises:
        rep.warn(where, "a barrel has holdsRaised but the tank has no raises list")
    if not barrels and not shapes and not turrets:
        rep.warn(where, "tank has no barrels, body shapes or turrets: a bare hull")
    # part limits (spec §9c): the editor keeps 32 body shapes, 32 barrels and 8 turrets per tank
    # and drops the rest on import (read from the editor's code, 2026-09-29)
    if len(shapes) > MAX_BODY_SHAPES:
        rep.error(where, f"{len(shapes)} body shapes: the editor keeps only {MAX_BODY_SHAPES} and drops the rest")
    if len(barrels) > MAX_BARRELS:
        rep.error(where, f"{len(barrels)} barrels: the editor keeps only {MAX_BARRELS} and drops the rest")
    if len(turrets) > MAX_TURRETS:
        rep.error(where, f"{len(turrets)} turrets: the editor keeps only {MAX_TURRETS} and drops the rest")
    if len(projs) > MAX_PROJECTILES:
        rep.error(where, f"{len(projs)} projectiles: the editor keeps only {MAX_PROJECTILES} and drops the rest")
    check_import_limits(rep, where, t)
    # the lobby's import budget (spec §7a): the editor's own estimate, which reproduces every refusal
    # message seen word for word; the lobby refuses the first limit a tank passes, in this order
    b = import_budget(t)
    if b["drones"] > LIMIT_DRONES:
        rep.error(where, f"has {b['drones']} drones; a tank may have {LIMIT_DRONES} (spec §7a)")
    if b["pieces"] > LIMIT_PIECES:
        rep.error(where, f"has {b['pieces']} pieces; a tank may have {LIMIT_PIECES} (shapes + barrels + turrets "
                         "on the tank and on every projectile, spec §9c)")
    if b["volley"] > LIMIT_VOLLEY:
        rep.error(where, f"puts {b['volley']} entities out per volley; a tank may put out {LIMIT_VOLLEY} (spec §7a)")
    if b["rate"] > LIMIT_RATE or b["alive"] > LIMIT_ALIVE:
        rep.error(where, f"fires too much: {round(b['rate'])}/{LIMIT_RATE} per second, {round(b['alive'])}/"
                         f"{LIMIT_ALIVE} in the air (spec §7a: lower the Reload stat cap, raise reloads, shorten "
                         "lifetimes, or carry fewer pieces on the shot)")
    if b["load"] > LIMIT_LOAD:
        rep.error(where, f"takes too much room: {round(b['load'])}/{LIMIT_LOAD} bullet-areas in the air "
                         "(spec §7a: shot size counts squared, collidable parts add their own area)")
    used = set()
    for bb in barrels + [sb for p in projs if isinstance(p, dict) for sb in p.get("barrels", []) if isinstance(sb, dict)]:
        if isinstance(bb, dict):
            for i in projectile_indices(bb.get("projectile", -1)) or []:
                used.add(i)
    for pi in range(len(projs)):
        if pi not in used:
            rep.warn(where, f"projectiles[{pi}] is never fired by any barrel")


# --- what the editor does to a pack on import (spec §0, read from its code 2026-09-29) ------------
# The editor reads every pack through one normaliser before it shows or loads it: counts past these
# are dropped, numbers past these are clamped, and what it then sends to the lobby is its own export.
MAX_BODY_SHAPES = 32      # per tank, and parts per projectile
MAX_BARRELS = 32          # per tank, and sub-barrels per projectile
MAX_TURRETS = 8           # per tank, and per projectile
MAX_PROJECTILES = 16
MAX_TANKS = 512
MAX_CUSTOM_SHAPES = 256
MAX_COLLIDABLE_PARTS = 3  # further collidable parts become drawing-only
MAX_PACK_BYTES = 921600   # 900 KB of the exported JSON; the lobby refuses a bigger pack
# (key, max) clamps: the editor keeps min(value, max). Negative values pass unless noted.
TANK_CLAMPS = {"baseHealth": 100000, "baseBodyDamage": 10000, "speedMultiplier": 3, "knockbackMultiplier": 3}
BARREL_CLAMPS = {"heightMultiplier": 2.5, "delay": 10, "reloadMultiplier": 20, "spreadMultiplier": 20,
                 "recoilMultiplier": 20, "damageMultiplier": 20, "penetrationMultiplier": 20,
                 "knockbackMultiplier": 20, "speedMultiplier": 3, "bulletSizeMultiplier": 3,
                 "initialVelocityMultiplier": 3, "lifetime": 30, "numBullets": 10, "numDrones": 24,
                 "droneAggressiveCrashRadius": 2000}
BARREL_SYMMETRIC = {"offset": 500, "distance": 500, "startDistance": 500}   # clamped to [-max, max]


def _clamped(rep, where, obj, key, top, low=None):
    v = obj.get(key)
    vals = v if isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v) else [v]
    for x in vals:
        if is_num(x) and (x > top or (low is not None and x < low)):
            rng = f"{low:g} to {top:g}" if low is not None else f"at most {top:g}"
            rep.warn(where, f"{key} {x:g} is outside what the editor keeps ({rng}); it is clamped on import")
            return


def check_import_limits(rep, where, t):
    """Warn wherever the editor would change the tank on import (spec §0 "Import")."""
    ml = t.get("minLevel")
    if is_int(ml) and ml > 120:
        rep.warn(where, f"minLevel {ml} is clamped to 120 on import")
    for k, top in TANK_CLAMPS.items():
        _clamped(rep, where, t, k, top)
    _clamped(rep, where, t, "zoomMultiplier", 5, 0.5)
    _clamped(rep, where, t, "scopeDistance", 3000, 0)
    if isinstance(t.get("helpText"), str) and len(t["helpText"]) > 80:
        rep.warn(where, f"helpText is {len(t['helpText'])} characters; the editor keeps the first 80")
    sml = t.get("statsMaxLevel")
    if isinstance(sml, list) and any(is_num(x) and x > 12 for x in sml):
        rep.warn(where, f"statsMaxLevel {sml}: the editor clamps each cap to 0-12")
    body = t.get("body") if isinstance(t.get("body"), dict) else {}
    _clamped(rep, where + ".body", body, "size", 67)
    _clamped(rep, where + ".body", body, "sides", 18)
    _clamped(rep, where + ".body", body, "spinSpeed", 0.5, -0.5)
    inv = t.get("invisibility") if isinstance(t.get("invisibility"), dict) else {}
    _clamped(rep, where + ".invisibility", inv, "revealDistance", 3000)
    projs = [p if isinstance(p, dict) else {} for p in (t.get("projectiles") or [])]

    def has_pieces(p):
        return bool(p.get("barrels") or p.get("parts") or p.get("turrets"))

    def barrel_limits(bw, b, sub_of=None):
        for k, top in BARREL_CLAMPS.items():
            _clamped(rep, bw, b, k, top)
        for k, top in BARREL_SYMMETRIC.items():
            _clamped(rep, bw, b, k, top, -top)
        idx = projectile_indices(b.get("projectile", -1)) or []
        ok = [i for i in idx if 0 <= i < len(projs)]
        if len(ok) > 1:
            base = projs[ok[0]].get("base")
            odd = [i for i in ok[1:] if projs[i].get("base") != base]
            if odd:
                rep.warn(bw, f"projectile alternatives {odd} have a different base from projectiles[{ok[0]}]; "
                             "the editor drops them")
        if sub_of is not None:
            flags = b.get("flags") or {}
            if flags.get("holdsRaised") or b.get("preSpawn"):
                rep.warn(bw, "holdsRaised and preSpawn are dropped from a projectile's barrels")
            bad = [i for i in ok if i == sub_of or has_pieces(projs[i])]
            if bad:
                rep.warn(bw, f"fires projectiles {bad}, but a projectile's barrel may only fire a projectile with no "
                             "barrels, parts or turrets of its own, and never its own: on import the editor swaps in "
                             "a plain default shot of the barrel's type, so those parts, guns and colour are lost "
                             "(spec §5b)")

    def shape_limits(sw, lst):
        n = 0
        for si, s in enumerate(lst or []):
            if not isinstance(s, dict):
                continue
            w = f"{sw}[{si}]"
            _clamped(rep, w, s, "sides", 18)
            _clamped(rep, w, s, "xOffset", 800, -800)
            _clamped(rep, w, s, "yOffset", 800, -800)
            if s.get("collidable"):
                n += 1
                if n == MAX_COLLIDABLE_PARTS + 1:
                    rep.warn(sw, f"more than {MAX_COLLIDABLE_PARTS} collidable parts: the editor turns every one "
                                 "after the third into a drawing-only part")
            _clamped(rep, w, s, "size", 150 if s.get("collidable") and n <= MAX_COLLIDABLE_PARTS else 300)

    for bi, b in enumerate(t.get("barrels") or []):
        if isinstance(b, dict):
            barrel_limits(f"{where}.barrels[{bi}]", b)
    shape_limits(f"{where}.bodyShapes", t.get("bodyShapes"))
    for pi, p in enumerate(projs):
        pw = f"{where}.projectiles[{pi}]"
        _clamped(rep, pw, p, "sides", 18)
        _clamped(rep, pw, p, "spin", 0.5, -0.5)
        dr = p.get("drone") if isinstance(p.get("drone"), dict) else {}
        for k in ("keepDistanceMin", "keepDistanceMax"):
            _clamped(rep, pw + ".drone", dr, k, 2000)
        for key, top in (("barrels", MAX_BARRELS), ("parts", MAX_BODY_SHAPES), ("turrets", MAX_TURRETS)):
            if isinstance(p.get(key), list) and len(p[key]) > top:
                rep.error(pw, f"{len(p[key])} {key}: the editor keeps only {top} per projectile")
        for bi, b in enumerate(p.get("barrels") or []):
            if isinstance(b, dict):
                barrel_limits(f"{pw}.barrels[{bi}]", b, sub_of=pi)
        shape_limits(pw + ".parts", p.get("parts"))


# --- the lobby's import budget (spec §7a) ------------------------------------------------------
# A port of the editor's own estimate (read from its code 2026-09-29). It reproduces all four
# refusal messages on record exactly (croc 196/120 and 71/250, then 121/120 and 66/250; Web Lab
# 84/120 and 437/250; Builder Lab 132/120 and 112/250), and the largest player-built tanks sit at
# 119.9/s, 250 in the air, 64 per volley and 96 pieces or drones. The whole tank is counted with the
# Reload stat at its cap and every trigger held, left and right click alike.
LIMIT_RATE = 120          # shots per second, counting what each shot carries
LIMIT_ALIVE = 250         # of those, alive at once
LIMIT_LOAD = 2000         # "room": collider area of everything alive, a standard bullet = 1
LIMIT_DRONES = 96
LIMIT_VOLLEY = 64         # entities one pull of every trigger puts out
LIMIT_PIECES = 96         # shapes + barrels + turrets on the tank and on every projectile
RELOAD_STAT_INDEX = 1


def _num(v, top, default):
    return min(v, top) if is_num(v) else default


def _range_lo(v):
    if isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v):
        return min(v)
    return v


def _range_hi(v, top):
    if not (isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v)):
        return None
    m = min(max(v), top)
    return m if m > min(v) else None


def _editor_barrel(b):
    """A barrel as the editor holds it after import: the fields the budget reads."""
    f = b.get("flags") or {}
    hm = _num(b.get("heightMultiplier"), 2.5, 1)
    ms = b.get("muzzleScale")
    muzzle = ms if is_num(ms) and ms > 0 else 1.75 if f.get("largeRectSide") else 0.75 if f.get("smallRectSide") else 1
    turned = abs(b.get("addFinalAngle") or 0) > 1.5     # legacy stock data: muzzle and base swap
    width = _num(hm * muzzle, 2.5, 1) if turned else hm
    k = hm / width if turned and width > 0 else 1
    bs = _range_lo(b.get("bulletSizeMultiplier"))
    bt = b.get("bulletType") if isinstance(b.get("bulletType"), str) else "bullet"
    life, btl = _range_lo(b.get("lifetime")), b.get("bulletTimeLeftMultiplier")
    if is_num(life) and life >= 0:
        lifetime = min(life, 30)
    elif is_num(btl) and btl != 1 and bt != "drone":
        lifetime = min(3 * btl, 30)
    else:
        lifetime = -1
    idx = projectile_indices(b.get("projectile", -1)) or [-1]
    prim = idx[0] if idx[0] >= 0 else -1
    alts = []
    for x in idx[1:]:
        if x >= 0 and x != prim and x not in alts:
            alts.append(x)
    mount = b.get("mount") if is_int(b.get("mount")) and b["mount"] >= 0 else -1
    mt = b.get("mountTurret")
    nb, nd = b.get("numBullets"), b.get("numDrones")
    return {
        "bulletType": bt, "width": width,
        "size": _num((bs if is_num(bs) else 1) * k, 3, 1), "sizeMax": _range_hi(b.get("bulletSizeMultiplier"), 3),
        "bullets": min(round(nb), 10) if is_num(nb) and nb >= 1 else 1,
        "reload": _num(b.get("reloadMultiplier"), 20, 1),
        "lifetime": lifetime, "lifetimeMax": _range_hi(b.get("lifetime"), 30),
        "numDrones": min(nd, 24) if is_num(nd) and nd >= 0 else 24,
        "mount": mount, "mountTurret": mt if is_int(mt) and mt >= 0 and mount < 0 else -1,
        "forceFire": bool(f.get("forceFire")), "firesOnDeath": bool(f.get("firesOnDeath")),
        "projectile": prim, "alts": alts[:16],
    }


def _editor_parts(lst):
    out, n = [], 0
    for s in (lst or [])[:MAX_BODY_SHAPES]:
        s = s if isinstance(s, dict) else {}
        col = bool(s.get("collidable"))
        if col:
            n += 1
            col = n <= MAX_COLLIDABLE_PARTS
        out.append({"collidable": col, "size": min(_num(s.get("size"), 300, 25), 150 if col else 300)})
    return out


def _editor_projectile(p):
    p = p if isinstance(p, dict) else {}
    sides, burst = p.get("sides"), p.get("burst") or {}
    return {
        "base": p.get("base") if p.get("base") in BASES else "bullet",
        "sides": min(round(sides), 18) if is_num(sides) and sides >= 0 else -1,
        "burst": bool(burst.get("onSecondary") or burst.get("onDestroyed") or burst.get("onExpire")),
        "barrels": [_editor_barrel(x) for x in (p.get("barrels") or [])[:MAX_BARRELS] if isinstance(x, dict)],
        "parts": _editor_parts(p.get("parts")),
        "turrets": (p.get("turrets") or [])[:MAX_TURRETS],
    }


def import_budget(t):
    """The editor's estimate of what the lobby checks (spec §7a): rate, alive, load, drones, volley, pieces."""
    projs = [_editor_projectile(p) for p in (t.get("projectiles") or [])[:MAX_PROJECTILES]]
    bars = [_editor_barrel(b) for b in (t.get("barrels") or [])[:MAX_BARRELS] if isinstance(b, dict)]
    for b in bars:            # an out-of-range projectile fires nothing; alternatives share the primary's base
        if b["projectile"] >= len(projs):
            b["projectile"], b["alts"] = -1, []
        elif b["projectile"] >= 0:
            base = projs[b["projectile"]]["base"]
            b["alts"] = [a for a in b["alts"] if a < len(projs) and projs[a]["base"] == base]
        else:
            b["alts"] = []

    def pieces(q):
        return len(q["parts"]) + len(q["barrels"]) + len(q["turrets"])

    for i, q in enumerate(projs):   # a projectile's barrel fires only piece-less projectiles, never its own
        def bad(x):
            return x >= len(projs) or x == i or pieces(projs[x]) > 0
        for b in q["barrels"]:
            if b["projectile"] >= 0 and bad(b["projectile"]):
                b["projectile"], b["alts"] = -1, []
            else:
                b["alts"] = [a for a in b["alts"] if not bad(a)]
    caps = t.get("statsMaxLevel")
    cap = caps[RELOAD_STAT_INDEX] if isinstance(caps, list) and len(caps) == 8 else 7
    cap = max(0, min(12, round(cap))) if is_num(cap) else 7
    period = 15 * 0.914 ** cap          # ticks per shot at reload 1 with Reload maxed

    def shots(b, n):                    # per second, 25 ticks a second, whole ticks only
        return 25 * n / max(1, math.ceil(period * b["reload"]))

    def life(b):                        # seconds; an unset lifetime counts 3 s whatever the base
        return max(b["lifetime"], b["lifetimeMax"] or 0) if b["lifetime"] >= 0 else 3.0

    def area(b, q):                     # a standard bullet is 1; size counts squared
        d = (21 if b["bulletType"] == "bullet" and (q["sides"] if q else -1) < 3 else 42 * 0.70710678) \
            * b["width"] * max(b["size"], b["sizeMax"] or 0)
        a = (d / 21) ** 2
        for s in (q["parts"] if q else []):
            if s["collidable"]:
                a += (s["size"] * d / 50 / 21) ** 2
        return a

    def on_turret(siblings, b):
        if b["mount"] >= 0:
            par = siblings[b["mount"]] if b["mount"] < len(siblings) else None
            return bool(par) and par["mount"] < 0 and par["mountTurret"] >= 0
        return b["mountTurret"] >= 0

    def count(b, mult, depth):
        best = dict(rate=0.0, alive=0.0, drones=0.0, load=0.0)
        if b["bulletType"] == "none" or mult <= 0 or depth > 8:
            return best
        options = [projs[i] for i in [b["projectile"], *b["alts"]]] if b["projectile"] >= 0 else []
        for q in options or [None]:     # a random pick counts at its costliest option
            c = dict(rate=0.0, alive=0.0, drones=0.0, load=0.0)
            direct = 0.0
            if b["bulletType"] == "drone":
                live = mult * b["numDrones"]
                c["drones"] += live
                c["load"] += live * area(b, q)
            else:
                r = mult * shots(b, b["bullets"] * (1 + (pieces(q) if q else 0)))
                c["rate"] += r
                c["alive"] += r * life(b)
                direct = mult * shots(b, b["bullets"])
                live = direct * life(b)
                c["load"] += live * area(b, q)
            for s in (q["barrels"] if q else []):
                if s["bulletType"] == "none":
                    continue
                if s["firesOnDeath"]:           # once per shot, and only if the projectile can burst
                    if direct and q["burst"]:
                        n = direct * s["bullets"]
                        sq = projs[s["projectile"]] if s["projectile"] >= 0 else None
                        c["rate"] += n
                        c["alive"] += n * life(s)
                        c["load"] += n * life(s) * area(s, sq)
                    continue
                if b["bulletType"] != "drone" and not s["forceFire"] and not on_turret(q["barrels"], s):
                    continue                    # never fires (spec §5)
                sub = count(s, live, depth + 1)  # every live copy fires it
                for k in c:
                    c[k] += sub[k]
            for k in best:
                best[k] = max(best[k], c[k])
        return best

    tot = dict(rate=0.0, alive=0.0, drones=0.0, load=0.0)
    for b in bars:
        if b["mount"] < 0 or b["forceFire"] or on_turret(bars, b):
            c = count(b, 1, 0)
            for k in tot:
                tot[k] += c[k]
    volley = 0
    for b in bars:
        if b["bulletType"] != "none":
            opts = [projs[i] for i in [b["projectile"], *b["alts"]]] if b["projectile"] >= 0 else []
            volley += b["bullets"] * (1 + max((pieces(q) for q in opts), default=0))
    for q in projs:
        volley += sum(s["bullets"] for s in q["barrels"] if s["bulletType"] != "none")
    n_pieces = (len(_editor_parts(t.get("bodyShapes"))) + len(bars) + len((t.get("turrets") or [])[:MAX_TURRETS])
                + sum(pieces(q) for q in projs))
    return {"rate": tot["rate"], "alive": tot["alive"], "load": tot["load"],
            "drones": math.ceil(tot["drones"] - 1e-9), "volley": volley, "pieces": n_pieces}


HEX_COLOUR = "^#[0-9a-fA-F]{6}$"


def check_custom_shape(rep, sw, s):
    """A pack-level custom polygon (spec §1a): an arena shape, not a tank part."""
    import re
    if not check_keys(rep, sw, s, CUSTOM_SHAPE_KEYS):
        return
    sid = s.get("id")
    if not isinstance(sid, str) or not re.match(r"^custom_shape_\d+$", sid):
        rep.error(sw, f"id must be a string of the form custom_shape_N, got {sid!r}")
    if not isinstance(s.get("name"), str):
        rep.error(sw, "name must be a string")
    if not is_int(s.get("sides")) or s["sides"] < 0:
        rep.error(sw, "sides must be an int >= 0 (0 = circle)")
    for k in ("size", "maxHealth", "xpBounty", "damageOnTouch", "knockbackOnTouch", "knockbackMultiplier"):
        if k in s and not is_num(s[k]):
            rep.error(sw, f"{k} must be a number")
    for path, v, top in (("sides", s.get("sides"), SHAPE_EDITOR_MAX["sides"]),
                         *((k, s.get(k), SHAPE_EDITOR_MAX[k]) for k in ("size", "maxHealth", "xpBounty",
                           "damageOnTouch", "knockbackOnTouch", "knockbackMultiplier")),
                         *(("ai." + k, (s.get("ai") or {}).get(k), SHAPE_EDITOR_MAX[k])
                           for k in ("floatSpeed", "aggressiveCrashSpeed", "aggressiveCrashRadius")),
                         ("spawn.densityMultiplier", (s.get("spawn") or {}).get("densityMultiplier"),
                          SHAPE_EDITOR_MAX["densityMultiplier"])):
        low = SHAPE_EDITOR_MIN.get(path.split(".")[-1], 0)
        if is_num(v) and not low <= v <= top:
            rep.warn(sw, f"{path} {v} is outside the shape editor's {low:g}-{top:g} range")
    for k, dflt in (("size", 50), ("maxHealth", 10)):
        if k not in s:
            rep.warn(sw, f"{k} is omitted: the editor fills in {dflt} on import (spec §1a); write it to be explicit")
    c = s.get("color")
    if c is not None and not (isinstance(c, str) and re.match(HEX_COLOUR, c)):
        rep.error(sw, f"custom shape color is a hex string like #FFE869 (not a palette index), got {c!r}")
    if "ai" in s and check_keys(rep, sw + ".ai", s["ai"], CUSTOM_SHAPE_AI_KEYS):
        for k, v in s["ai"].items():
            if not is_num(v):
                rep.error(sw + ".ai", f"{k} must be a number")
    ai = s.get("ai") if isinstance(s.get("ai"), dict) else {}
    if is_num(ai.get("aggressiveCrashSpeed")) and ai["aggressiveCrashSpeed"] > 0             and not (is_num(ai.get("aggressiveCrashRadius")) and ai["aggressiveCrashRadius"] > 0):
        rep.warn(sw + ".ai", "aggressiveCrashSpeed without an aggressiveCrashRadius above 0: not a crasher "
                             "(the radius switches chasing on), so it only drifts")
    if "spawn" in s and check_keys(rep, sw + ".spawn", s["spawn"], CUSTOM_SHAPE_SPAWN_KEYS):
        for k, v in s["spawn"].items():
            if not is_num(v):
                rep.error(sw + ".spawn", f"{k} must be a number")
            elif k in ("radiusMin", "radiusMax") and not 0 <= v <= 1:
                rep.warn(sw + ".spawn", f"{k} {v} is outside 0-1 (0 = centre, 1 = edge)")
        sp = s["spawn"]
        if is_num(sp.get("radiusMin")) and is_num(sp.get("radiusMax")) and sp["radiusMin"] >= sp["radiusMax"]:
            rep.warn(sw + ".spawn", f"radiusMin {sp['radiusMin']} is not below radiusMax {sp['radiusMax']}: an empty spawn band")
    if "editor" in s and check_keys(rep, sw + ".editor", s["editor"], CUSTOM_SHAPE_EDITOR_KEYS):
        e = s["editor"]
        if "replaces" in e and e["replaces"] not in RAISABLE:
            rep.error(sw + ".editor", f"replaces must name a vanilla shape {sorted(RAISABLE)}, got {e['replaces']!r}")
        if "disabled" in e and not isinstance(e["disabled"], bool):
            rep.error(sw + ".editor", "disabled must be a boolean")
        if "spawnWeight" in e and not is_num(e["spawnWeight"]):
            rep.error(sw + ".editor", "spawnWeight must be a number")


def validate(pack):
    rep = Report()
    if not check_keys(rep, "pack", pack, PACK_KEYS):
        return rep
    if pack.get("version") != 2:
        rep.error("pack", f"version must be 2, got {pack.get('version')!r}")
    if not isinstance(pack.get("name"), str):
        rep.error("pack", "name must be a string")
    if "author" in pack and not isinstance(pack.get("author"), str):
        rep.error("pack", "author must be a string when present (one user pack omits it)")
    # the shape editor exports an arena-only pack (shapes, no tanks key), so tanks are optional there
    tanks = pack.get("tanks", [])
    if not isinstance(tanks, list):
        rep.error("pack", "tanks must be a list")
        return rep
    if not tanks and not (pack.get("shapes") or pack.get("hiddenShapes")):
        rep.error("pack", "a pack needs tanks, or custom shapes for an arena-only pack")
        return rep
    if not tanks:
        rep.warn("pack", "no tanks: an arena-only pack imports only with 'Add to this pack'; "
                         "'Import as new pack' refuses it (\"A pack needs a tank\", editor code)")
    # custom arena shapes (spec §1a)
    shape_ids = set()
    shapes = pack.get("shapes", [])
    if "shapes" in pack:
        if not isinstance(shapes, list):
            rep.error("pack", "shapes must be a list")
            shapes = []
        for si, s in enumerate(shapes):
            check_custom_shape(rep, f"shapes[{si}]", s)
            if isinstance(s, dict) and isinstance(s.get("id"), str):
                if s["id"] in shape_ids:
                    rep.error("pack", f"duplicate custom shape id {s['id']}")
                shape_ids.add(s["id"])
    if "hiddenShapes" in pack:
        hs = pack["hiddenShapes"]
        if not isinstance(hs, list) or not all(isinstance(x, str) for x in hs):
            rep.error("pack", "hiddenShapes must be a list of vanilla shape names")
        else:
            for x in hs:
                if x not in RAISABLE:
                    rep.error("pack", f"hiddenShapes entry {x!r} is not a vanilla shape name {sorted(RAISABLE)}")
    hidden = pack.get("hidden", [])
    if "hidden" in pack:
        if not isinstance(hidden, list) or not all(is_int(x) for x in hidden):
            rep.error("pack", "hidden must be a list of ints")
            hidden = []
        else:
            for h in hidden:
                if h == 0:
                    rep.error("pack", "hidden id 0 (Tank): the lobby refuses it (\"the base tank cannot be hidden\", "
                                      "2026-09-29); a total conversion hides the other 53 and names its own tanks "
                                      "in starters")
                elif h in SPECIAL_IDS:
                    rep.error("pack", f"hidden id {h} ({VANILLA_NAMES[h]}) is not a stock tank: the lobby refuses it")
                elif h not in STOCK_IDS:
                    rep.error("pack", f"hidden id {h} is not a known vanilla ID")
            # hidden works alone (spec 1, Confirmed 2026-09-26: a total conversion left only its own tanks)
    pack_ids = [t.get("id") for t in tanks if isinstance(t, dict)]
    if "starters" in pack:
        st = pack["starters"]
        if not isinstance(st, list) or not all(is_int(x) for x in st):
            rep.error("pack", "starters must be a list of tank ids")
        else:
            for x in st:
                if x not in STOCK_IDS and x not in pack_ids:
                    rep.error("pack", f"starters id {x} is neither a vanilla ID nor a tank in this pack")
            if not st:
                rep.warn("pack", "starters is empty: nothing to spawn as")
    seen = set()
    for i in pack_ids:
        if i in seen:
            rep.error("pack", f"duplicate tank id {i}")
        seen.add(i)
    if len(tanks) > MAX_TANKS:
        rep.error("pack", f"{len(tanks)} tanks: the editor keeps only {MAX_TANKS} and drops the rest")
    if len(shapes) > MAX_CUSTOM_SHAPES:
        rep.error("pack", f"{len(shapes)} custom shapes: the editor keeps only {MAX_CUSTOM_SHAPES} and drops the rest")
    size = len(json.dumps(pack, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    if size > MAX_PACK_BYTES:
        rep.error("pack", f"the pack is {round(size / 1024)} KB; the lobby takes {MAX_PACK_BYTES // 1024} KB "
                          "(spec §0): split it or trim barrels and parts")
    for ti, t in enumerate(tanks):
        check_tank(rep, ti, t, set(pack_ids), set(hidden), shape_ids)
    check_upgrade_counts(rep, tanks, set(hidden) if isinstance(hidden, list) else set())
    return rep


def check_upgrade_counts(rep, tanks, hidden):
    """Each tank may offer at most MAX_UPGRADES upgrades, stock children included (engine
    message "tank 0 offers 20 upgrades, the most is 19"). Hidden stock children are assumed
    not to count (untested). "Add to this pack" appends copies, so re-importing a pack into
    itself stacks its children: the validator cannot see that, the recap must warn."""
    children = {}
    for child, parents in VANILLA_PARENTS.items():
        if child in hidden:
            continue
        for p in parents:
            children.setdefault(p, set()).add(("vanilla", child))
    for t in tanks:
        if not isinstance(t, dict):
            continue
        for p in t.get("upgradesFrom") or []:
            if is_int(p):
                children.setdefault(p, set()).add(("pack", t.get("id")))
        for c in t.get("advancesInto") or []:
            if is_int(c):
                children.setdefault(t.get("id"), set()).add(("pack", c) if c >= 100000 else ("vanilla", c))
    names = {t.get("id"): t.get("name") for t in tanks if isinstance(t, dict)}
    for p, kids in sorted(children.items(), key=lambda kv: str(kv[0])):
        own = sum(1 for k in kids if k[0] == "pack")
        if not own:
            continue
        label = VANILLA_NAMES.get(p) if p in VANILLA_NAMES and p not in names else names.get(p, p)
        if len(kids) > MAX_UPGRADES:
            rep.error("pack", f"tank {p} ({label}) offers {len(kids)} upgrades ({len(kids) - own} stock, {own} "
                              f"from this pack); the engine refuses more than {MAX_UPGRADES}")
        elif len(kids) > MAX_UPGRADES - own:
            rep.warn("pack", f"tank {p} ({label}) offers {len(kids)} upgrades ({len(kids) - own} stock, {own} from "
                             f"this pack): adding this pack to one that already holds it would pass the engine's "
                             f"limit of {MAX_UPGRADES}; import revised versions as a new pack")


# --- cosmetic check: a stand-in tank against its stock twin -----------------------------------
# Fields that only change the picture. Anything else a stock tank carries is play: barrel
# angles, offsets, delays, multipliers and width (a bullet's radius is 21 x heightMultiplier x
# bulletSizeMultiplier, spec 4), projectile fields, statsMaxLevel, speed, zoom, hull size, and
# any shape with `collidable` (a non-collidable part is picture only, spec 5).

COSMETIC_TANK = {"id", "name", "upgradesFrom", "advancesInto", "editor", "helpText"}   # tree links and labels
TANK_PARTS = {"body", "projectiles", "barrels", "bodyShapes", "turrets"}
COSMETIC_BARREL = {"color", "editor", "order", "muzzleScale", "invisible"}
COSMETIC_SHAPE = {"color", "editor", "order", "aboveBody", "staysVisible"}
COSMETIC_TURRET = {"color", "editor", "order", "baseSize", "aboveBody"}
COSMETIC_BODY = {"color"}
COSMETIC_PROJECTILE = {"name", "parts"}


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool) or not (is_num(a) and is_num(b)):
        return a == b
    return math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-4)


def _diff(a, b, path=""):
    """Lines for every field that differs between two JSON values, numbers within 1e-4."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            sub = f"{path}.{k}" if path else k
            if k not in a:
                out.append(f"{sub}: absent -> {json.dumps(b[k])}")
            elif k not in b:
                out.append(f"{sub}: {json.dumps(a[k])} -> absent")
            else:
                out += _diff(a[k], b[k], sub)
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and any(isinstance(x, (dict, list)) for x in a):
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in _diff(p, q, f"{path}[{i}]")]
    if isinstance(a, list) and isinstance(b, list):
        return [] if len(a) == len(b) and all(_same(p, q) for p, q in zip(a, b)) else [f"{path}: {json.dumps(a)} -> {json.dumps(b)}"]
    return [] if _same(a, b) else [f"{path}: {json.dumps(a)} -> {json.dumps(b)}"]


def _norm_barrel(b):
    b = {k: v for k, v in b.items() if k not in COSMETIC_BARREL}
    flags = {k: v for k, v in (b.get("flags") or {}).items() if k != "aboveBody"}
    b.pop("flags", None)
    if flags:
        b["flags"] = flags
    return b


def _norm_turret(u):
    return {k: v for k, v in u.items() if k not in COSMETIC_TURRET}


def _norm_projectile(p):
    q = {k: v for k, v in p.items() if k not in COSMETIC_PROJECTILE}
    if "barrels" in q:
        q["barrels"] = [_norm_barrel(b) for b in q["barrels"]]
    if "turrets" in q:
        q["turrets"] = [_norm_turret(u) for u in q["turrets"]]
    solid = [_norm_shape(s) for s in p.get("parts") or [] if s.get("collidable")]
    if solid:
        q["collidable parts"] = solid
    return q


def _norm_shape(s):
    return {k: v for k, v in s.items() if k not in COSMETIC_SHAPE}


def _pair_off(stock, twin, what, describe):
    """Exact matches cancel; what is left pairs in order and diffs, then extras and gaps."""
    left = list(twin)
    rest = []
    for s in stock:
        hit = next((i for i, t in enumerate(left) if not _diff(s, t)), None)
        if hit is None:
            rest.append(s)
        else:
            left.pop(hit)
    out = []
    for i, s in enumerate(rest):
        if i < len(left):
            out += [f"{what} {describe(s)}: {d}" for d in _diff(s, left[i])]
        else:
            out.append(f"{what} {describe(s)} removed")
    out += [f"{what} added that plays: {describe(t)}" for t in left[len(rest):]]
    return out


def _describe_barrel(b):
    return f"{b.get('bulletType')} @ angle {b.get('angle', 0):.3g} offset {b.get('offset', 0):.3g}"


def _describe_shape(s):
    return f"{s.get('sides')}-gon r{s.get('size', 25):g} at ({s.get('xOffset', 0):g}, {s.get('yOffset', 0):g})"


def play_changes(tank, stock):
    """Every difference between a tank and its stock twin that changes play, as short lines;
    [] when the tank only adds decoration (bulletType none barrels, non-collidable shapes,
    turrets without barrels, projectile parts) or changes colours, draw order, names and the
    like. Both are tank dicts as the pack writes them."""
    out = []
    own = {k: v for k, v in tank.items() if k not in COSMETIC_TANK | TANK_PARTS}
    base = {k: v for k, v in stock.items() if k not in COSMETIC_TANK | TANK_PARTS}
    out += _diff(base, own)
    out += [f"body.{d}" for d in _diff({k: v for k, v in stock.get("body", {}).items() if k not in COSMETIC_BODY},
                                       {k: v for k, v in tank.get("body", {}).items() if k not in COSMETIC_BODY})]
    sb = [_norm_barrel(b) for b in stock.get("barrels") or []]
    tb = [_norm_barrel(b) for b in tank.get("barrels") or [] if b.get("bulletType") != "none" or
          any(_diff(_norm_barrel(b), x) == [] for x in sb)]
    out += _pair_off(sb, tb, "barrel", _describe_barrel)
    solid = lambda lst: [_norm_shape(s) for s in lst or [] if s.get("collidable")]
    out += _pair_off(solid(stock.get("bodyShapes")), solid(tank.get("bodyShapes")), "collidable shape", _describe_shape)
    su = [_norm_turret(u) for u in stock.get("turrets") or []]
    tu = [_norm_turret(u) for u in tank.get("turrets") or []]
    for i, s in enumerate(su):
        out += [f"turret {i}: {d}" for d in (_diff(s, tu[i]) if i < len(tu) else ["removed"])]
    sp = [_norm_projectile(p) for p in stock.get("projectiles") or []]
    tp = [_norm_projectile(p) for p in tank.get("projectiles") or []]
    for i, s in enumerate(sp):
        out += [f"projectile {i}: {d}" for d in (_diff(s, tp[i]) if i < len(tp) else ["removed"])]
    return out


def _load_ref():
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("ref", os.path.join(here, "ref.py"))
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    return ref


def _stock_id(query):
    vid = _load_ref().stock_tank(query)[0]
    if vid is None:
        raise ValueError(f"{query!r} has no vanilla id")
    return vid


def stock_twins(pack, twins=None):
    """[(label, tank, stock tank, differences)] for every tank with editor.replaces naming a
    stock tank in references/stock-tanks.diep-pack, or [] when that roster is absent. `twins`
    {pack tank id: vanilla id} adds tanks that cannot carry replaces: a clone of the base Tank
    (0), which cannot be hidden, so a reskinned starter has no replaces to read."""
    try:
        roster = _load_ref().stock_by_vanilla_id()
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for i, t in enumerate(pack.get("tanks") or []):
        if not isinstance(t, dict):
            continue
        r = (t.get("editor") or {}).get("replaces") if isinstance(t.get("editor"), dict) else None
        r = (twins or {}).get(t.get("id"), r)
        if is_int(r) and r in roster:
            label = f"tanks[{i}] {t.get('name')!r} (twin of {r} {roster[r]['name']})"
            out.append((label, t, roster[r], play_changes(t, roster[r])))
    return out


# --- summary ----------------------------------------------------------------------------

def describe_tank(t, pack_ids_to_names):
    def tank_name(i):
        if i in VANILLA_NAMES:
            return f"{VANILLA_NAMES[i]} (vanilla {i})"
        return f"{pack_ids_to_names.get(i, '?')} (custom {i})"

    parts = [f"{t.get('name')!s} (id {t.get('id')}), level {t.get('minLevel')}"]
    if t.get("upgradesFrom"):
        parts.append("upgrades from " + ", ".join(tank_name(i) for i in t["upgradesFrom"]))
    if t.get("advancesInto"):
        parts.append("advances into " + ", ".join(tank_name(i) for i in t["advancesInto"]))
    body = t.get("body", {})
    hull = "circle" if body.get("sides", 0) == 0 else f"{body['sides']}-gon"
    if body.get("size"):
        hull += f" r{body['size']:g}"
    if body.get("spinSpeed"):
        hull += " spinning"
    parts.append("hull " + hull)
    projs = t.get("projectiles", [])
    counts = {}
    for b in t.get("barrels", []):
        bt = b.get("bulletType")
        label = bt
        if b.get("flags", {}).get("holdsRaised"):
            label = "necro spawner"
        elif bt == "drone":
            label = f"spawner x{b.get('numDrones')}"
        elif bt == "none":
            label = "decorative"
        if b.get("invisible"):
            label = "invisible " + label
        if b.get("speedMultiplier") == 0 and bt in ("bullet", "trap"):
            label += " (stationary shots)"
        if "mountTurret" in b:
            label += " (on turret)"
        if b.get("flags", {}).get("firesOnSecondary"):
            label += " (right-click)"
        elif b.get("flags", {}).get("forceFire") and bt != "drone":
            label += " (auto-fire)"
        counts[label] = counts.get(label, 0) + 1
    if counts:
        parts.append("barrels: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    if projs:
        desc = []
        for p in projs:
            d = f"{p.get('name') or 'unnamed'} [{p.get('base')}"
            if p.get("barrels"):
                fl = {k for sb in p["barrels"] for k in sb.get("flags", {})}
                if "forceFire" in fl:
                    d += ", missile"
                if "firesOnDeath" in fl:
                    d += ", explodes"
                if not fl & {"forceFire", "firesOnDeath"}:
                    d += ", minion" if p.get("base") == "drone" else ", sub-barrels fire on click"
            if p.get("drone", {}).get("idle") == "cruise":
                d += ", swarm"
            if p.get("drone", {}).get("controllable") is False:
                d += ", AI-only"
            if p.get("burst"):
                d += ", burst " + "/".join(k for k, v in p["burst"].items() if v)
            if p.get("spinFlipsOnSecondary"):
                d += ", spin flips on right-click"
            if p.get("parts"):
                d += f", {len(p['parts'])} decorative part(s)"
            if p.get("turrets"):
                d += f", {len(p['turrets'])} turret(s)"
            desc.append(d + "]")
        parts.append("projectiles: " + "; ".join(desc))
    if t.get("bodyShapes"):
        parts.append(f"{len(t['bodyShapes'])} body shape(s)")
    if t.get("turrets"):
        parts.append(f"{len(t['turrets'])} turret(s)")
    if t.get("raises"):
        parts.append("raises " + ", ".join(t["raises"]))
    if t.get("invisibility", {}).get("enabled"):
        auto = sum(1 for b in t.get("barrels", []) if b.get("flags", {}).get("forceFire") and b.get("bulletType") != "drone")
        parts.append("invisible when idle" + (f" (its {auto} auto-fire barrel(s) keep firing, and shots never fade: "
                                               "they mark where it hides)" if auto else ""))
    sml = t.get("statsMaxLevel")
    if isinstance(sml, list) and sml != [7] * 8:
        parts.append(f"stat caps {sml}")
    extras = [k for k in ("speedMultiplier", "zoomMultiplier", "scopeDistance", "knockbackMultiplier",
                          "baseHealth", "baseBodyDamage") if k in t]
    if extras:
        parts.append(", ".join(f"{k} {t[k]:g}" for k in extras))
    if t.get("helpText"):
        parts.append(f"help: \"{t['helpText']}\"")
    b = import_budget(t)
    parts.append(f"import budget {b['rate']:.0f}/{LIMIT_RATE} per second, {b['alive']:.0f}/{LIMIT_ALIVE} in the air, "
                 f"room {b['load']:.0f}/{LIMIT_LOAD}, volley {b['volley']}/{LIMIT_VOLLEY}, "
                 f"pieces {b['pieces']}/{LIMIT_PIECES}" + (f", drones {b['drones']}/{LIMIT_DRONES}" if b["drones"] else ""))
    return ". ".join(parts) + "."


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    path = argv[1]
    summary = "--summary" in argv[2:]
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # pack and tank names may carry emoji
    except (AttributeError, ValueError):
        pass
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        pack = json.loads(text)
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e.msg} at line {e.lineno} column {e.colno}")
        return 1
    if not isinstance(pack, dict):
        print("ERROR: top level must be a JSON object")
        return 1
    rep = validate(pack)
    cosmetic = "--cosmetic" in argv[2:]
    named = {}
    rest = argv[2:]
    for i, a in enumerate(rest):
        if a == "--twin":
            tid, _, stock = (rest[i + 1] if i + 1 < len(rest) else "").partition("=")
            try:
                named[int(tid)] = _stock_id(stock)
            except ValueError as e:
                print(f"ERROR --twin needs ID=STOCK (a pack tank id, a stock name or vanilla id): {e}")
                return 1
    twins = stock_twins(pack, named) if isinstance(pack.get("tanks"), list) else []
    notes = []
    for label, _, _, diffs in twins:
        for line in diffs:
            if cosmetic:
                rep.error(label, f"plays differently from stock: {line}")
            else:
                notes.append(f"{label} differs from stock in play: {line}")
    if cosmetic and not twins:
        rep.error("pack", "--cosmetic: no tank has editor.replaces naming a stock tank (or a --twin), so there is nothing to compare")
    for w in rep.warnings:
        print("WARNING " + w)
    for n in notes:
        print("NOTE " + n)
    for e in rep.errors:
        print("ERROR " + e)
    tanks = pack.get("tanks") or []
    n_lines = text.count("\n")
    if n_lines > 1:
        print(f"NOTE file has {n_lines} line breaks; the editor writes one line, paste works either way")
    if summary and isinstance(tanks, list):
        names = {t.get("id"): t.get("name") for t in tanks if isinstance(t, dict)}
        print("--- summary ---")
        if pack.get("shapes"):
            print(f"custom shapes: " + ", ".join(f"{s.get('name')} ({s.get('sides')}-gon r{s.get('size')})"
                                                 for s in pack["shapes"] if isinstance(s, dict)))
        if pack.get("hiddenShapes"):
            print("hidden vanilla shapes: " + ", ".join(pack["hiddenShapes"]))
        if pack.get("starters"):
            print("starters: " + ", ".join(VANILLA_NAMES.get(i, names.get(i, str(i))) for i in pack["starters"]))
        if pack.get("hidden"):
            print(f"hidden vanilla tanks: {len(pack['hidden'])}")
        for t in tanks:
            if isinstance(t, dict):
                print(describe_tank(t, names))
    status = "FAIL" if rep.errors else "OK"
    print(f"{status}: {path}: {len(tanks)} tank(s), {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
