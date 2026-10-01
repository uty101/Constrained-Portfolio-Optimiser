"""Regenerate every table, figure and result file from data/raw/, with no network (PLAN 7.1).

Calls the Section 1 to 6 writers in section order and prints the time each takes. Running it
twice leaves `git status` clean.

    python scripts/run_all.py
"""

from __future__ import annotations

import contextlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pc import charts, cli, cov_eval, data, experiments, report, sensitivity, stats  # noqa: E402
from pc.backtest import write_walk_forward  # noqa: E402
from pc.config import Config, load_config  # noqa: E402

# Step 6.5: the demo command, from the repo root.
DEMO_ARGV = ["--positions", "examples/positions_demo.csv", "--cash", "500790.0747", "--asof", cli.DEMO_ASOF,
             "--out", "examples/trades_demo.csv"]


def cli_demo(cfg: Config) -> int:
    code = cli.main(DEMO_ARGV)
    if code != 0:
        raise RuntimeError(f"pctrade demo exited {code}")
    return code


def writers() -> list[tuple[str, object]]:
    """(name, writer(cfg)) in section order (instruction 07, amendment 7.1)."""
    return [
        # 1. data issues and data summary
        ("data.write_data_issues", data.write_data_issues),
        ("data.write_data_summary", data.write_data_summary),
        # 2. covariance evaluation
        ("cov_eval.write_cov_eval", cov_eval.write_cov_eval),
        # 3. the walk forward
        ("backtest.write_walk_forward", write_walk_forward),
        # 4. metrics, intervals and the primary table
        ("stats.write_metrics", stats.write_metrics),
        ("stats.write_sharpe_intervals", stats.write_sharpe_intervals),
        ("stats.write_results_primary", stats.write_results_primary),
        # 5. Charts 1 and 2
        ("charts.write_charts", charts.write_charts),
        # 6. every Section 5 writer, and Charts 3 and 4
        ("sensitivity.write_sensitivity", sensitivity.write_sensitivity),
        ("experiments.write_turnover_frontier", experiments.write_turnover_frontier),
        ("experiments.write_cost_sensitivity", experiments.write_cost_sensitivity),
        ("experiments.write_monthly_cov", experiments.write_monthly_cov),
        ("experiments.write_levered", experiments.write_levered),
        ("experiments.write_answers", experiments.write_answers),
        # 7. the README tables
        ("report.write_readme_tables", report.write_readme_tables),
        # 8. the CLI demo
        ("cli.main (6.5 demo)", cli_demo),
    ]


def main() -> int:
    with contextlib.chdir(ROOT):
        cfg = load_config("config.toml")
        for d in (cfg.outputs.results_dir, cfg.outputs.tables_dir, cfg.outputs.figures_dir):
            os.makedirs(d, exist_ok=True)
        total = time.perf_counter()
        for name, writer in writers():
            start = time.perf_counter()
            writer(cfg)
            print(f"{name}: {time.perf_counter() - start:.1f} s", flush=True)
        print(f"total: {time.perf_counter() - total:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
