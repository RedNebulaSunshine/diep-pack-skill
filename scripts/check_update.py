#!/usr/bin/env python3
"""Is a newer version of this skill published? If so, what is new, and can it update itself?

    python check_update.py            # at most once a day; one line when there is nothing new
    python check_update.py --force    # check now
    python check_update.py --apply    # update this install (only after the user said yes)

The published version is the `version` in the repository's SKILL.md (`metadata.repository`,
see skill_meta.py); what is new comes from its CHANGELOG.md. A git checkout of the skill
asks its own remote with `git fetch` (so a private repository works with the user's
credentials, and no prompt ever appears); any other install downloads the two files from
GitHub. Nothing about the user or their work is sent. Offline, private or blocked: one
NOT CHECKED line and exit 0, never an error. Set DIEP_PACK_NO_UPDATE_CHECK=1 to turn it off.

`--apply` fast-forwards a git checkout that has no local edits and no local commits. Any other
install gets instructions instead; nothing is overwritten.

Output, first word of each line: UP TO DATE, AHEAD, UPDATE (then NEW IN lines and HOW),
NOT CHECKED, OFF, UPDATED, CANNOT UPDATE. Standard library only.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

import skill_meta
from skill_meta import SKILL_DIR

ONCE_EVERY = 20 * 3600     # seconds between network checks
MAX_NOTES = 14             # changelog lines shown before "… and more"
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never",
               GIT_ASKPASS="", SSH_ASKPASS="")
GIT_ENV.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=5")


def git(*args, timeout=15):
    try:
        r = subprocess.run(["git", *args], cwd=SKILL_DIR, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=GIT_ENV, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def is_checkout():
    """True when the skill folder is the top of its own git work tree (a clone or submodule)."""
    code, top = git("rev-parse", "--show-toplevel", timeout=5)
    return code == 0 and os.path.normcase(os.path.realpath(top)) == \
        os.path.normcase(os.path.realpath(SKILL_DIR))


def upstream_ref(meta):
    code, ref = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", timeout=5)
    return ref if code == 0 and ref else f"origin/{skill_meta.branch(meta)}"


def fetch_git(meta):
    ref = upstream_ref(meta)
    remote, _, br = ref.partition("/")
    code, _ = git("fetch", "--quiet", remote, br, timeout=20)
    if code != 0:
        return None
    files = {}
    for name in ("SKILL.md", "CHANGELOG.md"):
        c, text = git("show", f"{ref}:{name}", timeout=5)
        files[name] = text if c == 0 else ""
    return files


def fetch_http(meta):
    slug, br = skill_meta.repo_slug(meta), skill_meta.branch(meta)
    if not slug:
        return None
    files = {}
    for name in ("SKILL.md", "CHANGELOG.md"):
        url = f"https://raw.githubusercontent.com/{slug}/{br}/{name}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "diep-pack-update-check"})
            with urllib.request.urlopen(req, timeout=4) as r:
                files[name] = r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError, ValueError):
            files[name] = gh_file(slug, br, name)
        if name == "SKILL.md" and not files[name]:
            return None
    return files


def gh_file(slug, br, name):
    """A private repository, through the GitHub CLI if it is installed and signed in."""
    try:
        r = subprocess.run(["gh", "api", f"repos/{slug}/contents/{name}?ref={br}",
                            "-H", "Accept: application/vnd.github.raw"],
                           capture_output=True, text=True, encoding="utf-8", timeout=8)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def notes_between(changelog, have, latest):
    """Changelog lines for versions newer than `have`, up to `latest`, newest first."""
    out, keep = [], False
    lo, hi = skill_meta.version_key(have), skill_meta.version_key(latest)
    for line in changelog.splitlines():
        m = re.match(r"^##\s+v?(\d+\.\d+\.\d+)", line)
        if m:
            v = skill_meta.version_key(m.group(1))
            keep = bool(v and lo and hi and lo < v <= hi)
            if keep:
                out.append(f"NEW IN {m.group(1)}")
            continue
        if keep and line.strip():
            out.append("  " + line.strip())
    if len(out) > MAX_NOTES:
        out = out[:MAX_NOTES] + ["  … and more in CHANGELOG.md"]
    return out


def cache_path():
    base = (os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME") or
            os.path.join(os.path.expanduser("~"), ".cache"))
    return os.path.join(base, "diep-pack", "update-check.json")


def load_cache():
    try:
        with open(cache_path(), encoding="utf-8") as f:
            return json.load(f).get(os.path.normcase(SKILL_DIR)) or {}
    except (OSError, ValueError, AttributeError):
        return {}


def save_cache(entry):
    path = cache_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
        data[os.path.normcase(SKILL_DIR)] = entry
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    except OSError:
        pass   # a read-only home is fine: the check just runs every time


def how_to_update(meta, checkout):
    slug, br = skill_meta.repo_slug(meta), skill_meta.branch(meta)
    if checkout:
        return "HOW  python <skill>/scripts/check_update.py --apply  (a git fast-forward)"
    return (f"HOW  this install is not a git clone: download "
            f"https://github.com/{slug}/releases/latest/download/diep-pack.zip and replace the "
            f"skill folder with the diep-pack folder inside it (on claude.ai or ChatGPT: remove "
            f"the old diep-pack skill and upload the new zip), or reinstall with: "
            f"git clone https://github.com/{slug} <skills folder>/diep-pack")


def report(have, latest, notes, meta, checkout, moved):
    hk, lk = skill_meta.version_key(have), skill_meta.version_key(latest)
    if not (hk and lk):
        print(f"NOT CHECKED the published version could not be read ({latest or 'none'})")
        return
    if lk <= hk:
        print(f"{'AHEAD' if lk < hk else 'UP TO DATE'} diep-pack {have}"
              + (f" (published: {latest})" if lk < hk else ""))
        return
    print(f"UPDATE diep-pack {latest} is available (this install is {have})")
    for line in notes or ["  (no changelog entry)"]:
        print(line)
    if moved:
        print(f"MOVED the skill now lives at {moved}")
    print(how_to_update(meta, checkout))


def check(force):
    meta = skill_meta.read_meta()
    have = meta.get("version", "")
    checkout = is_checkout()
    cached = load_cache()
    if not force and cached.get("have") == have and time.time() - cached.get("at", 0) < ONCE_EVERY:
        report(have, cached.get("latest", ""), cached.get("notes"), meta, checkout,
               cached.get("moved"))
        return 0
    files = fetch_git(meta) if checkout else None
    files = files or fetch_http(meta)
    if not files or not files.get("SKILL.md"):
        print(f"NOT CHECKED diep-pack {have}: offline, private or unreachable; carry on")
        return 0
    remote = skill_meta.parse_meta(files["SKILL.md"])
    latest = remote.get("version", "")
    notes = notes_between(files.get("CHANGELOG.md", ""), have, latest)
    moved = None
    if remote.get("repository") and skill_meta.slug_of(remote["repository"]) != \
            skill_meta.slug_of(meta.get("repository", "")):
        moved = remote["repository"]
    save_cache({"at": time.time(), "have": have, "latest": latest, "notes": notes,
                "moved": moved})
    report(have, latest, notes, meta, checkout, moved)
    return 0


def apply():
    meta = skill_meta.read_meta()
    have = meta.get("version", "")
    if not is_checkout():
        print("CANNOT UPDATE this install itself: it is not a git clone")
        print(how_to_update(meta, False))
        return 0
    code, dirty = git("status", "--porcelain", "--untracked-files=no", timeout=10)
    if code != 0 or dirty:
        print("CANNOT UPDATE the skill folder has local edits; commit or stash them, or "
              "update it by hand (git pull)")
        return 0
    ref = upstream_ref(meta)
    remote, _, br = ref.partition("/")
    if git("fetch", "--quiet", remote, br, timeout=30)[0] != 0:
        print("CANNOT UPDATE could not reach the repository (offline or no access)")
        return 0
    if git("merge-base", "--is-ancestor", "HEAD", ref, timeout=10)[0] != 0:
        print(f"CANNOT UPDATE this checkout has commits that are not in {ref}; not touching it")
        return 0
    on_branch = git("symbolic-ref", "-q", "HEAD", timeout=5)[0] == 0
    code, out = (git("merge", "--ff-only", "--quiet", ref, timeout=30) if on_branch else
                 git("checkout", "--quiet", "--detach", ref, timeout=30))
    if code != 0:
        print(f"CANNOT UPDATE git said: {out or 'the fast-forward failed'}")
        return 0
    now = skill_meta.read_meta().get("version", "?")
    save_cache({})
    print(f"UPDATED diep-pack {have} -> {now}. Re-read SKILL.md before carrying on: "
          f"it may have changed.")
    return 0


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if "--apply" in argv:
        return apply()
    if os.environ.get("DIEP_PACK_NO_UPDATE_CHECK", "").strip() not in ("", "0"):
        print("OFF update check disabled (DIEP_PACK_NO_UPDATE_CHECK)")
        return 0
    return check("--force" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
