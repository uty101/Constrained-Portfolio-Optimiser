import numpy as np
import pandas as pd
import pytest

from pc.cov import condition_cov, window_daily

TICKERS = list("ABCDEFGHIJKLMNOPQR")


def spectral_matrix(eigenvalues: np.ndarray, seed: int) -> pd.DataFrame:
    """Q diag(eigenvalues) Q' with Q a random orthogonal matrix."""
    n = len(eigenvalues)
    Q, _ = np.linalg.qr(np.random.default_rng(seed).standard_normal((n, n)))
    A = Q @ np.diag(eigenvalues) @ Q.T
    return pd.DataFrame(0.5 * (A + A.T), index=TICKERS[:n], columns=TICKERS[:n])


def test_window_boundaries_exclusive_start_inclusive_end():
    index = pd.bdate_range("2019-01-01", "2023-06-30", name="date")
    rets = pd.DataFrame({"A": np.arange(len(index), dtype=float)}, index=index)
    t = pd.Timestamp("2023-03-31")

    for months, start in ((1, "2023-02-28"), (36, "2020-03-31")):
        start = pd.Timestamp(start)
        assert start in index
        w = window_daily(rets, t, months)
        assert start not in w.index
        assert w.index[0] == index[index.get_loc(start) + 1]
        assert w.index[-1] == t
        assert len(w) == ((index > start) & (index <= t)).sum()


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
