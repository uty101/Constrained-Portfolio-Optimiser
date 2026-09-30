"""Expected return models, in monthly excess return units (kickoff 5.1)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def trailing_months(monthly: pd.DataFrame, t: pd.Timestamp, first: int, last: int) -> pd.DataFrame:
    """Rows whose month is in [month(t) - first, month(t) - last], one row per month.

    Raises ValueError unless every month in that span is present exactly once.
    """
    p = pd.Timestamp(t).to_period("M")
    months = monthly.index.to_period("M")
    rows = monthly.loc[(months >= p - first) & (months <= p - last)]
    if len(rows) != first - last + 1:
        raise ValueError(f"{len(rows)} monthly rows for months {p - first} to {p - last}; expected {first - last + 1}")
    return rows


def mu_sample(monthly_excess: pd.DataFrame, t: pd.Timestamp, months: int) -> pd.Series:
    """Mean of the `months` trailing monthly excess returns ending at t (the month of t included)."""
    return trailing_months(monthly_excess, t, months - 1, 0).mean()


def mu_bayes_stein(mu_hat: pd.Series, Sigma: pd.DataFrame, T: int) -> tuple[pd.Series, float]:
    """Jorion (1986): (mu_BS, phi), mu_BS = (1 - phi) mu_hat + phi mu0 1.

    mu0 = 1'Sigma^-1 mu_hat / 1'Sigma^-1 1 and
    phi = (N + 2) / [(N + 2) + T (mu_hat - mu0 1)' Sigma^-1 (mu_hat - mu0 1)],
    Sigma the monthly Ledoit-Wolf covariance at t.
    """
    if list(mu_hat.index) != list(Sigma.index) or list(Sigma.columns) != list(Sigma.index):
        raise ValueError("mu_hat and Sigma must share one ticker index")
    m = mu_hat.to_numpy(dtype=float)
    n = len(m)
    S = Sigma.to_numpy(dtype=float)
    inv = np.linalg.solve(S, np.column_stack([m, np.ones(n)]))
    mu0 = inv[:, 0].sum() / inv[:, 1].sum()
    dev = m - mu0
    phi = (n + 2) / ((n + 2) + T * dev @ np.linalg.solve(S, dev))
    return pd.Series((1 - phi) * m + phi * mu0, index=mu_hat.index), float(phi)
