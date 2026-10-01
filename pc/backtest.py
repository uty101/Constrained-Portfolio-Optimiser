"""Walk-forward engine (kickoff 5.7): the strategy registry and the monthly backtest."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pc.allocators import (
    Constraints,
    black_litterman,
    equal_weight,
    min_variance,
    mv_constrained,
    mv_unconstrained,
    risk_parity,
)
from pc.bl import bl_posterior, implied_returns, momentum_views
from pc.calendar import build_calendar
from pc.config import Config
from pc.cov import estimate_cov
from pc.data import load_prices, load_rf_daily
from pc.hrp import hrp
from pc.returns import _month_end_closes, daily_returns, holding_returns, holding_rf, monthly_excess_returns
from pc.returns_model import mu_bayes_stein, mu_sample


@dataclass(frozen=True)
class StrategySpec:
    allocator: str
    cov: str  # an estimator in cov.estimators, or "none"
    mu_model: str  # "sample", "bayes_stein", "bl" or "none"
    cons_set: str  # "A", "B", "C" or "none"
    id: str


def spec(allocator: str, cov: str, mu_model: str, cons_set: str) -> StrategySpec:
    return StrategySpec(allocator, cov, mu_model, cons_set, f"{allocator}|{cov}|{mu_model}|{cons_set}")


def build_registry(cfg: Config) -> list[StrategySpec]:
    """The 26 strategies of kickoff 5.7, in the order listed there; estimators in config order."""
    est = cfg.cov.estimators
    return [
        *(spec("mv_unconstrained", e, "sample", "A") for e in est),
        *(spec("mv_constrained", e, "sample", "C") for e in est),
        spec("mv_constrained", "lw_cc", "bayes_stein", "C"),
        *(spec("min_variance", e, "none", "B") for e in est),
        *(spec("risk_parity", e, "none", "none") for e in est),
        *(spec("black_litterman", e, "bl", "C") for e in est),
        *(spec("hrp", e, "none", "none") for e in est),
        spec("equal_weight", "none", "none", "none"),
    ]


# --- engine ---------------------------------------------------------------------------

PERIOD_COLUMNS = [
    "strategy_id", "decision_date", "exec_date", "next_exec_date", "ret_gross", "cost", "ret_net",
    "rf_hold", "excess_net", "forecast_vol_ann", "mu_exante", "turnover", "n_positions",
    "gross_leverage", "solver", "status", "fallback", "turnover_dual", "tau_relaxed", "tau_eff",
    "cond_before", "cond_after", "ridge", "ruined", "rp_converged",
]
WEIGHT_COLUMNS = [
    "strategy_id", "decision_date", "exec_date", "ticker", "w_target", "w_prev_drifted", "trade", "cost_i",
]

ALLOCATORS = {
    "mv_unconstrained": mv_unconstrained,
    "mv_constrained": mv_constrained,
    "min_variance": min_variance,
    "risk_parity": risk_parity,
    "black_litterman": black_litterman,
    "hrp": hrp,
    "equal_weight": equal_weight,
}

# Instruction 04, amendment 4.2.3: a strategy with cov "none" (equal_weight) is given the
# lw_cc Sigma, used only for forecast_vol_ann.
NO_COV_ESTIMATOR = "lw_cc"
# Basis points per unit: one_way_bp / 1e4 is the one-way cost in decimals (kickoff 4.6).
BP_PER_UNIT = 1e4
MONTHS_PER_YEAR = 12


def cost_vector(cfg: Config) -> pd.Series:
    """One-way cost c_i in decimals, config ticker order."""
    tickers = list(cfg.universe.tickers)
    return pd.Series([cfg.costs.one_way_bp[t] / BP_PER_UNIT for t in tickers], index=tickers, name="cost")


def constraint_sets(cfg: Config) -> dict[str, Constraints]:
    """Sets A, B, C and none (instruction 04, amendment 4.2.4)."""
    mv = cfg.mv
    return {
        "A": Constraints(lower=None, upper=None, gamma=mv.gamma),
        "B": Constraints(lower=mv.lower, upper=mv.upper, gamma=mv.gamma),
        "C": Constraints(lower=mv.lower, upper=mv.upper, max_turnover=mv.max_turnover,
                         cost=cost_vector(cfg), gamma=mv.gamma),
        "none": Constraints(),
    }


def monthly_total_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Month-end to month-end total returns, on the same index as monthly_excess_returns."""
    total = _month_end_closes(prices).pct_change(fill_method=None).iloc[1:]
    total.index = pd.DatetimeIndex(total.index, name="date")
    return total


def drift(w: pd.Series, r: pd.Series) -> pd.Series:
    """w_i (1 + r_i) / sum_j w_j (1 + r_j). Raises ValueError when the denominator is <= 0."""
    grown = w * (1 + r)
    total = float(grown.sum())
    if not total > 0:
        raise ValueError(f"drift denominator {total} <= 0: the fund has lost everything")
    return grown / total


class DateInputs:
    """mu and Sigma at one decision date, each computed once and shared across strategies."""

    def __init__(self, t, returns_d, monthly_excess, monthly_total, cfg):
        self.t, self.returns_d, self.cfg = t, returns_d, cfg
        self.monthly_excess, self.monthly_total = monthly_excess, monthly_total
        self.mu_sample = mu_sample(monthly_excess, t, cfg.sample.window_months)
        self._sigma, self._bl = {}, {}
        self._views = None
        self._mu_bs = None

    def sigma(self, est: str) -> tuple[pd.DataFrame, dict]:
        """Conditioned monthly Sigma and its log."""
        if est not in self._sigma:
            self._sigma[est] = estimate_cov(self.returns_d, self.t, est, self.cfg)
        return self._sigma[est]

    def mu_bayes_stein(self) -> pd.Series:
        """mu_bayes_stein(mu_sample, Sigma_lw_cc, 36)."""
        if self._mu_bs is None:
            Sigma_lw = self.sigma("lw_cc")[0]
            self._mu_bs = mu_bayes_stein(self.mu_sample, Sigma_lw, self.cfg.sample.window_months)[0]
        return self._mu_bs

    def bl(self, est: str) -> tuple[pd.Series, pd.DataFrame]:
        """(mu_BL, Sigma_BL): Pi = delta Sigma_cov w_mkt, the views at t, bl_posterior on Sigma_cov."""
        if est not in self._bl:
            if self._views is None:
                self._views = momentum_views(self.monthly_total, self.monthly_excess, self.t, self.cfg)
            P, Q = self._views
            Sigma = self.sigma(est)[0]
            w_mkt = pd.Series(self.cfg.bl.w_mkt)[list(self.cfg.universe.tickers)]
            Pi = implied_returns(Sigma, w_mkt, self.cfg.bl.delta)
            self._bl[est] = bl_posterior(Sigma, Pi, P, Q, self.cfg.bl.tau)
        return self._bl[est]

    def for_spec(self, spec: StrategySpec) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, dict]:
        """(mu passed, Sigma passed, Sigma_cov, Sigma_cov log) for one strategy (amendments 4.2.2, 4.2.3)."""
        est = NO_COV_ESTIMATOR if spec.cov == "none" else spec.cov
        Sigma_cov, log = self.sigma(est)
        if spec.mu_model == "bl":
            mu, Sigma = self.bl(est)
            return mu, Sigma, Sigma_cov, log
        if spec.mu_model == "bayes_stein":
            return self.mu_bayes_stein(), Sigma_cov, Sigma_cov, log
        if spec.mu_model in ("sample", "none"):
            return self.mu_sample, Sigma_cov, Sigma_cov, log
        raise ValueError(f"unknown mu_model {spec.mu_model!r}")


def _ruined_row(spec: StrategySpec, row) -> dict:
    """A month after ruin: kept with NaN returns, not solved (amendment 4.2.8)."""
    nan = math.nan
    return {
        "strategy_id": spec.id, "decision_date": row.decision_date, "exec_date": row.exec_date,
        "next_exec_date": row.next_exec_date, "ret_gross": nan, "cost": nan, "ret_net": nan,
        "rf_hold": nan, "excess_net": nan, "forecast_vol_ann": nan, "mu_exante": nan, "turnover": nan,
        "n_positions": nan, "gross_leverage": nan, "solver": "none", "status": "not_solved",
        "fallback": False, "turnover_dual": nan, "tau_relaxed": False, "tau_eff": nan,
        "cond_before": nan, "cond_after": nan, "ridge": nan, "ruined": True, "rp_converged": True,
    }


def _sort(frame: pd.DataFrame, specs: list[StrategySpec]) -> pd.DataFrame:
    """Registry order, then decision date; the row order within a key is kept."""
    order = {s.id: i for i, s in enumerate(specs)}
    return frame.sort_values(
        ["strategy_id", "decision_date"],
        key=lambda col: col.map(order) if col.name == "strategy_id" else col,
        kind="stable", ignore_index=True,
    )


def walk_forward(
    specs: list[StrategySpec], prices: pd.DataFrame, rf_daily: pd.Series, cfg: Config
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    """run_walk_forward, plus wall seconds per strategy id (allocation and bookkeeping) and under
    "shared" (mu and Sigma at each date, each computed once and reused by every strategy)."""
    tickers = list(cfg.universe.tickers)
    if list(prices.columns) != tickers:
        raise ValueError("prices columns are not the configured tickers in config order")
    returns_d = daily_returns(prices)
    monthly_excess = monthly_excess_returns(prices, rf_daily)
    monthly_total = monthly_total_returns(prices)
    cal = build_calendar(prices.index, cfg)
    if not (cal["next_exec_date"].iloc[:-1].to_numpy() == cal["exec_date"].iloc[1:].to_numpy()).all():
        raise ValueError("holding periods are not contiguous")
    hold = holding_returns(prices, cal)
    rf_h = holding_rf(rf_daily, cal)
    cons = constraint_sets(cfg)
    c = cost_vector(cfg)
    threshold = cfg.positions.threshold

    w_last: dict[str, pd.Series | None] = {s.id: None for s in specs}
    ruined = {s.id: False for s in specs}
    seconds = {s.id: 0.0 for s in specs}
    seconds["shared"] = 0.0
    periods, weights = [], []

    for k, row in enumerate(cal.itertuples(index=False)):
        t = row.decision_date
        start = time.perf_counter()
        inputs = DateInputs(t, returns_d, monthly_excess, monthly_total, cfg)
        seconds["shared"] += time.perf_counter() - start
        r = hold.iloc[k]
        rf = float(rf_h.iloc[k])
        for spec in specs:
            if ruined[spec.id]:
                periods.append(_ruined_row(spec, row))
                continue
            start = time.perf_counter()
            mu, Sigma, Sigma_cov, log = inputs.for_spec(spec)
            mid = time.perf_counter()
            seconds["shared"] += mid - start

            w_prev = None if w_last[spec.id] is None else drift(w_last[spec.id], hold.iloc[k - 1])
            res = ALLOCATORS[spec.allocator](mu, Sigma, w_prev, cons[spec.cons_set])
            w = res.weights.astype(float)
            if w_prev is None:
                trade = pd.Series(math.nan, index=tickers)
                cost_i = pd.Series(0.0, index=tickers)
                turnover, cost = math.nan, 0.0
            else:
                trade = w - w_prev
                cost_i = c * trade.abs()
                turnover, cost = float(trade.abs().sum()), float(cost_i.sum())
            gross = float(w @ r)
            net = (1 - cost) * (1 + gross) - 1
            is_ruined = net <= -1
            if is_ruined:
                net = -1.0
            S = Sigma_cov.to_numpy(dtype=float)
            wv = w.to_numpy()
            periods.append({
                "strategy_id": spec.id, "decision_date": t, "exec_date": row.exec_date,
                "next_exec_date": row.next_exec_date, "ret_gross": gross, "cost": cost, "ret_net": net,
                "rf_hold": rf, "excess_net": net - rf,
                "forecast_vol_ann": math.sqrt(MONTHS_PER_YEAR * float(wv @ S @ wv)),
                "mu_exante": float(mu @ w), "turnover": turnover,
                "n_positions": int((w.abs() >= threshold).sum()), "gross_leverage": float(w.abs().sum()),
                "solver": res.solver, "status": res.status, "fallback": bool(res.fallback),
                "turnover_dual": float(res.turnover_dual), "tau_relaxed": bool(res.tau_relaxed),
                "tau_eff": float(res.tau_eff), "cond_before": log["cond_before"],
                "cond_after": log["cond_after"], "ridge": log["ridge"], "ruined": bool(is_ruined),
                "rp_converged": spec.allocator != "risk_parity" or res.status == "optimal",
            })
            weights.append(pd.DataFrame({
                "strategy_id": spec.id, "decision_date": t, "exec_date": row.exec_date, "ticker": tickers,
                "w_target": wv,
                "w_prev_drifted": math.nan if w_prev is None else w_prev.to_numpy(),
                "trade": trade.to_numpy(), "cost_i": cost_i.to_numpy(),
            }))
            w_last[spec.id] = w
            ruined[spec.id] = is_ruined
            seconds[spec.id] += time.perf_counter() - mid

    periods = _sort(pd.DataFrame(periods, columns=PERIOD_COLUMNS), specs)
    weights = _sort(pd.concat(weights, ignore_index=True)[WEIGHT_COLUMNS], specs)
    return weights, periods, seconds


def run_walk_forward(specs, prices, rf_daily, cfg) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(weights_long, periods) over the decision calendar (kickoff 4 and 5.7; instruction 04, 4.2).

    At each decision date t: mu and Sigma from data <= t; w_prev = the previous target
    drifted over (exec_{t-1}, exec_t] and renormalised; solve; cost sum_i c_i |w_i - w_prev_i|
    charged at execution; net = (1 - cost)(1 + w'r) - 1, r the gross asset returns over
    (exec_t, next_exec_t]. First period: w_prev None (no turnover constraint, no cost term),
    cost 0, turnover NaN, trade NaN, w_prev_drifted NaN. Ruin: the month whose net <= -1 is
    kept with net = -1 and ruined True; later months are kept in periods with NaN returns and
    ruined True, are not solved, and have no weights_long rows.
    """
    weights, periods, _ = walk_forward(specs, prices, rf_daily, cfg)
    return weights, periods


def write_walk_forward(cfg: Config) -> tuple[list[Path], dict[str, float]]:
    """Run the 26 strategies on the committed data and write the two parquet files."""
    prices = load_prices(cfg)
    rf_daily = load_rf_daily(cfg, prices.index)
    weights, periods, seconds = walk_forward(build_registry(cfg), prices, rf_daily, cfg)
    out = Path(cfg.outputs.results_dir)
    paths = [out / "weights_long.parquet", out / "periods.parquet"]
    weights.to_parquet(paths[0], index=False)
    periods.to_parquet(paths[1], index=False)
    return paths, seconds
