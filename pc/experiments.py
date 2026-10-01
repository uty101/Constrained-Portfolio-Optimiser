"""Section 5 experiments on the walk-forward engine (PLAN 5.2 to 5.5, instruction 05 5.2 to 5.6)."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pc.backtest import (  # noqa: E402
    BP_PER_UNIT,
    MONTHS_PER_YEAR,
    build_registry,
    walk_forward,
)
from pc.config import Config  # noqa: E402
from pc.data import load_prices, load_rf_daily  # noqa: E402
from pc.stats import CSV_KWARGS  # noqa: E402

DPI = 150  # kickoff Section 6: figures at 150 dpi
# bp of monthly return per 1% of turnover = dual x 1e4 bp x 0.01 = dual x 100 (kickoff 5.3, allocator 2).
BP_PER_PCT = BP_PER_UNIT / 100
# Amendment 5.2: a month binds when turnover >= tau_eff - 1e-6 (convention 22).
BINDING_SLACK = 1e-6
# Chart 4 presentation: axis padding, and the share of each axis span within which a point counts as
# at the origin and its label is stacked.
CHART4_PAD = 0.06
CHART4_NEAR = 0.03


def load_panel(cfg: Config) -> tuple[pd.DataFrame, pd.Series]:
    prices = load_prices(cfg)
    return prices, load_rf_daily(cfg, prices.index)


def specs_for(cfg: Config, ids: list[str]):
    """The registry specs with these ids, in the order of ids."""
    by_id = {s.id: s for s in build_registry(cfg)}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise ValueError(f"not in the registry: {missing}")
    return [by_id[i] for i in ids]


def after_first(p: pd.DataFrame) -> pd.DataFrame:
    """Every month but the first decision date of one strategy (amendment 5.2: monthly means
    exclude the first period)."""
    p = p.sort_values("decision_date")
    return p.iloc[1:]


def ann_return(r_net: np.ndarray) -> float:
    """(prod(1 + r_net))^(12/n) - 1 over the wealth path (kickoff 5.8)."""
    return float(np.prod(1 + r_net) ** (MONTHS_PER_YEAR / len(r_net)) - 1)


def bp_pa(monthly: float) -> float:
    """A monthly decimal as basis points per annum: x 12 x 1e4 (amendment 5.2)."""
    return monthly * MONTHS_PER_YEAR * BP_PER_UNIT


# --- 5.2 turnover frontier -------------------------------------------------------------------

TURNOVER_SPEC = "mv_constrained|lw_cc|sample|C"
FRONTIER_COLUMNS = [
    "tau", "mean_mu_exante", "exante_return_given_up_bp_pa", "mean_cost", "cost_saved_bp_pa",
    "realised_net_ann_return", "realised_net_vs_none_bp_pa", "mean_turnover", "mean_dual_bp_per_pct",
    "n_binding", "n_relaxed",
]


def turnover_grid(cfg: Config) -> list[float | None]:
    """turnover_grid.taus, then None (no turnover limit, cost term kept) when include_none."""
    return [*cfg.turnover_grid.taus, *([None] if cfg.turnover_grid.include_none else [])]


def turnover_runs(prices: pd.DataFrame, rf_daily: pd.Series, cfg: Config) -> tuple[dict, dict]:
    """(periods by tau, wall seconds by tau): mv_constrained|lw_cc|sample|C with mv.max_turnover set
    to each tau; None drops the turnover constraint and keeps the cost term."""
    spec = specs_for(cfg, [TURNOVER_SPEC])
    runs, seconds = {}, {}
    for tau in turnover_grid(cfg):
        start = time.perf_counter()
        _, periods, _ = walk_forward(spec, prices, rf_daily, replace(cfg, mv=replace(cfg.mv, max_turnover=tau)))
        runs[tau], seconds[tau] = periods, time.perf_counter() - start
    return runs, seconds


def turnover_frontier(runs: dict) -> pd.DataFrame:
    """One row per tau, then "none" (amendment 5.2).

    Monthly means (mu_exante, cost, turnover, turnover_dual, ret_net) exclude the first period.
    exante_return_given_up_bp_pa = (mean mu'w at none - mean mu'w at tau) x 12 x 1e4;
    cost_saved_bp_pa = (mean cost at none - mean cost at tau) x 12 x 1e4;
    realised_net_vs_none_bp_pa = (mean ret_net at tau - mean ret_net at none) x 12 x 1e4;
    realised_net_ann_return is the annualised net return over the whole wealth path, as in
    metrics_all; mean_dual_bp_per_pct = mean turnover_dual x 100; n_binding counts months with
    turnover >= tau_eff - 1e-6; n_relaxed counts tau_relaxed months.
    """
    if None not in runs:
        raise ValueError("the turnover frontier needs the run with no turnover limit")
    none = after_first(runs[None])
    rows = []
    for tau, p in runs.items():
        live = after_first(p)
        rows.append({
            "tau": "none" if tau is None else tau,
            "mean_mu_exante": float(live["mu_exante"].mean()),
            "exante_return_given_up_bp_pa": bp_pa(none["mu_exante"].mean() - live["mu_exante"].mean()),
            "mean_cost": float(live["cost"].mean()),
            "cost_saved_bp_pa": bp_pa(none["cost"].mean() - live["cost"].mean()),
            "realised_net_ann_return": ann_return(p["ret_net"].dropna().to_numpy(dtype=float)),
            "realised_net_vs_none_bp_pa": bp_pa(live["ret_net"].mean() - none["ret_net"].mean()),
            "mean_turnover": float(live["turnover"].mean()),
            "mean_dual_bp_per_pct": float(live["turnover_dual"].mean() * BP_PER_PCT),
            "n_binding": int((live["turnover"] >= live["tau_eff"] - BINDING_SLACK).sum()),
            "n_relaxed": int(live["tau_relaxed"].sum()),
        })
    return pd.DataFrame(rows, columns=FRONTIER_COLUMNS)


def plot_turnover_frontier(table: pd.DataFrame, path: Path) -> None:
    """Chart 4: ex-ante return given up (y) against cost saved (x), bp per annum, points labelled
    by tau, with the 45 degree line where the two are equal and the region below it shaded: there
    a limit saved more in cost than it gave up in expected return. Labels of points that sit
    within 3% of both axis spans of the origin are stacked above it with leader lines."""
    x = table["cost_saved_bp_pa"].to_numpy(dtype=float)
    y = table["exante_return_given_up_bp_pa"].to_numpy(dtype=float)
    pad = CHART4_PAD
    x_lo, x_hi = min(x.min(), 0.0), max(x.max(), 0.0)
    y_lo, y_hi = min(y.min(), 0.0), max(y.max(), 0.0)
    xlim = (x_lo - pad * (x_hi - x_lo), x_hi + pad * (x_hi - x_lo))
    ylim = (y_lo - pad * (y_hi - y_lo), y_hi + pad * (y_hi - y_lo))
    fig, ax = plt.subplots(figsize=(9, 6.5))
    line = np.array(xlim)
    ax.fill_between(line, ylim[0], line, color="#2ca02c", alpha=0.08, lw=0,
                    label="Below the line: cost saved > expected return given up")
    ax.plot(line, line, color="0.4", lw=1, ls="--", label="45° line: cost saved = expected return given up")
    ax.plot(x, y, color="#1f77b4", lw=1, alpha=0.5)
    ax.scatter(x, y, color="#1f77b4", zorder=3, s=24, label="mv_constrained|lw_cc|sample|C, one run per τ")
    near = CHART4_NEAR
    stacked = 0
    for row in table.itertuples():
        label = "none (no limit)" if row.tau == "none" else f"τ = {float(row.tau):g}"
        xy = (row.cost_saved_bp_pa, row.exante_return_given_up_bp_pa)
        if abs(xy[0]) <= near * (xlim[1] - xlim[0]) and abs(xy[1]) <= near * (ylim[1] - ylim[0]):
            stacked += 1
            ax.annotate(label, xy, xytext=(28, 4 + 13 * stacked), textcoords="offset points", fontsize=8,
                        arrowprops={"arrowstyle": "-", "color": "0.5", "lw": 0.6})
        else:
            ax.annotate(label, xy, xytext=(7, -3), textcoords="offset points", fontsize=8)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Trading cost saved against no limit (bp per annum)")
    ax.set_ylabel("Ex-ante expected return given up against no limit (bp per annum)")
    ax.set_title("Turnover limit: expected return given up against cost saved")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)

def write_turnover_frontier(cfg: Config) -> tuple[list[Path], dict, dict]:
    prices, rf_daily = load_panel(cfg)
    runs, seconds = turnover_runs(prices, rf_daily, cfg)
    table = turnover_frontier(runs)
    paths = [Path(cfg.outputs.tables_dir) / "turnover_frontier.csv", Path(cfg.outputs.figures_dir) / "turnover_frontier.png"]
    table.to_csv(paths[0], **CSV_KWARGS)
    plot_turnover_frontier(table, paths[1])
    return paths, runs, seconds
