"""Chart: what each RFC publication and each CVE patch did to its OWN
mechanism's adoption curve, as a percentile among all months of that curve.

One row per event month; the dot is where the four-month window after the
event ranks among every month of the same series (0 = the most negative
month that series ever had, 100 = the most positive). The grey band is the
middle half of ordinary months.

Reads the same inputs as scripts/cve_vs_rfc_rates.py.
Writes reporting/charts/cve_vs_rfc_mechanism.png and
out/analysis/dns_cve_vs_rfc_mechanism_events.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cve_vs_rfc_rates as M  # noqa: E402

SURFACE, INK, INK_2, MUTED, BASELINE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7", "#e1e0d9"
S3, CRITICAL = "#1baf7a", "#d03b3b"
plt.rcParams.update({"font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE, "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": MUTED,
                     "ytick.color": INK, "axes.edgecolor": BASELINE, "figure.dpi": 120})
MECH_NAME = {"NSEC3": "NSEC3 share", "ECDSA/EdDSA": "ECDSA / EdDSA share"}
CORPUS = {"forward": "OpenINTEL", "reverse panel": "reverse DNS"}


def events_table():
    cases = json.loads(Path("out/analysis/program_rfc_cases.json").read_text("utf-8"))["cases"]
    cves = json.loads(Path("out/analysis/cve_crossref.json").read_text("utf-8"))
    rc = json.loads(Path("reporting/rfc_classification.json").read_text("utf-8"))
    ev_cve, ev_rfc = M.cve_events(cves), M.rfc_events(rc)
    mech_of = {"nsec3": "NSEC3", "algorithm": "ECDSA/EdDSA"}
    rows = []
    for mech, spec in M.MECH.items():
        f_rate, r_rate = M.mechanism_series(cases, spec["case"])
        for corpus, rate in (("forward", f_rate), ("reverse panel", r_rate)):
            if rate.empty:
                continue
            base = pd.Series({m: M.windowed(rate, m) for m in rate.index}).dropna()
            evs = [e for e in ev_rfc if e["event"] in spec["rfcs"]] + [e for e in ev_cve if mech_of.get(e["mechanism"]) == mech]
            grouped = {}
            for e in evs:
                if e["month"] in base.index:
                    grouped.setdefault((e["kind"], e["month"]), []).append(e["event"])
            for (kind, month), names in grouped.items():
                v = float(base[month])
                rows.append({"mechanism": mech, "corpus": corpus, "kind": kind, "month": month,
                             "event": names[0] if len(names) == 1 else names[0] + f" +{len(names)-1} more",
                             "events": ", ".join(names), "rate_window_pp": round(v, 3),
                             "series_median_pp": round(float(base.median()), 3),
                             "percentile": round(float((base < v).mean() * 100), 1)})
    df = pd.DataFrame(rows).sort_values(["mechanism", "corpus", "month"]).reset_index(drop=True)
    return df


def main() -> int:
    df = events_table()
    df.to_csv("out/analysis/dns_cve_vs_rfc_mechanism_events.csv", index=False)
    order = ["ECDSA/EdDSA", "NSEC3"]
    df["mk"] = df.mechanism.map(order.index)
    df = df.sort_values(["mk", "corpus", "month"]).reset_index(drop=True)
    n = len(df)
    fig, ax = plt.subplots(figsize=(12.5, 0.5 * n + 2.6))
    ax.axvspan(25, 75, color=GRID, alpha=0.6, zorder=0)
    for x, t in ((10, "unusually\nnegative"), (90, "unusually\npositive")):
        ax.axvline(x, color=BASELINE, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.text(50, n - 0.3, "ordinary months (middle half)", ha="center", va="bottom", fontsize=9, color=INK_2)
    ax.text(10, n - 0.3, "unusually negative", ha="center", va="bottom", fontsize=9, color=INK_2)
    ax.text(90, n - 0.3, "unusually positive", ha="center", va="bottom", fontsize=9, color=INK_2)
    labels = []
    ymap = {}
    y = n - 1
    prev = None
    for i, r in df.iterrows():
        key = (r.mechanism, r.corpus)
        if key != prev and prev is not None:
            ax.axhline(y + 0.5, color=BASELINE, linewidth=0.8)
        prev = key
        col = CRITICAL if r.kind == "cve_patch" else S3
        ax.plot([0, r.percentile], [y, y], color=col, linewidth=1.2, alpha=0.5, zorder=2)
        ax.plot(r.percentile, y, marker="o", ms=11, color=col, mec=SURFACE, mew=1.4, zorder=3, ls="none")
        ax.annotate(f'{r.rate_window_pp:+.2f} pp/mo', (r.percentile, y), (0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color=INK_2)
        what = ("patched" if r.kind == "cve_patch" else "published")
        labels.append(f'{r.event}  {what} {r.month}\n{MECH_NAME[r.mechanism]}, {CORPUS[r.corpus]}')
        ymap[i] = y
        y -= 1
    ax.set_yticks([ymap[i] for i in df.index])
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-0.7, n + 0.6)
    ax.set_xlabel("where the 4 months after the event rank among all months of that mechanism's own adoption curve (percentile)", fontsize=9.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", color=S3, ls="none", ms=9, label="RFC published"),
                       Line2D([], [], marker="o", color=CRITICAL, ls="none", ms=9, label="CVE patched")],
              loc="lower right", fontsize=9, frameon=False)
    h = 0.5 * n + 2.6
    fig.suptitle("On its own mechanism: RFC publications sit in ordinary or dead months; two CVE patch months are extreme",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold", y=1 - 0.12 / h)
    fig.text(0.01, 1 - 0.42 / h, "Each row is an event month. The dot is how that mechanism's adoption moved in the event month and the three after it,",
             fontsize=9, color=INK_2)
    fig.text(0.01, 1 - 0.60 / h, "ranked against every month of the same curve. Only events inside each corpus's coverage appear.",
             fontsize=9, color=INK_2)
    fig.subplots_adjust(left=0.36, right=0.98, top=1 - 1.0 / h, bottom=0.9 / h)
    fig.savefig("reporting/charts/cve_vs_rfc_mechanism.png", dpi=150)
    print(df[["mechanism", "corpus", "kind", "event", "month", "rate_window_pp", "percentile"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
