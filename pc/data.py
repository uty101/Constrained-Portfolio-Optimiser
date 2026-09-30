"""Loaders for the committed raw snapshot, and price validation.

Validation reports issues and never fixes them.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pc.config import Config

ISSUE_COLUMNS = ["date", "ticker", "issue", "value"]
ALL_TICKERS = "ALL"


def _read_prices_csv(cfg: Config) -> pd.DataFrame:
    raw = pd.read_csv(cfg.data.prices_csv, index_col="date", parse_dates=["date"])
    raw.index = pd.DatetimeIndex(raw.index, name="date")
    return raw[list(cfg.universe.tickers)].astype(float)


def load_prices(cfg: Config) -> pd.DataFrame:
    """Daily adjusted closes from the panel start (first row where all tickers have a price)."""
    raw = _read_prices_csv(cfg)
    full = raw.notna().all(axis=1)
    if not full.any():
        raise ValueError("no date on which every ticker has a price")
    prices = raw.loc[full.idxmax():]
    if prices.isna().any().any():
        bad = prices.columns[prices.isna().any()].tolist()
        raise ValueError(f"NaN prices after the panel start for {bad}")
    return prices


def load_rf_daily(cfg: Config, index: pd.DatetimeIndex) -> pd.Series:
    """Daily rf on trading day d = DGS3MO(d-1)/100/252, d-1 the previous day in `index`.

    FRED blanks are forward filled from the last published value. The first day of
    `index` has no previous day and is NaN.
    """
    raw = pd.read_csv(cfg.data.rf_csv, dtype=str, keep_default_na=False)
    published = pd.Series(
        pd.to_numeric(raw["DGS3MO"].replace("", None)).to_numpy(dtype=float),
        index=pd.DatetimeIndex(pd.to_datetime(raw["date"]), name="date"),
    ).dropna()
    level = published.reindex(index.union(published.index)).ffill().reindex(index)
    days_per_year = 12 * cfg.sample.days_per_month
    rf = level.shift(1) / 100 / days_per_year
    rf.index = pd.DatetimeIndex(index, name="date")
    return rf.rename("rf")


def validate_prices(prices: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Issues table (date, ticker, issue, value). Gap and duplicate issues apply to every ticker."""
    parts = []

    def per_ticker(values: pd.DataFrame, flagged: pd.DataFrame, issue: str) -> pd.DataFrame:
        stacked = values.stack()
        hit = stacked[flagged.stack().to_numpy()]
        return pd.DataFrame({
            "date": hit.index.get_level_values(0),
            "ticker": hit.index.get_level_values(1),
            "issue": issue,
            "value": hit.to_numpy(dtype=float),
        })

    rets = prices.pct_change(fill_method=None)
    parts.append(per_ticker(
        rets, rets.abs().gt(cfg.data.max_abs_daily_return_flag), "abs_daily_return_gt_flag"))
    parts.append(per_ticker(prices, prices.le(0), "non_positive_price"))

    dates = pd.Series(prices.index, index=prices.index)
    gaps = dates.diff().dt.days
    gaps = gaps[gaps > cfg.data.max_gap_days_flag]
    parts.append(pd.DataFrame({
        "date": gaps.index,
        "ticker": ALL_TICKERS,
        "issue": "gap_days_gt_flag",
        "value": gaps.to_numpy(dtype=float),
    }))

    counts = prices.index.value_counts()
    dups = counts[counts > 1].sort_index()
    parts.append(pd.DataFrame({
        "date": dups.index,
        "ticker": ALL_TICKERS,
        "issue": "duplicate_date",
        "value": dups.to_numpy(dtype=float),
    }))

    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    issues = pd.concat(parts, ignore_index=True)
    issues["date"] = pd.to_datetime(issues["date"])
    return issues.sort_values(["date", "issue"], kind="stable", ignore_index=True)[ISSUE_COLUMNS]


def write_data_issues(cfg: Config) -> Path:
    issues = validate_prices(load_prices(cfg), cfg)
    path = Path(cfg.outputs.tables_dir) / "data_issues.csv"
    issues.to_csv(path, index=False, float_format="%.10g", date_format="%Y-%m-%d", lineterminator="\n")
    return path
