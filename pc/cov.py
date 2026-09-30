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
