"""Segmented regression: does prevalence break at a known RFC cutoff?

Fits ``prevalence ~ time + post + time_since_cutoff`` per record type, for one
TLD, against the per-(tld, month) table ``prevalence.rollup_tld_month_prevalence``
produces -- correcting for autocorrelation with HAC standard errors when
Durbin-Watson flags it. Driven from the CLI's ``regress`` subcommand.

Requires: pip install statsmodels matplotlib
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

from openintel_rfc.utils import PipelineError

__all__ = ["DEFAULT_METRICS", "run_segmented_regression"]

DEFAULT_METRICS: tuple[str, ...] = ("ds_prevalence", "dnskey_prevalence", "rrsig_prevalence")


def run_segmented_regression(
    input_path: Path | str,
    tld: str,
    cutoff: str,
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    out_path: Path | str | None = None,
) -> Path:
    """Fit and plot a segmented regression for one TLD at one cutoff month.

    ``cutoff`` is a "YYYY-MM" string (e.g. an RFC's publication month). Prints
    the b1/b2/b3 coefficients and their p-values for each metric, saves one
    figure with a panel per metric, and returns the path it was saved to.
    """
    df = pd.read_parquet(input_path)
    tld_df = df[df["tld"] == tld].copy()
    if tld_df.empty:
        raise PipelineError(f"No rows for tld={tld!r} in {input_path}")

    tld_df["month"] = pd.PeriodIndex(tld_df["month"], freq="M")
    tld_df = tld_df.sort_values("month").reset_index(drop=True)

    cutoff_period = pd.Period(cutoff, freq="M")
    expected_months = pd.period_range(tld_df["month"].min(), tld_df["month"].max(), freq="M")
    missing_months = expected_months.difference(tld_df["month"])
    if len(missing_months):
        raise PipelineError(
            f"{tld}: missing {len(missing_months)} month(s): {list(missing_months)}"
        )
    if cutoff_period not in set(tld_df["month"]):
        raise PipelineError(f"{tld}: cutoff month {cutoff_period} is not present in the data.")

    tld_df["time"] = range(len(tld_df))
    cutoff_time = tld_df.loc[tld_df["month"] == cutoff_period, "time"].iloc[0]
    tld_df["post"] = (tld_df["month"] >= cutoff_period).astype(int)
    tld_df["time_since_cutoff"] = (tld_df["time"] - cutoff_time).clip(lower=0)

    X = sm.add_constant(tld_df[["time", "post", "time_since_cutoff"]])
    # Position of each column, since `get_robustcov_results` below returns plain
    # arrays for params/pvalues -- name-based lookup only works on the first fit.
    col = {name: i for i, name in enumerate(X.columns)}

    metrics = list(metrics)
    fig, axes = plt.subplots(len(metrics), 1, figsize=(9, 3 * len(metrics)), sharex=True)
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        y = tld_df[metric]
        model = sm.OLS(y, X).fit()

        dw = durbin_watson(model.resid)
        used_hac = not (1.5 < dw < 2.5)
        if used_hac:
            model = model.get_robustcov_results(cov_type="HAC", maxlags=3)

        params = np.asarray(model.params)
        pvalues = np.asarray(model.pvalues)

        print(f"\n{tld} / {metric}")
        print(f"  Durbin-Watson: {dw:.2f} (HAC correction {'applied' if used_hac else 'not needed'})")
        print(f"  pre-period slope (b1):      {params[col['time']]:.5f}  p={pvalues[col['time']]:.4f}")
        print(f"  level shift at cutoff (b2): {params[col['post']]:.5f}  p={pvalues[col['post']]:.4f}")
        print(f"  slope change after (b3):    {params[col['time_since_cutoff']]:.5f}  "
              f"p={pvalues[col['time_since_cutoff']]:.4f}")

        fitted = X.values @ params
        counterfactual = params[col["const"]] + params[col["time"]] * tld_df["time"]

        labels = tld_df["month"].astype(str)
        ax.plot(labels, y, "o", label="observed", markersize=3)
        ax.plot(labels, fitted, "-", label="fitted (segmented)")
        ax.plot(labels, counterfactual, "--", label="pre-trend extended")
        ax.axvline(str(cutoff_period), color="black", linewidth=0.8)
        ax.set_title(f"{tld}: {metric}")
        ax.legend(fontsize=8)

    axes[-1].set_xlabel("month")
    plt.xticks(rotation=90, fontsize=6)
    plt.tight_layout()

    out_path = Path(out_path) if out_path else Path(f"{tld}_segmented_regression.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
