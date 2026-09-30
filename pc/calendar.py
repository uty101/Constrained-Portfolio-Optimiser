"""Decision, execution and holding-period calendar.

Decision dates are month-end trading days; each target trades at the next trading day's
close (exec_date) and is held to the next month's exec_date (next_exec_date).
"""

from __future__ import annotations

import pandas as pd

from pc.config import Config

CALENDAR_COLUMNS = ["decision_date", "exec_date", "next_exec_date", "n_hold_days"]


def build_calendar(prices_index: pd.DatetimeIndex, cfg: Config) -> pd.DataFrame:
    days = pd.DatetimeIndex(prices_index).sort_values()
    month_ends = pd.Series(days, index=days).groupby(days.to_period("M")).max()
    month_ends = pd.DatetimeIndex(month_ends.to_numpy())

    first = pd.Timestamp(cfg.sample.first_decision)
    last = pd.Timestamp(cfg.sample.last_decision)
    for label, d in (("first_decision", first), ("last_decision", last)):
        if d not in month_ends:
            raise ValueError(f"{label} {d.date()} is not a month-end trading day")

    k0, k1 = month_ends.get_loc(first), month_ends.get_loc(last)
    if k1 + 1 >= len(month_ends):
        raise ValueError("prices end before the month after last_decision")

    def next_trading_day(d: pd.Timestamp) -> pd.Timestamp:
        pos = days.searchsorted(d, side="right")
        if pos >= len(days):
            raise ValueError(f"no trading day after {d.date()}")
        return days[pos]

    decision = month_ends[k0 : k1 + 1]
    exec_date = pd.DatetimeIndex([next_trading_day(d) for d in decision])
    next_exec = pd.DatetimeIndex([next_trading_day(d) for d in month_ends[k0 + 1 : k1 + 2]])
    n_hold = days.searchsorted(next_exec, side="right") - days.searchsorted(exec_date, side="right")

    cal = pd.DataFrame({
        "decision_date": decision,
        "exec_date": exec_date,
        "next_exec_date": next_exec,
        "n_hold_days": n_hold.astype(int),
    })
    if len(cal) != cfg.sample.expected_n_decisions:
        raise ValueError(f"{len(cal)} decision dates, expected {cfg.sample.expected_n_decisions}")
    return cal[CALENDAR_COLUMNS]
