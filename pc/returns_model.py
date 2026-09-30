"""Expected return models, in monthly excess return units (kickoff 5.1)."""

from __future__ import annotations

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
