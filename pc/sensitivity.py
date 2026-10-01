"""Sensitivity of weights to sampling noise in expected returns (PLAN 5.1, instruction 05 amendment 5.1).

At each date in sensitivity.dates, mu_hat is perturbed by eps ~ N(0, Sigma_lw_cc / 36) and the
Black-Litterman view returns Q by eps_Q ~ N(0, P Sigma_lw_cc P' / 11), 11 being the months in
the momentum window (convention 23). Every strategy is re-optimised with w_prev = None on each
draw. Min variance, risk parity and HRP do not read mu; they are run on the same perturbed mu
and shown as zero-dispersion references.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pc.allocators import (  # noqa: E402
    AllocResult,
    black_litterman,
    min_variance,
    mv_constrained,
    mv_unconstrained,
    risk_parity,
)
from pc.backtest import DateInputs, constraint_sets, monthly_total_returns  # noqa: E402
from pc.bl import bl_posterior  # noqa: E402
from pc.calendar import build_calendar  # noqa: E402
from pc.config import Config  # noqa: E402
from pc.data import load_prices, load_rf_daily  # noqa: E402
from pc.hrp import hrp  # noqa: E402
from pc.returns import daily_returns, monthly_excess_returns  # noqa: E402
from pc.returns_model import mu_bayes_stein  # noqa: E402
from pc.stats import CSV_KWARGS  # noqa: E402

# Amendment 5.1: the 4 mu-based strategies, then the 3 references. The references use
# Sigma_lw_cc (decisions/OPEN.md, item 7, implemented as option 1).
MU_STRATEGIES = [
    "mv_unconstrained|sample|sample|A",
    "mv_constrained|lw_cc|sample|B",
    "mv_constrained|lw_cc|bayes_stein|B",
    "black_litterman|lw_cc|bl|B",
]
REFERENCE_STRATEGIES = [
    "min_variance|lw_cc|none|B",
    "risk_parity|lw_cc|none|none",
    "hrp|lw_cc|none|none",
]
STRATEGIES = MU_STRATEGIES + REFERENCE_STRATEGIES
# The quantiles named by the sensitivity.csv columns p05, p25, p50, p75 and p95 (PLAN 5.1).
QUANTILES = {"p05": 0.05, "p25": 0.25, "p50": 0.50, "p75": 0.75, "p95": 0.95}
SENSITIVITY_COLUMNS = ["date", "strategy", "ticker", "w_base", *QUANTILES, "iqr"]
SUMMARY_COLUMNS = ["date", "strategy", "mean_abs_change", "frac_top_asset_changes"]
DPI = 150  # kickoff Section 6: figures at 150 dpi


@dataclass
class DateDraws:
    """One sensitivity date: base weights (N,) and weights per draw (draws, N) by strategy, the
    perturbations, and a record of the solver calls."""

    date: pd.Timestamp
    tickers: list[str]
    base: dict[str, np.ndarray]
    draws: dict[str, np.ndarray]
    eps: np.ndarray
    eps_q: np.ndarray
    solver_log: pd.DataFrame


def momentum_months(cfg: Config) -> int:
    """Months in the 12-1 momentum window: mom_lookback - mom_skip (11; convention 23)."""
    return cfg.bl.mom_lookback - cfg.bl.mom_skip


def perturbations(Sigma_lw: pd.DataFrame, P: pd.DataFrame, k: int, cfg: Config) -> tuple[np.ndarray, np.ndarray]:
    """(eps, eps_Q) for the k-th date (0-based) in sensitivity.dates.

    One generator per date, default_rng(run.sensitivity_seed + k). Z (draws x N) is drawn
    first, then Z_Q (draws x views). eps = Z L', L = chol(Sigma_lw / window_months);
    eps_Q = Z_Q L_Q', L_Q = chol(P Sigma_lw P' / momentum_months).
    """
    S = Sigma_lw.to_numpy(dtype=float)
    p = P.to_numpy(dtype=float)
    n_draws = cfg.sensitivity.draws
    rng = np.random.default_rng(cfg.run.sensitivity_seed + k)
    Z = rng.standard_normal((n_draws, S.shape[0]))
    Z_q = rng.standard_normal((n_draws, p.shape[0]))
    L = np.linalg.cholesky(S / cfg.sample.window_months)
    L_q = np.linalg.cholesky(p @ S @ p.T / momentum_months(cfg))
    return Z @ L.T, Z_q @ L_q.T


def strategy_solvers(inputs: DateInputs, cfg: Config) -> dict:
    """strategy -> f(mu_draw, q_draw) -> AllocResult, with w_prev = None throughout (amendment 5.1).

    mv_unconstrained uses the sample Sigma; the 3 set B strategies and the references use
    Sigma_lw_cc. Bayes-Stein shrinks mu_hat + eps. Black-Litterman perturbs Q only. The
    references are given mu_hat + eps, which they do not read.
    """
    cons = constraint_sets(cfg)
    S_sample = inputs.sigma("sample")[0]
    S_lw = inputs.sigma("lw_cc")[0]
    P, _ = inputs.views()
    Pi = inputs.pi("lw_cc")
    T = cfg.sample.window_months

    def bl(mu, q):
        mu_bl, S_bl = bl_posterior(S_lw, Pi, P, q, cfg.bl.tau)
        return black_litterman(mu_bl, S_bl, None, cons["B"])

    return {
        "mv_unconstrained|sample|sample|A": lambda mu, q: mv_unconstrained(mu, S_sample, None, cons["A"]),
        "mv_constrained|lw_cc|sample|B": lambda mu, q: mv_constrained(mu, S_lw, None, cons["B"]),
        "mv_constrained|lw_cc|bayes_stein|B":
            lambda mu, q: mv_constrained(mu_bayes_stein(mu, S_lw, T)[0], S_lw, None, cons["B"]),
        "black_litterman|lw_cc|bl|B": bl,
        "min_variance|lw_cc|none|B": lambda mu, q: min_variance(mu, S_lw, None, cons["B"]),
        "risk_parity|lw_cc|none|none": lambda mu, q: risk_parity(mu, S_lw, None, cons["none"]),
        "hrp|lw_cc|none|none": lambda mu, q: hrp(mu, S_lw, None, cons["none"]),
    }


def sensitivity_at(inputs: DateInputs, k: int, cfg: Config) -> DateDraws:
    """Base weights and the weights on every draw, for the 7 strategies at one date."""
    tickers = list(cfg.universe.tickers)
    mu_hat = inputs.mu_sample
    _, Q = inputs.views()
    eps, eps_q = perturbations(inputs.sigma("lw_cc")[0], inputs.views()[0], k, cfg)
    solvers = strategy_solvers(inputs, cfg)
    base, draws, log = {}, {}, []

    def record(sid: str, j: int, res: AllocResult, seconds: float) -> np.ndarray:
        log.append({"strategy": sid, "draw": j, "solver": res.solver, "status": res.status,
                    "fallback": res.fallback, "seconds": seconds})
        return res.weights.to_numpy(dtype=float)

    for sid in STRATEGIES:
        f = solvers[sid]
        start = time.perf_counter()
        res = f(mu_hat, Q)
        base[sid] = record(sid, -1, res, time.perf_counter() - start)
        W = np.empty((len(eps), len(tickers)))
        for j in range(len(eps)):
            start = time.perf_counter()
            res = f(mu_hat + pd.Series(eps[j], index=mu_hat.index), Q + pd.Series(eps_q[j], index=Q.index))
            W[j] = record(sid, j, res, time.perf_counter() - start)
        draws[sid] = W
    return DateDraws(pd.Timestamp(inputs.t), tickers, base, draws, eps, eps_q, pd.DataFrame(log))


def summarise(dd: DateDraws) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(sensitivity rows, summary rows) for one date.

    Quantiles are np.quantile with numpy's default rule; iqr = p75 - p25.
    mean_abs_change = mean over draws of sum_i |w_draw,i - w_base,i|.
    frac_top_asset_changes = the share of draws whose argmax ticker differs from the base argmax.
    """
    rows, summary = [], []
    for sid in STRATEGIES:
        W, w0 = dd.draws[sid], dd.base[sid]
        q = np.quantile(W, list(QUANTILES.values()), axis=0)
        frame = pd.DataFrame({"date": dd.date, "strategy": sid, "ticker": dd.tickers, "w_base": w0})
        for name, row in zip(QUANTILES, q):
            frame[name] = row
        frame["iqr"] = frame["p75"] - frame["p25"]
        rows.append(frame)
        summary.append({
            "date": dd.date, "strategy": sid,
            "mean_abs_change": float(np.abs(W - w0).sum(axis=1).mean()),
            "frac_top_asset_changes": float(np.mean(W.argmax(axis=1) != w0.argmax())),
        })
    return pd.concat(rows, ignore_index=True)[SENSITIVITY_COLUMNS], pd.DataFrame(summary, columns=SUMMARY_COLUMNS)


def plot_sensitivity(sens: pd.DataFrame, summary: pd.DataFrame, date: pd.Timestamp, path: Path) -> None:
    """Chart 3: one panel per strategy at one date. Boxes p25 to p75 with the median at p50,
    whiskers p05 to p95, no fliers; each panel has its own y-axis; the title gives mean_abs_change."""
    sens = sens[sens["date"] == date]
    summary = summary[summary["date"] == date].set_index("strategy")
    ncols = 2
    nrows = -(-len(STRATEGIES) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 3.2 * nrows))
    axes = axes.ravel()
    for ax, sid in zip(axes, STRATEGIES):
        s = sens[sens["strategy"] == sid]
        stats = [{"label": r.ticker, "med": r.p50, "q1": r.p25, "q3": r.p75, "whislo": r.p05, "whishi": r.p95}
                 for r in s.itertuples()]
        ax.bxp(stats, showfliers=False, widths=0.6)
        ax.axhline(0, color="0.6", lw=0.6)
        ax.set_title(f"{sid}\nmean_abs_change {summary.loc[sid, 'mean_abs_change']:.4f}", fontsize=9)
        ax.tick_params(axis="x", labelrotation=90, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.grid(axis="y", alpha=0.3)
    for ax in axes[len(STRATEGIES):]:
        ax.set_visible(False)
    fig.suptitle(f"Weights under sampling noise in expected returns, {date.date()} "
                 "(box p25 to p75, line p50, whiskers p05 to p95)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


def load_inputs(cfg: Config):
    """(returns_d, monthly_excess, monthly_total, decision dates) from the committed data."""
    prices = load_prices(cfg)
    rf_daily = load_rf_daily(cfg, prices.index)
    cal = build_calendar(prices.index, cfg)
    return (daily_returns(prices), monthly_excess_returns(prices, rf_daily), monthly_total_returns(prices),
            pd.DatetimeIndex(cal["decision_date"]))


def run_sensitivity(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame, list[DateDraws]]:
    returns_d, monthly_excess, monthly_total, decisions = load_inputs(cfg)
    sens, summary, all_draws = [], [], []
    for k, d in enumerate(cfg.sensitivity.dates):
        t = pd.Timestamp(d)
        if t not in decisions:
            raise ValueError(f"sensitivity date {d} is not a decision date")
        dd = sensitivity_at(DateInputs(t, returns_d, monthly_excess, monthly_total, cfg), k, cfg)
        s, m = summarise(dd)
        sens.append(s)
        summary.append(m)
        all_draws.append(dd)
    return pd.concat(sens, ignore_index=True), pd.concat(summary, ignore_index=True), all_draws


def write_sensitivity(cfg: Config) -> tuple[list[Path], list[DateDraws]]:
    sens, summary, all_draws = run_sensitivity(cfg)
    tables, figures = Path(cfg.outputs.tables_dir), Path(cfg.outputs.figures_dir)
    paths = [tables / "sensitivity.csv", tables / "sensitivity_summary.csv", figures / "sensitivity_boxplots.png"]
    sens.to_csv(paths[0], **CSV_KWARGS)
    summary.to_csv(paths[1], **CSV_KWARGS)
    plot_sensitivity(sens, summary, pd.Timestamp(cfg.sensitivity.dates[-1]), paths[2])
    return paths, all_draws
