"""Daily, monthly excess and holding-period returns. All simple decimals."""

from __future__ import annotations

import pandas as pd


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Close-to-close simple returns; the first row (no previous close) is dropped."""
    return prices.pct_change(fill_method=None).iloc[1:]


def _month_end_closes(prices: pd.DataFrame) -> pd.DataFrame:
    """Close on the last trading day of each month, indexed by that day.

    A final month whose last row falls before that month's last business day is
    incomplete and is dropped.
    """
    months = prices.index.to_period("M")
    closes = prices.groupby(months).tail(1)
    last = closes.index[-1]
    if last < last + pd.offsets.BMonthEnd(0):
        closes = closes.iloc[:-1]
    return closes


def monthly_excess_returns(prices: pd.DataFrame, rf_daily: pd.Series) -> pd.DataFrame:
    """Month-end to month-end simple returns minus rf compounded over the month's trading days.

    Indexed by the month's last trading day (name "date"). The first month has no prior
    month-end close and is dropped.
    """
    closes = _month_end_closes(prices)
    total = closes.pct_change(fill_method=None).iloc[1:]
    rf = rf_daily.reindex(prices.index)
    rf_month = (1 + rf).groupby(prices.index.to_period("M")).prod(min_count=1) - 1
    rf_month = rf_month.reindex(total.index.to_period("M")).to_numpy()
    excess = total.sub(rf_month, axis=0)
    excess.index = pd.DatetimeIndex(excess.index, name="date")
    return excess


def holding_returns(prices: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    """Gross asset returns from the exec_date close to the next_exec_date close."""
    start = prices.loc[pd.DatetimeIndex(cal["exec_date"])].to_numpy()
    end = prices.loc[pd.DatetimeIndex(cal["next_exec_date"])].to_numpy()
    return pd.DataFrame(
        end / start - 1,
        index=pd.DatetimeIndex(cal["decision_date"], name="decision_date"),
        columns=prices.columns,
    )


def holding_rf(rf_daily: pd.Series, cal: pd.DataFrame) -> pd.Series:
    """rf compounded over the holding days (exec_date, next_exec_date]."""
    growth = (1 + rf_daily).cumprod()
    start = growth.loc[pd.DatetimeIndex(cal["exec_date"])].to_numpy()
    end = growth.loc[pd.DatetimeIndex(cal["next_exec_date"])].to_numpy()
    return pd.Series(
        end / start - 1,
        index=pd.DatetimeIndex(cal["decision_date"], name="decision_date"),
        name="rf_hold",
    )
