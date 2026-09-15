"""Figures for the per-RFC, per-program case studies.

One figure per RFC, three panels on one time axis:

    programs   -- each program's lane: the release that implements the RFC,
                  the release that made it the default or capped it, the OS
                  packages that first carried that release, and its CVEs
    OpenINTEL  -- share of signed zones carrying the mechanism, per TLD;
                  numbered marks are the spikes in the ledger
    reverse    -- share of signed delegations per RIR, the strict
                  AFRINIC+ARIN panel in black; numbered marks again

and for the algorithm RFCs a second figure: the share of *new* reverse-DNS
signings that chose the algorithm, per quarter, with the default changes and
OS package dates on it. That is the auto-update test.

Reads out/analysis/program_rfc_cases.json, data/software/distro_ships.json.
Writes reporting/charts/cases/<rfc>.png and .../<rfc>_new_signings.png.

    python reporting/program_rfc_cases.py [--bare --out reporting/charts/cases/bare]
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
S1, S2, S3, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
PURPLE, PINK, TEAL, CRITICAL = "#8a5cd6", "#d64f8f", "#1b9fb0", "#d03b3b"
FWD = {"se": S1, "nu": S2, "ch": S3, "li": YELLOW, "ee": PURPLE, "gov": PINK, "fed.us": TEAL}
REV = {"arin": S1, "ripe": S2, "apnic": S3, "lacnic": YELLOW, "afrinic": PURPLE}

plt.rcParams.update({
    "font.family": ["DejaVu Sans", "sans-serif"], "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "text.color": INK,
    "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": BASELINE, "axes.linewidth": 0.8, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "figure.dpi": 120,
})


def yr(m: str) -> float:
    return int(m[:4]) + (int(m[5:7]) - 1) / 12.0 + (int(m[8:10]) - 1) / 365.0 if len(m) >= 10 \
        else int(m[:4]) + (int(m[5:7]) - 1) / 12.0


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def year_axis(ax, lo, hi):
    ax.set_xlim(lo, hi)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=12))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))


def vcmp(a: str) -> tuple:
    a = a.split(":")[-1].split("~")[0].split("+")[0].split("-")[0]
    out = []
    for p in a.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out + [0] * (4 - len(out)))


def first_ships(distro, program, version):
    """OS releases that were the first, per distribution, to carry >= version."""
    hits = {}
    for d in sorted(distro["ships"], key=lambda x: x["released"]):
        v = d["versions"].get(program)
        if v and vcmp(v) >= vcmp(version) and d["distribution"] not in hits:
            hits[d["distribution"]] = d
    return list(hits.values())


# ------------------------------------------------------------- the figure --

def draw(rfc, case, distro, out: Path, bare=False):
    progs = [p for p in case["programs"] if p["key"] != "_unattributed"]
    other = [p for p in case["programs"] if p["key"] == "_unattributed"]
    ship_rows = []   # (program key, distro row, version) for default/support releases
    for p in progs:
        for e in p["events"]:
            if e["kind"] in ("default", "limit", "support") and p["key"] in ("bind9", "knot", "pdns-auth"):
                key = {"pdns-auth": "pdns"}.get(p["key"], p["key"])
                for d in first_ships(distro, key, e["version"]):
                    ship_rows.append((p["key"], d, e))
    # Only the first OS ship per (program, event) family matters: dedupe by distro+event.
    seen, ships = set(), []
    for k, d, e in ship_rows:
        tag = (k, d["name"])              # one tick per OS release per lane
        if tag not in seen:
            seen.add(tag); ships.append((k, d, e))

    lo = min([yr(case["published"]) - 1.0] + [yr(e["date"]) for p in case["programs"] for e in p["events"]]) - 0.3
    hi = 2026.75
    have_rev = bool(case["series"]["reverse"])
    n_lanes = len(progs) + (1 if other else 0)
    heights = [0.55 * n_lanes + 0.6, 3.0] + ([3.0] if have_rev else [])
    fig, axes = plt.subplots(len(heights), 1, figsize=(15, sum(heights) + 1.2),
                             gridspec_kw={"height_ratios": heights, "hspace": 0.32})
    axes = list(axes)
    ax0 = axes[0]

    # --- programs lanes
    lanes = progs + other
    for i, p in enumerate(lanes):
        y = n_lanes - 1 - i
        ax0.axhline(y, color=GRID, linewidth=0.8, zorder=0)
        ax0.text(lo - 0.05, y, p["program"] + ("" if p["role"] == "other" else
                                                 f"  ({p['role']})"),
                 ha="right", va="center", fontsize=10, color=INK_2)
        used = {1: [], -1: []}   # labelled x positions above/below the lane, to stack close ones

        def bump(x, sign):
            k = min(2, sum(1 for u in used[sign] if abs(u - x) < 0.9))
            used[sign].append(x)
            return sign * (9 + 10 * k)

        shown = set()
        for e in p["events"]:
            tag = (e["kind"], e.get("version"), e.get("cve"))
            if tag in shown:          # PowerDNS lists its ZSK and KSK default separately
                continue
            shown.add(tag)
            x = yr(e["date"])
            if e["kind"] == "support":
                ax0.plot(x, y, marker="o", ms=8, color=S2 if p["role"] == "signer" else S1,
                         mec=SURFACE, mew=1.2, zorder=4, ls="none")
                ax0.annotate(e["version"], (x, y), (0, bump(x, 1)), textcoords="offset points",
                             ha="center", fontsize=8.5, color=INK_2)
            elif e["kind"] == "default":
                ax0.plot(x, y, marker="D", ms=9, color=YELLOW, mec=SURFACE, mew=1.2, zorder=5, ls="none")
                ax0.annotate(e["version"] + (" (opt-in)" if e.get("opt_in") else " default"),
                             (x, y), (0, bump(x, 1)), textcoords="offset points", ha="center",
                             fontsize=8.5, color=INK)
            elif e["kind"] == "limit":
                ax0.plot(x, y, marker="s", ms=8, color=YELLOW, mec=SURFACE, mew=1.2, zorder=5, ls="none")
                ax0.annotate(e["version"] + " cap", (x, y), (0, bump(x, 1)), textcoords="offset points",
                             ha="center", fontsize=8.5, color=INK)
            elif e["kind"] == "cve":
                ax0.plot(x, y, marker="x", ms=8, color=CRITICAL, mew=2, zorder=6, ls="none")
                ax0.annotate(e["cve"].replace("CVE-", ""), (x, y), (0, bump(x, -1) - 4),
                             textcoords="offset points", ha="center", fontsize=7.5, color=CRITICAL)
        for k, d, e in ships:
            if k == p["key"]:
                x = yr(d["released"])
                ax0.plot(x, y, marker="|", ms=13, color=INK_2, mew=1.6, zorder=3, ls="none")
                ax0.annotate(d["name"], (x, y), (0, bump(x, -1) - 4), textcoords="offset points",
                             ha="center", fontsize=7.5, color=INK_2)
    ax0.set_ylim(-0.7, n_lanes + 0.15)
    ax0.set_yticks([])
    for s in ("top", "right", "left", "bottom"):
        ax0.spines[s].set_visible(False)
    ax0.tick_params(length=0, labelbottom=False)
    year_axis(ax0, lo, hi)
    ax0.set_title("Programs", loc="left", fontsize=11, color=INK_2, pad=6)

    # --- forward
    ax1 = axes[1]
    unit_f = case["unit"]
    for src, s in case["series"]["forward"].items():
        x = [yr(m) for m in s["months"]]
        yv = s["count"] if case["rfc"] == "RFC 9276" else s["share_pct"]
        ax1.plot(x, yv, color=FWD.get(src, MUTED), linewidth=2, label=f".{src}")
        ax1.annotate(f".{src}", (x[-1], yv[-1] if yv[-1] is not None else 0), (4, 0),
                     textcoords="offset points", va="center", fontsize=9, color=FWD.get(src, MUTED))
    if case["rfc"] == "RFC 9276":
        ax1.set_yscale("log")
        ax1.set_ylabel(f"{unit_f} (log)", fontsize=10)
    else:
        ax1.set_ylabel("% of signed zones", fontsize=10)
        ax1.set_ylim(0, max(1, ax1.get_ylim()[1]))
    style(ax1); year_axis(ax1, lo, hi)
    ax1.set_title("OpenINTEL zone files, per TLD  (coverage 2016-06 to 2023-12; .ch/.li from 2020-05)",
                  loc="left", fontsize=11, color=INK_2, pad=6)

    # --- reverse
    if have_rev:
        ax2 = axes[2]
        for src, s in case["series"]["reverse"].items():
            x = [yr(m) for m in s["months"]]
            ax2.plot(x, s["share_pct"], color=REV.get(src, MUTED), linewidth=1.4, alpha=0.9)
            last = next((v for v in reversed(s["share_pct"]) if v is not None), 0)
            ax2.annotate(src.upper(), (x[-1], last), (4, 0), textcoords="offset points",
                         va="center", fontsize=8.5, color=REV.get(src, MUTED))
        pnl = case["series"].get("reverse_panel")
        if pnl:
            x = [yr(m) for m in pnl["months"]]
            ax2.plot(x, pnl["share_pct"], color=INK, linewidth=2.4, label="strict panel")
            last = next((v for v in reversed(pnl["share_pct"]) if v is not None), 0)
            ax2.annotate("panel", (x[-1], last), (4, 0), textcoords="offset points",
                         va="center", fontsize=9, color=INK, fontweight="bold")
        ax2.set_ylabel("% of signed delegations", fontsize=10)
        ax2.set_ylim(0, max(1, ax2.get_ylim()[1]))
        style(ax2); year_axis(ax2, lo, hi)
        ax2.set_title("Reverse DNS (in-addr.arpa), per RIR; strict AFRINIC+ARIN panel in black"
                      + (f"  --  {case.get('reverse_note', '')}" if case.get("reverse_note") else ""),
                      loc="left", fontsize=11, color=INK_2, pad=6)

    # --- spikes, numbered by size
    ranked = sorted(case["spikes"], key=lambda j: -j["delta"])
    label_n = {j["n"]: i + 1 for i, j in enumerate(ranked[:10])}
    placed = {}
    for j in sorted(case["spikes"], key=lambda j: j["end"]):
        ax = ax1 if j["basis"] == "forward" else (axes[2] if have_rev else None)
        if ax is None:
            continue
        s = case["series"][j["basis"]][j["source"]]
        idx = s["months"].index(j["end"])
        yv = (s["count"] if case["rfc"] == "RFC 9276" else s["share_pct"])[idx]
        if yv is None:
            continue
        x = yr(j["end"])
        if j["n"] in label_n:
            span = ax.get_ylim()[1] - ax.get_ylim()[0]
            near = [q for q in placed.get(id(ax), []) if abs(q[0] - x) < 0.3 and abs(q[1] - yv) < 0.06 * span]
            dy = 14 * len(near)
            placed.setdefault(id(ax), []).append((x, yv))
            ax.annotate(str(label_n[j["n"]]), (x, yv), (0, dy), textcoords="offset points",
                        ha="center", va="center", fontsize=8.5, fontweight="bold", color=INK, zorder=8,
                        bbox=dict(boxstyle="circle,pad=0.25", fc=SURFACE, ec=INK, lw=1.2))
            if dy:
                ax.plot(x, yv, marker="o", ms=5, color=INK, mec=SURFACE, mew=0.8, zorder=6, ls="none")
        else:
            ax.plot(x, yv, marker="o", ms=5, color=INK, mec=SURFACE, mew=0.8, zorder=6, ls="none")

    # --- RFC line through every panel
    xr = yr(case["published"])
    for ax in axes:
        ax.axvline(xr, color=S3, linewidth=1.4, linestyle=(0, (4, 3)), zorder=2)
    ax0.annotate(f'{rfc} published {case["published"]}', (xr, n_lanes + 0.1), (4, 0),
                 textcoords="offset points", fontsize=9.5, color=S3, fontweight="bold", va="center")
    for r in case.get("related_rfcs", []):
        pass

    # legend
    handles = [Line2D([], [], marker="o", color=S2, ls="none", ms=8, label="signer: first release with it"),
               Line2D([], [], marker="o", color=S1, ls="none", ms=8, label="validator: first release with it"),
               Line2D([], [], marker="D", color=YELLOW, ls="none", ms=8, label="release that changed the default"),
               Line2D([], [], marker="s", color=YELLOW, ls="none", ms=8, label="release that capped it (validator limit)"),
               Line2D([], [], marker="|", color=INK_2, ls="none", ms=12, mew=1.6, label="first OS package carrying it"),
               Line2D([], [], marker="x", color=CRITICAL, ls="none", ms=8, mew=2, label="CVE on this mechanism"),
               Line2D([], [], marker="o", color=SURFACE, mec=INK, ls="none", ms=11, label="spike, numbered by size (see ledger)")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0),
               ncol=4, fontsize=8.5, frameon=False, handletextpad=0.4, columnspacing=1.2)
    if not bare:
        fig.suptitle(f"{rfc}: {case['title']}  --  what each program did, and when the corpora moved",
                     x=0.01, ha="left", fontsize=14, fontweight="bold", y=0.995)
    h = sum(heights) + 1.2
    fig.subplots_adjust(left=0.13, right=0.96, top=1 - (0.75 if not bare else 0.35) / h, bottom=0.9 / h)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def draw_new_signings(rfc, case, distro, out: Path, bare=False):
    ns = case.get("new_signings")
    if not ns:
        return False
    q = pd.DataFrame(ns["quarterly"])
    q = q[q.n >= 20]
    x = [int(s[:4]) + (int(s[-1]) - 1) / 4.0 + 0.125 for s in q.q]
    fig, ax = plt.subplots(figsize=(15, 4.6))
    ax.plot(x, q.share_pct, color=S1, linewidth=2.2)
    ax.scatter(x, q.share_pct, s=[min(80, 8 + n / 6) for n in q.n], color=S1, zorder=4,
               edgecolor=SURFACE, linewidth=0.8)
    ax.set_ylabel("% of that quarter's new signings", fontsize=10)
    ax.set_ylim(0, max(5, q.share_pct.max() * 1.15))
    lo, hi = min(x) - 0.4, 2026.75
    style(ax); year_axis(ax, lo, hi)
    xr = yr(case["published"])
    ax.axvline(xr, color=S3, linewidth=1.4, linestyle=(0, (4, 3)))
    ax.annotate(f"{rfc}", (xr, ax.get_ylim()[1]), (4, -4), textcoords="offset points",
                fontsize=9.5, color=S3, fontweight="bold", va="top")
    marks, seen = [], set()
    for p in case["programs"]:
        for e in p["events"]:
            if e["kind"] not in ("default", "support") or p["role"] != "signer":
                continue
            tag = (p["key"], e["version"], e["kind"])
            if tag in seen:
                continue
            seen.add(tag)
            marks.append((yr(e["date"]), p, e))
    lane_end = []      # greedy lane packing: x where each lane's last label ends
    for xe, p, e in sorted(marks, key=lambda t: t[0]):
        text = f'{p["program"]} {e["version"]}' + (" default" if e["kind"] == "default" else "")
        width = len(text) * 0.075 * (hi - lo) / 15.0
        lane = next((i for i, end in enumerate(lane_end) if end < xe), None)
        if lane is None:
            lane = len(lane_end); lane_end.append(0)
        lane_end[lane] = xe + width
        col = YELLOW if e["kind"] == "default" else S2
        ax.axvline(xe, color=col, linewidth=1.2, alpha=0.9)
        ax.annotate(text, (xe, ax.get_ylim()[1]), (3, -14 - 11 * lane), textcoords="offset points",
                    fontsize=8, color=INK_2 if e["kind"] == "support" else INK, va="top")
        if True:
            if e["kind"] == "default":
                key = {"pdns-auth": "pdns"}.get(p["key"], p["key"])
                for d in first_ships(distro, key, e["version"]):
                    xd = yr(d["released"])
                    ax.axvline(xd, color=INK_2, linewidth=0.9, linestyle=(0, (1, 2)))
                    ax.annotate(d["name"], (xd, 0), (2, 4), textcoords="offset points",
                                fontsize=7.5, color=INK_2, rotation=90, va="bottom")
    ax.set_title("Reverse DNS, all five RIRs: share of newly signed delegations that chose the algorithm, "
                 "per quarter (dot size = number of new signings; quarters with <20 hidden)",
                 loc="left", fontsize=10.5, color=INK_2, pad=6)
    if not bare:
        fig.suptitle(f"{rfc}: {case['title']}  --  did new signings follow the defaults?",
                     x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.subplots_adjust(left=0.06, right=0.98, top=0.8 if not bare else 0.88, bottom=0.12)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bare", action="store_true")
    ap.add_argument("--out", default="reporting/charts/cases")
    a = ap.parse_args()
    doc = json.loads(Path("out/analysis/program_rfc_cases.json").read_text("utf-8"))
    distro = json.loads(Path("data/software/distro_ships.json").read_text("utf-8"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for rfc, case in doc["cases"].items():
        slug = rfc.lower().replace(" ", "_")
        draw(rfc, case, distro, out / f"{slug}.png", bare=a.bare)
        if draw_new_signings(rfc, case, distro, out / f"{slug}_new_signings.png", bare=a.bare):
            print(f"{rfc}: figure + new-signings figure")
        else:
            print(f"{rfc}: figure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
