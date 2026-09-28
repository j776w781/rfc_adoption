"""DNSSEC prevalence per month, per corpus, with every denominator stated.

Three metrics were asked for: the share of unique domains in a month that
carry at least one DS, at least one DNSKEY, at least one RRSIG. What each one
can honestly mean differs by corpus, and the definitions below are the whole
point of this script -- change one and the number changes meaning.

Inputs
------
``out/server_run/timeline_monthly.parquet``
    basis ``reverse``  -- five RIR in-addr.arpa zone files (afrinic, apnic,
    arin, lacnic, ripe), one snapshot day per month (``measured_days`` == 1).
    The only DNSSEC record in a parent zone file is the DS, so DNSKEY and
    RRSIG prevalence are **not observable** here and no row is emitted.
    basis ``zonefile`` -- seven OpenINTEL TLD corpora (se, nu, ch, li, ee,
    gov, fed.us), daily measurements folded into months over NAMES.
``out/panel_run/timeline_monthly.parquet``
    ``_pooled-afrinic-arin`` -- the strict two-RIR reverse panel the project
    uses for headline shares, plus its afrinic / arin components.
``data/external/secspider/secspider_wayback_snapshots.csv`` (optional)
    SecSpider "Monitoring Summary" counts scraped from Wayback captures by
    ``scripts/fetch_secspider_wayback.py``.

Column semantics (from ``openintel_rfc.timeline_extract.merge_checkpoints``)
    ``domains_peak`` = the largest single-day distinct-domain count in the
    month. It is a lower bound on the month's distinct count; the per-day
    checkpoints carry no identities to union. Every count below is a
    ``domains_peak``. For the reverse basis measured_days == 1, so it is
    simply the snapshot count.

Denominator rules (pinned by tests/test_prevalence_metrics.py)
    reverse : unique domains = dimension ``all`` (every delegation in the
              zone file); signed = ``algorithm_ds`` ``_total`` (delegations
              with >= 1 DS). Identical to ``rr_type DS`` in every month.
    forward : unique domains = ``rr_type NS`` (names with an NS RRset = the
              delegated zones). NEVER ``rr_type _total`` -- that is every
              measured name (www., mail., ...), 1.4-3.5x the zone count
              (mean 2.3x; .se 2.7x).
              DS       = ``rr_type DS``            (names with >= 1 DS; DS only
                         exists at a delegation point, so these are zones)
              DNSKEY   = ``algorithm_dnskey _total`` (names with >= 1 DNSKEY;
                         identical to ``rr_type DNSKEY`` in every month)
              RRSIG    = ``rr_type RRSIG`` counts NAMES, and every name in a
                         signed zone carries RRSIGs, so it exceeds the zone
                         count. It is reported as a share of measured names.
                         The zone-level proxy is ``rrsig_type_covered DNSKEY``:
                         a name carrying an RRSIG over its DNSKEY RRset is a
                         signed apex. It agrees with the DNSKEY count to within
                         0.5 % in every month of every TLD.

Outputs
-------
``out/analysis/prevalence_metrics.csv``  long: corpus, source, month, metric,
                                          numerator, denominator, pct, measured_days
``out/analysis/prevalence_metrics.json`` definitions, coverage, gaps, headline
                                          (latest month per source), SecSpider.

Usage: python scripts/prevalence_metrics.py [--server out/server_run/timeline_monthly.parquet]
           [--panel out/panel_run/timeline_monthly.parquet] [--secspider data/external/secspider]
           [--out out/analysis]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "out/server_run/timeline_monthly.parquet"
PANEL = ROOT / "out/panel_run/timeline_monthly.parquet"
SECSPIDER_DIR = ROOT / "data/external/secspider"
OUT = ROOT / "out/analysis"

REVERSE_SOURCES = ["afrinic", "apnic", "arin", "lacnic", "ripe"]
PANEL_SOURCE = "_pooled-afrinic-arin"
FORWARD_SOURCES = ["se", "nu", "ch", "li", "ee", "gov", "fed.us"]

# (metric, numerator (dimension, value), denominator (dimension, value))
# A selector is applied to the source's monthly rows; the count is domains_peak.
REVERSE_METRICS = {
    "ds_share": (("algorithm_ds", "_total"), ("all", "all")),
}
FORWARD_METRICS = {
    "ds_share": (("rr_type", "DS"), ("rr_type", "NS")),
    "dnskey_share": (("algorithm_dnskey", "_total"), ("rr_type", "NS")),
    "rrsig_zone_share": (("rrsig_type_covered", "DNSKEY"), ("rr_type", "NS")),
    "rrsig_names_share": (("rr_type", "RRSIG"), ("rr_type", "_total")),
}
# Domain-level metrics: their denominator must be a domain count, never _total.
DOMAIN_LEVEL_FORWARD = ("ds_share", "dnskey_share", "rrsig_zone_share")

DEFINITIONS = {
    "reverse": {
        "unit": "delegations in the RIR's in-addr.arpa zone file (one snapshot day per month)",
        "ds_share": {
            "numerator": "domains_peak of dimension=algorithm_ds value=_total: delegations with at least one DS record in the parent zone file",
            "denominator": "domains_peak of dimension=all: every delegation in the zone file that month",
            "missing_numerator_row": "counted as 0 signed (the month's snapshot had no DS at all)",
        },
        "dnskey_share": {"status": "not observable", "why": "an in-addr.arpa zone file holds only the parent-side delegation (NS, DS, glue); DNSKEY lives in the child zone and was not measured"},
        "rrsig_share": {"status": "not observable", "why": "same: RRSIGs are child-side data; the RIR zone files carry only the DS"},
    },
    "reverse_panel": {
        "unit": "delegations, strict two-RIR panel (afrinic + arin) built for share statements; same rules as reverse",
        "ds_share": {
            "numerator": "domains_peak of dimension=algorithm_ds value=_total",
            "denominator": "domains_peak of dimension=all",
        },
        "dnskey_share": {"status": "not observable"},
        "rrsig_share": {"status": "not observable"},
    },
    "forward": {
        "unit": "delegated zones in the TLD (names with an NS RRset), peak single day in the month, from OpenINTEL daily measurements of the TLD zone file's names",
        "ds_share": {
            "numerator": "domains_peak of rr_type=DS: names with at least one DS. DS exists only at a delegation point, so these are delegated zones",
            "denominator": "domains_peak of rr_type=NS: names with an NS RRset = delegated zones in the TLD",
        },
        "dnskey_share": {
            "numerator": "domains_peak of algorithm_dnskey=_total: names answering with at least one DNSKEY (a zone apex serving keys). Equals rr_type=DNSKEY in every month",
            "denominator": "domains_peak of rr_type=NS",
        },
        "rrsig_zone_share": {
            "numerator": "domains_peak of rrsig_type_covered=DNSKEY: names carrying an RRSIG whose type-covered field is DNSKEY. Only a signed zone apex has one, so this is 'zones with an RRSIG' at zone level. Within 0.5% of the DNSKEY count in every TLD-month",
            "denominator": "domains_peak of rr_type=NS",
            "note": "the justified zone-level proxy for 'domains with at least one RRSIG'",
        },
        "rrsig_names_share": {
            "numerator": "domains_peak of rr_type=RRSIG: NAMES (apex and subnames such as www.) with at least one RRSIG of any type. Every name inside a signed zone carries RRSIGs, so this exceeds the zone count (e.g. se 2023-12: 2,571,213 names vs 1,339,712 zones)",
            "denominator": "domains_peak of rr_type=_total: every NAME OpenINTEL measured that month. This is a name count and is NOT a domain count; it is used only for this name-level metric",
            "note": "name-level share, reported because the raw RRSIG column counts names; use rrsig_zone_share for a zone statement",
        },
        "excluded_from_headline": {"fed.us": "1-2 delegated zones, no DS or DNSKEY ever observed; kept in the CSV, excluded from charts"},
    },
    "secspider": {
        "unit": "zones SecSpider tracks (crawled + user-submitted + NSEC-walked), as printed in its Monitoring Summary at capture time",
        "dnssec_enabled_share": {
            "numerator": "'DNSSEC enabled zones': zones whose online nameservers all pass SecSpider's checks (EDNS0, RRSIG with DO bit, RRSIG matches served DNSKEY, no apex CNAME, NSEC/NSEC3 for nonexistent names)",
            "denominator": "'Zones': every zone in SecSpider's tracked set. That set is assembled by looking for DNSSEC (submissions, crawling, NSEC walking), so it over-represents signed zones; the share is NOT a prevalence over the DNS",
        },
        "dnssec_verified_share": {"numerator": "'DNSSEC verified zones' (verifiable from SecSpider's trust anchors / parent DS)", "denominator": "'Zones'"},
        "production_share": {"numerator": "'Production DNSSEC-enabled zones' (SecSpider's stricter production criterion)", "denominator": "'Zones'"},
        "sampling": "one Wayback capture per month where one exists; when two hosts were captured in the same month the newer host wins (secspider.net > verisignlabs > ucla). Dropped captures: no summary block, the 2007-08 outage page, frozen pages (counts identical to the host's previous capture), and internally inconsistent pages (a numerator above 'Zones'). Months without a usable capture are absent, not interpolated; 'month' is the capture month (the page's own 'as of' date can lag it by weeks on the UCLA host)",
    },
}


def _count(rows: pd.DataFrame, dim: str, val: str) -> pd.Series:
    """domains_peak per (source, month) for one (dimension, value) selector."""
    sel = rows[(rows.dimension == dim) & (rows.value == val)]
    return sel.groupby(["source", "month"]).domains_peak.max()


def compute_corpus(rows: pd.DataFrame, corpus: str, metrics: dict) -> pd.DataFrame:
    """Long-format rows for one corpus. The denominator row must exist; a missing
    numerator row is 0 (the month had no record of that kind)."""
    days = rows.groupby(["source", "month"]).measured_days.max()
    out = []
    for metric, (num_sel, den_sel) in metrics.items():
        den = _count(rows, *den_sel)
        num = _count(rows, *num_sel).reindex(den.index).fillna(0)
        frame = pd.DataFrame({"numerator": num.astype(int), "denominator": den.astype(int)})
        frame["pct"] = (frame.numerator / frame.denominator * 100).round(4)
        frame["measured_days"] = days.reindex(frame.index).astype(int)
        frame["metric"] = metric
        frame["corpus"] = corpus
        out.append(frame.reset_index())
    res = pd.concat(out, ignore_index=True)
    return res[["corpus", "source", "month", "metric", "numerator", "denominator", "pct", "measured_days"]]


def load_reverse(server: Path) -> pd.DataFrame:
    df = pd.read_parquet(server)
    return df[(df.basis == "reverse") & (df.source.isin(REVERSE_SOURCES))]


def load_forward(server: Path) -> pd.DataFrame:
    df = pd.read_parquet(server)
    return df[(df.basis == "zonefile") & (df.source.isin(FORWARD_SOURCES))]


def load_panel(panel: Path) -> pd.DataFrame:
    df = pd.read_parquet(panel)
    return df[df.basis == "reverse"]


# SecSpider moved hosts twice; where two hosts were captured in the same month the
# newer host is authoritative (the UCLA page went stale in 2012 while Verisign
# Labs served the live crawler: 42k vs 68k zones in 2012-02).
SECSPIDER_HOST_RANK = {"secspider.cs.ucla.edu": 1, "secspider.verisignlabs.com": 2, "secspider.net": 3}


SECSPIDER_COUNTS = ["zones_tracked", "dnssec_enabled_zones", "dnssec_verified_zones", "production_dnssec_zones"]


def secspider_usable(snap: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Split the snapshot table into usable captures and a tally of the dropped.

    Dropped, in this order, each for a stated reason:
      no_counts     the capture has no Monitoring Summary block (landing pages,
                    truncated captures);
      outage        the page carried an outage banner and printed zeros
                    (UCLA 2007-08-10: 1849 zones, 0 enabled);
      frozen        the four counts are identical to the same host's previous
                    capture: the page was not being regenerated (Verisign Labs
                    served 42,084 zones unchanged from 2012-01 to 2012-10 while
                    the UCLA page's own "as of" date kept moving), so a repeat
                    is the same observation, not a new month;
      inconsistent  a numerator exceeds "Zones" (secspider.net 2021-12-06:
                    960,264 zones but 1,135,208 production zones, during what
                    looks like a rebuild of its database).
    """
    snap = snap.copy()
    if "page_notice" not in snap.columns:
        snap["page_notice"] = ""
    dropped = {"no_counts": int((snap.zones_tracked == "").sum())}
    snap = snap[snap.zones_tracked != ""]
    dropped["outage"] = int((snap.page_notice != "").sum())
    snap = snap[snap.page_notice == ""].copy()
    for c in SECSPIDER_COUNTS:
        snap[c] = pd.to_numeric(snap[c], errors="coerce")
    snap = snap.sort_values("capture_ts")
    key = snap[SECSPIDER_COUNTS].fillna(-1)
    frozen = key.eq(key.groupby(snap.host).shift()).all(axis=1)
    dropped["frozen"] = int(frozen.sum())
    snap = snap[~frozen]
    num_max = snap[SECSPIDER_COUNTS[1:]].max(axis=1)
    inconsistent = num_max > snap.zones_tracked
    dropped["inconsistent"] = int(inconsistent.sum())
    return snap[~inconsistent], dropped


def secspider_monthly(csv_path: Path) -> pd.DataFrame:
    """Same long shape from the SecSpider snapshot CSV: one row per month. Within
    a month the newest host's latest usable capture wins (see secspider_usable)."""
    snap, _ = secspider_usable(pd.read_csv(csv_path, dtype=str).fillna(""))
    snap["_rank"] = snap.host.map(SECSPIDER_HOST_RANK).fillna(0)
    snap = snap.sort_values(["_rank", "capture_ts"]).groupby("month").tail(1).set_index("month")
    out = []
    for metric, col in [("dnssec_enabled_share", "dnssec_enabled_zones"),
                        ("dnssec_verified_share", "dnssec_verified_zones"),
                        ("production_share", "production_dnssec_zones")]:
        s = snap[snap[col].notna()]
        frame = pd.DataFrame({
            "corpus": "secspider", "source": s.host, "month": s.index,
            "metric": metric, "numerator": s[col].astype(int),
            "denominator": s.zones_tracked.astype(int),
        })
        frame["pct"] = (frame.numerator / frame.denominator * 100).round(4)
        frame["measured_days"] = 1
        out.append(frame.reset_index(drop=True))
    return pd.concat(out, ignore_index=True)


def month_gaps(months: list[str]) -> list[str]:
    """Calendar months missing between the first and last observed month."""
    if not months:
        return []
    full = pd.period_range(months[0], months[-1], freq="M").strftime("%Y-%m")
    have = set(months)
    return [m for m in full if m not in have]


def coverage(long: pd.DataFrame) -> dict:
    cov: dict = {}
    for (corpus, source), g in long.groupby(["corpus", "source"]):
        months = sorted(g.month.unique())
        cov.setdefault(corpus, {})[source] = {
            "first": months[0], "last": months[-1], "months": len(months),
            "gap_months": month_gaps(months),
            "metrics": sorted(g.metric.unique()),
        }
    return cov


def headline(long: pd.DataFrame) -> dict:
    head: dict = {}
    for (corpus, source, metric), g in long.groupby(["corpus", "source", "metric"]):
        last = g.sort_values("month").iloc[-1]
        head.setdefault(corpus, {}).setdefault(source, {})[metric] = {
            "month": last.month, "numerator": int(last.numerator),
            "denominator": int(last.denominator), "pct": float(last.pct),
        }
    return head


def build(server: Path = SERVER, panel: Path = PANEL, secspider_dir: Path = SECSPIDER_DIR) -> tuple[pd.DataFrame, dict]:
    parts = [
        compute_corpus(load_reverse(server), "reverse", REVERSE_METRICS),
        compute_corpus(load_panel(panel), "reverse_panel", REVERSE_METRICS),
        compute_corpus(load_forward(server), "forward", FORWARD_METRICS),
    ]
    sec_status: dict = {"status": "not available", "path": str(secspider_dir / "secspider_wayback_snapshots.csv")}
    csv_path = secspider_dir / "secspider_wayback_snapshots.csv"
    if csv_path.exists():
        sec = secspider_monthly(csv_path)
        parts.append(sec)
        snap = pd.read_csv(csv_path, dtype=str).fillna("")
        usable, dropped = secspider_usable(snap)
        sec_status = {
            "status": "available",
            "path": str(csv_path.relative_to(ROOT)),
            "captures": int(len(snap)),
            "captures_usable": int(len(usable)),
            "captures_dropped": dropped,
            "months": int(sec.month.nunique()),
            "first_month": sec.month.min(), "last_month": sec.month.max(),
            "hosts": sorted(snap.host.unique().tolist()),
            "readme": "data/external/secspider/README.md",
        }
    long = pd.concat(parts, ignore_index=True).sort_values(["corpus", "source", "metric", "month"]).reset_index(drop=True)
    meta = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "inputs": {"server": str(server.relative_to(ROOT)) if server.is_relative_to(ROOT) else str(server),
                   "panel": str(panel.relative_to(ROOT)) if panel.is_relative_to(ROOT) else str(panel)},
        "count_column": "domains_peak (largest single-day distinct count in the month; == snapshot count for reverse where measured_days == 1)",
        "definitions": DEFINITIONS,
        "selectors": {
            "reverse": {m: {"numerator": list(n), "denominator": list(d)} for m, (n, d) in REVERSE_METRICS.items()},
            "reverse_panel": {m: {"numerator": list(n), "denominator": list(d)} for m, (n, d) in REVERSE_METRICS.items()},
            "forward": {m: {"numerator": list(n), "denominator": list(d)} for m, (n, d) in FORWARD_METRICS.items()},
        },
        "not_observable": [
            {"corpus": "reverse", "metric": "dnskey_share", "why": DEFINITIONS["reverse"]["dnskey_share"]["why"]},
            {"corpus": "reverse", "metric": "rrsig_share", "why": DEFINITIONS["reverse"]["rrsig_share"]["why"]},
            {"corpus": "reverse_panel", "metric": "dnskey_share", "why": "same as reverse"},
            {"corpus": "reverse_panel", "metric": "rrsig_share", "why": "same as reverse"},
        ],
        "coverage": coverage(long),
        "headline": headline(long),
        "secspider": sec_status,
        "rows": int(len(long)),
    }
    return long, meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", type=Path, default=SERVER)
    ap.add_argument("--panel", type=Path, default=PANEL)
    ap.add_argument("--secspider", type=Path, default=SECSPIDER_DIR)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    long, meta = build(args.server, args.panel, args.secspider)
    args.out.mkdir(parents=True, exist_ok=True)
    long.to_csv(args.out / "prevalence_metrics.csv", index=False)
    (args.out / "prevalence_metrics.json").write_text(json.dumps(meta, indent=2))
    print(f"wrote {args.out / 'prevalence_metrics.csv'} ({len(long)} rows)")
    print(f"wrote {args.out / 'prevalence_metrics.json'}")
    for corpus, srcs in meta["headline"].items():
        for source, mets in srcs.items():
            bits = ", ".join(f"{m}={v['pct']:.2f}% ({v['numerator']:,}/{v['denominator']:,} @ {v['month']})" for m, v in mets.items())
            print(f"  {corpus:14s} {source:22s} {bits}")
    print(f"  secspider: {meta['secspider']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
