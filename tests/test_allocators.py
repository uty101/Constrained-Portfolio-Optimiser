import itertools

import cvxpy as cp
import numpy as np
import pandas as pd
import pytest
from conftest import REAL_DATES

from pc.allocators import Constraints, min_variance, mv_constrained, mv_problem, mv_unconstrained, risk_parity
from pc.risk import gmv_closed_form, pct_risk_contributions
from pc.solver import solve, solver_config

CASES = list(itertools.product(REAL_DATES, ("sample", "lw_cc", "ewma", "pca3")))


def _clarabel_opts():
    tol = solver_config().clarabel_tol
    return {"tol_gap_abs": tol, "tol_gap_rel": tol, "tol_feas": tol}


def _clean(res):
    """No fallback and no SCS retry."""
    assert not res.fallback, res.status
    assert "SCS" not in res.solver, res.solver
    assert res.status == "optimal"


def _set_b(cfg, **kw):
    return Constraints(lower=cfg.mv.lower, upper=cfg.mv.upper, gamma=cfg.mv.gamma, **kw)


def set_a_reference(mu, Sigma, gamma):
    """Set A mean-variance by cvxpy: max mu'w - gamma/2 w'Sigma w s.t. 1'w = 1."""
    w = cp.Variable(len(mu))
    S = Sigma.to_numpy()
    prob = cp.Problem(cp.Maximize(mu.to_numpy() @ w - gamma / 2 * cp.quad_form(w, 0.5 * (S + S.T))), [cp.sum(w) == 1])
    prob.solve(solver="CLARABEL", **_clarabel_opts())
    assert prob.status == "optimal"
    return pd.Series(w.value, index=mu.index)


@pytest.mark.parametrize("t,name", CASES)
def test_mv_unconstrained_matches_cvxpy_budget_only(real, cfg, t, name):
    Sigma, mu = real.sigma(t, name), real.mu(t)
    res = mv_unconstrained(mu, Sigma, None, Constraints(gamma=cfg.mv.gamma))
    ref = set_a_reference(mu, Sigma, cfg.mv.gamma)
    assert np.max(np.abs(res.weights - ref)) <= 1e-7
    assert abs(res.weights.sum() - 1) <= 1e-12


@pytest.mark.parametrize("t,name", CASES)
def test_budget_only_min_variance_matches_closed_form(real, t, name):
    Sigma = real.sigma(t, name)
    res = min_variance(None, Sigma, None, Constraints(lower=None, upper=None))
    _clean(res)
    assert np.max(np.abs(res.weights - gmv_closed_form(Sigma))) <= 1e-7


@pytest.mark.parametrize("t,name", CASES)
def test_min_variance_set_b_respects_bounds(real, cfg, t, name):
    res = min_variance(None, real.sigma(t, name), None, _set_b(cfg))
    _clean(res)
    w = res.weights
    assert w.min() >= cfg.mv.lower - 1e-9
    assert w.max() <= cfg.mv.upper + 1e-9
    assert abs(w.sum() - 1) <= 1e-9


def test_index_mismatch_raises(real):
    Sigma = real.sigma(REAL_DATES[0], "lw_cc")
    mu = real.mu(REAL_DATES[0])
    with pytest.raises(ValueError):
        mv_unconstrained(mu.iloc[::-1], Sigma, None, Constraints())
    with pytest.raises(ValueError):
        min_variance(mu, Sigma, mu.iloc[1:], Constraints())


def _costs(cfg):
    # one_way_bp in basis points -> decimals.
    return pd.Series(cfg.costs.one_way_bp, dtype=float) / 1e4


def _equal(cfg):
    n = len(cfg.universe.tickers)
    return pd.Series(1.0 / n, index=list(cfg.universe.tickers))


def _drifted_above_cap(cfg):
    n = len(cfg.universe.tickers)
    w = np.full(n, 0.55 / (n - 1))
    w[0] = 0.45
    return pd.Series(w, index=list(cfg.universe.tickers))


@pytest.mark.parametrize("t", REAL_DATES)
def test_mv_constrained_no_tau_no_cost_equals_set_b(real, cfg, t):
    """w_prev given with cost None and no tau still builds the zero-cost |w - w_prev| term."""
    Sigma, mu = real.sigma(t, "sample"), real.mu(t)
    with_term = mv_constrained(mu, Sigma, _equal(cfg), _set_b(cfg))
    set_b = mv_constrained(mu, Sigma, None, _set_b(cfg))
    _clean(with_term)
    _clean(set_b)
    assert np.isnan(with_term.turnover_dual) and np.isnan(with_term.tau_eff)
    assert np.max(np.abs(with_term.weights - set_b.weights)) <= 1e-7


@pytest.mark.parametrize("name", ("sample", "lw_cc", "ewma", "pca3"))
def test_mv_constrained_kkt_stationarity(real, cfg, name):
    """Smooth set B: mu - gamma Sigma w - nu 1 + lambda_lo - lambda_hi = 0 from cvxpy's duals."""
    t = "2016-06-30"
    Sigma, mu = real.sigma(t, name), real.mu(t)
    cons = _set_b(cfg)
    prob, w, c = mv_problem(mu, Sigma, None, cons, None)
    record = solve(prob)
    assert not record.fallback and record.solvers == ("CLARABEL",)
    x = w.value
    S = Sigma.to_numpy()
    resid = (
        mu.to_numpy()
        - cons.gamma * (0.5 * (S + S.T)) @ x
        - c["budget"].dual_value
        + c["lower"].dual_value
        - c["upper"].dual_value
    )
    assert np.max(np.abs(resid)) < 1e-6
    np.testing.assert_array_equal(x, mv_constrained(mu, Sigma, None, cons).weights.to_numpy())


@pytest.mark.parametrize("t", REAL_DATES)
def test_turnover_dual_nonnegative_and_zero_when_slack(real, cfg, t):
    Sigma, mu = real.sigma(t, "lw_cc"), real.mu(t)
    w_prev = _equal(cfg)
    binding = mv_constrained(mu, Sigma, w_prev, _set_b(cfg, max_turnover=0.05, cost=_costs(cfg)))
    # Two long-only portfolios are at most 2 apart in L1, so tau = 2 is never binding.
    slack = mv_constrained(mu, Sigma, w_prev, _set_b(cfg, max_turnover=2.0, cost=_costs(cfg)))
    for res in (binding, slack):
        _clean(res)
        assert res.tau_relaxed is False
        assert res.turnover_dual >= 0
    assert abs((binding.weights - w_prev).abs().sum() - 0.05) <= 1e-7
    assert binding.turnover_dual > 1e-8
    assert (slack.weights - w_prev).abs().sum() < 2.0 - 1e-3
    assert slack.turnover_dual <= 1e-8


@pytest.mark.parametrize("t", REAL_DATES)
def test_turnover_never_exceeds_tau_eff(real, cfg, t):
    Sigma, mu = real.sigma(t, "lw_cc"), real.mu(t)
    for w_prev, tau in itertools.product((_equal(cfg), _drifted_above_cap(cfg)), cfg.turnover_grid.taus):
        res = mv_constrained(mu, Sigma, w_prev, _set_b(cfg, max_turnover=tau, cost=_costs(cfg)))
        _clean(res)
        assert (res.weights - w_prev).abs().sum() <= res.tau_eff + 1e-7
        assert res.tau_eff >= tau
        assert res.tau_relaxed == (res.tau_eff > tau)


def _fail(self, *args, **kwargs):
    self._status = cp.OPTIMAL_INACCURATE
    return None


@pytest.mark.parametrize("allocator", ("min_variance", "mv_constrained"))
@pytest.mark.parametrize("has_w_prev", [True, False])
def test_allocator_fallback_holds_w_prev_or_equal_weight(real, cfg, monkeypatch, allocator, has_w_prev):
    Sigma, mu = real.sigma(REAL_DATES[0], "lw_cc"), real.mu(REAL_DATES[0])
    w_prev = _drifted_above_cap(cfg) if has_w_prev else None
    monkeypatch.setattr(cp.Problem, "solve", _fail)
    fn = {"min_variance": min_variance, "mv_constrained": mv_constrained}[allocator]
    res = fn(mu, Sigma, w_prev, _set_b(cfg, max_turnover=cfg.mv.max_turnover, cost=_costs(cfg)))
    assert res.fallback is True
    assert res.status == cp.OPTIMAL_INACCURATE
    assert res.solver.split("+")[-2:] == ["CLARABEL", "SCS"]
    expected = w_prev if has_w_prev else _equal(cfg)
    np.testing.assert_array_equal(res.weights.to_numpy(), expected.to_numpy())


@pytest.mark.parametrize("t,name", CASES)
def test_risk_parity_equal_contributions_real_sigma(real, t, name):
    Sigma = real.sigma(t, name)
    res = risk_parity(None, Sigma, None, Constraints())
    pct = pct_risk_contributions(res.weights, Sigma)
    assert np.max(np.abs(pct - 1 / len(pct))) <= 1e-6


@pytest.mark.parametrize("t,name", CASES)
def test_risk_parity_weights_positive_sum_to_one(real, t, name):
    res = risk_parity(None, real.sigma(t, name), None, Constraints())
    assert (res.weights > 0).all()
    assert abs(res.weights.sum() - 1) <= 1e-12
