"""The full-corpus path: two drives in, the same analyses and notebook out.

Pins the configuration contract -- which run each analysis reads, how the driver combines a
main and a spill drive, and that the notebook reads coverage from the data instead of typing it.
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import _run_paths  # noqa: E402
import run_openintel_full as drv  # noqa: E402


def test_default_runs_are_the_committed_ones(monkeypatch):
    monkeypatch.delenv(_run_paths.SERVER_ENV, raising=False)
    monkeypatch.delenv(_run_paths.PANEL_ENV, raising=False)
    assert _run_paths.server_timeline() == ROOT / "out/server_run/timeline_monthly.parquet"
    assert _run_paths.panel_timeline() == ROOT / "out/panel_run/timeline_monthly.parquet"
    assert _run_paths.inputs_record() == {"server_run": "out/server_run/timeline_monthly.parquet",
                                          "panel_run": "out/panel_run/timeline_monthly.parquet"}


def test_env_selects_another_run(monkeypatch, tmp_path):
    monkeypatch.setenv(_run_paths.SERVER_ENV, str(tmp_path / "full" / "server"))
    monkeypatch.setenv(_run_paths.PANEL_ENV, str(tmp_path / "full" / "panel" / "timeline_monthly.parquet"))
    assert _run_paths.server_timeline() == tmp_path / "full" / "server" / "timeline_monthly.parquet"
    assert _run_paths.panel_timeline() == tmp_path / "full" / "panel" / "timeline_monthly.parquet"
    assert _run_paths.inputs_record()["server_run"].endswith("full/server/timeline_monthly.parquet")


def test_forward_sources_keep_known_order_and_add_new_ones():
    df = pd.DataFrame({"basis": ["zonefile"] * 4 + ["reverse"],
                       "source": ["nu", "zz", "se", "aa", "ripe"]})
    assert _run_paths.forward_sources(df) == ["se", "nu", "aa", "zz"]


def test_driver_plan_uses_both_drives_and_builds_the_strict_panel(tmp_path):
    a = drv.parse_args(["--main", "/data/main", "--spill", "/data/spill", "--run-dir", str(tmp_path),
                        "--reverse-corpus", "/data/reverse", "--threads", "8"])
    plan = drv.plan(a)
    steps = [s for s, _, _ in plan]
    assert steps[:3] == ["server", "panel", "coverage"] and steps.count("analyses") == 3
    server = plan[0][1]
    roots = [server[i + 1] for i, x in enumerate(server) if x == "--roots"]
    assert roots == ["/data/main", "/data/spill", "/data/reverse"]
    assert ["--stage", "index", "--stage", "extract"] == server[server.index("--stage"):server.index("--stage") + 4]
    panel = plan[1][1]
    assert "--pool-sources" in panel and panel[panel.index("--sources") + 1] == "afrinic,arin"
    env = plan[3][2]
    assert env["DNSSEC_SERVER_RUN"] == str(tmp_path / "server")
    assert env["DNSSEC_PANEL_RUN"] == str(tmp_path / "panel")


def test_driver_can_reuse_an_existing_panel(tmp_path):
    a = drv.parse_args(["--main", "/m", "--run-dir", str(tmp_path), "--reuse-panel", "out/panel_run"])
    plan = drv.plan(a)
    assert "panel" not in [s for s, _, _ in plan]
    assert plan[-1][2]["DNSSEC_PANEL_RUN"] == str(ROOT / "out" / "panel_run")


def test_coverage_attributes_days_to_drives(tmp_path):
    run = tmp_path / "run"
    (run / "server").mkdir(parents=True)
    main, spill = tmp_path / "main", tmp_path / "spill"
    inv = {"summary": {"unmatched_files": 0, "duplicate_files": 0, "days_split_across_roots": 1},
           "days": [
               {"source": "se", "basis": "zonefile", "day": "2023-12-31", "roots": [main.as_posix()]},
               {"source": "se", "basis": "zonefile", "day": "2024-01-01", "roots": [spill.as_posix()]},
               {"source": "se", "basis": "zonefile", "day": "2024-01-02",
                "roots": [main.as_posix(), spill.as_posix()]}]}
    (run / "server" / "inventory.json").write_text(json.dumps(inv))
    a = drv.parse_args(["--main", str(main), "--spill", str(spill), "--run-dir", str(run), "--reverse-corpus", ""])
    out = drv.coverage(a)
    se = out["per_source"]["zonefile/se"]
    assert se["days"] == 3 and se["last_day"] == "2024-01-02" and se["split_days"] == 1
    assert se["by_drive"] == {"main": 1, "spill": 1, "main + spill": 1}
    assert out["spill_contributed_days"] == 2


def test_notebook_builder_types_no_forward_coverage_dates():
    src = (ROOT / "notebooks" / "build_software_vs_adoption_notebook.py").read_text()
    for literal in ("2023-12", "2016.3", "2024.1", "2026.8"):
        assert literal not in src, literal
    assert "OPENINTEL_MAIN" in src and "OPENINTEL_SPILL" in src and "fwd_coverage_text()" in src
