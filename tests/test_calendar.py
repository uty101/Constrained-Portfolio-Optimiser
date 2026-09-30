import pandas as pd
import pytest

from pc.calendar import build_calendar
from pc.data import load_prices


@pytest.fixture
def days(cfg):
    return load_prices(cfg).index


@pytest.fixture
def cal(days, cfg):
    return build_calendar(days, cfg)


def test_calendar_has_196_rows(cal):
    assert len(cal) == 196
    assert list(cal.columns) == ["decision_date", "exec_date", "next_exec_date", "n_hold_days"]
    assert isinstance(cal.index, pd.RangeIndex)


def test_first_decision_2010_04_30(cal):
    assert cal["decision_date"].iloc[0] == pd.Timestamp("2010-04-30")


def test_last_decision_2026_07_31(cal):
    assert cal["decision_date"].iloc[-1] == pd.Timestamp("2026-07-31")
    assert cal["next_exec_date"].iloc[-1] == pd.Timestamp("2026-09-01")


def test_exec_date_is_next_trading_day(cal, days):
    pos = days.get_indexer(cal["decision_date"])
    assert (days[pos + 1] == pd.DatetimeIndex(cal["exec_date"])).all()
    assert (cal["next_exec_date"].iloc[:-1].to_numpy() == cal["exec_date"].iloc[1:].to_numpy()).all()
    n_hold = days.get_indexer(cal["next_exec_date"]) - days.get_indexer(cal["exec_date"])
    assert (n_hold == cal["n_hold_days"].to_numpy()).all()


def test_decision_dates_are_trading_days(cal, days):
    assert pd.DatetimeIndex(cal["decision_date"]).isin(days).all()
    # each is the last trading day of its month
    last_of_month = pd.Series(days, index=days).groupby(days.to_period("M")).max()
    periods = pd.DatetimeIndex(cal["decision_date"]).to_period("M")
    assert (last_of_month.loc[periods].to_numpy() == cal["decision_date"].to_numpy()).all()
