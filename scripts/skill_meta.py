"""The skill's identity, read from one place: the `metadata` block of SKILL.md.

    metadata:
      version: "1.2.0"
      repository: "https://github.com/<owner>/<name>"

Every script that needs the version or the repository (report_issue.py, check_update.py) reads
it from here, so moving the repository to another account or name is a one-line change in
SKILL.md (GitHub also redirects the old address). $DIEP_PACK_REPO (owner/name or a URL)
overrides it, for a fork. Standard library only.
"""
import os
import re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BRANCH = "main"


def read_meta(skill_md=None):
    """{'version': ..., 'repository': ..., 'branch': ...} from SKILL.md's front matter."""
    try:
        with open(skill_md or os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
            return parse_meta(f.read())
    except OSError:
        return {}


def parse_meta(text):
    meta = {}
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return meta
    head = text[3:].split("\n---", 1)[0]
    for key in ("version", "repository", "branch"):
        m = re.search(rf"^\s+{key}:\s*[\"']?([^\"'\n]+?)[\"']?\s*$", head, re.M)
        if m:
            meta[key] = m.group(1).strip()
    return meta


def slug_of(raw):
    """owner/name from a GitHub URL, git remote or owner/name; None if it is none of those."""
    m = re.search(r"(?:github\.com[/:])?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", (raw or "").strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def repo_slug(meta=None):
    """The repository as owner/name: $DIEP_PACK_REPO, else SKILL.md's metadata.repository."""
    meta = read_meta() if meta is None else meta
    raw = (os.environ.get("DIEP_PACK_REPO") or os.environ.get("DIEP_PACK_FEEDBACK_REPO") or
           meta.get("repository", ""))
    return slug_of(raw)


def branch(meta=None):
    meta = read_meta() if meta is None else meta
    return os.environ.get("DIEP_PACK_BRANCH") or meta.get("branch") or DEFAULT_BRANCH


def version_key(v):
    """'1.10.2' -> (1, 10, 2); None when it is not MAJOR.MINOR.PATCH."""
    m = re.match(r"^\s*v?(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else None
