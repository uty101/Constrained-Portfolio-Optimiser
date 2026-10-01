"""Statistics: stationary block bootstrap, strategy metrics, Sharpe intervals and the primary table."""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from pc.config import BootstrapConfig, Config, load_config


def stationary_bootstrap_indices(n: int, mean_block: float, reps: int, seed: int) -> np.ndarray:
    """Politis-Romano index paths, reps x n, int64.

    Draw order is fixed: for each replication in turn, index 0 is rng.integers(n); for
    j >= 1, u = rng.random(), and if u < 1/mean_block the index is rng.integers(n),
    otherwise (previous + 1) mod n.
    """
    rng = np.random.default_rng(seed)
    p = 1 / mean_block
    idx = np.empty((reps, n), dtype=np.int64)
    for r in range(reps):
        cur = int(rng.integers(n))
        idx[r, 0] = cur
        for j in range(1, n):
            cur = int(rng.integers(n)) if rng.random() < p else (cur + 1) % n
            idx[r, j] = cur
    return idx


# --- strategy metrics (kickoff 5.8, PLAN 4.3, instruction 04 amendment 4.3) -------------

MONTHS_PER_YEAR = 12
# Kickoff 5.8 gives ddof 1 for annualised vol and no ddof for the Sharpe std; the Sharpe ratio
# uses ddof 1 too (decisions/OPEN.md, item 6, implemented as option 1).
SHARPE_DDOF = 1

METRIC_COLUMNS = [
    "strategy_id", "n_months", "ruined", "ann_return", "ann_vol", "sharpe", "max_dd",
    "forecast_vol_ann", "fcst_realised_ratio", "mean_turnover", "mean_positions",
    "scs_retries", "fallbacks", "rp_not_converged", "ridged_months",
]


def sharpe(excess: np.ndarray) -> float:
    """mean / std(ddof SHARPE_DDOF) * sqrt(12) of monthly excess returns."""
    return float(np.mean(excess) / np.std(excess, ddof=SHARPE_DDOF) * np.sqrt(MONTHS_PER_YEAR))


def max_drawdown(r_net: np.ndarray) -> float:
    """min over the path of W / running peak - 1, W the net wealth path starting at 1 (start included)."""
    wealth = np.concatenate([[1.0], np.cumprod(1 + r_net)])
    return float(np.min(wealth / np.maximum.accumulate(wealth) - 1))


def strategy_metrics(periods: pd.DataFrame) -> pd.DataFrame:
    """One row per strategy, in order of first appearance in periods.

    The wealth path is every month with a ret_net, the ruin month included (amendment 4.2.8),
    so a ruined strategy has wealth 0, ann_return -1 and max_dd -1. mean_turnover skips the
    first period (NaN). scs_retries counts "SCS" in every solver string; fallbacks,
    rp_not_converged and ridged_months (ridge > 0) count months.
    """
    rows = []
    for sid, p in periods.groupby("strategy_id", sort=False):
        live = p[p["ret_net"].notna()]
        r = live["ret_net"].to_numpy(dtype=float)
        n = len(r)
        ann_vol = float(np.std(r, ddof=1) * np.sqrt(MONTHS_PER_YEAR))
        fcst = float(live["forecast_vol_ann"].mean())
        rows.append({
            "strategy_id": sid,
            "n_months": n,
            "ruined": bool(p["ruined"].any()),
            "ann_return": float(np.prod(1 + r) ** (MONTHS_PER_YEAR / n) - 1),
            "ann_vol": ann_vol,
            "sharpe": sharpe(live["excess_net"].to_numpy(dtype=float)),
            "max_dd": max_drawdown(r),
            "forecast_vol_ann": fcst,
            "fcst_realised_ratio": fcst / ann_vol,
            "mean_turnover": float(live["turnover"].mean()),
            "mean_positions": float(live["n_positions"].mean()),
            "scs_retries": int(p["solver"].str.count("SCS").sum()),
            "fallbacks": int(p["fallback"].sum()),
            "rp_not_converged": int((~p["rp_converged"].astype(bool)).sum()),
            "ridged_months": int((p["ridge"] > 0).sum()),
        })
    return pd.DataFrame(rows, columns=METRIC_COLUMNS)


CSV_KWARGS = dict(index=False, float_format="%.10g", date_format="%Y-%m-%d", lineterminator="\n")


def write_metrics(cfg: Config) -> Path:
    periods = pd.read_parquet(Path(cfg.outputs.results_dir) / "periods.parquet")
    path = Path(cfg.outputs.tables_dir) / "metrics_all.csv"
    strategy_metrics(periods).to_csv(path, **CSV_KWARGS)
    return path


# --- Sharpe intervals (kickoff 5.8, PLAN 4.4) ---------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.toml"


@lru_cache(maxsize=1)
def bootstrap_config() -> BootstrapConfig:
    """[bootstrap] from the repo's config.toml: sharpe_intervals has no Config argument (as pc.solver)."""
    return load_config(CONFIG_PATH).bootstrap


# PLAN 4.4: the Sharpe difference is reported against these two strategies.
BENCHMARKS = ["equal_weight|none|none|none", "min_variance|lw_cc|none|B"]


def interval_columns(benchmarks: list[str]) -> list[str]:
    cols = ["strategy_id", "ruined", "sharpe", "sharpe_p05", "sharpe_p95"]
    for b in benchmarks:
        cols += [f"diff_vs_{b}", f"diff_p05_vs_{b}", f"diff_p95_vs_{b}", f"frac_le_0_vs_{b}"]
    return cols


def boot_sharpe(excess: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Sharpe on each resampled path: excess[idx] row by row, ddof SHARPE_DDOF."""
    x = excess[idx]
    return x.mean(axis=1) / x.std(axis=1, ddof=SHARPE_DDOF) * np.sqrt(MONTHS_PER_YEAR)


def sharpe_intervals(periods: pd.DataFrame, idx: np.ndarray, benchmarks: list[str]) -> pd.DataFrame:
    """Sharpe 90% interval per strategy and paired differences against each benchmark.

    Every strategy is resampled on the same index paths idx (reps x n, n = months per
    strategy), so a difference is taken path by path. Percentiles are np.quantile at
    (p05, p95) = bootstrap.ci with numpy's default rule (decisions/section_2_review.md, 1).
    frac_le_0 is the fraction of paths whose difference is <= 0. A ruined strategy keeps its
    point Sharpe (over the months of its wealth path, as in strategy_metrics); its interval,
    and every difference involving it, is NaN (amendment 4.2.8).
    """
    ci = bootstrap_config().ci
    series, ruined = {}, {}
    for sid, p in periods.groupby("strategy_id", sort=False):
        p = p.sort_values("decision_date")
        series[sid] = p["excess_net"].to_numpy(dtype=float)
        ruined[sid] = bool(p["ruined"].any())
        if len(series[sid]) != idx.shape[1]:
            raise ValueError(f"{sid}: {len(series[sid])} months, index paths have {idx.shape[1]}")
    for b in benchmarks:
        if b not in series:
            raise ValueError(f"benchmark {b!r} is not in periods")

    boots = {sid: None if ruined[sid] else boot_sharpe(x, idx) for sid, x in series.items()}
    point = {sid: sharpe(x[~np.isnan(x)]) for sid, x in series.items()}
    nan = math.nan
    rows = []
    for sid in series:
        row = {"strategy_id": sid, "ruined": ruined[sid], "sharpe": point[sid]}
        if boots[sid] is None:
            row["sharpe_p05"] = row["sharpe_p95"] = nan
        else:
            row["sharpe_p05"], row["sharpe_p95"] = np.quantile(boots[sid], ci)
        for b in benchmarks:
            if boots[sid] is None or boots[b] is None:
                vals = (nan, nan, nan, nan)
            else:
                d = boots[sid] - boots[b]
                lo, hi = np.quantile(d, ci)
                vals = (point[sid] - point[b], lo, hi, float(np.mean(d <= 0)))
            for col, v in zip(interval_columns([b])[5:], vals):
                row[col] = v
        rows.append(row)
    return pd.DataFrame(rows, columns=interval_columns(benchmarks))


def write_sharpe_intervals(cfg: Config) -> Path:
    periods = pd.read_parquet(Path(cfg.outputs.results_dir) / "periods.parquet")
    n = periods.groupby("strategy_id").size().iloc[0]
    b = cfg.bootstrap
    idx = stationary_bootstrap_indices(int(n), b.mean_block, b.reps, cfg.run.bootstrap_seed)
    path = Path(cfg.outputs.tables_dir) / "sharpe_intervals.csv"
    sharpe_intervals(periods, idx, BENCHMARKS).to_csv(path, **CSV_KWARGS)
    return path
