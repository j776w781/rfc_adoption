"""Regenerate docs/handoff/01_program_timelines.md from data/software/timelines/*.json.

Counts come from the JSON files. Verification outcomes come from VERIFIED below, which
records the totals each Phase 3 report states (docs/handoff/verify/<program>.md); a
program missing from VERIFIED is shown as not verified.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "data" / "software" / "timelines"
OUT = ROOT / "docs" / "handoff" / "01_program_timelines.md"

ORDER = ["bind9", "unbound", "nsd", "knot", "kresd", "opendnssec", "pdns-auth", "pdns-rec"]
NAMES = {
    "bind9": "BIND 9", "unbound": "Unbound", "nsd": "NSD", "knot": "Knot DNS",
    "kresd": "Knot Resolver", "opendnssec": "OpenDNSSEC",
    "pdns-auth": "PowerDNS Authoritative", "pdns-rec": "PowerDNS Recursor",
}
# program -> (checks run, correction items applied, commit that applied them)
VERIFIED: dict[str, tuple[int, int, str]] = {
    "unbound": (170, 8, ""),
    "nsd": (201, 8, ""),
    "knot": (397, 7, ""),
    "kresd": (220, 5, ""),
    "opendnssec": (219, 6, ""),
    "bind9": (254, 9, "e0cb29de"),
    "pdns-auth": (261, 7, "26dbf70b"),
    "pdns-rec": (144, 9, ""),
}
GAPS_SHOWN = 6
CLIP = 240

LESSONS = """\
## What verification established that downstream must respect

- **Release date = commit date of `<tag>^{commit}`.** Tag-object dates from CVS/SVN imports
  are migration days (Unbound before 1.6.3, old NSD and BIND tags; BIND tagger dates are
  all 2023-03-16).
- **Order same-day tags by UTC instant, never by offset strings.** bind9 picked the later
  of two same-day patch releases for six CVEs until Phase 3 compared UTC instants.
- **Some tags are lies.** Unbound has five bare re-tags (trees identical to the predecessor)
  and mis-imported 1.3.4 / 1.8.2 / 1.8.3. NSD has fifteen manufactured 1.x/2.x tags, and
  NSD_2_3_0_REL does not contain its own default-change commit. BIND tags up to 2012-02 are
  cvs2git-manufactured, so `git tag --contains` over-reports; verify by tree content.
  PowerDNS Recursor rec-3.1.7.2 has the same tree as rec-3.1.7.1. Each such row carries a note.
- **Branch point releases ship fixes under different commits than master**, and often never
  touch the changelog. The NVD-derived inventory named the next master release in most
  disagreements. `cve_inventory.json` carries two correction batches (9cd7b41d: six rows;
  52290c82: 82 bind9 and pdns-auth rows), each row with `correction` and the old value.
- **Embargoed security releases are tagged days before announcement.** `latency_days` uses
  the tag commit date for every program; where a public date is known it is stored beside it
  (pdns-auth `latency_days_public`, pdns-rec `fix_changelog_released_text`).
- **A default change must touch product code.** A changed test fixture reads identically in
  a log; every default row names the file.
- **Pre-release-pinned defaults carry a separate stable tag** (bind9 `first_stable_tag`,
  OpenDNSSEC `first_stable_tag`, pdns-auth `stable_tag`, whose row `released` is the first
  pre-release date). Release-event analysis must use the stable release; the field mapping
  per program is in `04_phase4_brief.md`.
- **Some stable tags were never released publicly.** PowerDNS Recursor rec-4.5.0, rec-4.5.3
  and rec-5.0.0 were tagged but never shipped; rows citing them carry `first_public_tag` /
  `first_public_released`. Use the public release for deployment timing.
- **`total_entries` is not comparable across programs.** bind9 de-duplicates across
  branches; pdns-auth counts prose paragraphs.
"""


def clip(s: str, n: int = CLIP) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 3] + "..."


def load(p: str) -> dict:
    return json.loads((TL / f"{p}.json").read_text(encoding="utf-8"))


def stage(d: dict) -> str:
    return "complete" if d.get("default_changes") or d.get("cve_fixes") else "release list only"


def build() -> str:
    progs = [p for p in ORDER if (TL / f"{p}.json").exists()]
    data = {p: load(p) for p in progs}
    out = [
        "# Phase 2 handoff: the eight program timelines",
        "",
        f"Generated {date.today().isoformat()} by `scripts/build_timeline_index.py` from "
        "`data/software/timelines/*.json`. For an agent with no other context: what exists for "
        "each program and whether it survived adversarial verification. Schema and standards: "
        "`00_phase1_brief.md`; verification method: `02_phase3_verify_brief.md`; reports: "
        "`verify/<program>.md`.",
        "",
        "## State",
        "",
        "| program | key | role | releases | span | kept changelog entries | default changes | CVE rows | stage | verification |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for p in progs:
        d = data[p]
        rel = d["releases"]
        n_st = sum(1 for r in rel if r.get("stable"))
        dates = sorted(r["released"] for r in rel if r.get("released"))
        entries = sum(len(r.get("changelog_entries") or []) for r in rel)
        v = VERIFIED.get(p)
        vtxt = (f"verified + corrected ({v[0]} checks, {v[1]} correction items"
                + (f", {v[2]}" if v[2] else "") + ")") if v else "NOT verified"
        out.append(
            f"| {NAMES[p]} | `{p}` | {clip(d.get('role', ''), 90)} | {len(rel)} ({n_st} stable) | "
            f"{dates[0]} .. {dates[-1]} | {entries} | {len(d.get('default_changes') or [])} | "
            f"{len(d.get('cve_fixes') or [])} | {stage(d)} | {vtxt} |"
        )
    done = [p for p in progs if p in VERIFIED]
    todo = [p for p in progs if p not in VERIFIED]
    out += ["", f"{len(done)} of {len(progs)} timelines are complete and verified: every default-change "
            "and CVE row was re-derived from the bare clone by a fresh agent, and corrections were "
            "applied by the session in a pass that asserts each pre-change value and writes nothing "
            "on failure."
            + (f" Not yet verified: {', '.join(todo)}." if todo else ""), "", LESSONS, "## Per program", ""]
    for p in progs:
        d = data[p]
        rep = ROOT / "docs" / "handoff" / "verify" / f"{p}.md"
        files = f"`data/software/timelines/{p}.json`, `.md`" + (
            f"; verify report `docs/handoff/verify/{p}.md`" if rep.exists() else "")
        gaps = d.get("gaps") or []
        out += [f"### {NAMES[p]} (`{p}`)", "", f"Files: {files}",
                f"Branch note: {clip(d.get('branch_note', ''), 400)}", "", "Gaps:"]
        for g in gaps[:GAPS_SHOWN]:
            out.append(f"  - {clip(g if isinstance(g, str) else json.dumps(g))}")
        if len(gaps) > GAPS_SHOWN:
            out.append(f"  - ... {len(gaps) - GAPS_SHOWN} more in the JSON")
        out.append("")
    out += ["## Not yet done", ""]
    if todo:
        out.append(f"- Phase 3 verification and corrections for: {', '.join(todo)}.")
    out.append("- Phase 4 onward per `RESUME.md`.")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
