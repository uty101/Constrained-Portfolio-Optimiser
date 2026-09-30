"""Covariance estimators on daily simple returns, and conditioning.

Every estimator takes the daily returns in a window (rows are dates, columns tickers)
and returns a daily covariance with the tickers as index and columns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def window_daily(returns_d: pd.DataFrame, t: pd.Timestamp, months: int) -> pd.DataFrame:
    """Rows with date in (t - months, t]: exclusive start, inclusive end."""
    t = pd.Timestamp(t)
    start = t - pd.DateOffset(months=months)
    return returns_d.loc[(returns_d.index > start) & (returns_d.index <= t)]


def _frame(values: np.ndarray, X: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(values, index=X.columns, columns=X.columns)


def cov_sample(X: pd.DataFrame) -> pd.DataFrame:
    return _frame(np.cov(X.to_numpy(dtype=float), rowvar=False, ddof=1), X)


def cov_lw_cc(X: pd.DataFrame, ddof: int = 0) -> tuple[pd.DataFrame, float]:
    """Ledoit-Wolf 2004 shrinkage to constant correlation. Returns (daily Sigma, delta).

    ddof changes S = Xm'Xm/(T - ddof) only, and everything built from S follows it
    (variances, r_bar, F, and every term that multiplies S). The raw sample moments
    inside pi_hat and theta_hat always divide by T. ddof 0 matches the authors'
    covCor.m; ddof 1 matches PyPortfolioOpt and is used only for that cross-check.
    """
    x = X.to_numpy(dtype=float)
    T, N = x.shape
    xm = x - x.mean(axis=0)
    S = xm.T @ xm / (T - ddof)

    var = np.diag(S)
    sd = np.sqrt(var)
    sd_outer = np.outer(sd, sd)
    r_bar = (np.sum(S / sd_outer) - N) / (N * (N - 1))
    F = r_bar * sd_outer
    np.fill_diagonal(F, var)

    m2 = xm.T @ xm / T
    y = xm**2
    pi_mat = y.T @ y / T - 2 * m2 * S + S**2
    pi_hat = np.sum(pi_mat)

    # theta[i, j] = theta_ii,ij = (1/T) sum_t (x_ti^2 - s_ii)(x_ti x_tj - s_ij), expanded
    theta = (xm**3).T @ xm / T - np.diag(m2)[:, None] * S - m2 * var[:, None] + var[:, None] * S
    np.fill_diagonal(theta, 0.0)
    rho_hat = np.trace(pi_mat) + r_bar * np.sum((sd[None, :] / sd[:, None]) * theta)

    gamma_hat = np.linalg.norm(S - F, "fro") ** 2
    delta = max(0.0, min(1.0, (pi_hat - rho_hat) / gamma_hat / T))
    return _frame(delta * F + (1 - delta) * S, X), float(delta)


def cov_lw_identity(X: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Ledoit-Wolf 2004 shrinkage to mu*I, mu = tr(S)/N, S the ddof 0 covariance. Test use only.

    d2 = ||S - mu I||^2/N, b2 = min(d2, sum_t ||x_t x_t' - S||^2/(N T^2)), shrinkage b2/d2.
    """
    x = X.to_numpy(dtype=float)
    T, N = x.shape
    xm = x - x.mean(axis=0)
    S = xm.T @ xm / T
    mu = np.trace(S) / N
    d2 = (np.sum(S**2) - 2 * mu * np.trace(S) + N * mu**2) / N
    b2_bar = (np.sum(np.sum(xm**2, axis=1) ** 2) - T * np.sum(S**2)) / (N * T**2)
    b2 = min(b2_bar, d2)
    shrinkage = 0.0 if b2 == 0 else b2 / d2
    Sigma = (1 - shrinkage) * S
    Sigma[np.diag_indices(N)] += shrinkage * mu
    return _frame(Sigma, X), float(shrinkage)


def ewma_weights(n: int, lam: float) -> np.ndarray:
    """w_k = (1 - lam) lam^k / (1 - lam^n), returned in row order: k = 0 is the last row."""
    k = np.arange(n - 1, -1, -1)
    return (1 - lam) * lam**k / (1 - lam**n)


def cov_ewma(X: pd.DataFrame, lam: float) -> pd.DataFrame:
    """sum_k w_k r_{t-k} r_{t-k}', no demeaning."""
    x = X.to_numpy(dtype=float)
    w = ewma_weights(len(x), lam)
    return _frame((x * w[:, None]).T @ x, X)


def _pca_corr(R: np.ndarray, k: int) -> np.ndarray:
    """R_f = V_k L_k V_k' + diag(1 - diag(V_k L_k V_k')), the k largest eigenpairs of R."""
    vals, vecs = np.linalg.eigh(R)
    top = np.argsort(vals)[::-1][:k]
    L = (vecs[:, top] * vals[top]) @ vecs[:, top].T
    L = 0.5 * (L + L.T)
    return L + np.diag(1 - np.diag(L))


def cov_pca(X: pd.DataFrame, k: int) -> pd.DataFrame:
    """D R_f D, R the sample correlation and D the sample vols (ddof 1)."""
    S = np.cov(X.to_numpy(dtype=float), rowvar=False, ddof=1)
    sd = np.sqrt(np.diag(S))
    R = S / np.outer(sd, sd)
    return _frame(np.outer(sd, sd) * _pca_corr(R, k), X)


def _cond(S: np.ndarray) -> float:
    """lambda_max / lambda_min of a symmetric matrix; inf when lambda_min <= 0."""
    eig = np.linalg.eigvalsh(S)
    return float(eig[-1] / eig[0]) if eig[0] > 0 else float("inf")


def condition_cov(S: pd.DataFrame, max_cond: float) -> tuple[pd.DataFrame, dict]:
    """Symmetrise, then add r*I when cond > max_cond, r = max(0, (l_max - max_cond*l_min)/(max_cond - 1)).

    The ridge sets cond to max_cond. cond_after is recomputed from the returned matrix.
    """
    A = S.to_numpy(dtype=float)
    A = 0.5 * (A + A.T)
    eig = np.linalg.eigvalsh(A)
    cond_before = float(eig[-1] / eig[0]) if eig[0] > 0 else float("inf")
    ridge = 0.0
    if cond_before > max_cond:
        ridge = max(0.0, float((eig[-1] - max_cond * eig[0]) / (max_cond - 1)))
        A = A + ridge * np.eye(len(A))
    log = {"cond_before": cond_before, "cond_after": _cond(A), "ridge": ridge}
    return pd.DataFrame(A, index=S.index, columns=S.columns), log
