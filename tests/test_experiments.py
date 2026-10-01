from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from pc.experiments import (
    MonthlySampleInputs,
    cost_runs,
    cost_sensitivity,
    monthly_sample_cov,
    turnover_frontier,
    turnover_runs,
)

# 6 assets, so that the 0.30 cap of sets B and C leaves a feasible set.
PANEL = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
PANEL_BP = {"AAA": 3, "BBB": 6, "CCC": 3, "DDD": 6, "EEE": 3, "FFF": 10}


def panel(cfg, n_decisions=12):
    """6-asset prices on business days 2014-01-01 to 2019-02-28, constant daily rf, and a Config
    for them with decisions at the month-ends from 2018-01."""
    index = pd.bdate_range("2014-01-01", "2019-02-28", name="date")
    rng = np.random.default_rng(cfg.run.seed_master)
    drift = np.array([0.0004, 0.0003, 0.0002, 0.0005, 0.0001, 0.0003])
    vol = np.array([0.012, 0.010, 0.006, 0.015, 0.004, 0.009])
    r = drift + vol * rng.standard_normal((len(index), len(PANEL)))
    prices = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=index, columns=PANEL)
    rf_daily = pd.Series(1e-4, index=index, name="rf")
    month_ends = pd.Series(index, index=index).groupby(index.to_period("M")).max()
    month_ends = month_ends[month_ends >= "2018-01-01"]
    pcfg = replace(
        cfg,
        sample=replace(cfg.sample, first_decision=str(month_ends.iloc[0].date()),
                       last_decision=str(month_ends.iloc[n_decisions - 1].date()), expected_n_decisions=n_decisions),
        universe=replace(cfg.universe, tickers=tuple(PANEL), asset_class={t: "x" for t in PANEL}),
        costs=replace(cfg.costs, one_way_bp=dict(PANEL_BP)),
        bl=replace(cfg.bl, w_mkt={t: 1 / len(PANEL) for t in PANEL},
                   equity_basket=("AAA", "BBB"), bond_basket=("CCC", "EEE"), n_long_short=2),
    )
    return prices, rf_daily, pcfg


def test_turnover_frontier_monotone_turnover(cfg):
    prices, rf_daily, pcfg = panel(cfg)
    runs, _ = turnover_runs(prices, rf_daily, pcfg)
    table = turnover_frontier(runs)
    assert table["tau"].tolist() == [*cfg.turnover_grid.taus, "none"]
    turnover = table["mean_turnover"].to_numpy(dtype=float)
    # Non-decreasing in tau, "none" last. 1e-7 is the step 3.4 turnover tolerance: a slack limit
    # moves the solution only at solver precision.
    assert (np.diff(turnover) >= -1e-7).all(), turnover
    # The limit binds somewhere on this panel, so the test is not vacuous.
    assert turnover[0] < turnover[-1] - 1e-3
    # Each tau run respects its limit (relaxed months use tau_eff).
    for tau, p in runs.items():
        if tau is not None:
            live = p.iloc[1:]
            assert (live["turnover"] <= live["tau_eff"] + 1e-7).all()
    none = table.set_index("tau").loc["none"]
    assert none.exante_return_given_up_bp_pa == 0 and none.cost_saved_bp_pa == 0
    assert none.realised_net_vs_none_bp_pa == 0 and none.n_binding == 0


def test_zero_cost_scale_net_equals_gross(cfg):
    prices, rf_daily, pcfg = panel(cfg, n_decisions=6)
    ids = ["mv_constrained|lw_cc|sample|C", "min_variance|lw_cc|none|B", "equal_weight|none|none|none"]
    runs, _ = cost_runs(prices, rf_daily, pcfg, ids)
    assert list(runs) == list(cfg.costs.cost_scales)
    zero = runs[0.0]
    assert (zero["cost"] == 0).all()
    # (1 - 0)(1 + g) - 1 is g up to the rounding of (1 + g) - 1 (the step 4.2 first-period tolerance).
    assert (zero["ret_net"] - zero["ret_gross"]).abs().max() <= 1e-15
    table = cost_sensitivity(runs, ids)
    assert (table.loc[table["cost_scale"] == 0.0, "mean_cost_bp_pa"] == 0).all()
    # The scale reaches the charge: equal weight trades the same at every scale, so its cost scales.
    ew = {s: p[p["strategy_id"] == "equal_weight|none|none|none"] for s, p in runs.items()}
    np.testing.assert_array_equal(ew[1.0]["turnover"].to_numpy(), ew[3.0]["turnover"].to_numpy())
    np.testing.assert_allclose(ew[3.0]["cost"].to_numpy(), 3 * ew[1.0]["cost"].to_numpy(), rtol=1e-14, atol=0)
    assert (ew[1.0]["cost"].iloc[1:] > 0).all()


def test_monthly_cov_uses_36_rows(cfg):
    rng = np.random.default_rng(cfg.run.seed_master)
    index = pd.DatetimeIndex(pd.date_range("2015-01-31", "2019-12-31", freq="ME"), name="date")
    monthly = pd.DataFrame(rng.normal(0.005, 0.04, (len(index), len(PANEL))), index=index, columns=PANEL)
    t = pd.Timestamp("2018-06-29")  # a last trading day, not the calendar month end
    Sigma, log, X = monthly_sample_cov(monthly, t, cfg)
    assert len(X) == cfg.sample.window_months == 36
    assert X.index[0].to_period("M") == pd.Period("2015-07", "M")
    assert X.index[-1].to_period("M") == pd.Period("2018-06", "M")
    rows = monthly.loc["2015-07-01":"2018-06-30"].to_numpy()
    assert rows.shape[0] == 36
    C = np.cov(rows, rowvar=False, ddof=1)
    assert log["ridge"] == 0.0
    np.testing.assert_array_equal(Sigma.to_numpy(), 0.5 * (C + C.T))
    # The engine's "sample" Sigma is this matrix; returns_d is not read for it.
    inputs = MonthlySampleInputs(t, None, monthly, None, cfg)
    np.testing.assert_array_equal(inputs.sigma("sample")[0].to_numpy(), Sigma.to_numpy())
    # A month missing from the window is an error, not a 35-row covariance.
    with pytest.raises(ValueError):
        monthly_sample_cov(monthly.drop(pd.Timestamp("2017-03-31")), t, cfg)
