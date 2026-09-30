import csv
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from pc.calendar import build_calendar
from pc.data import load_prices, load_rf_daily
from pc.returns import daily_returns, holding_returns, holding_rf, monthly_excess_returns


@pytest.fixture
def prices(cfg):
    return load_prices(cfg)


@pytest.fixture
def cal(prices, cfg):
    return build_calendar(prices.index, cfg)


def test_compounded_daily_equals_holding_return(prices, cal, cfg):
    rets = daily_returns(prices)
    hold = holding_returns(prices, cal)
    compounded = []
    for row in cal.itertuples():
        window = rets.loc[(rets.index > row.exec_date) & (rets.index <= row.next_exec_date)]
        assert len(window) == row.n_hold_days
        compounded.append((1 + window).prod().to_numpy() - 1)
    np.testing.assert_allclose(hold.to_numpy(), np.array(compounded), rtol=0, atol=1e-12)
    assert list(hold.columns) == list(cfg.universe.tickers)
    assert hold.index.name == "decision_date"

    rf = load_rf_daily(cfg, prices.index)
    rf_h = holding_rf(rf, cal)
    rf_compounded = [
        (1 + rf.loc[(rf.index > r.exec_date) & (rf.index <= r.next_exec_date)]).prod() - 1
        for r in cal.itertuples()
    ]
    np.testing.assert_allclose(rf_h.to_numpy(), rf_compounded, rtol=0, atol=1e-12)


def test_rf_constant_5pct_gives_005_over_252(cfg, tmp_path):
    index = pd.bdate_range("2021-01-04", "2021-03-31", name="date")
    path = tmp_path / "rf.csv"
    pd.DataFrame({"date": index.strftime("%Y-%m-%d"), "DGS3MO": "5.00"}).to_csv(path, index=False)
    rf = load_rf_daily(replace(cfg, data=replace(cfg.data, rf_csv=str(path))), index)
    assert np.isnan(rf.iloc[0])
    np.testing.assert_allclose(rf.iloc[1:].to_numpy(), 0.05 / 252, rtol=0, atol=1e-18)

    cal = pd.DataFrame({
        "decision_date": [index[20]], "exec_date": [index[21]], "next_exec_date": [index[42]],
    })
    np.testing.assert_allclose(holding_rf(rf, cal).iloc[0], (1 + 0.05 / 252) ** 21 - 1,
                               rtol=0, atol=1e-15)


def manual_2020_03(cfg) -> pd.DataFrame:
    """2020-03 excess return per ticker, computed straight from the raw CSV rows."""
    with open(cfg.data.prices_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    dates = [r["date"] for r in rows]
    feb_end = max(d for d in dates if d.startswith("2020-02"))
    mar_end = max(d for d in dates if d.startswith("2020-03"))
    p0 = next(r for r in rows if r["date"] == feb_end)
    p1 = next(r for r in rows if r["date"] == mar_end)

    with open(cfg.data.rf_csv, newline="") as f:
        fred = [(r["date"], r["DGS3MO"]) for r in csv.DictReader(f)]
    march_days = [d for d in dates if d.startswith("2020-03")]
    rf_growth = 1.0
    for d in march_days:
        prev_trading_day = dates[dates.index(d) - 1]
        published = [float(v) for fd, v in fred if fd <= prev_trading_day and v != ""]
        rf_growth *= 1 + published[-1] / 100 / 252
    rf_month = rf_growth - 1

    out = pd.DataFrame(index=list(cfg.universe.tickers))
    out["close_2020_02"] = [float(p0[t]) for t in out.index]
    out["close_2020_03"] = [float(p1[t]) for t in out.index]
    out["total_return"] = out["close_2020_03"] / out["close_2020_02"] - 1
    out["rf_month"] = rf_month
    out["excess_manual"] = out["total_return"] - rf_month
    out.attrs["dates"] = (feb_end, mar_end)
    return out


def test_monthly_excess_2020_03_manual(prices, cfg):
    rf = load_rf_daily(cfg, prices.index)
    excess = monthly_excess_returns(prices, rf)
    manual = manual_2020_03(cfg)
    row = excess.loc[pd.Timestamp(manual.attrs["dates"][1])]
    np.testing.assert_allclose(row.to_numpy(), manual["excess_manual"].to_numpy(), rtol=0, atol=1e-12)
    assert list(excess.columns) == list(cfg.universe.tickers)
    assert excess.index.name == "date"
