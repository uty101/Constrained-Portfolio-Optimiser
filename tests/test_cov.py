import numpy as np
import pandas as pd
import pytest

from pc.cov import (
    _daily_estimate,
    _monthly_unconditioned,
    _pca_corr,
    condition_cov,
    cov_ewma,
    cov_pca,
    cov_sample,
    estimate_cov,
    ewma_weights,
    window_daily,
)
from pc.calendar import build_calendar
from pc.data import load_prices
from pc.returns import daily_returns

TICKERS = list("ABCDEFGHIJKLMNOPQR")


@pytest.fixture
def returns_d(cfg):
    return daily_returns(load_prices(cfg))


@pytest.fixture
def X(returns_d, cfg):
    """The real daily window at the first decision date."""
    return window_daily(returns_d, pd.Timestamp(cfg.sample.first_decision), cfg.sample.window_months)


def spectral_matrix(eigenvalues: np.ndarray, seed: int) -> pd.DataFrame:
    """Q diag(eigenvalues) Q' with Q a random orthogonal matrix."""
    n = len(eigenvalues)
    Q, _ = np.linalg.qr(np.random.default_rng(seed).standard_normal((n, n)))
    A = Q @ np.diag(eigenvalues) @ Q.T
    return pd.DataFrame(0.5 * (A + A.T), index=TICKERS[:n], columns=TICKERS[:n])


def test_window_boundaries():
    """Calendar-month periods (convention 23). t is the 28th, so t - DateOffset(months) would
    have started on the 28th of an earlier month and taken in its 29th to 31st."""
    index = pd.bdate_range("2019-01-01", "2023-06-30", name="date")
    rets = pd.DataFrame({"A": np.arange(len(index), dtype=float)}, index=index)
    t = pd.Timestamp("2023-02-28")
    assert t in index

    for months, first_month, offset_extra in (
        (1, "2023-02", ["2023-01-30", "2023-01-31"]),
        (3, "2022-12", ["2022-11-29", "2022-11-30"]),
        (36, "2020-03", []),
    ):
        p0 = pd.Period(first_month, "M")
        expected = index[(index.to_period("M") >= p0) & (index <= t)]
        w = window_daily(rets, t, months)
        assert w.index.equals(expected)
        assert w.index[0] == index[index.to_period("M") == p0][0]
        assert w.index[-1] == t
        assert w.index.to_period("M").nunique() == months
        old = index[(index > t - pd.DateOffset(months=months)) & (index <= t)]
        assert list(old.difference(w.index)) == [pd.Timestamp(d) for d in offset_extra]

    # A date inside a month: rows after t are excluded, the month itself still counts.
    w = window_daily(rets, pd.Timestamp("2023-03-15"), 2)
    assert w.index[0] == pd.Timestamp("2023-02-01") and w.index[-1] == pd.Timestamp("2023-03-15")

    # Too few months of data raises.
    with pytest.raises(ValueError):
        window_daily(rets, pd.Timestamp("2019-06-28"), 36)


def test_window_matches_calendar_months_real(returns_d, cfg):
    cal = build_calendar(load_prices(cfg).index, cfg)
    days = returns_d.index
    months = cfg.sample.window_months
    assert len(cal) == cfg.sample.expected_n_decisions
    for t in cal["decision_date"]:
        w = window_daily(returns_d, t, months)
        first_month = t.to_period("M") - (months - 1)
        assert w.index[0] == days[days.to_period("M") == first_month][0], t
        assert w.index[-1] == t
        assert w.index.to_period("M").nunique() == months


def test_ridge_sets_cond_to_1e6(cfg):
    max_cond = cfg.cov.max_cond
    S = spectral_matrix(np.logspace(0, -9, 18), cfg.run.seed_master)
    out, log = condition_cov(S, max_cond)
    np.testing.assert_allclose(log["cond_before"], 1e9, rtol=1e-6)
    assert log["ridge"] > 0
    eig = np.linalg.eigvalsh(out.to_numpy())
    assert abs(eig[-1] / eig[0] / max_cond - 1) <= 1e-6
    assert abs(log["cond_after"] / max_cond - 1) <= 1e-6
    np.testing.assert_array_equal(out.to_numpy(), out.to_numpy().T)


def test_condition_cov_noop_when_well_conditioned(cfg):
    S = spectral_matrix(np.linspace(2.0, 1.0, 18), cfg.run.seed_master)
    out, log = condition_cov(S, cfg.cov.max_cond)
    assert log["ridge"] == 0.0
    assert log["cond_after"] == log["cond_before"]
    np.testing.assert_allclose(log["cond_before"], 2.0, rtol=1e-12)
    np.testing.assert_array_equal(out.to_numpy(), S.to_numpy())


def test_condition_cov_nonpositive_eigenvalue_is_inf_and_ridged(cfg):
    S = spectral_matrix(np.r_[np.linspace(1.0, 0.1, 17), -1e-3], cfg.run.seed_master)
    out, log = condition_cov(S, cfg.cov.max_cond)
    assert log["cond_before"] == np.inf
    eig = np.linalg.eigvalsh(out.to_numpy())
    assert eig[0] > 0
    assert log["cond_after"] == pytest.approx(cfg.cov.max_cond, rel=1e-6)


def test_ewma_weights_sum_to_one(X, cfg):
    w = ewma_weights(len(X), cfg.cov.ewma_lambda)
    assert abs(w.sum() - 1) <= 1e-12
    assert w[-1] == w.max()
    np.testing.assert_allclose(w[:-1] / w[1:], cfg.cov.ewma_lambda, rtol=1e-12)


def test_ewma_lambda_near_zero_is_last_outer_product(X):
    last = X.iloc[-1].to_numpy()
    out = cov_ewma(X, 1e-12)
    # The row before the last still carries weight ~1e-12, about 1e-15 in absolute terms.
    np.testing.assert_allclose(out.to_numpy(), np.outer(last, last), rtol=1e-10, atol=1e-14)
    assert list(out.index) == list(X.columns)


def sample_corr(X):
    S = cov_sample(X).to_numpy()
    sd = np.sqrt(np.diag(S))
    return S / np.outer(sd, sd)


def test_pca_rf_unit_diagonal(X, cfg):
    Rf = _pca_corr(sample_corr(X), cfg.cov.pca_k)
    np.testing.assert_allclose(np.diag(Rf), 1.0, rtol=0, atol=1e-14)


def test_pca_positive_definite(X, cfg):
    Sigma = cov_pca(X, cfg.cov.pca_k).to_numpy()
    np.testing.assert_array_equal(Sigma, Sigma.T)
    assert np.linalg.eigvalsh(Sigma)[0] > 0


def test_pca_full_rank_equals_sample(X):
    full = cov_pca(X, X.shape[1])
    assert np.allclose(full.to_numpy(), cov_sample(X).to_numpy(), rtol=1e-10, atol=0)

def test_monthly_is_daily_times_21_exactly(returns_d, X, cfg):
    t = pd.Timestamp(cfg.sample.first_decision)
    for name in cfg.cov.estimators:
        monthly, _ = _monthly_unconditioned(returns_d, t, name, cfg)
        daily, _ = _daily_estimate(X, name, cfg)
        assert (monthly.to_numpy() == 21 * daily.to_numpy()).all(), name


def test_conditioning_log_fields_always_present(returns_d, cfg):
    t = pd.Timestamp(cfg.sample.first_decision)
    for name in cfg.cov.estimators:
        Sigma, log = estimate_cov(returns_d, t, name, cfg)
        assert set(log) == {"cond_before", "cond_after", "ridge", "lw_delta"}, name
        assert log["cond_after"] <= cfg.cov.max_cond * (1 + 1e-6)
        assert np.isnan(log["lw_delta"]) == (name != "lw_cc")
        np.testing.assert_array_equal(Sigma.to_numpy(), Sigma.to_numpy().T)