import numpy as np
import pandas as pd

from pc.cov import estimate_cov
from pc.data import load_prices
from pc.returns import daily_returns
from pc.risk import gmv_closed_form


def test_gmv_closed_form_sums_to_one(cfg):
    rets = daily_returns(load_prices(cfg))
    t = pd.Timestamp(cfg.sample.first_decision)
    for name in cfg.cov.estimators:
        Sigma, _ = estimate_cov(rets, t, name, cfg)
        w = gmv_closed_form(Sigma)
        assert abs(w.sum() - 1) <= 1e-12
        assert list(w.index) == list(cfg.universe.tickers)
        # First-order condition: Sigma w is proportional to 1.
        grad = Sigma.to_numpy() @ w.to_numpy()
        np.testing.assert_allclose(grad, grad.mean(), rtol=1e-8)
