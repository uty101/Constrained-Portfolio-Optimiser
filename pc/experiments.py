"""Section 5 experiments on the walk-forward engine (PLAN 5.2 to 5.5, instruction 05 5.2 to 5.6)."""

from __future__ import annotations

import math
import time
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import cvxpy as cp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pc.backtest import (  # noqa: E402
    BP_PER_UNIT,
    MONTHS_PER_YEAR,
    DateInputs,
    build_registry,
    cost_vector,
    walk_forward,
)
from pc.calendar import build_calendar  # noqa: E402
from pc.charts import frontier_inputs, holding_excess  # noqa: E402
from pc.config import Config  # noqa: E402
from pc.cov import condition_cov, estimate_cov  # noqa: E402
from pc.data import load_prices, load_rf_daily  # noqa: E402
from pc.returns import daily_returns, holding_returns, holding_rf, monthly_excess_returns  # noqa: E402
from pc.returns_model import trailing_months  # noqa: E402
from pc.sensitivity import MU_STRATEGIES  # noqa: E402
from pc.solver import solve, symmetrise  # noqa: E402
from pc.stats import (  # noqa: E402
    CSV_KWARGS,
    PRIMARY_IDS,
    max_drawdown,
    sharpe_intervals,
    stationary_bootstrap_indices,
    strategy_metrics,
)

DPI = 150  # kickoff Section 6: figures at 150 dpi
# bp of monthly return per 1% of turnover = dual x 1e4 bp x 0.01 = dual x 100 (kickoff 5.3, allocator 2).
BP_PER_PCT = BP_PER_UNIT / 100
# Amendment 5.2: a month binds when turnover >= tau_eff - 1e-6 (convention 22).
BINDING_SLACK = 1e-6
EW_ID = "equal_weight|none|none|none"
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


# --- 5.3 cost sensitivity --------------------------------------------------------------------

COST_COLUMNS = ["strategy_id", "cost_scale", "ruined", "ann_return", "ann_vol", "sharpe", "mean_turnover",
                "mean_cost_bp_pa"]


def scale_costs(cfg: Config, scale: float) -> Config:
    """cfg with every one-way cost multiplied by scale. The engine reads costs.one_way_bp for both the
    set C cost term and the cost charged, so the scale applies to both (amendment 5.3)."""
    return replace(cfg, costs=replace(cfg.costs, one_way_bp={t: bp * scale for t, bp in cfg.costs.one_way_bp.items()}))


def cost_runs(prices: pd.DataFrame, rf_daily: pd.Series, cfg: Config, ids: list[str]) -> tuple[dict, dict]:
    """(periods by cost scale, wall seconds by cost scale) for the strategies ids."""
    specs = specs_for(cfg, ids)
    runs, seconds = {}, {}
    for scale in cfg.costs.cost_scales:
        start = time.perf_counter()
        _, runs[scale], _ = walk_forward(specs, prices, rf_daily, scale_costs(cfg, scale))
        seconds[scale] = time.perf_counter() - start
    return runs, seconds


def cost_sensitivity(runs: dict, ids: list[str]) -> pd.DataFrame:
    """One row per strategy and cost scale, strategies in the order of ids.

    ann_return, ann_vol, sharpe, ruined and mean_turnover are strategy_metrics' (a ruined strategy
    has a NaN Sharpe; decisions/section_5_review.md, 2). mean_cost_bp_pa = mean monthly cost over
    the wealth path without its first period, x 12 x 1e4.
    """
    rows = []
    for sid in ids:
        for scale, periods in runs.items():
            p = periods[periods["strategy_id"] == sid]
            m = strategy_metrics(p).iloc[0]
            live = after_first(p[p["ret_net"].notna()])
            rows.append({
                "strategy_id": sid, "cost_scale": scale, "ruined": bool(m.ruined), "ann_return": m.ann_return,
                "ann_vol": m.ann_vol, "sharpe": m.sharpe, "mean_turnover": m.mean_turnover,
                "mean_cost_bp_pa": bp_pa(live["cost"].mean()),
            })
    return pd.DataFrame(rows, columns=COST_COLUMNS)


def write_cost_sensitivity(cfg: Config) -> tuple[Path, dict, dict]:
    prices, rf_daily = load_panel(cfg)
    runs, seconds = cost_runs(prices, rf_daily, cfg, PRIMARY_IDS)
    path = Path(cfg.outputs.tables_dir) / "cost_sensitivity.csv"
    cost_sensitivity(runs, PRIMARY_IDS).to_csv(path, **CSV_KWARGS)
    return path, runs, seconds


# --- 5.4 N close to T ------------------------------------------------------------------------

MONTHLY_COV_SPECS = ["mv_unconstrained|sample|sample|A", "min_variance|sample|none|B"]
ROBUSTNESS_COLUMNS = ["decision_date", "cond_daily", "cond_monthly_before", "cond_monthly_after", "ridge_monthly"]


def monthly_sample_cov(monthly_excess: pd.DataFrame, t: pd.Timestamp, cfg: Config) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """(Sigma, log, X): np.cov (ddof 1) of the window_months monthly excess returns of trailing_months
    for the month of t, conditioned by condition_cov (amendment 5.4). X is the rows used."""
    X = trailing_months(monthly_excess, t, cfg.sample.window_months - 1, 0)
    S = pd.DataFrame(np.cov(X.to_numpy(dtype=float), rowvar=False, ddof=1), index=X.columns, columns=X.columns)
    Sigma, log = condition_cov(S, cfg.cov.max_cond)
    log["lw_delta"] = math.nan
    return Sigma, log, X


class MonthlySampleInputs(DateInputs):
    """DateInputs whose "sample" Sigma is the monthly sample covariance; every other estimator is unchanged."""

    def sigma(self, est: str) -> tuple[pd.DataFrame, dict]:
        if est == "sample" and est not in self._sigma:
            Sigma, log, _ = monthly_sample_cov(self.monthly_excess, self.t, self.cfg)
            self._sigma[est] = (Sigma, log)
        return super().sigma(est)


def monthly_cov_robustness(prices: pd.DataFrame, rf_daily: pd.Series, cfg: Config) -> pd.DataFrame:
    """One row per decision date: cond of the daily sample Sigma (before conditioning), and cond
    before and after conditioning and the ridge of the monthly sample Sigma."""
    returns_d = daily_returns(prices)
    monthly_excess = monthly_excess_returns(prices, rf_daily)
    rows = []
    for t in build_calendar(prices.index, cfg)["decision_date"]:
        _, daily_log = estimate_cov(returns_d, t, "sample", cfg)
        _, log, _ = monthly_sample_cov(monthly_excess, t, cfg)
        rows.append({"decision_date": t, "cond_daily": daily_log["cond_before"],
                     "cond_monthly_before": log["cond_before"], "cond_monthly_after": log["cond_after"],
                     "ridge_monthly": log["ridge"]})
    return pd.DataFrame(rows, columns=ROBUSTNESS_COLUMNS)


def monthly_cov_strategies(daily_periods: pd.DataFrame, monthly_periods: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    """metrics_all columns for each strategy on the daily Sigma, then on the monthly Sigma, with a
    leading column sigma_basis ("daily" or "monthly")."""
    frames = []
    for sid in ids:
        for basis, periods in (("daily", daily_periods), ("monthly", monthly_periods)):
            m = strategy_metrics(periods[periods["strategy_id"] == sid])
            m.insert(0, "sigma_basis", basis)
            frames.append(m)
    return pd.concat(frames, ignore_index=True)


def write_monthly_cov(cfg: Config) -> tuple[list[Path], pd.DataFrame, dict]:
    prices, rf_daily = load_panel(cfg)
    seconds = {}
    start = time.perf_counter()
    robustness = monthly_cov_robustness(prices, rf_daily, cfg)
    seconds["robustness"] = time.perf_counter() - start
    start = time.perf_counter()
    _, monthly, _ = walk_forward(specs_for(cfg, MONTHLY_COV_SPECS), prices, rf_daily, cfg, MonthlySampleInputs)
    seconds["walk_forward"] = time.perf_counter() - start
    daily = pd.read_parquet(Path(cfg.outputs.results_dir) / "periods.parquet")
    tables = Path(cfg.outputs.tables_dir)
    paths = [tables / "monthly_cov_robustness.csv", tables / "monthly_cov_strategies.csv"]
    robustness.to_csv(paths[0], **CSV_KWARGS)
    monthly_cov_strategies(daily, monthly, MONTHLY_COV_SPECS).to_csv(paths[1], **CSV_KWARGS)
    return paths, monthly, seconds


# --- 5.5 answers table -----------------------------------------------------------------------

MAX_SHARPE_COLUMNS = ["frontier", "max_sharpe", "tangency_return", "tangency_vol", "solver", "status"]
ANSWER_COLUMNS = ["question", "figure", "value", "p05", "p95", "source_table", "source_row"]
# Amendment 5.5, Q1 and Q2: the strategies whose out-of-sample Sharpe is reported.
Q1_STRATEGIES = ["mv_constrained|lw_cc|sample|C", EW_ID, "min_variance|lw_cc|none|B"]
SENSITIVITY_BASE = "mv_constrained|lw_cc|sample|B"
SENSITIVITY_RATIOS = ["mv_constrained|lw_cc|bayes_stein|B", "black_litterman|lw_cc|bl|B"]


def frontier_max_sharpe(mu: pd.Series, Sigma: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """The in-sample maximum Sharpe ratio of the set A and set B frontiers of Chart 1 (annualised
    mu and Sigma of the holding-period excess returns).

    Set A, closed form, with A = mu'S^-1 mu, B = 1'S^-1 mu, C = 1'S^-1 1. When B > 0 the maximum
    is sqrt(A), at the tangency return A/B. When B <= 0 the budget-1 frontier's Sharpe ratio
    rises towards sqrt(A - B^2/C) as the target return grows and never reaches it: that supremum
    is reported, with NaN tangency return and vol and status "supremum_not_attained"
    (decisions/OPEN.md, item 8).
    Set B: with y = kappa w, min y'Sigma y s.t. mu'y = 1, 1'y = kappa, lower kappa <= y <= upper kappa,
    kappa >= 0, under the solver policy; w = y / kappa.
    """
    m = mu.to_numpy(dtype=float)
    S = symmetrise(Sigma)
    inv = np.linalg.solve(S, np.column_stack([m, np.ones(len(m))]))
    A, B, C = float(m @ inv[:, 0]), float(inv[:, 0].sum()), float(inv[:, 1].sum())
    if B > 0:
        row_a = {"max_sharpe": float(np.sqrt(A)), "tangency_return": A / B, "tangency_vol": float(np.sqrt(A)) / B,
                 "status": "optimal"}
    else:
        row_a = {"max_sharpe": float(np.sqrt(A - B**2 / C)), "tangency_return": math.nan, "tangency_vol": math.nan,
                 "status": "supremum_not_attained"}
    rows = [{"frontier": "A", **row_a, "solver": "closed_form"}]
    y, kappa = cp.Variable(len(m)), cp.Variable()
    prob = cp.Problem(cp.Minimize(cp.quad_form(y, S)), [
        m @ y == 1, cp.sum(y) == kappa, y >= cfg.mv.lower * kappa, y <= cfg.mv.upper * kappa, kappa >= 0])
    rec = solve(prob)
    if rec.fallback:
        rows.append({"frontier": "B", "max_sharpe": math.nan, "tangency_return": math.nan,
                     "tangency_vol": math.nan, "solver": rec.solver, "status": rec.status})
    else:
        w_b = np.asarray(y.value, dtype=float) / float(kappa.value)
        ret, vol = float(m @ w_b), float(np.sqrt(w_b @ S @ w_b))
        rows.append({"frontier": "B", "max_sharpe": ret / vol, "tangency_return": ret, "tangency_vol": vol,
                     "solver": rec.solver, "status": rec.status})
    return pd.DataFrame(rows, columns=MAX_SHARPE_COLUMNS)


def source_rows(table: pd.DataFrame, query: str) -> pd.DataFrame:
    """The rows of a source table that an answers.csv source_row selects (a DataFrame.query string)."""
    return table.query(query, engine="python")


def answers(tables: dict[str, pd.DataFrame], cfg: Config) -> pd.DataFrame:
    """answers.csv (amendment 5.5): one row per figure, each read from its source table, with the
    table's file name and a DataFrame.query string selecting the row or rows it came from. p05 and
    p95 are NaN for a figure that has no interval."""
    rows = []

    def add(question, figure, table, query, value, p05=math.nan, p95=math.nan):
        if len(source_rows(tables[table], query)) == 0:
            raise ValueError(f"{table}: no row for {query!r}")
        rows.append({"question": question, "figure": figure, "value": value, "p05": p05, "p95": p95,
                     "source_table": table, "source_row": query})

    def one(table, query):
        r = source_rows(tables[table], query)
        if len(r) != 1:
            raise ValueError(f"{table}: {len(r)} rows for {query!r}, expected 1")
        return r.iloc[0]

    # Q1: in-sample gap against out-of-sample results.
    for frontier in ("A", "B"):
        q = f'frontier == "{frontier}"'
        add("Q1", f"in-sample max Sharpe, set {frontier} frontier", "frontier_max_sharpe.csv", q,
            one("frontier_max_sharpe.csv", q)["max_sharpe"])
    for sid in Q1_STRATEGIES:
        q = f'strategy_id == "{sid}"'
        r = one("sharpe_intervals.csv", q)
        add("Q1", f"out-of-sample Sharpe, {sid}", "sharpe_intervals.csv", q, r["sharpe"], r["sharpe_p05"],
            r["sharpe_p95"])
    q = 'strategy_id.str.endswith("|A")'
    set_a = source_rows(tables["metrics_all.csv"], q)
    add("Q1", f"ruined set A strategies, of {len(set_a)}", "metrics_all.csv", q, int(set_a["ruined"].sum()))

    # Q2: the turnover limit.
    tau = str(cfg.mv.max_turnover)
    q = f'tau == "{tau}"'
    r = one("turnover_frontier.csv", q)
    for col, figure in (("exante_return_given_up_bp_pa", "ex-ante return given up, bp pa"),
                        ("cost_saved_bp_pa", "trading cost saved, bp pa"),
                        ("realised_net_vs_none_bp_pa", "realised net return against no limit, bp pa")):
        add("Q2", f"tau = {tau}: {figure}", "turnover_frontier.csv", q, r[col])
    q = 'tau != "none" and exante_return_given_up_bp_pa < cost_saved_bp_pa'
    below = source_rows(tables["turnover_frontier.csv"], q)
    largest = float(below["tau"].astype(float).max()) if len(below) else math.nan
    rows.append({"question": "Q2", "figure": "largest tau whose point lies below the 45 degree line",
                 "value": largest, "p05": math.nan, "p95": math.nan, "source_table": "turnover_frontier.csv",
                 "source_row": q})

    # Q3: sensitivity of the weights to sampling noise in mu, at the last date.
    last = str(cfg.sensitivity.dates[-1])
    summary = "sensitivity_summary.csv"
    for sid in MU_STRATEGIES:
        q = f'date == "{last}" and strategy == "{sid}"'
        add("Q3", f"{last}: mean_abs_change, {sid}", summary, q, one(summary, q)["mean_abs_change"])
    base = one(summary, f'date == "{last}" and strategy == "{SENSITIVITY_BASE}"')["mean_abs_change"]
    for sid in SENSITIVITY_RATIOS:
        q = f'date == "{last}" and strategy in ["{sid}", "{SENSITIVITY_BASE}"]'
        add("Q3", f"{last}: mean_abs_change ratio, {sid} / {SENSITIVITY_BASE}", summary, q,
            one(summary, f'date == "{last}" and strategy == "{sid}"')["mean_abs_change"] / base)

    # Q4: covariance estimators.
    for pset in ("ew", "gmv"):
        q = f'estimator == "ewma" and portfolio_set == "{pset}"'
        r = one("cov_eval_qlike_diff.csv", q)
        add("Q4", f"QLIKE difference against lw_cc, ewma on {pset}", "cov_eval_qlike_diff.csv", q,
            r["diff_vs_lw_cc"], r["p05"], r["p95"])
    for est in ("ewma", "lw_cc"):
        q = f'estimator == "{est}" and portfolio_set == "gmv"'
        add("Q4", f"bias ratio, {est} on gmv", "cov_eval.csv", q, one("cov_eval.csv", q)["bias_ratio"])
    return pd.DataFrame(rows, columns=ANSWER_COLUMNS)


ANSWER_SOURCES = ["frontier_max_sharpe.csv", "sharpe_intervals.csv", "metrics_all.csv", "turnover_frontier.csv",
                  "sensitivity_summary.csv", "cov_eval_qlike_diff.csv", "cov_eval.csv"]


def read_tables(tables_dir: Path, names: list[str]) -> dict[str, pd.DataFrame]:
    """Source tables as written. turnover_frontier.csv's tau and sensitivity_summary.csv's date are
    read as text, the form answers.csv's source_row queries use."""
    as_text = {"turnover_frontier.csv": {"tau": str}, "sensitivity_summary.csv": {"date": str}}
    return {n: pd.read_csv(tables_dir / n, dtype=as_text.get(n)) for n in names}


def write_answers(cfg: Config) -> tuple[list[Path], pd.DataFrame]:
    prices, rf_daily = load_panel(cfg)
    mu, Sigma = frontier_inputs(holding_excess(prices, rf_daily, cfg))
    tables = Path(cfg.outputs.tables_dir)
    paths = [tables / "frontier_max_sharpe.csv", tables / "answers.csv"]
    frontier_max_sharpe(mu, Sigma, cfg).to_csv(paths[0], **CSV_KWARGS)
    table = answers(read_tables(tables, ANSWER_SOURCES), cfg)
    table.to_csv(paths[1], **CSV_KWARGS)
    return paths, table

# --- 5.6 levered risk-based funds ------------------------------------------------------------

LEVERED_PERIOD_COLUMNS = ["strategy_id", "decision_date", "k", "ret_gross", "financing", "cost", "turnover",
                          "ret_net", "rf_hold", "excess_net", "ruined"]
LEVERED_COLUMNS = ["strategy_id", "mean_k", "max_k", "ann_return", "ann_vol", "sharpe", "sharpe_p05", "sharpe_p95",
                   "diff_vs_ew", "diff_p05", "diff_p95", "frac_le_0", "max_dd"]


def levered_k(periods: pd.DataFrame, sid: str) -> pd.Series:
    """k_t = forecast_vol_ann(equal weight) / forecast_vol_ann(sid) by decision date, both from the
    walk-forward periods (both on Sigma_lw_cc for the configured strategies). No cap."""
    def fvol(s):
        return periods.loc[periods["strategy_id"] == s].set_index("decision_date")["forecast_vol_ann"]

    return (fvol(EW_ID) / fvol(sid)).rename("k")


def levered_variants(sid: str, w: pd.DataFrame, k: pd.Series, hold: pd.DataFrame, rf_hold: pd.Series,
                     n_hold_days: pd.Series, cost: pd.Series, spread: float, days_per_month: int) -> pd.DataFrame:
    """The levered path of one strategy (instruction 05, step 5.6). Every input is indexed by decision
    date; w and hold have the tickers as columns, in the order of cost.

    Target holdings are k_t w_t in the risky assets and 1 - k_t in cash. w_prev is the previous
    risky holdings drifted by the asset returns and the previous cash by rf_hold, divided by
    their sum; turnover and cost use the risky weights only. With
    gross = k_t w_t'r + (1 - k_t) rf_hold - max(k_t - 1, 0) spread n_hold_days / (12 days_per_month),
    net = (1 - cost)(1 + gross) - 1, the kickoff 4.6 convention (decisions/OPEN.md, item 10).
    First period: cost 0, turnover NaN. Ruin rule as in the engine (amendment 4.2.8).
    """
    nan = math.nan
    rows, prev, ruined = [], None, False
    for t in w.index:
        if ruined:
            rows.append({"strategy_id": sid, "decision_date": t, "k": float(k[t]), "ret_gross": nan,
                         "financing": nan, "cost": nan, "turnover": nan, "ret_net": nan, "rf_hold": nan,
                         "excess_net": nan, "ruined": True})
            continue
        kt = float(k[t])
        wt = w.loc[t]
        risky, cash = kt * wt, 1.0 - kt
        r, rf = hold.loc[t], float(rf_hold[t])
        if prev is None:
            turnover, c = nan, 0.0
        else:
            risky_prev, cash_prev, r_prev, rf_prev = prev
            grown = risky_prev * (1 + r_prev)
            total = float(grown.sum()) + cash_prev * (1 + rf_prev)
            if not total > 0:
                raise ValueError(f"{sid} at {t}: drift denominator {total} <= 0")
            trade = risky - grown / total
            turnover, c = float(trade.abs().sum()), float((cost * trade.abs()).sum())
        financing = max(kt - 1.0, 0.0) * spread * float(n_hold_days[t]) / (MONTHS_PER_YEAR * days_per_month)
        gross = kt * float(wt @ r) + (1.0 - kt) * rf - financing
        net = (1 - c) * (1 + gross) - 1
        ruined = net <= -1
        if ruined:
            net = -1.0
        rows.append({"strategy_id": sid, "decision_date": t, "k": kt, "ret_gross": gross, "financing": financing,
                     "cost": c, "turnover": turnover, "ret_net": net, "rf_hold": rf, "excess_net": net - rf,
                     "ruined": bool(ruined)})
        prev = (risky, cash, r, rf)
    return pd.DataFrame(rows, columns=LEVERED_PERIOD_COLUMNS)


def levered_periods(periods: pd.DataFrame, weights_long: pd.DataFrame, prices: pd.DataFrame, rf_daily: pd.Series,
                    cfg: Config, ids: list[str], k_override: float | None = None) -> pd.DataFrame:
    """levered_variants for each strategy in ids, with k from levered_k, or k_override in every month."""
    tickers = list(cfg.universe.tickers)
    cal = build_calendar(prices.index, cfg)
    hold = holding_returns(prices, cal)
    rf_h = holding_rf(rf_daily, cal)
    n_days = cal.set_index("decision_date")["n_hold_days"]
    cost = cost_vector(cfg)
    spread = cfg.levered.financing_spread_bp_pa / BP_PER_UNIT
    frames = []
    for sid in ids:
        w = weights_long[weights_long["strategy_id"] == sid].pivot(
            index="decision_date", columns="ticker", values="w_target")[tickers]
        if len(w) != len(cal):
            raise ValueError(f"{sid}: {len(w)} target months, the calendar has {len(cal)}")
        k = levered_k(periods, sid) if k_override is None else pd.Series(float(k_override), index=w.index)
        frames.append(levered_variants(sid, w, k, hold, rf_h, n_days, cost, spread, cfg.sample.days_per_month))
    return pd.concat(frames, ignore_index=True)


def levered_table(lev: pd.DataFrame, idx: np.ndarray, ids: list[str]) -> pd.DataFrame:
    """One row per strategy in ids. Sharpe, its interval and the paired difference against equal weight
    come from sharpe_intervals on the index paths idx (NaN for a ruined path)."""
    iv = sharpe_intervals(lev, idx, [EW_ID]).set_index("strategy_id")
    rows = []
    for sid in ids:
        p = lev[lev["strategy_id"] == sid]
        r = p["ret_net"].dropna().to_numpy(dtype=float)
        i = iv.loc[sid]
        rows.append({
            "strategy_id": sid, "mean_k": float(p["k"].mean()), "max_k": float(p["k"].max()),
            "ann_return": ann_return(r), "ann_vol": float(np.std(r, ddof=1) * np.sqrt(MONTHS_PER_YEAR)),
            "sharpe": i["sharpe"], "sharpe_p05": i["sharpe_p05"], "sharpe_p95": i["sharpe_p95"],
            "diff_vs_ew": i[f"diff_vs_{EW_ID}"], "diff_p05": i[f"diff_p05_vs_{EW_ID}"],
            "diff_p95": i[f"diff_p95_vs_{EW_ID}"], "frac_le_0": i[f"frac_le_0_vs_{EW_ID}"],
            "max_dd": max_drawdown(r),
        })
    return pd.DataFrame(rows, columns=LEVERED_COLUMNS)


def write_levered(cfg: Config) -> tuple[Path, pd.DataFrame]:
    prices, rf_daily = load_panel(cfg)
    results = Path(cfg.outputs.results_dir)
    periods = pd.read_parquet(results / "periods.parquet")
    weights_long = pd.read_parquet(results / "weights_long.parquet")
    ids = [*cfg.levered.strategies, EW_ID]
    lev = levered_periods(periods, weights_long, prices, rf_daily, cfg, ids)
    b = cfg.bootstrap
    n = lev.groupby("strategy_id").size().iloc[0]
    idx = stationary_bootstrap_indices(int(n), b.mean_block, b.reps, cfg.run.bootstrap_seed)
    path = Path(cfg.outputs.tables_dir) / "levered_risk_based.csv"
    levered_table(lev, idx, ids).to_csv(path, **CSV_KWARGS)
    return path, lev
