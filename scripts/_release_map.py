"""Version -> release date, and "which release first contained this commit".

Shared by scripts/cve_fetch.py and the software cross-reference. Kept separate
because both need it and neither owns it.

The date of a release is the date of the *commit the tag points at*, never the
tag object's own date: every tag imported from CVS or SVN carries the migration
day, which dates BIND 9.0.1 to 2012 and all of Unbound before 1.6.3 to a single
afternoon in June 2017.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_DIR = {"pdns-auth": "pdns", "pdns-rec": "pdns"}

#: Stable-release tag patterns. Anything with rc/alpha/beta/dev/pre is not one.
TAGPAT = {
    "unbound":    r"^release-(\d+\.\d+\.\d+)$",
    "nsd":        r"^NSD_(\d+)_(\d+)_(\d+)_REL$",
    "bind9":      r"^v(\d+\.\d+\.\d+)$",
    "knot":       r"^v(\d+\.\d+\.\d+)$",
    "kresd":      r"^v(\d+\.\d+\.\d+)$",
    "opendnssec": r"^(\d+\.\d+\.\d+)$",
    "pdns-auth":  r"^auth-(\d+\.\d+\.\d+)$",
    "pdns-rec":   r"^rec-(\d+\.\d+\.\d+)$",
}
ROLE = {"unbound": "resolver", "nsd": "authoritative", "bind9": "both",
        "knot": "authoritative", "kresd": "resolver", "opendnssec": "signer",
        "pdns-auth": "authoritative", "pdns-rec": "resolver"}

PRERELEASE = re.compile(r"(rc|alpha|beta|dev|pre|[ab]\d)", re.I)


def is_development(proj: str, ver: str) -> bool:
    """BIND 9.13 onward uses odd minor versions for development branches.

    9.15.6 is not a release an operator runs; treating it as stable dates
    dnssec-policy's CDS publication to 2019 instead of 9.16.0 in 2020. Before
    9.13 the scheme did not apply -- 9.9 and 9.11 were stable.
    """
    if proj != "bind9":
        return False
    parts = ver.split(".")
    return len(parts) >= 2 and parts[0] == "9" and int(parts[1]) >= 13 and int(parts[1]) % 2 == 1
FMT = ("%(if)%(*committerdate:short)%(then)%(*committerdate:short)"
       "%(else)%(committerdate:short)%(end)\t%(refname:short)")

_CACHE = Path("data/software/release_dates.json")
_repos = Path("out/software_repos")
_loaded: dict | None = None


def build(repos: Path) -> dict:
    out = {}
    for proj, pat in TAGPAT.items():
        repo = repos / f"{REPO_DIR.get(proj, proj)}.git"
        if not repo.exists():
            continue
        raw = subprocess.run(["git", "-C", str(repo), "for-each-ref", "--format", FMT,
                              "refs/tags"], capture_output=True, text=True).stdout
        rx, versions = re.compile(pat), {}
        for line in raw.splitlines():
            d, _, ref = line.partition("\t")
            m = rx.match(ref)
            if not m or PRERELEASE.search(ref):
                continue
            ver = ".".join(m.groups()) if m.lastindex and m.lastindex > 1 else m.group(1)
            if is_development(proj, ver):
                continue
            if ver not in versions or d < versions[ver]:      # a version can be re-tagged
                versions[ver] = d
        out[proj] = {"role": ROLE[proj],
                     "releases": dict(sorted(versions.items(), key=lambda kv: kv[1]))}
    return out


def releases(repos: Path | None = None) -> dict:
    global _loaded, _repos
    if repos is not None:
        _repos = repos
    if _loaded is None:
        if _CACHE.exists():
            _loaded = json.loads(_CACHE.read_text(encoding="utf-8"))
        else:
            _loaded = build(_repos)
            _CACHE.parent.mkdir(parents=True, exist_ok=True)
            _CACHE.write_text(json.dumps(_loaded, indent=2) + "\n", encoding="utf-8")
    return _loaded


def git(proj: str, *args: str) -> str:
    repo = _repos / f"{REPO_DIR.get(proj, proj)}.git"
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True).stdout


def first_release(proj: str, sha: str, not_before: str | None = None):
    """Earliest stable release containing `sha`, as (version, date).

    A tag dated before the commit cannot have shipped it. Those exist: the
    cvs2git import left old BIND and NSD tags pointing at rewritten commits, so
    v9.0.1 "contains" work from 2012.
    """
    rel = releases().get(proj, {}).get("releases", {})
    rx, best = re.compile(TAGPAT[proj]), None
    for tag in git(proj, "tag", "--contains", sha).splitlines():
        m = rx.match(tag.strip())
        if not m:
            continue
        ver = ".".join(m.groups()) if m.lastindex and m.lastindex > 1 else m.group(1)
        d = rel.get(ver)
        if not d or (not_before and d < not_before):
            continue
        if best is None or d < best[1]:
            best = (ver, d)
    return best
