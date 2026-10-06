#!/usr/bin/env python3
"""Turn a finding into a GitHub issue the user files themselves: sanitise it, then print a link.

The skill never posts anything. This script strips what should not leave the user's machine
(paths, user and host names, e-mail addresses, keys and tokens, IP addresses, @-handles,
pack authors and any names passed with --redact), saves the issue body beside the draft,
and prints a link that opens GitHub's new-issue form already filled in. The user reads it,
edits it if they like, and presses Submit. See references/feedback.md.

    python report_issue.py output/feedback/<slug>.json
    python report_issue.py draft.json --redact "Author Name" --redact "Some Pack"
    python report_issue.py draft.json --plain      # one markdown body (a fork without the form)
    python report_issue.py draft.json --open       # also open the form in the user's browser

Terminals wrap long links and break them, so the link is also saved as `<draft>.link.html`, a
page with one button, and `--open` opens it in the browser (only after the user says yes).

The draft is a JSON object; `title`, `kind`, `believed` and `observed` are required:

    {"title": "...", "kind": "spec", "area": "references/schema/04-barrels.md §7a",
     "believed": "...", "observed": "...", "tested": "...", "suggestion": "...",
     "confidence": "Confirmed in game", "pack": "{...}", "agent": "Claude Code"}

The repository comes from $DIEP_PACK_REPO (owner/name) or else from
`metadata.repository` in SKILL.md. Standard library only. Exit 1 on a bad draft.
"""
import getpass
import html
import json
import os
import re
import socket
import subprocess
import sys
import webbrowser
from datetime import date
from urllib.parse import quote, urlencode, urlsplit

import skill_meta
from skill_meta import SKILL_DIR
TEMPLATE = "skill-feedback.yml"
KINDS = ("spec", "validator", "renderer", "build-library", "missing-move", "skill-behaviour", "boss",
         "discovery", "other")
FIELDS = [  # (form field id, heading in a plain body), as labelled in the issue form
    ("kind", "Kind"), ("area", "Where in the skill"),
    ("believed", "What the skill says, did or did not know"),
    ("observed", "What happened instead, or the new way"), ("tested", "How it was tested"),
    ("suggestion", "Suggested change"), ("confidence", "Confidence"),
    ("pack", "Pack excerpt"), ("context", "Skill version and agent"),
]
REQUIRED = ("title", "kind", "believed", "observed")
MAX_URL = 7000      # GitHub answers 414 somewhere past ~8 KB; stay well under it
MAX_PACK = 2500     # an excerpt, not a pack
TRUNCATED = "\n\n… (shortened to fit the link; the rest is in the draft the skill saved)"
SAFE_HOSTS = ("diep.io", "agentskills.io")
DECORATORS = {"property", "staticmethod", "classmethod", "dataclass", "contextmanager"}
GENERIC_NAMES = {"user", "admin", "root", "runner", "localhost", "home", "owner"}

SECRETS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
]
KEY_VALUE = re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password|passwd|"
                       r"authorization)(\s*[:=]\s*)([^\s\"',;]{6,})")
BEARER = re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{16,}")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
URL = re.compile(r"\bhttps?://[^\s<>\"'`)\]]+")
WIN_PATH = re.compile(r"(?<![\w/])(?:[A-Za-z]:[\\/]|\\\\[\w.$-]+\\)[^\s\"'`<>|*?]*")
NIX_PATH = re.compile(r"(?<![\w.<])(?:~(?=/)|/(?:home|Users|root|mnt|media|Volumes|private|var|tmp|"
                      r"opt|srv|workspace|workspaces|run|data))(?:/[^\s\"'`<>|*?]*)?")
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
HANDLE = re.compile(r"(?<![\w.`<@])@([A-Za-z0-9][\w-]{0,38})")
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report a finding</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 16px/1.5 system-ui, "Segoe UI", Arial; max-width: 40rem; margin: 3rem auto;
         padding: 0 16px; background: Canvas; color: CanvasText; }}
  a.button {{ display: inline-block; padding: .7rem 1.2rem; border-radius: .4rem;
             background: #1f6feb; color: #fff; text-decoration: none; font-weight: 600; }}
</style></head><body>
<h1>{title}</h1>
<p>This opens GitHub with the issue already filled in. Read it, change anything you like,
tick the privacy box and submit. Nothing has been sent yet.</p>
<p><a class="button" href="{url}">Open the issue on GitHub</a></p>
<p><a href="{search}">Check for a similar issue first</a></p>
</body></html>
"""
AUTHOR = re.compile(r"(\"author\"\s*:\s*)\"(?:[^\"\\]|\\.)*\"")


def repo_slug():
    slug = skill_meta.repo_slug()
    if not slug:
        sys.exit("report_issue.py: no repository: set metadata.repository in SKILL.md "
                 "(or DIEP_PACK_REPO=owner/name)")
    return slug


def _git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=SKILL_DIR, capture_output=True, text=True,
                             timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def private_terms(extra):
    """Words that identify this machine or person: (term, placeholder), longest first."""
    terms = [(t, "<redacted>") for t in extra if t and t.strip()]
    found = []
    for get in (getpass.getuser, lambda: os.environ.get("USERNAME", ""),
                lambda: os.environ.get("USER", ""),
                lambda: os.path.basename(os.path.expanduser("~"))):
        try:
            found.append((get(), "<user>"))
        except Exception:
            pass
    try:
        found.append((socket.gethostname(), "<host>"))
    except OSError:
        pass
    found += [(_git("config", "user.name"), "<user>"), (_git("config", "user.email"), "<email>")]
    for t, ph in found:
        if t and len(t) >= 3 and t.lower() not in GENERIC_NAMES:
            terms.append((t, ph))
            if ph == "<user>" and " " in t:   # a git name: its parts too ("Ada Lovelace")
                terms += [(p, ph) for p in t.split() if len(p) >= 3]
    return sorted({t for t in terms}, key=lambda tp: -len(tp[0]))


class Sanitiser:
    def __init__(self, repo, extra):
        self.repo = repo.lower()
        self.terms = private_terms(extra)
        self.counts = {}

    def _n(self, kind, n=1):
        if n:
            self.counts[kind] = self.counts.get(kind, 0) + n

    def _path(self, m):
        p = m.group(0).rstrip(".,:;")
        tail = m.group(0)[len(p):]
        norm = p.replace("\\", "/")
        self._n("paths")
        for anchor, label in (("/diep-pack/", "<skill>/"), ("/output/", "output/")):
            i = norm.lower().rfind(anchor)
            if i >= 0:
                return label + norm[i + len(anchor):] + tail
        base = norm.rstrip("/").rsplit("/", 1)[-1]
        return ("<path>/" + base if base and "." in base else "<path>") + tail

    def _url(self, m):
        url = m.group(0).rstrip(".,:;")
        tail = m.group(0)[len(url):]
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host.endswith(SAFE_HOSTS) or (host == "github.com" and
                                         parts.path.lower().startswith("/" + self.repo)):
            return "\0URL" + url.encode("utf-8").hex() + "\0" + tail
        self._n("links (kept the site only)")
        return f"\0URL{(parts.scheme + '://' + host + '/…').encode('utf-8').hex()}\0" + tail

    def clean(self, text):
        if not text:
            return text
        for pat in SECRETS:
            text, n = pat.subn("<secret>", text)
            self._n("keys and tokens", n)
        text, n = BEARER.subn(lambda m: m.group(1) + "<secret>", text)
        self._n("keys and tokens", n)
        text, n = KEY_VALUE.subn(lambda m: m.group(1) + m.group(2) + "<secret>", text)
        self._n("keys and tokens", n)
        text, n = EMAIL.subn("<email>", text)
        self._n("e-mail addresses", n)
        text = URL.sub(self._url, text)      # parked as hex so the path rules leave them alone
        text = WIN_PATH.sub(self._path, text)
        text = NIX_PATH.sub(self._path, text)
        text, n = IPV4.subn("<ip>", text)
        self._n("IP addresses", n)
        text, n = AUTHOR.subn(lambda m: m.group(1) + '"<author>"', text)
        self._n("pack authors", n)
        for term, ph in self.terms:
            text, n = re.subn(r"(?<![\w])" + re.escape(term) + r"(?![\w])", ph, text, flags=re.I)
            self._n("names" if ph == "<redacted>" else "user and machine names", n)

        def handle(m):
            if m.group(1).lower() in DECORATORS:
                return m.group(0)
            self._n("@-handles")
            return "<handle>"
        text = HANDLE.sub(handle, text)
        return re.sub(r"\0URL([0-9a-f]*)\0", lambda m: bytes.fromhex(m.group(1)).decode("utf-8"),
                      text)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        sys.exit(f"report_issue.py: cannot read {path}: {e}")
    if not isinstance(d, dict):
        sys.exit("report_issue.py: the draft must be a JSON object")
    missing = [k for k in REQUIRED if not str(d.get(k) or "").strip()]
    if missing:
        sys.exit(f"report_issue.py: the draft needs {', '.join(missing)}")
    if d["kind"] not in KINDS:
        print(f"note: kind {d['kind']!r} is not one of {', '.join(KINDS)}", file=sys.stderr)
    if isinstance(d.get("pack"), (dict, list)):
        d["pack"] = json.dumps(d["pack"], ensure_ascii=False, separators=(",", ":"))
    return {k: ("" if v is None else str(v)) for k, v in d.items()}


def fields_of(d, meta):
    commit = _git("rev-parse", "--short", "HEAD")
    ctx = [f"diep-pack {meta.get('version', '?')}" + (f" ({commit})" if commit else ""),
           f"reported {date.today().isoformat()}"]
    if d.get("agent"):
        ctx.append(f"agent: {d['agent']}")
    d = dict(d, context="; ".join(ctx))
    if len(d.get("pack", "")) > MAX_PACK:
        d["pack"] = d["pack"][:MAX_PACK] + TRUNCATED
    return d


def plain_body(f):
    out = []
    for key, head in FIELDS:
        v = f.get(key, "").strip()
        if v:
            out.append(f"### {head}\n\n" + (f"```json\n{v}\n```" if key == "pack" else v))
    return "\n\n".join(out) + "\n"


def link(repo, f, plain):
    base = f"https://github.com/{repo}/issues/new?"
    title = f"[{f['kind']}] {f['title']}"
    if plain:
        q = {"title": title, "body": plain_body(f)}
    else:
        q = {"template": TEMPLATE, "title": title}
        q.update({k: f[k] for k, _ in FIELDS if f.get(k, "").strip()})
    return base + urlencode(q, quote_via=quote)


def fit(repo, f, plain):
    """Shorten the longest free-text fields until the link fits; drop the pack first."""
    f = dict(f)
    url = link(repo, f, plain)
    if len(url) > MAX_URL and f.get("pack"):
        f["pack"] = "(left out to fit the link; the skill saved the draft with it)"
        url = link(repo, f, plain)
    while len(url) > MAX_URL:
        key = max(("believed", "observed", "tested", "suggestion"), key=lambda k: len(f.get(k, "")))
        over = len(url) - MAX_URL
        keep = max(200, len(f[key]) - over // 2 - len(TRUNCATED) - 50)
        if keep >= len(f[key]):
            break
        f[key] = f[key][:keep].rstrip() + TRUNCATED
        url = link(repo, f, plain)
    return url, f


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    plain = "--plain" in argv
    want_open = "--open" in argv
    extra, args, i = [], [], 0
    while i < len(argv):
        if argv[i] == "--redact" and i + 1 < len(argv):
            extra.append(argv[i + 1])
            i += 2
            continue
        if argv[i] not in ("--plain", "--open"):
            args.append(argv[i])
        i += 1
    if len(args) != 1:
        sys.exit("report_issue.py: give one draft file")
    draft = args[0]
    repo = repo_slug()
    meta = skill_meta.read_meta()
    s = Sanitiser(repo, extra)
    f = {k: s.clean(v) for k, v in fields_of(load(draft), meta).items()}
    url, shown = fit(repo, f, plain)

    body_path = os.path.splitext(draft)[0] + ".md"
    with open(body_path, "w", encoding="utf-8", newline="\n") as out:
        out.write(plain_body(f))

    gh_title = f["title"].replace('"', "'")
    words = " ".join(re.findall(r"[A-Za-z0-9§]+", f["title"])[:6])
    search = f"https://github.com/{repo}/issues?" + urlencode(
        {"q": f"is:issue {words}"}, quote_via=quote)

    # terminals wrap a long link and break it, so it also goes in a page the user can open
    page_path = os.path.splitext(draft)[0] + ".link.html"
    with open(page_path, "w", encoding="utf-8", newline="\n") as out:
        out.write(PAGE.format(title=html.escape(f"[{f['kind']}] {f['title']}"),
                              url=html.escape(url, quote=True),
                              search=html.escape(search, quote=True)))
    print(f"ISSUE  [{f['kind']}] {f['title']}")
    print(f"REPO   {repo}")
    removed = ", ".join(f"{n} {k}" for k, n in sorted(s.counts.items())) or "nothing"
    print(f"REMOVED {removed}")
    if shown != f:
        print("SHORTENED to fit the link: " +
              ", ".join(k for k in f if shown.get(k) != f.get(k)))
    print(f"BODY   {body_path}  (sanitised, unshortened)")
    print("\n" + plain_body(shown))
    if re.search(r"\battach(ed|ment|ing)?\b", plain_body(f), re.I):
        print("NOTE   the draft mentions an attachment, but neither the link nor `gh issue create` can carry a "
              "file: reword it, and tell the user to drop the file into a comment on the issue page after filing.")
    print(f"DUPLICATES  {search}")
    print(f"LINK ({len(url)} chars, {'plain body' if plain else 'issue form'})\n{url}")
    print(f"PAGE   {page_path}  (the same link as a button: a terminal wraps long links)")
    print(f"\nGH (only if the user asks you to file it for them; it posts as them)\n"
          f"gh issue create --repo {repo} --title \"[{f['kind']}] {gh_title}\" "
          f"--body-file \"{body_path}\"")
    if want_open:
        try:
            opened = webbrowser.open(url)
        except webbrowser.Error:
            opened = False
        print("\nOPENED the new-issue form in the browser" if opened else
              f"\nNO BROWSER could be opened here; open the page instead: {page_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
