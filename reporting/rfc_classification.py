"""One table saying, for every DNSSEC RFC in the checklist, what we can know.

The pipeline already answers this per *indicator*: `schema-check` classifies each
one queryable / partially queryable / ambiguous / non-queryable and writes the
reason it decided that. What was missing was the roll-up -- the per-RFC view a
person actually reads before trusting a number.

Three axes, kept separate on purpose because they answer different questions:

``signal_type``   what a match *means*
    ``adoption`` the mechanism is deployed; ``non_conformance`` a deprecated
    mechanism is still present (a match is bad news); ``meta`` the document
    defines a process or resolver behaviour, so nothing in a zone file bears on
    it either way.

``queryability``  whether this corpus can answer it at all
    Rolled up from the indicators: an RFC is measurable if at least one required
    indicator is queryable, and unmeasurable when none are.

``observable_from``  the earliest date an answer could exist
    An RFC published before the fields its indicators need is left-censored, and
    a first-seen date from this corpus is a bound rather than a measurement. That
    is a property of the corpus, not of the RFC, and it is why the same RFC can be
    measurable and still not datable.

Reads `schema_check.json` and the checklist; writes Markdown, CSV and JSON.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

CHECK = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_output/schema_check.json")
CHECKLIST = Path(sys.argv[2] if len(sys.argv) > 2
                 else "data/rfc_checklists/dnssec_rfc_checklists.json")
OUT = Path(sys.argv[3] if len(sys.argv) > 3 else "reporting")

check = json.loads(CHECK.read_text(encoding="utf-8"))
db = json.loads(CHECKLIST.read_text(encoding="utf-8"))

by_rfc: dict[str, list[dict]] = {}
for row in check["indicators"]:
    by_rfc.setdefault(row["rfc_id"], []).append(row)

#: Worst-to-best, so an RFC is summarised by its strongest evidence.
RANK = {"non_queryable": 0, "ambiguous": 1, "partially_queryable": 2, "queryable": 3}
LABEL = {
    3: "measurable",
    2: "partly measurable",
    1: "ambiguous only",
    0: "not measurable here",
}

rows = []
for entry in sorted(db["rfcs"], key=lambda r: int(r["rfc_id"].split()[1])):
    rfc_id = entry["rfc_id"]
    inds = by_rfc.get(rfc_id, [])
    required = [i for i in inds if i["required"]]
    # An RFC stands on its required indicators: an optional one being queryable
    # does not make the RFC attributable on its own.
    basis = required or inds
    best = max((RANK[i["queryability"]] for i in basis), default=0)

    # Earliest date every field of the best required indicator is available.
    available = ""
    for i in basis:
        if RANK[i["queryability"]] != best:
            continue
        dates = [c.get("available_from") for c in i["condition_checks"]
                 if c.get("available_from")]
        if dates:
            available = max(available, max(d[:10] for d in dates))

    published = entry["publication_date"][:10]
    censored = bool(available) and available > published

    reason = next((i["reasoning"] for i in basis
                   if RANK[i["queryability"]] == best), "no indicators defined")

    # The schema checker's reason is mechanical ("this field is not in the
    # dictionary"). The checklist's own note is where the *why* lives -- whether a
    # field is missing because the corpus cannot carry it, because the RFC defines
    # nothing observable, or because the indicator model cannot express the test.
    # A reader needs the second one, so carry both.
    rows.append({
        "rfc_id": rfc_id,
        "title": entry["title"],
        "published": published,
        "status": entry.get("status", ""),
        "obsoleted_by": ", ".join(entry.get("obsoleted_by", [])),
        "signal_type": entry.get("signal_type", "adoption"),
        "specificity": entry["specificity"],
        "verdict": LABEL[best],
        "indicators": len(inds),
        "required_indicators": len(required),
        "observable_from": available,
        "left_censored": censored,
        "reason": " ".join(reason.split()),
        "note": " ".join((entry.get("notes") or "").split()),
    })

OUT.mkdir(parents=True, exist_ok=True)

(OUT / "rfc_classification.json").write_text(
    json.dumps({
        "checklist_version": db["checklist_version"],
        "dictionary_fields": check["dictionary_field_count"],
        "rfc_count": len(rows),
        "counts_by_verdict": dict(Counter(r["verdict"] for r in rows)),
        "counts_by_signal_type": dict(Counter(r["signal_type"] for r in rows)),
        "rfcs": rows,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")

with open(OUT / "rfc_classification.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

# ----------------------------------------------------------------- Markdown --
lines = [
    "# DNSSEC RFC classification",
    "",
    f"Checklist `{db['checklist_version']}` against a dictionary of "
    f"{check['dictionary_field_count']} fields: **{len(rows)} RFCs, "
    f"{check['indicator_count']} indicators**.",
    "",
    "`signal_type` is what a match means. `verdict` is whether this corpus can "
    "answer it. They are independent: an RFC can be perfectly well specified and "
    "still unmeasurable here.",
    "",
]

for signal, heading, blurb in (
    ("adoption", "Adoption signals",
     "A match means the mechanism is deployed."),
    ("non_conformance", "Non-conformance signals",
     "A match means a **deprecated** mechanism is still published. Counting these "
     "as adoption would invert the finding."),
    ("meta", "Process and resolver-side documents",
     "These define a process, an operational practice, or resolver behaviour. "
     "Nothing an authoritative zone publishes can evidence them, so they are "
     "carried for completeness and are expected to be unmeasurable."),
):
    group = [r for r in rows if r["signal_type"] == signal]
    if not group:
        continue
    lines += [f"## {heading}", "", blurb, "",
              "| RFC | Published | Status | Verdict | Observable from | Title |",
              "| --- | --- | --- | --- | --- | --- |"]
    for r in group:
        obs = r["observable_from"] or "—"
        if r["left_censored"]:
            obs += " ⚠"
        obsolete = f" *(obs. by {r['obsoleted_by']})*" if r["obsoleted_by"] else ""
        lines.append(
            f"| {r['rfc_id']} | {r['published']} | {r['status'].title()} | "
            f"{r['verdict']} | {obs} | {r['title'][:64]}{obsolete} |"
        )
    lines.append("")

censored = [r for r in rows if r["left_censored"]]
if censored:
    lines += [
        "## ⚠ Left-censored RFCs", "",
        "Published before the corpus can see the fields their indicators need. A "
        "first-seen date for these is an **upper bound on the lag**, not a "
        "measurement of it.", "",
        "| RFC | Published | Observable from |", "| --- | --- | --- |",
    ]
    for r in censored:
        lines.append(f"| {r['rfc_id']} | {r['published']} | {r['observable_from']} |")
    lines.append("")

lines += ["## Why each verdict was reached", "",
          "The first line under each RFC is the checker's mechanical finding. The "
          "second, where present, is the checklist's own account of *why* — which is "
          "usually the part that matters.", ""]
for r in rows:
    lines += [f"**{r['rfc_id']}** — {r['verdict']}  ", f"{r['reason']}"]
    if r["note"]:
        lines += ["", f"> {r['note']}"]
    lines.append("")

(OUT / "rfc_classification.md").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8", newline="\n")

print(f"{len(rows)} RFCs classified (checklist {db['checklist_version']})")
for verdict, n in Counter(r["verdict"] for r in rows).most_common():
    print(f"  {verdict:22} {n}")
print()
for signal, n in Counter(r["signal_type"] for r in rows).most_common():
    print(f"  signal_type={signal:16} {n}")
print(f"  left-censored          {len(censored)}")
print(f"\nwrote {OUT / 'rfc_classification.md'}, .csv, .json")
