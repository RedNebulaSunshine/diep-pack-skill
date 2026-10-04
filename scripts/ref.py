#!/usr/bin/env python3
"""Print the parts of the references a design needs, instead of whole files.

The references are long (recipes.md alone is ~12k tokens) and most designs use a few
sections of each. Every heading is a section; a section runs to the next heading of the same
or a higher level, so `## 7` includes its `### 7a` and `### 7b`.

    python ref.py                         # every file: its sections and their sizes
    python ref.py recipes                 # one file's table of contents
    python ref.py recipes intro           # the text before the first section (recipes' preset table)
    python ref.py recipes 5 20 dash       # sections by number or by a word in the heading
    python ref.py spec 7a                 # the spec by section number, across references/schema/
    python ref.py figurative 7b --toc     # one section's sub-headings, not its text
    python ref.py --find keepDistance     # which sections mention a term, with the lines
    python ref.py recipes --find forceFire
    python ref.py api                     # compose.py / mechanics.py: every call, one line each
    python ref.py api trail jaws          # those calls in full (signature and docstring)
    python ref.py api trail --source      # ... and their code
    python ref.py stock                   # the editor's 54 stock tanks: id, level, parts, size
    python ref.py stock "Twin Flank" 14   # those tanks verbatim, by name or vanilla id
    python ref.py stock --using raises    # only the stock tanks whose JSON has that field

`stock` serves `references/stock-tanks.diep-pack`, the sandbox editor's own export of its
roster (55 KB; never read it whole): a design that must keep a stock tank's mechanics exactly
clones the printed JSON instead of rebuilding it from recipes.

`api` reads the build library (`compose.py` with its `mechanics.py` presets, ~31k tokens as
source) without loading it: the module docstrings and one line per public call, or named calls
in full. Python 3.8+ standard library only.

Files: quick (quick-reference), recipes, moves, arena, figurative, vanilla, spec (all of
references/schema/), feedback, or any path. A query that is a number (`7`, `7a`, `§7a`)
matches the section's number, including a `(§7)` in its heading; anything else matches a word
or phrase in the heading, ignoring case. Exit 1 when a query matches nothing.
"""
import ast
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "references")
ALIASES = {
    "quick": "quick-reference.md", "quick-reference": "quick-reference.md",
    "recipes": "recipes.md", "moves": "moves.md", "arena": "arena.md",
    "figurative": "figurative.md", "vanilla": "vanilla-tanks.md",
    "vanilla-tanks": "vanilla-tanks.md", "feedback": "feedback.md",
}
SPEC = ("spec", "schema")
NUM = re.compile(r"^§?(\d+[a-z]?)$", re.I)
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def tokens(text):
    return max(1, round(len(text) / 4))  # rough: ~4 characters a token for this prose


def files_for(name):
    if name in SPEC:
        return sorted(glob.glob(os.path.join(REFS, "schema", "*.md")))
    if name in ALIASES:
        return [os.path.join(REFS, ALIASES[name])]
    for cand in (name, os.path.join(REFS, name), os.path.join(REFS, name + ".md")):
        if os.path.isfile(cand):
            return [cand]
    sys.exit(f"ref.py: no reference called {name!r}; try one of "
             f"{', '.join(sorted(set(ALIASES) - {'quick-reference', 'vanilla-tanks'}))}, spec")


def sections(path):
    """[(level, title, ids, start, end)] with 0-based line indexes; end is exclusive."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    heads, fence = [], False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else HEAD.match(ln)
        if m:
            title = m.group(2)
            ids = set()
            lead = re.match(r"^(\d+[a-z]?)\.", title)
            if lead:
                ids.add(lead.group(1).lower())
            ids.update(x.lower() for x in re.findall(r"§(\d+[a-z]?)", title))
            heads.append((len(m.group(1)), title, ids, i))
    out = []
    for k, (lvl, title, ids, start) in enumerate(heads):
        end = len(lines)
        for lvl2, _, _, s2 in heads[k + 1:]:
            if lvl2 <= lvl:
                end = s2
                break
        out.append((lvl, title, ids, start, end))
    # a lone level-1 heading is the document's title, not a section: what follows it up to the
    # first real section is the intro
    if len([s for s in out if s[0] == 1]) == 1 and out[0][0] == 1:
        out = out[1:]
    return lines, out


def intro_span(lines, secs):
    first = secs[0][3] if secs else len(lines)
    start = next((i + 1 for i, ln in enumerate(lines[:first]) if HEAD.match(ln)), 0)
    return start, first


def rel(path):
    return os.path.relpath(path, os.path.dirname(REFS)).replace(os.sep, "/")


def toc(path, within=None):
    lines, secs = sections(path)
    top = min((s[0] for s in secs), default=1)
    a, b = intro_span(lines, secs)
    print(f"{rel(path)}  (~{tokens(chr(10).join(lines))} tokens)")
    if within is None and "".join(lines[a:b]).strip():
        print(f"{'  intro':<58} ~{tokens(chr(10).join(lines[a:b]))}")
    for lvl, title, _, start, end in secs:
        if within and not (within[0] <= start < within[1]):
            continue
        name = "  " * (lvl - top + 1) + title
        print(f"{name[:58]:<58} ~{tokens(chr(10).join(lines[start:end]))}")


def match(query, title, ids):
    m = NUM.match(query)
    if m:
        return m.group(1).lower() in ids
    return query.lower() in title.lower()


def show(paths, queries, toc_only):
    found_any = True
    for q in queries:
        hits = []
        for p in paths:
            lines, secs = sections(p)
            if q.lower() == "intro":
                a, b = intro_span(lines, secs)
                if "".join(lines[a:b]).strip():
                    hits.append((p, "intro", lines[a:b], (a, b)))
                continue
            for lvl, title, ids, start, end in secs:
                if match(q, title, ids):
                    hits.append((p, title, lines[start:end], (start, end)))
        # a number names one section; keep the outermost when a parent and child both say it
        if NUM.match(q):
            hits = [h for h in hits if not any(o is not h and o[0] == h[0] and
                    o[3][0] <= h[3][0] and h[3][1] <= o[3][1] and o[3] != h[3] for o in hits)]
        if not hits:
            found_any = False
            print(f"ref.py: no section matches {q!r} in "
                  f"{', '.join(rel(p) for p in paths)}; its sections:", file=sys.stderr)
            for p in paths:
                toc(p)
            continue
        for p, title, body, span in hits:
            if toc_only:
                toc(p, within=span)
            else:
                print(f"<!-- {rel(p)} lines {span[0] + 1}-{span[1]} -->")
                print("\n".join(body).rstrip() + "\n")
    return found_any


def find(paths, term):
    pat = re.compile(re.escape(term), re.I)
    n = 0
    for p in paths:
        lines, secs = sections(p)
        for i, ln in enumerate(lines):
            if pat.search(ln):
                inner = [s for s in secs if s[3] <= i < s[4]]
                where = inner[-1][1] if inner else "intro"
                print(f"{rel(p)}:{i + 1}  [{where}]  {ln.strip()[:140]}")
                n += 1
    if not n:
        print(f"ref.py: {term!r} appears nowhere in {len(paths)} file(s)", file=sys.stderr)
    return n > 0


STOCK = os.path.join(REFS, "stock-tanks.diep-pack")
VANILLA = os.path.join(REFS, "vanilla-tanks.md")
ROW = re.compile(r"^\| (\d+) \| ([^|*]+?) \| (\d+|—) \| ([^|]*?) \|", re.M)


def _vanilla():
    """{name: (id, level, parents)} from the table in vanilla-tanks.md."""
    with open(VANILLA, encoding="utf-8") as f:
        text = f.read()
    return {n.strip(): (int(i), lv, par.strip()) for i, n, lv, par in ROW.findall(text)}


def _stock_tanks():
    import json
    with open(STOCK, encoding="utf-8") as f:
        return json.load(f)["tanks"]


def _parts(t):
    b, s, u = len(t.get("barrels") or []), len(t.get("bodyShapes") or []), len(t.get("turrets") or [])
    return " ".join(f"{n} {w}" for n, w in ((b, "barrels"), (s, "shapes"), (u, "turrets")) if n) or "no parts"


def stock(queries, using=None):
    """The editor's own stock roster (references/stock-tanks.diep-pack), one tank at a time.
    No query: every tank, one line each. Names or vanilla ids: those tanks as compact JSON,
    verbatim from the export (their pack ids are the export's; no tree links). --using FIELD:
    only the tanks whose JSON contains that field name."""
    import json
    van = _vanilla()
    tanks = _stock_tanks()
    if using:
        tanks = [t for t in tanks if f'"{using}"' in json.dumps(t, separators=(",", ":"))]
        if not tanks:
            print(f"ref.py: no stock tank uses {using!r}", file=sys.stderr)
            return False
    if not queries:
        rows = sorted(tanks, key=lambda t: van.get(t["name"], (999,))[0])
        for t in rows:
            vid, lv, par = van.get(t["name"], ("?", t["minLevel"], "?"))
            size = len(json.dumps(t, separators=(",", ":")))
            print(f"{str(vid):>3}  {t['name']:<16} L{t['minLevel']:<3} {_parts(t):<32} {size:>5} B   from {par}")
        print(f"\n{len(rows)} tanks. `ref.py stock <name|id> …` prints them verbatim; a clone that stands in for the "
              f"stock tank sets editor.replaces to the id shown and the pack hides that id.")
        return True
    ok = True
    for q in queries:
        hit = [t for t in tanks if t["name"].lower() == q.lower()
               or (q.isdigit() and van.get(t["name"], (None,))[0] == int(q))]
        if not hit:
            near = [t["name"] for t in tanks if q.lower() in t["name"].lower()]
            print(f"ref.py: no stock tank called {q!r}" + (f"; did you mean {', '.join(near)}?" if near else ""),
                  file=sys.stderr)
            ok = False
            continue
        for t in hit:
            vid, lv, par = van.get(t["name"], ("?", t["minLevel"], "?"))
            print(f"# {t['name']}: vanilla id {vid}, level {t['minLevel']}, upgrades from {par}; {_parts(t)}. "
                  f"To stand in for it: editor.replaces {vid} on the clone and {vid} in the pack's hidden list.")
            print(json.dumps(t, separators=(",", ":"), ensure_ascii=False))
    return ok


API_FILES = ("compose.py", "mechanics.py")


def _calls():
    """(file, owner class, node, source lines) for the modules and every public def and class."""
    out = []
    for name in API_FILES:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)
        lines = src.splitlines()
        out.append((name, None, tree, lines))
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                out.append((name, None, n, lines))
                if isinstance(n, ast.ClassDef):
                    out.extend((name, n.name, m, lines) for m in n.body
                               if isinstance(m, ast.FunctionDef) and
                               (not m.name.startswith("_") or m.name == "__init__"))
    return out


def _signature(node, lines):
    if isinstance(node, ast.ClassDef):
        return f"class {node.name}"
    head = lines[node.lineno - 1:node.body[0].lineno - 1] or [lines[node.lineno - 1]]
    head = re.sub(r"\s+", " ", " ".join(ln.strip() for ln in head))
    head = re.sub(r"^def ", "", head)
    return head[:-1] if head.endswith(":") else head


def api(names, source):
    calls = _calls()
    if not names:
        for fname, owner, node, lines in calls:
            if isinstance(node, ast.Module):
                print(f"## {fname}\n\n{ast.get_docstring(node) or ''}\n")
                continue
            doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
            print(("  " if owner else "") + _signature(node, lines) + (f"  # {doc}" if doc else ""))
        print("\n(`ref.py api <name>` prints a call in full. Mechanics presets are mixed into "
              "Tank, so they are all methods of `d`.)")
        return True
    ok = True
    for q in names:
        defs = [c for c in calls if not isinstance(c[2], ast.Module)]
        hits = [c for c in defs if c[2].name == q or (c[1] and f"{c[1]}.{c[2].name}" == q)]
        hits = hits or [c for c in defs if q.lower() in c[2].name.lower()]
        if not hits:
            print(f"ref.py: no call named {q!r} in {', '.join(API_FILES)}", file=sys.stderr)
            ok = False
            continue
        for fname, owner, node, lines in hits:
            print(f"<!-- {fname}:{node.lineno}" + (f" ({owner})" if owner else "") + " -->")
            if source:
                end = getattr(node, "end_lineno", None) or node.lineno
                print("\n".join(lines[node.lineno - 1:end]) + "\n")
                continue
            doc = ast.get_docstring(node)
            print(_signature(node, lines))
            print(("    " + doc.replace("\n", "\n    ")) if doc else "    (no docstring)")
            print()
    return ok


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    toc_only = "--toc" in argv
    argv = [a for a in argv if a != "--toc"]
    if "--find" in argv:
        i = argv.index("--find")
        term = " ".join(argv[i + 1:])
        names = argv[:i]
        if not term:
            sys.exit("ref.py: --find needs a term")
        paths = [p for n in names for p in files_for(n)] if names else (
            sorted(glob.glob(os.path.join(REFS, "*.md"))) +
            sorted(glob.glob(os.path.join(REFS, "schema", "*.md"))))
        return 0 if find(paths, term) else 1
    if argv and argv[0] == "api":
        rest = [a for a in argv[1:] if a != "--source"]
        return 0 if api(rest, "--source" in argv) else 1
    if argv and argv[0] == "stock":
        rest, using = argv[1:], None
        if "--using" in rest:
            i = rest.index("--using")
            if i + 1 >= len(rest):
                sys.exit("ref.py: --using needs a field name")
            using = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        return 0 if stock(rest, using) else 1
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if not argv:
        for p in sorted(glob.glob(os.path.join(REFS, "*.md"))) + \
                sorted(glob.glob(os.path.join(REFS, "schema", "*.md"))):
            toc(p)
            print()
        return 0
    paths = files_for(argv[0])
    if len(argv) == 1:
        for p in paths:
            toc(p)
        return 0
    return 0 if show(paths, argv[1:], toc_only) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
