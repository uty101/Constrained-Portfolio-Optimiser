import numpy as np
import pandas as pd
import pytest
from conftest import REAL_DATES

from pc.returns_model import mu_bayes_stein, mu_sample


def test_mu_sample_is_mean_of_36_months_ending_at_t(real, cfg):
    t = pd.Timestamp(cfg.sample.first_decision)
    mu = mu_sample(real.monthly_excess, t, cfg.sample.window_months)
    rows = real.monthly_excess.loc[:t].tail(cfg.sample.window_months)
    assert rows.index[0] == pd.Timestamp("2007-05-31") and rows.index[-1] == t
    pd.testing.assert_series_equal(mu, rows.mean())


@pytest.mark.parametrize("t", REAL_DATES)
def test_bayes_stein_phi_in_unit_interval(real, cfg, t):
    mu_bs, phi = mu_bayes_stein(real.mu(t), real.sigma(t, "lw_cc"), cfg.sample.window_months)
    assert 0 <= phi <= 1
    assert list(mu_bs.index) == list(cfg.universe.tickers)


def test_bayes_stein_constant_mu_unchanged(real, cfg):
    t = REAL_DATES[0]
    mu_hat = pd.Series(0.004, index=list(cfg.universe.tickers))
    mu_bs, phi = mu_bayes_stein(mu_hat, real.sigma(t, "lw_cc"), cfg.sample.window_months)
    # mu0 = mu_hat's common value, so the deviation is 0 and phi = 1.
    assert abs(phi - 1) <= 1e-12
    np.testing.assert_allclose(mu_bs.to_numpy(), mu_hat.to_numpy(), rtol=1e-12, atol=0)
