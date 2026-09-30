import numpy as np
import pandas as pd
import pytest
from pypfopt.risk_models import CovarianceShrinkage
from sklearn.covariance import LedoitWolf

from pc.calendar import build_calendar
from pc.cov import cov_lw_cc, cov_lw_identity, window_daily
from pc.data import load_prices
from pc.returns import daily_returns


def real_window(cfg) -> pd.DataFrame:
    rets = daily_returns(load_prices(cfg))
    return window_daily(rets, pd.Timestamp(cfg.sample.first_decision), cfg.sample.window_months)


def synthetic_panel(cfg) -> pd.DataFrame:
    """Gaussian panel, T = 100, N = 18, with a random positive definite covariance."""
    rng = np.random.default_rng(cfg.run.seed_master)
    N = len(cfg.universe.tickers)
    A = rng.standard_normal((N, N))
    cov = 1e-4 * (A @ A.T / N + 0.1 * np.eye(N))
    x = rng.multivariate_normal(np.zeros(N), cov, size=100)
    return pd.DataFrame(x, columns=list(cfg.universe.tickers))


PANELS = {"real_2010_04_30": real_window, "synthetic_T100": synthetic_panel}


@pytest.mark.parametrize("panel", PANELS)
def test_lw_cc_matches_pypfopt(cfg, panel):
    X = PANELS[panel](cfg)
    ours, delta = cov_lw_cc(X, ddof=1)
    cs = CovarianceShrinkage(X, returns_data=True, frequency=1)
    ref = cs.ledoit_wolf("constant_correlation")
    assert np.allclose(ours.to_numpy(), ref.to_numpy(), rtol=1e-10, atol=0)
    assert abs(delta - cs.delta) <= 1e-10


@pytest.mark.parametrize("panel", PANELS)
def test_lw_identity_matches_sklearn(cfg, panel):
    X = PANELS[panel](cfg)
    ours, shrinkage = cov_lw_identity(X)
    ref = LedoitWolf(assume_centered=False).fit(X.to_numpy())
    assert np.allclose(ours.to_numpy(), ref.covariance_, rtol=1e-10, atol=0)
    assert abs(shrinkage - ref.shrinkage_) <= 1e-10


def lw_cc_deltas_on_random_windows(cfg) -> pd.DataFrame:
    """delta at the 50 decision dates drawn with seed run.seed_master, in draw order."""
    prices = load_prices(cfg)
    rets = daily_returns(prices)
    cal = build_calendar(prices.index, cfg)
    picks = np.random.default_rng(cfg.run.seed_master).choice(len(cal), size=50, replace=False)
    dates = cal["decision_date"].iloc[picks]
    deltas = [cov_lw_cc(window_daily(rets, t, cfg.sample.window_months))[1] for t in dates]
    return pd.DataFrame({"decision_date": dates.to_numpy(), "delta": deltas})


def test_lw_cc_delta_in_unit_interval(cfg):
    deltas = lw_cc_deltas_on_random_windows(cfg)
    assert len(deltas) == 50
    assert deltas["decision_date"].is_unique
    assert ((deltas["delta"] >= 0) & (deltas["delta"] <= 1)).all()
