"""Pull the raw data snapshot. The only network code in the repo.

Writes data/raw/prices_adjclose.csv (yfinance, auto_adjust=True), data/raw/rf_dgs3mo.csv
(FRED DGS3MO as published, blanks kept) and data/raw/MANIFEST.json. Run once; the three
files are committed. If either source fails, this script fails; no other source is used.

    python scripts/pull_data.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pc.config import load_config  # noqa: E402

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO"


def pull_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    # yfinance treats end as exclusive; the configured end is inclusive.
    end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw = yf.download(
        tickers,
        start=start,
        end=end_exclusive,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if raw is None or raw.empty:
        raise RuntimeError("yfinance returned no data")
    close = raw["Close"]
    missing = [t for t in tickers if t not in close.columns or close[t].isna().all()]
    if missing:
        raise RuntimeError(f"yfinance returned no prices for {missing}")
    close = close[tickers]
    close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
    close.index.name = "date"
    return close.loc[start:end]


def pull_rf(start: str, end: str) -> pd.DataFrame:
    with urllib.request.urlopen(FRED_URL, timeout=60) as resp:
        text = resp.read().decode("utf-8")
    rf = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    if list(rf.columns) != ["observation_date", "DGS3MO"]:
        raise RuntimeError(f"unexpected FRED columns {list(rf.columns)}")
    rf = rf.rename(columns={"observation_date": "date"})
    dates = pd.to_datetime(rf["date"])
    rf = rf[(dates >= start) & (dates <= end)].reset_index(drop=True)
    if rf.empty:
        raise RuntimeError("FRED returned no DGS3MO rows in range")
    return rf


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    cfg = load_config(ROOT / "config.toml")
    tickers = list(cfg.universe.tickers)
    start, end = cfg.sample.price_start, cfg.sample.price_end
    prices_path = ROOT / cfg.data.prices_csv
    rf_path = ROOT / cfg.data.rf_csv
    manifest_path = ROOT / cfg.data.manifest

    prices = pull_prices(tickers, start, end)
    rf = pull_rf(start, end)
    pulled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    prices.to_csv(prices_path, date_format="%Y-%m-%d", lineterminator="\n")
    rf.to_csv(rf_path, index=False, lineterminator="\n")

    per_ticker = {
        t: {
            "first_date": prices[t].first_valid_index().strftime("%Y-%m-%d"),
            "last_date": prices[t].last_valid_index().strftime("%Y-%m-%d"),
        }
        for t in tickers
    }
    manifest = {
        "pulled_at_utc": pulled_at,
        "yfinance_version": yf.__version__,
        "sources": {
            "prices": "yfinance download, auto_adjust=True, Close",
            "rf": FRED_URL,
        },
        "range": {"start": start, "end": end},
        "row_counts": {
            Path(cfg.data.prices_csv).name: len(prices),
            Path(cfg.data.rf_csv).name: len(rf),
        },
        "tickers": per_ticker,
        "sha256": {
            Path(cfg.data.prices_csv).name: sha256(prices_path),
            Path(cfg.data.rf_csv).name: sha256(rf_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
