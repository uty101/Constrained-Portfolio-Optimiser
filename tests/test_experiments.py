from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from pc.backtest import walk_forward
from pc.experiments import (
    ANSWER_COLUMNS,
    EW_ID,
    MonthlySampleInputs,
    answers,
    cost_runs,
    cost_sensitivity,
    frontier_max_sharpe,
    levered_periods,
    levered_variants,
    monthly_sample_cov,
    source_rows,
    specs_for,
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
    table = turnover_frontier(runs, pcfg)
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
    # Step 6.0.b: the bootstrap interval is NaN on the "none" row and ordered on every tau row.
    assert np.isnan(none.realised_net_vs_none_p05) and np.isnan(none.realised_net_vs_none_p95)
    assert np.isnan(none.realised_net_vs_none_frac_le_0)
    taus = table[table["tau"] != "none"]
    assert (taus["realised_net_vs_none_p05"] <= taus["realised_net_vs_none_p95"]).all()
    assert taus["realised_net_vs_none_frac_le_0"].between(0, 1).all()


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


def answer_tables(cfg):
    """Synthetic source tables with the columns and rows answers() reads, and distinct values."""
    rng = np.random.default_rng(cfg.run.seed_master)
    ids = ["mv_unconstrained|sample|sample|A", "mv_unconstrained|lw_cc|sample|A", "mv_constrained|lw_cc|sample|C",
           "min_variance|lw_cc|none|B", EW_ID]
    taus = [*(str(x) for x in cfg.turnover_grid.taus), "none"]
    strategies = ["mv_unconstrained|sample|sample|A", "mv_constrained|lw_cc|sample|B",
                  "mv_constrained|lw_cc|bayes_stein|B", "black_litterman|lw_cc|bl|B", "min_variance|lw_cc|none|B"]
    est = [(e, s) for e in ("sample", "lw_cc", "ewma") for s in ("ew", "gmv")]
    return {
        "frontier_max_sharpe.csv": pd.DataFrame({"frontier": ["A", "B"], "max_sharpe": [2.5, 1.5]}),
        "sharpe_intervals.csv": pd.DataFrame({"strategy_id": ids, "sharpe": rng.random(5),
                                              "sharpe_p05": rng.random(5) - 1, "sharpe_p95": rng.random(5) + 1}),
        "metrics_all.csv": pd.DataFrame({"strategy_id": ids, "ruined": [True, False, False, False, False]}),
        "turnover_frontier.csv": pd.DataFrame({
            "tau": taus, "exante_return_given_up_bp_pa": [9.0, 7.0, 5.0, 3.0, 0.4, 0.2, 0.1, 0.0],
            "cost_saved_bp_pa": [4.0, 3.0, 2.0, 1.0, 0.5, 0.1, 0.05, 0.0], "realised_net_vs_none_bp_pa": rng.random(8),
            "realised_net_vs_none_p05": rng.random(8) - 1, "realised_net_vs_none_p95": rng.random(8) + 1,
            # tau 1.0 lies below the line (0.0 < 0.05) but never binds, so it lies on it (step 6.0.a.3).
            "n_binding": [9, 8, 7, 6, 5, 4, 0, 0]}),
        "sensitivity_summary.csv": pd.DataFrame({
            "date": [str(d) for d in cfg.sensitivity.dates for _ in strategies],
            "strategy": strategies * len(cfg.sensitivity.dates),
            "mean_abs_change": [40.0, 0.8, 0.6, 0.2, 0.0, 30.0, 0.5, 0.4, 0.75, 0.0, 20.0, 0.8, 0.6, 0.2, 0.0]}),
        "cov_eval_qlike_diff.csv": pd.DataFrame({"estimator": [e for e, _ in est], "portfolio_set": [s for _, s in est],
                                                 "diff_vs_lw_cc": rng.random(6), "p05": rng.random(6) - 1,
                                                 "p95": rng.random(6) + 1}),
        "cov_eval.csv": pd.DataFrame({"estimator": [e for e, _ in est], "portfolio_set": [s for _, s in est],
                                      "bias_ratio": rng.random(6) + 0.5}),
    }


def test_answers_has_4_rows_with_sources(cfg):
    tables = answer_tables(cfg)
    out = answers(tables, cfg)
    assert list(out.columns) == ANSWER_COLUMNS
    # The 4 research questions (kickoff Section 1), each answered, in order.
    assert out["question"].unique().tolist() == ["Q1", "Q2", "Q3", "Q4"]
    # Step 6.0: Q2 gains the realised difference at tau 0.05 with its interval; Q3 carries the 2
    # ratios at each of the 3 sensitivity dates.
    assert out.groupby("question").size().tolist() == [6, 5, 10, 4]
    for row in out.itertuples():
        src = source_rows(tables[row.source_table], row.source_row)
        assert len(src) >= 1, row.figure
        if len(src) == 1:
            # A single source row holds the value itself, and the interval when there is one.
            cells = src.iloc[0].tolist()
            assert row.value in cells, row.figure
            for bound in (row.p05, row.p95):
                assert np.isnan(bound) or bound in cells, row.figure
    a = out.set_index("figure")
    assert a.loc["ruined set A strategies, of 2", "value"] == 1
    # Only tau 0.5 lies below the 45 degree line (given up 0.4 < saved 0.5); 0.75 lies above, and
    # 1.0 lies below it numerically but never binds.
    assert a.loc["largest tau whose point lies below the 45 degree line", "value"] == 0.5
    frontier = tables["turnover_frontier.csv"].set_index("tau")
    for t in ("0.05", "0.3"):
        r = a.loc[f"tau = {t}: realised net return against no limit, bp pa"]
        assert (r.value, r.p05, r.p95) == tuple(frontier.loc[t, ["realised_net_vs_none_bp_pa", "realised_net_vs_none_p05",
                                                                   "realised_net_vs_none_p95"]])
    pair = "black_litterman|lw_cc|bl|B / mv_constrained|lw_cc|sample|B"
    for date, expected in zip(cfg.sensitivity.dates, (0.2 / 0.8, 0.75 / 0.5, 0.2 / 0.8)):
        assert a.loc[f"{date}: mean_abs_change ratio, {pair}", "value"] == expected


def test_largest_tau_below_line_nan_when_none_binds(cfg):
    # Decision 9, option 2: points below the line only where the limit never binds give NaN.
    tables = answer_tables(cfg)
    tables["turnover_frontier.csv"]["cost_saved_bp_pa"] = [4.0, 3.0, 2.0, 1.0, 0.3, 0.1, 0.05, 0.0]
    out = answers(tables, cfg).set_index("figure")
    assert np.isnan(out.loc["largest tau whose point lies below the 45 degree line", "value"])


def test_frontier_max_sharpe(cfg):
    rng = np.random.default_rng(cfg.run.seed_master)
    X = rng.normal(0.0, 0.04, (120, len(PANEL)))
    Sigma = pd.DataFrame(np.cov(X, rowvar=False), index=PANEL, columns=PANEL)
    S = Sigma.to_numpy()
    for sign in (1, -1):
        mu = pd.Series(sign * np.array([0.06, 0.05, 0.02, 0.08, 0.01, 0.04]), index=PANEL)
        m = mu.to_numpy()
        A, B, C = m @ np.linalg.solve(S, m), np.linalg.solve(S, m).sum(), np.linalg.solve(S, np.ones(6)).sum()
        out = frontier_max_sharpe(mu, Sigma, cfg).set_index("frontier")
        targets = np.concatenate([np.linspace(B / C, 1.0, 200001), np.linspace(1.0, 1e3, 200001)])
        grid = targets / np.sqrt((C * targets**2 - 2 * B * targets + A) / (A * C - B**2))
        a = out.loc["A"]
        if B > 0:
            assert abs(a.max_sharpe - np.sqrt(A)) <= 1e-12 and a.status == "optimal"
            assert abs(a.tangency_return / a.tangency_vol - a.max_sharpe) <= 1e-12
        else:
            assert a.status == "supremum_not_attained" and np.isnan(a.tangency_return)
        # No point on the budget-1 frontier beats it, and the frontier gets within 1e-4 of it.
        assert grid.max() <= a.max_sharpe + 1e-12
        assert grid.max() >= a.max_sharpe - 1e-4
        b = out.loc["B"]
        if sign > 0:
            assert b.status == "optimal" and b.max_sharpe <= a.max_sharpe + 1e-9
        else:
            # Every mu < 0: no long-only portfolio has mu'y = 1, so the set B program is infeasible.
            assert np.isnan(b.max_sharpe) and b.status != "optimal"


LEVERED_IDS = ["risk_parity|lw_cc|none|none", "min_variance|lw_cc|none|B", "hrp|lw_cc|none|none"]


def test_levered_k1_equals_unlevered(cfg):
    prices, rf_daily, pcfg = panel(cfg, n_decisions=8)
    weights, periods, _ = walk_forward(specs_for(pcfg, [*LEVERED_IDS, EW_ID]), prices, rf_daily, pcfg)
    lev = levered_periods(periods, weights, prices, rf_daily, pcfg, LEVERED_IDS, k_override=1.0)
    for sid in LEVERED_IDS:
        a = lev[lev["strategy_id"] == sid].reset_index(drop=True)
        b = periods[periods["strategy_id"] == sid].reset_index(drop=True)
        assert len(a) == len(b) == 8
        assert (a["financing"] == 0).all()
        assert np.abs(a["ret_net"] - b["ret_net"]).max() <= 1e-12, sid
        np.testing.assert_allclose(a["cost"], b["cost"], rtol=0, atol=1e-12)
        np.testing.assert_allclose(a["turnover"], b["turnover"], rtol=0, atol=1e-12)
    # Without the override, k is equal weight's forecast vol over the strategy's, which levers up.
    lev = levered_periods(periods, weights, prices, rf_daily, pcfg, LEVERED_IDS)
    fvol = periods.set_index(["strategy_id", "decision_date"])["forecast_vol_ann"]
    for sid in LEVERED_IDS:
        a = lev[lev["strategy_id"] == sid]
        expected = fvol.loc[EW_ID].to_numpy() / fvol.loc[sid].to_numpy()
        np.testing.assert_array_equal(a["k"].to_numpy(), expected)


def test_levered_zero_spread_cash_leg():
    # Risky returns are 0 and costs are 0, so the fund earns only its cash leg, (1 - k) rf_hold.
    # k and rf are dyadic, so (1 - k) rf and (1 + x) - 1 are exact and the check is ==.
    tickers = ["X", "Y", "Z"]
    dates = pd.DatetimeIndex(pd.date_range("2020-01-31", periods=6, freq="ME"), name="decision_date")
    w = pd.DataFrame([[0.5, 0.25, 0.25]] * 6, index=dates, columns=tickers)
    hold = pd.DataFrame(0.0, index=dates, columns=tickers)
    k = pd.Series([0.5, 1.5, 0.75, 1.25, 2.0, 1.0], index=dates)
    rf = pd.Series([2.0**-10, 2.0**-9, 3 * 2.0**-11, 2.0**-10, 2.0**-12, 2.0**-9], index=dates)
    days = pd.Series(21, index=dates)
    zero_cost = pd.Series(0.0, index=tickers)
    out = levered_variants("s", w, k, hold, rf, days, zero_cost, 0.0, 21)
    assert (out["financing"] == 0).all() and (out["cost"] == 0).all()
    assert (out["ret_net"].to_numpy() == ((1 - k) * rf).to_numpy()).all()
    assert (out["excess_net"].to_numpy() == (-k * rf).to_numpy()).all()
    # With a spread, financing is charged on the borrowed part only: max(k - 1, 0) spread n / (12 x 21).
    spread = 0.005
    out = levered_variants("s", w, k, hold, rf, days, zero_cost, spread, 21)
    expected = np.maximum(k.to_numpy() - 1, 0) * spread * 21 / (12 * 21)
    np.testing.assert_allclose(out["financing"].to_numpy(), expected, rtol=1e-15, atol=0)
    assert (out.loc[k.to_numpy() <= 1, "financing"] == 0).all()
