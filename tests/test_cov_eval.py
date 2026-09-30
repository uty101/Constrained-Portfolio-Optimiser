import numpy as np
import pandas as pd

from pc.cov_eval import BAND_Z, bias_band, holding_period_stats, qlike, random_portfolios


def test_random_portfolios_fixed_and_long_only(cfg):
    W = random_portfolios(cfg)
    assert W.shape == (cfg.cov_eval.n_random, len(cfg.universe.tickers))
    assert list(W.columns) == list(cfg.universe.tickers)
    assert (W.to_numpy() >= 0).all()
    np.testing.assert_allclose(W.sum(axis=1), 1.0, rtol=0, atol=1e-12)
    # Drawn once from the seed: every call, so every date, gets the same 100.
    pd.testing.assert_frame_equal(W, random_portfolios(cfg))
    assert len(np.unique(W.to_numpy().round(12), axis=0)) == cfg.cov_eval.n_random


def test_qlike_on_synthetic_perfect_forecast():
    realised = np.array([1e-4, 4e-4, 2.5e-3])
    np.testing.assert_allclose(qlike(realised, realised), np.log(realised) + 1, rtol=0, atol=1e-15)
    # QLIKE is minimised in the forecast at the realised variance.
    for factor in (0.5, 0.9, 1.1, 2.0):
        assert (qlike(factor * realised, realised) > qlike(realised, realised)).all()

    # A forecast from the true covariance of iid returns matches expected realised variance.
    rng = np.random.default_rng(0)
    Sigma = np.array([[4e-4, 1e-4], [1e-4, 9e-4]])
    w = np.array([[0.5, 0.5]])
    R = rng.multivariate_normal(np.zeros(2), Sigma / 21, size=(20000, 21))
    s2_hat, s2_real, r_h = zip(*(holding_period_stats(w, Sigma, R[k], 21, 21) for k in range(len(R))))
    assert s2_hat[0][0] == (w @ Sigma @ w.T).item()
    assert abs(np.mean(s2_real) / s2_hat[0][0] - 1) < 0.01
    np.testing.assert_allclose(np.concatenate(r_h), [R[k].sum(axis=0) @ w[0] for k in range(len(R))],
                               rtol=0, atol=1e-15)


def test_bias_band_formula():
    for n in (1, 196, 10000):
        lo, hi = bias_band(n)
        assert lo == 1 - 1.645 * np.sqrt(1 / (2 * n))
        assert hi == 1 + 1.645 * np.sqrt(1 / (2 * n))
    assert BAND_Z == 1.645
    np.testing.assert_allclose(bias_band(196), (0.9169149532, 1.0830850468), rtol=0, atol=1e-10)
