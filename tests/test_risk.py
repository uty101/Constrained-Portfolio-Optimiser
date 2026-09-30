import ast
from pathlib import Path

import numpy as np
import pandas as pd

import pc.risk

from pc.cov import estimate_cov
from pc.data import load_prices
from pc.returns import daily_returns
from pc.risk import gmv_closed_form, pct_risk_contributions, risk_contributions


def test_gmv_closed_form_sums_to_one(cfg):
    rets = daily_returns(load_prices(cfg))
    t = pd.Timestamp(cfg.sample.first_decision)
    for name in cfg.cov.estimators:
        Sigma, _ = estimate_cov(rets, t, name, cfg)
        w = gmv_closed_form(Sigma)
        assert abs(w.sum() - 1) <= 1e-12
        assert list(w.index) == list(cfg.universe.tickers)
        # First-order condition: Sigma w is proportional to 1.
        grad = Sigma.to_numpy() @ w.to_numpy()
        np.testing.assert_allclose(grad, grad.mean(), rtol=1e-8)


def _synthetic(cfg):
    """A random positive definite monthly Sigma and a long-short w summing to 1."""
    rng = np.random.default_rng(cfg.run.seed_master)
    tickers = list(cfg.universe.tickers)
    n = len(tickers)
    A = rng.standard_normal((n, n))
    Sigma = pd.DataFrame(1e-3 * (A @ A.T / n + 0.1 * np.eye(n)), index=tickers, columns=tickers)
    x = rng.standard_normal(n)
    w = pd.Series(x - (x.sum() - 1) / n, index=tickers)
    return w, Sigma


def test_rc_sums_to_fund_vol(cfg):
    w, Sigma = _synthetic(cfg)
    vol = np.sqrt(w.to_numpy() @ Sigma.to_numpy() @ w.to_numpy())
    rc = risk_contributions(w, Sigma)
    assert list(rc.index) == list(w.index)
    assert abs(rc.sum() - vol) <= 1e-12
    assert abs(pct_risk_contributions(w, Sigma).sum() - 1) <= 1e-12


def test_euler_identity(cfg):
    w, Sigma = _synthetic(cfg)
    x, S = w.to_numpy(), Sigma.to_numpy()
    vol = np.sqrt(x @ S @ x)
    grad = S @ x / vol  # d sigma / d w, analytic
    # Euler: sigma is homogeneous of degree 1, so w' grad = sigma, and w_i grad_i = RC_i.
    assert abs(x @ grad - vol) <= 1e-12
    np.testing.assert_allclose(x * grad, risk_contributions(w, Sigma).to_numpy(), rtol=0, atol=1e-15)
    # The analytic gradient against central differences.
    h = 1e-6
    fd = np.array([(np.sqrt((x + h * e) @ S @ (x + h * e)) - np.sqrt((x - h * e) @ S @ (x - h * e))) / (2 * h)
                   for e in np.eye(len(x))])
    np.testing.assert_allclose(grad, fd, rtol=1e-6, atol=0)


def test_risk_module_imports_nothing_from_pc():
    tree = ast.parse(Path(pc.risk.__file__).read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    assert all(not (m == "pc" or m.startswith("pc.") or m.startswith(".")) for m in modules), modules
    assert set(modules) <= {"__future__", "numpy", "pandas"}, modules
