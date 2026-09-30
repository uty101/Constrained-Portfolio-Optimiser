"""Portfolio risk functions. Pure numpy/pandas: nothing here imports from the rest of pc/."""

from __future__ import annotations

import numpy as np
import pandas as pd


def gmv_closed_form(Sigma: pd.DataFrame) -> pd.Series:
    """Budget-only minimum variance, Sigma^-1 1 / (1' Sigma^-1 1)."""
    x = np.linalg.solve(Sigma.to_numpy(dtype=float), np.ones(len(Sigma)))
    return pd.Series(x / x.sum(), index=Sigma.index)


def risk_contributions(w: pd.Series, Sigma: pd.DataFrame) -> pd.Series:
    """RC_i = w_i (Sigma w)_i / sqrt(w' Sigma w); sums to the fund vol."""
    x = w.to_numpy(dtype=float)
    Sw = Sigma.to_numpy(dtype=float) @ x
    return pd.Series(x * Sw / np.sqrt(x @ Sw), index=w.index)


def pct_risk_contributions(w: pd.Series, Sigma: pd.DataFrame) -> pd.Series:
    """RC_i / sqrt(w' Sigma w); sums to 1."""
    x = w.to_numpy(dtype=float)
    Sw = Sigma.to_numpy(dtype=float) @ x
    return pd.Series(x * Sw / (x @ Sw), index=w.index)
