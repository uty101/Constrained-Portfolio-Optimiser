import math

import cvxpy as cp
import numpy as np
import pandas as pd
import pytest

from pc.allocators import solved_result
from pc.solver import TAU_RELAX, solve, turnover_feasibility


def _w_prev_above_cap(cfg):
    """Drifted weights with 0.45 in the first ticker and the rest spread equally."""
    tickers = list(cfg.universe.tickers)
    w = np.full(len(tickers), 0.55 / (len(tickers) - 1))
    w[0] = 0.45
    return pd.Series(w, index=tickers)


def test_tau_relaxed_when_drifted_weight_above_cap(cfg):
    w_prev = _w_prev_above_cap(cfg)
    tau_min, tau_eff, relaxed, record = turnover_feasibility(w_prev, 0.05, cfg.mv.lower, cfg.mv.upper)
    assert not record.fallback
    assert relaxed is True
    # 0.15 must leave the first ticker and land elsewhere: ||w - w_prev||_1 >= 0.30.
    assert abs(tau_min - 0.30) <= 1e-8
    assert abs(tau_eff - (0.30 + 1e-6)) <= 1e-8
    assert tau_eff == tau_min + TAU_RELAX


def test_tau_not_relaxed_when_feasible(cfg):
    n = len(cfg.universe.tickers)
    w_prev = pd.Series(1.0 / n, index=list(cfg.universe.tickers))
    tau_min, tau_eff, relaxed, record = turnover_feasibility(w_prev, 0.05, cfg.mv.lower, cfg.mv.upper)
    assert not record.fallback
    assert relaxed is False
    assert abs(tau_min) <= 1e-8
    assert tau_eff == 0.05


def _fail(self, *args, **kwargs):
    # Every solver "runs" and reports a non-optimal status.
    self._status = cp.OPTIMAL_INACCURATE
    return None


@pytest.mark.parametrize("has_w_prev", [True, False])
def test_fallback_returns_w_prev_on_solver_failure(cfg, monkeypatch, has_w_prev):
    tickers = list(cfg.universe.tickers)
    n = len(tickers)
    w_prev = _w_prev_above_cap(cfg) if has_w_prev else None
    w = cp.Variable(n)
    prob = cp.Problem(cp.Minimize(cp.sum_squares(w)), [cp.sum(w) == 1, w >= 0])

    monkeypatch.setattr(cp.Problem, "solve", _fail)
    record = solve(prob)
    assert record.fallback is True
    assert record.solvers == (cfg.solver.primary, cfg.solver.fallback)
    assert record.status == cp.OPTIMAL_INACCURATE

    res = solved_result(w, prob, [record], pd.Index(tickers), w_prev)
    assert res.fallback is True
    assert res.status == cp.OPTIMAL_INACCURATE
    assert res.solver == "CLARABEL+SCS"
    assert math.isnan(res.objective)
    expected = w_prev if has_w_prev else pd.Series(1.0 / n, index=tickers)
    pd.testing.assert_series_equal(res.weights, expected, check_exact=True, check_names=False)
