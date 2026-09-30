"""Covariance forecast evaluation over the decision calendar.

At each decision date every estimator forecasts the variance of 3 portfolio sets held
fixed over the holding period (exec_date, next_exec_date]: ew (1/N), gmv (budget-only
closed form from that estimator) and random (n_random long-only Dirichlet(1,...,1)
portfolios, drawn once, the same at every date).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pc.calendar import build_calendar
from pc.config import Config
from pc.cov import estimate_cov
from pc.data import load_prices
from pc.returns import daily_returns
from pc.risk import gmv_closed_form
from pc.stats import stationary_bootstrap_indices

PORTFOLIO_SETS = ("ew", "gmv", "random")
BASE_ESTIMATOR = "lw_cc"
# Kickoff 5.6: the 90% band for a well-calibrated forecast is 1 +/- 1.645 sqrt(1/(2n)).
BAND_Z = 1.645

EVAL_COLUMNS = ["estimator", "portfolio_set", "n", "qlike_mean", "bias_ratio", "band_lo", "band_hi",
                "mean_cond_before", "n_ridged"]
DIFF_COLUMNS = ["estimator", "portfolio_set", "diff_vs_lw_cc", "p05", "p95", "frac_le_0"]
BY_DATE_COLUMNS = ["decision_date", "estimator", "portfolio_set", "sigma2_hat", "sigma2_realised",
                   "r_h", "qlike"]
DIAG_COLUMNS = ["decision_date", "estimator", "cond_before", "cond_after", "ridge", "lw_delta"]


def random_portfolios(cfg: Config) -> pd.DataFrame:
    """n_random x N long-only Dirichlet(1,...,1) weights, seed run.cov_eval_seed."""
    tickers = list(cfg.universe.tickers)
    rng = np.random.default_rng(cfg.run.cov_eval_seed)
    W = rng.dirichlet(np.ones(len(tickers)), size=cfg.cov_eval.n_random)
    return pd.DataFrame(W, columns=tickers)


def qlike(sigma2_hat, sigma2_realised):
    return np.log(sigma2_hat) + sigma2_realised / sigma2_hat


def bias_band(n: int) -> tuple[float, float]:
    half = BAND_Z * np.sqrt(1 / (2 * n))
    return 1 - half, 1 + half


def holding_period_stats(W: np.ndarray, Sigma: np.ndarray, R: np.ndarray, n_hold_days: int,
                         days_per_month: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per portfolio (rows of W): forecast variance w'Sigma w * n_hold_days/days_per_month,
    realised variance sum_d (w'r_d)^2 and holding return sum_d w'r_d, R the holding-day returns.
    """
    sigma2_hat = np.einsum("pi,ij,pj->p", W, Sigma, W) * n_hold_days / days_per_month
    daily = R @ W.T
    return sigma2_hat, np.sum(daily**2, axis=0), np.sum(daily, axis=0)


def run_cov_eval(prices: pd.DataFrame, cfg: Config) -> dict[str, pd.DataFrame]:
    """The four output tables: cov_eval, cov_eval_qlike_diff, cov_eval_by_date, cov_diagnostics."""
    rets = daily_returns(prices)
    cal = build_calendar(prices.index, cfg)
    tickers = list(cfg.universe.tickers)
    N = len(tickers)
    W_sets = {"ew": None, "gmv": None, "random": random_portfolios(cfg).to_numpy()}
    W_ew = np.full((1, N), 1 / N)
    D = len(cal)

    # arrays[(estimator, set)][stat] has shape (dates, portfolios)
    arrays = {(e, s): {} for e in cfg.cov.estimators for s in PORTFOLIO_SETS}
    for key in arrays:
        P = cfg.cov_eval.n_random if key[1] == "random" else 1
        for stat in ("sigma2_hat", "sigma2_realised", "r_h"):
            arrays[key][stat] = np.empty((D, P))
    diagnostics = []

    for i, row in enumerate(cal.itertuples()):
        R = rets.loc[(rets.index > row.exec_date) & (rets.index <= row.next_exec_date)].to_numpy()
        if len(R) != row.n_hold_days:
            raise ValueError(f"{len(R)} holding days at {row.decision_date.date()}, expected {row.n_hold_days}")
        for est in cfg.cov.estimators:
            Sigma, log = estimate_cov(rets, row.decision_date, est, cfg)
            diagnostics.append({"decision_date": row.decision_date, "estimator": est, **log})
            W_sets["ew"] = W_ew
            W_sets["gmv"] = gmv_closed_form(Sigma).to_numpy()[None, :]
            for s in PORTFOLIO_SETS:
                out = holding_period_stats(W_sets[s], Sigma.to_numpy(), R, row.n_hold_days,
                                           cfg.sample.days_per_month)
                for stat, values in zip(("sigma2_hat", "sigma2_realised", "r_h"), out):
                    arrays[(est, s)][stat][i] = values

    diag = pd.DataFrame(diagnostics)[DIAG_COLUMNS]
    dates = cal["decision_date"].to_numpy()
    idx = stationary_bootstrap_indices(D, cfg.bootstrap.mean_block, cfg.bootstrap.reps, cfg.run.bootstrap_seed)

    eval_rows, by_date, q_by_date = [], [], {}
    for (est, s), a in arrays.items():
        q = qlike(a["sigma2_hat"], a["sigma2_realised"])
        q_by_date[(est, s)] = q.mean(axis=1)
        z = a["r_h"] / np.sqrt(a["sigma2_hat"])
        lo, hi = bias_band(D)
        d = diag[diag["estimator"] == est]
        eval_rows.append({
            "estimator": est, "portfolio_set": s, "n": D,
            "qlike_mean": q_by_date[(est, s)].mean(),
            "bias_ratio": z.std(axis=0, ddof=1).mean(),
            "band_lo": lo, "band_hi": hi,
            "mean_cond_before": d["cond_before"].mean(),
            "n_ridged": int((d["ridge"] > 0).sum()),
        })
        by_date.append(pd.DataFrame({
            "decision_date": dates, "estimator": est, "portfolio_set": s,
            "sigma2_hat": a["sigma2_hat"].mean(axis=1),
            "sigma2_realised": a["sigma2_realised"].mean(axis=1),
            "r_h": a["r_h"].mean(axis=1),
            "qlike": q_by_date[(est, s)],
        }))

    diff_rows = []
    for est in cfg.cov.estimators:
        if est == BASE_ESTIMATOR:
            continue
        for s in PORTFOLIO_SETS:
            d = q_by_date[(est, s)] - q_by_date[(BASE_ESTIMATOR, s)]
            boot = d[idx].mean(axis=1)
            p05, p95 = np.quantile(boot, cfg.bootstrap.ci)
            diff_rows.append({
                "estimator": est, "portfolio_set": s, "diff_vs_lw_cc": d.mean(),
                "p05": p05, "p95": p95, "frac_le_0": float(np.mean(boot <= 0)),
            })

    by_date = pd.concat(by_date, ignore_index=True)
    order = {e: k for k, e in enumerate(cfg.cov.estimators)}
    by_date = by_date.sort_values(
        ["decision_date", "estimator", "portfolio_set"],
        key=lambda c: c.map(order) if c.name == "estimator" else c,
        kind="stable", ignore_index=True,
    )
    return {
        "cov_eval": pd.DataFrame(eval_rows)[EVAL_COLUMNS],
        "cov_eval_qlike_diff": pd.DataFrame(diff_rows)[DIFF_COLUMNS],
        "cov_eval_by_date": by_date[BY_DATE_COLUMNS],
        "cov_diagnostics": diag,
    }


def write_cov_eval(cfg: Config) -> list[Path]:
    tables = run_cov_eval(load_prices(cfg), cfg)
    out = Path(cfg.outputs.tables_dir)
    kwargs = dict(index=False, float_format="%.10g", date_format="%Y-%m-%d", lineterminator="\n")
    paths = []
    for name, table in tables.items():
        path = out / f"{name}.csv"
        table.to_csv(path, **kwargs)
        paths.append(path)
    return paths
