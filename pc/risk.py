"""Portfolio risk functions. Pure numpy/pandas: nothing here imports from the rest of pc/."""

from __future__ import annotations

import numpy as np
import pandas as pd


def gmv_closed_form(Sigma: pd.DataFrame) -> pd.Series:
    """Budget-only minimum variance, Sigma^-1 1 / (1' Sigma^-1 1)."""
    x = np.linalg.solve(Sigma.to_numpy(dtype=float), np.ones(len(Sigma)))
    return pd.Series(x / x.sum(), index=Sigma.index)
