from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from pc.data import corr_full_sample, data_summary, load_prices, load_rf_daily, validate_prices


def _with_data(cfg, **paths):
    return replace(cfg, data=replace(cfg.data, **paths))


def _synthetic_prices(cfg, n=10, start="2020-01-01"):
    idx = pd.bdate_range(start, periods=n, name="date")
    tickers = list(cfg.universe.tickers)
    values = 100.0 + np.arange(n)[:, None] * 0.1 + np.arange(len(tickers))[None, :]
    return pd.DataFrame(values, index=idx, columns=tickers)


def test_load_prices_shape_and_order(cfg):
    prices = load_prices(cfg)
    assert list(prices.columns) == list(cfg.universe.tickers)
    assert isinstance(prices.index, pd.DatetimeIndex)
    assert prices.index.name == "date"
    assert prices.index.is_monotonic_increasing
    assert prices.index[0] == pd.Timestamp(cfg.sample.price_start)
    assert prices.index[-1] == pd.Timestamp(cfg.sample.price_end)


def test_load_prices_no_nan_from_panel_start(cfg):
    assert not load_prices(cfg).isna().any().any()


def test_panel_start_is_first_full_row(cfg, tmp_path):
    raw = _synthetic_prices(cfg)
    raw.iloc[:3, 4] = np.nan     # XLE starts on day 4
    raw.iloc[:1, 14] = np.nan    # HYG starts on day 2
    path = tmp_path / "prices.csv"
    raw.to_csv(path)
    prices = load_prices(_with_data(cfg, prices_csv=str(path)))
    assert prices.index[0] == raw.index[3]
    assert len(prices) == len(raw) - 3
    pd.testing.assert_frame_equal(prices, raw.iloc[3:], check_freq=False)


def test_rf_uses_previous_day_and_ffill(cfg, tmp_path):
    # FRED blank on 2020-01-08, and no row at all for 2020-01-09.
    path = tmp_path / "rf.csv"
    path.write_text(
        "date,DGS3MO\n"
        "2020-01-06,1.00\n"
        "2020-01-07,2.00\n"
        "2020-01-08,\n"
        "2020-01-10,5.00\n"
        "2020-01-13,6.00\n"
    )
    index = pd.DatetimeIndex(
        ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10", "2020-01-13"],
        name="date",
    )
    rf = load_rf_daily(_with_data(cfg, rf_csv=str(path)), index)
    expected_pct = [np.nan, 1.00, 2.00, 2.00, 2.00, 5.00]
    expected = pd.Series(np.array(expected_pct) / 100 / 252, index=index, name="rf")
    pd.testing.assert_series_equal(rf, expected, rtol=0, atol=1e-15)


def test_validate_flags_each_issue_type(cfg):
    prices = _synthetic_prices(cfg, n=8)
    prices.iloc[2, 0] = prices.iloc[1, 0] * 1.30                       # SPY +30%: return flag
    prices.iloc[5, 1] = 0.0                                            # IWM zero price
    idx = prices.index.tolist()
    idx[4] = idx[3] + pd.Timedelta(days=6)                             # gap of 6 days
    idx[5:] = [d + pd.Timedelta(days=7) for d in idx[5:]]
    idx[7] = idx[6]                                                    # duplicate date
    prices.index = pd.DatetimeIndex(idx, name="date")

    issues = validate_prices(prices, cfg)
    assert list(issues.columns) == ["date", "ticker", "issue", "value"]
    got = {(r.date, r.ticker, r.issue) for r in issues.itertuples()}
    assert (idx[2], "SPY", "abs_daily_return_gt_flag") in got
    assert (idx[5], "IWM", "non_positive_price") in got
    assert (idx[4], "ALL", "gap_days_gt_flag") in got
    assert (idx[7], "ALL", "duplicate_date") in got
    assert set(issues["issue"]) == {
        "abs_daily_return_gt_flag", "non_positive_price", "gap_days_gt_flag", "duplicate_date",
    }
    spy = issues[(issues.ticker == "SPY") & (issues.issue == "abs_daily_return_gt_flag")]
    assert spy["value"].iloc[0] == pytest.approx(prices.iloc[2, 0] / prices.iloc[1, 0] - 1)
    gap = issues[issues.issue == "gap_days_gt_flag"]
    assert gap["value"].iloc[0] == 6
    dup = issues[issues.issue == "duplicate_date"]
    assert dup["value"].iloc[0] == 2


def test_data_summary_columns_and_rows(cfg):
    summary = data_summary(load_prices(cfg), cfg)
    assert list(summary.columns) == [
        "ticker", "first_date", "last_date", "n_days", "ann_return", "ann_vol",
        "worst_day", "worst_date", "best_day", "best_date",
    ]
    assert len(summary) == 18
    assert list(summary["ticker"]) == list(cfg.universe.tickers)


def test_data_summary_annualisation(cfg):
    idx = pd.bdate_range("2020-01-01", periods=4, name="date")
    prices = pd.DataFrame({"SPY": 100.0 * np.cumprod([1.0, 1.01, 0.98, 1.03])}, index=idx)
    row = data_summary(prices, cfg).iloc[0]
    assert row["n_days"] == 3
    assert abs(row["ann_return"] - ((1.01 * 0.98 * 1.03) ** (252 / 3) - 1)) <= 1e-12
    assert abs(row["ann_vol"] - np.std([0.01, -0.02, 0.03], ddof=1) * np.sqrt(252)) <= 1e-12
    assert row["worst_date"] == idx[2] and row["best_date"] == idx[3]


def test_corr_full_sample_symmetric_unit_diagonal(cfg):
    corr = corr_full_sample(load_prices(cfg))
    assert list(corr.columns) == ["ticker", *cfg.universe.tickers]
    assert list(corr["ticker"]) == list(cfg.universe.tickers)
    m = corr.drop(columns="ticker").to_numpy()
    np.testing.assert_allclose(m, m.T, rtol=0, atol=1e-15)
    np.testing.assert_allclose(np.diag(m), 1.0, rtol=0, atol=1e-15)