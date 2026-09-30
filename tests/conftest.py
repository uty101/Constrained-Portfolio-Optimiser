import contextlib
from pathlib import Path

import pandas as pd
import pytest

from pc.config import load_config
from pc.cov import estimate_cov
from pc.data import load_prices, load_rf_daily
from pc.returns import _month_end_closes, daily_returns, monthly_excess_returns
from pc.returns_model import mu_sample

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _run_from_repo_root(monkeypatch):
    # Paths in config.toml are relative to the repo root.
    monkeypatch.chdir(ROOT)


@pytest.fixture
def cfg():
    return load_config(ROOT / "config.toml")


# The 5 dates of step 3.5 (decisions/section_0_review.md, 3c), reused by the Section 3 tests.
REAL_DATES = ("2010-04-30", "2012-12-31", "2016-06-30", "2020-02-28", "2026-07-31")


class RealData:
    """Real prices, returns and cached monthly conditioned Sigmas, loaded once per session."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.prices = load_prices(cfg)
        self.rf_daily = load_rf_daily(cfg, self.prices.index)
        self.returns_d = daily_returns(self.prices)
        self.monthly_excess = monthly_excess_returns(self.prices, self.rf_daily)
        # Month-end to month-end total returns on the same index as monthly_excess.
        total = _month_end_closes(self.prices).pct_change(fill_method=None).iloc[1:]
        total.index = pd.DatetimeIndex(total.index, name="date")
        self.monthly_total = total
        self._sigma = {}

    def sigma(self, t, name):
        key = (pd.Timestamp(t), name)
        if key not in self._sigma:
            self._sigma[key] = estimate_cov(self.returns_d, key[0], name, self.cfg)[0]
        return self._sigma[key]

    def mu(self, t):
        return mu_sample(self.monthly_excess, pd.Timestamp(t), self.cfg.sample.window_months)


@pytest.fixture(scope="session")
def real():
    with contextlib.chdir(ROOT):
        return RealData(load_config(ROOT / "config.toml"))
