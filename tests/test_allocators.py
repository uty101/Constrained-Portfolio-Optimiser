import itertools

import cvxpy as cp
import numpy as np
import pandas as pd
import pytest
from conftest import REAL_DATES

from pc.allocators import Constraints, min_variance, mv_unconstrained
from pc.risk import gmv_closed_form
from pc.solver import solver_config

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
