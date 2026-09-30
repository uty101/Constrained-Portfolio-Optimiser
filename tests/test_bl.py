import numpy as np
import pandas as pd
import pytest
from conftest import REAL_DATES

from pc.allocators import Constraints, black_litterman, equal_weight, mv_constrained, mv_unconstrained
from pc.bl import bl_posterior, implied_returns, momentum_views, momentum_window, omega, posterior


def _w_mkt(cfg):
    return pd.Series(cfg.bl.w_mkt, dtype=float)


def _views(real, cfg, t):
    return momentum_views(real.monthly_total, real.monthly_excess, pd.Timestamp(t), cfg)


@pytest.mark.parametrize("t", REAL_DATES)
def test_bl_no_views_returns_pi(real, cfg, t):
    Sigma = real.sigma(t, "lw_cc")
    Pi = implied_returns(Sigma, _w_mkt(cfg), cfg.bl.delta)
    P = pd.DataFrame(np.zeros((0, len(Sigma))), columns=Sigma.index)
    Q = pd.Series(np.zeros(0), index=P.index, dtype=float)
    mu_bl, Sigma_bl = bl_posterior(Sigma, Pi, P, Q, cfg.bl.tau)
    pd.testing.assert_series_equal(mu_bl, Pi, check_exact=True)
    S = Sigma.to_numpy()
    np.testing.assert_array_equal(Sigma_bl.to_numpy(), S + cfg.bl.tau * S)


@pytest.mark.parametrize("t", REAL_DATES)
def test_set_a_mv_on_pi_returns_w_mkt(real, cfg, t):
    """Uses Sigma, not Sigma_BL (convention 18)."""
    Sigma = real.sigma(t, "lw_cc")
    Pi = implied_returns(Sigma, _w_mkt(cfg), cfg.bl.delta)
    res = mv_unconstrained(Pi, Sigma, None, Constraints(gamma=cfg.bl.delta))
    assert np.max(np.abs(res.weights - _w_mkt(cfg))) <= 1e-8


@pytest.mark.parametrize("t", REAL_DATES)
def test_bl_tiny_omega_satisfies_views(real, cfg, t):
    Sigma = real.sigma(t, "lw_cc")
    Pi = implied_returns(Sigma, _w_mkt(cfg), cfg.bl.delta)
    P, Q = _views(real, cfg, t)
    mu_bl, _ = posterior(Sigma, Pi, P, Q, cfg.bl.tau, omega(Sigma, P, cfg.bl.tau) * 1e-10)
    assert np.max(np.abs(P.to_numpy() @ mu_bl.to_numpy() - Q.to_numpy())) <= 1e-6


def test_momentum_window_is_11_months_skipping_t(real, cfg):
    window = momentum_window(real.monthly_total, pd.Timestamp("2010-04-30"), cfg)
    expected = pd.DatetimeIndex(
        ["2009-05-29", "2009-06-30", "2009-07-31", "2009-08-31", "2009-09-30", "2009-10-30",
         "2009-11-30", "2009-12-31", "2010-01-29", "2010-02-26", "2010-03-31"],
        name="date",
    )
    pd.testing.assert_index_equal(window.index, expected)
    # Month t and month t - 12 are outside it: changing them changes no view.
    t = pd.Timestamp("2010-04-30")
    P, Q = _views(real, cfg, t)
    total, excess = real.monthly_total.copy(), real.monthly_excess.copy()
    for d in (pd.Timestamp("2010-04-30"), pd.Timestamp("2009-04-30")):
        total.loc[d] = np.arange(len(total.columns), dtype=float)
        excess.loc[d] = -np.arange(len(total.columns), dtype=float)
    P2, Q2 = momentum_views(total, excess, t, cfg)
    pd.testing.assert_frame_equal(P, P2)
    pd.testing.assert_series_equal(Q, Q2)


def _synthetic_monthly(cfg, per_ticker):
    """14 month-ends, each ticker's return constant across months, so equal values tie exactly."""
    idx = pd.DatetimeIndex(pd.date_range("2019-01-31", periods=14, freq="ME"), name="date")
    return pd.DataFrame(np.tile(per_ticker, (len(idx), 1)), index=idx, columns=list(cfg.universe.tickers))


def test_momentum_views_ties_by_config_order(cfg):
    tickers = list(cfg.universe.tickers)
    r = np.linspace(0.001, 0.018, len(tickers))[::-1].copy()  # distinct, highest first by default
    # Top boundary: 5 clear winners, then IWM (position 1) and XLV (8) tie for the 6th slot.
    top = ["SPY", "EFA", "EEM", "XLE", "XLF"]
    r[[tickers.index(s) for s in top]] = [0.050, 0.049, 0.048, 0.047, 0.046]
    r[tickers.index("IWM")] = r[tickers.index("XLV")] = 0.040
    # Bottom boundary: 5 clear losers, then XLK (6) and GLD (15) tie for the 13th/12th slot.
    bottom = ["SHY", "IEF", "TLT", "TIP", "VNQ"]
    r[[tickers.index(s) for s in bottom]] = [-0.050, -0.049, -0.048, -0.047, -0.046]
    r[tickers.index("XLK")] = r[tickers.index("GLD")] = -0.040
    monthly = _synthetic_monthly(cfg, r)
    P, _ = momentum_views(monthly, monthly, monthly.index[-1], cfg)
    row = P.loc["momentum"]
    k = cfg.bl.n_long_short
    # One ranking, highest first, ties by config order: IWM ranks above XLV, XLK above GLD.
    assert set(row[row > 0].index) == set(top + ["IWM"])
    assert set(row[row < 0].index) == set(bottom + ["GLD"])
    assert np.allclose(row[row > 0], 1 / k) and np.allclose(row[row < 0], -1 / k)
    assert row["XLV"] == 0 and row["XLK"] == 0
    sb = P.loc["stocks_bonds"]
    assert (sb[list(cfg.bl.equity_basket)] == 0.25).all() and np.allclose(sb[list(cfg.bl.bond_basket)], -1 / 3)
    assert sb.drop(list(cfg.bl.equity_basket) + list(cfg.bl.bond_basket)).eq(0).all()


def test_momentum_q_is_view_on_window_mean_excess(real, cfg):
    t = pd.Timestamp("2016-06-30")
    P, Q = _views(real, cfg, t)
    mean = momentum_window(real.monthly_excess, t, cfg).mean()
    long, short = P.columns[P.loc["momentum"] > 0], P.columns[P.loc["momentum"] < 0]
    assert abs(Q["momentum"] - (mean[long].mean() - mean[short].mean())) <= 1e-15
    eq, bd = list(cfg.bl.equity_basket), list(cfg.bl.bond_basket)
    assert abs(Q["stocks_bonds"] - (mean[eq].mean() - mean[bd].mean())) <= 1e-15


def test_equal_weight_is_one_over_n(real, cfg):
    Sigma = real.sigma(REAL_DATES[0], "lw_cc")
    res = equal_weight(None, Sigma, None, Constraints())
    np.testing.assert_array_equal(res.weights.to_numpy(), np.full(len(Sigma), 1 / len(Sigma)))
    assert list(res.weights.index) == list(cfg.universe.tickers)


def test_black_litterman_is_mv_constrained_on_posterior(real, cfg):
    t = "2020-02-28"
    Sigma = real.sigma(t, "lw_cc")
    P, Q = _views(real, cfg, t)
    mu_bl, Sigma_bl = bl_posterior(Sigma, implied_returns(Sigma, _w_mkt(cfg), cfg.bl.delta), P, Q, cfg.bl.tau)
    cons = Constraints(lower=cfg.mv.lower, upper=cfg.mv.upper, gamma=cfg.mv.gamma)
    a = black_litterman(mu_bl, Sigma_bl, None, cons)
    b = mv_constrained(mu_bl, Sigma_bl, None, cons)
    np.testing.assert_array_equal(a.weights.to_numpy(), b.weights.to_numpy())
