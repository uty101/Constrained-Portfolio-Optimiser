from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import pc.backtest as backtest
from pc.allocators import AllocResult
from pc.backtest import build_registry, drift, run_walk_forward
from pc.calendar import build_calendar
from pc.returns import holding_returns

REGISTRY_IDS = [
    "mv_unconstrained|sample|sample|A",
    "mv_unconstrained|lw_cc|sample|A",
    "mv_unconstrained|ewma|sample|A",
    "mv_unconstrained|pca3|sample|A",
    "mv_constrained|sample|sample|C",
    "mv_constrained|lw_cc|sample|C",
    "mv_constrained|ewma|sample|C",
    "mv_constrained|pca3|sample|C",
    "mv_constrained|lw_cc|bayes_stein|C",
    "min_variance|sample|none|B",
    "min_variance|lw_cc|none|B",
    "min_variance|ewma|none|B",
    "min_variance|pca3|none|B",
    "risk_parity|sample|none|none",
    "risk_parity|lw_cc|none|none",
    "risk_parity|ewma|none|none",
    "risk_parity|pca3|none|none",
    "black_litterman|sample|bl|C",
    "black_litterman|lw_cc|bl|C",
    "black_litterman|ewma|bl|C",
    "black_litterman|pca3|bl|C",
    "hrp|sample|none|none",
    "hrp|lw_cc|none|none",
    "hrp|ewma|none|none",
    "hrp|pca3|none|none",
    "equal_weight|none|none|none",
]

# Instruction 04, amendment 4.2.9: one spec per allocator.
LOOK_AHEAD_SPECS = [
    "mv_unconstrained|sample|sample|A",
    "mv_constrained|lw_cc|sample|C",
    "mv_constrained|lw_cc|bayes_stein|C",
    "min_variance|ewma|none|B",
    "risk_parity|pca3|none|none",
    "black_litterman|lw_cc|bl|C",
    "hrp|sample|none|none",
    "equal_weight|none|none|none",
]
USES_W_PREV = {"mv_constrained|lw_cc|sample|C", "mv_constrained|lw_cc|bayes_stein|C", "black_litterman|lw_cc|bl|C"}

SYN = ["AAA", "BBB", "CCC"]
SYN_BP = {"AAA": 3, "BBB": 6, "CCC": 10}


def test_registry_26_exact_ids(cfg):
    specs = build_registry(cfg)
    ids = [s.id for s in specs]
    assert len(ids) == 26
    assert len(set(ids)) == 26
    assert ids == REGISTRY_IDS
    for s in specs:
        assert s.id == f"{s.allocator}|{s.cov}|{s.mu_model}|{s.cons_set}"


def with_calendar(cfg, first, last, n):
    return replace(cfg, sample=replace(
        cfg.sample, first_decision=str(pd.Timestamp(first).date()),
        last_decision=str(pd.Timestamp(last).date()), expected_n_decisions=n))


def synthetic(cfg, n_decisions=5, jump=None):
    """3-asset prices on business days 2014-01-01 to 2018-08-31, constant daily rf, and a Config
    for them with decisions at the month-ends from 2018-01. jump = (ticker, date, factor)
    multiplies that ticker's prices from that date on."""
    index = pd.bdate_range("2014-01-01", "2018-08-31", name="date")
    rng = np.random.default_rng(cfg.run.seed_master)
    r = rng.normal(0.0003, 0.01, size=(len(index), len(SYN)))
    prices = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=index, columns=SYN)
    if jump is not None:
        ticker, date, factor = jump
        prices.loc[prices.index >= date, ticker] *= factor
    rf_daily = pd.Series(1e-4, index=index, name="rf")
    month_ends = pd.Series(index, index=index).groupby(index.to_period("M")).max()
    month_ends = month_ends[month_ends >= "2018-01-01"]
    scfg = replace(
        with_calendar(cfg, month_ends.iloc[0], month_ends.iloc[n_decisions - 1], n_decisions),
        universe=replace(cfg.universe, tickers=tuple(SYN), asset_class={t: "x" for t in SYN}),
        costs=replace(cfg.costs, one_way_bp=dict(SYN_BP)),
        bl=replace(cfg.bl, w_mkt={t: 1 / 3 for t in SYN}),
    )
    return prices, rf_daily, scfg


def specs_by_id(cfg, ids):
    specs = [s for s in build_registry(cfg) if s.id in ids]
    assert sorted(s.id for s in specs) == sorted(ids)
    return specs


def hand_wealth(prices, cal, targets, c):
    """Wealth path written out by hand: drift, renormalise, cost, then (1 - cost)(1 + w'r)."""
    wealth, prev = [1.0], None
    for k, row in enumerate(cal.itertuples(index=False)):
        w = targets[k]
        if prev is None:
            cost = 0.0
        else:
            grown = prev * (prices.loc[row.exec_date] / prices.loc[cal.exec_date.iloc[k - 1]]).to_numpy()
            cost = float(c @ np.abs(w - grown / grown.sum()))
        gross = float(w @ (prices.loc[row.next_exec_date] / prices.loc[row.exec_date] - 1).to_numpy())
        wealth.append(wealth[-1] * (1 - cost) * (1 + gross))
        prev = w
    return np.array(wealth[1:])


def test_synthetic_3_asset_5_period_wealth(cfg):
    prices, rf_daily, scfg = synthetic(cfg)
    cal = build_calendar(prices.index, scfg)
    ids = ["mv_unconstrained|sample|sample|A", "equal_weight|none|none|none"]
    weights, periods = run_walk_forward(specs_by_id(scfg, ids), prices, rf_daily, scfg)
    c = np.array([SYN_BP[t] for t in SYN]) / 1e4
    for sid in ids:
        p = periods[periods.strategy_id == sid]
        assert len(p) == 5
        engine = np.cumprod(1 + p.ret_net.to_numpy())
        if sid.startswith("equal_weight"):
            targets = [np.full(3, 1 / 3)] * 5
        else:
            w = weights[weights.strategy_id == sid]
            targets = [g.w_target.to_numpy() for _, g in w.groupby("decision_date", sort=True)]
            assert max(abs(t).sum() for t in targets) > 1  # shorts: set A is actually leveraged
        np.testing.assert_allclose(engine, hand_wealth(prices, cal, targets, c), rtol=0, atol=1e-12)
        np.testing.assert_allclose(p.excess_net, p.ret_net - p.rf_hold, rtol=0, atol=0)


def test_drift_renormalises_previous_target(cfg):
    w = pd.Series([0.5, 0.3, 0.2], index=SYN)
    r = pd.Series([0.10, -0.20, 0.15], index=SYN)
    out = drift(w, r)
    np.testing.assert_allclose(out, np.array([0.55, 0.24, 0.23]) / 1.02, rtol=0, atol=1e-15)
    assert abs(out.sum() - 1) <= 1e-15
    with pytest.raises(ValueError):
        drift(pd.Series([2.0, -1.5, 0.5], index=SYN), pd.Series([0.0, 1.0, 0.0], index=SYN))

    # In the engine: w_prev_drifted at k is the target at k - 1 drifted over holding period k - 1.
    prices, rf_daily, scfg = synthetic(cfg)
    cal = build_calendar(prices.index, scfg)
    hold = holding_returns(prices, cal)
    ids = ["mv_unconstrained|sample|sample|A", "equal_weight|none|none|none"]
    weights, _ = run_walk_forward(specs_by_id(scfg, ids), prices, rf_daily, scfg)
    for sid in ids:
        g = {d: x.set_index("ticker") for d, x in weights[weights.strategy_id == sid].groupby("decision_date")}
        dates = sorted(g)
        assert g[dates[0]].w_prev_drifted.isna().all()
        for k in range(1, len(dates)):
            expected = drift(g[dates[k - 1]].w_target, hold.loc[dates[k - 1]])
            np.testing.assert_allclose(g[dates[k]].w_prev_drifted, expected[SYN], rtol=0, atol=1e-15)
            assert abs(g[dates[k]].w_prev_drifted.sum() - 1) <= 1e-12
            np.testing.assert_allclose(
                g[dates[k]].trade, g[dates[k]].w_target - g[dates[k]].w_prev_drifted, rtol=0, atol=0)


def perturbed_prices(prices, after, seed):
    """Every price dated after `after` times its own Uniform(0.5, 1.5) factor (PLAN 4.2)."""
    rng = np.random.default_rng(seed)
    out = prices.copy()
    mask = out.index > after
    out.loc[mask] = out.loc[mask].to_numpy() * rng.uniform(0.5, 1.5, size=(int(mask.sum()), out.shape[1]))
    return out


def test_no_look_ahead(real):
    cfg = real.cfg
    cal = build_calendar(real.prices.index, cfg)
    cfg6 = with_calendar(cfg, cal.decision_date.iloc[0], cal.decision_date.iloc[5], 6)
    specs = specs_by_id(cfg, LOOK_AHEAD_SPECS)
    t, exec_t = cal.decision_date.iloc[2], cal.exec_date.iloc[2]
    base, _ = run_walk_forward(specs, real.prices, real.rf_daily, cfg6)
    keys = ["strategy_id", "decision_date", "ticker"]

    # (a) prices after exec_date(t): every weight at decision dates <= t is unchanged.
    wa, _ = run_walk_forward(specs, perturbed_prices(real.prices, exec_t, cfg.run.seed_master), real.rf_daily, cfg6)
    b, a = base[base.decision_date <= t], wa[wa.decision_date <= t]
    assert len(b) == 3 * 8 * 18
    assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
    assert np.array_equal(b.w_target.to_numpy(), a.w_target.to_numpy())
    assert np.array_equal(b.w_prev_drifted.to_numpy(), a.w_prev_drifted.to_numpy(), equal_nan=True)
    # The perturbation reaches the run: some weight after t differs.
    later = base[base.decision_date > t].merge(wa[wa.decision_date > t], on=keys)
    assert (later.w_target_x != later.w_target_y).any()

    # (b) prices after t: weights at t of the specs that do not use w_prev are unchanged.
    wb, _ = run_walk_forward(specs, perturbed_prices(real.prices, t, cfg.run.seed_master), real.rf_daily, cfg6)
    keep = [s for s in LOOK_AHEAD_SPECS if s not in USES_W_PREV]
    # The instruction names 3 exclusions from 8 specs and calls the rest "the 6 specs"; 8 - 3 = 5.
    assert len(keep) == 5
    b = base[(base.decision_date == t) & base.strategy_id.isin(keep)]
    a = wb[(wb.decision_date == t) & wb.strategy_id.isin(keep)]
    assert len(b) == len(keep) * 18
    assert b[keys].reset_index(drop=True).equals(a[keys].reset_index(drop=True))
    assert np.array_equal(b.w_target.to_numpy(), a.w_target.to_numpy())


def test_first_period_no_cost_no_turnover(real):
    cfg = real.cfg
    cal = build_calendar(real.prices.index, cfg)
    cfg2 = with_calendar(cfg, cal.decision_date.iloc[0], cal.decision_date.iloc[1], 2)
    weights, periods = run_walk_forward(build_registry(cfg), real.prices, real.rf_daily, cfg2)
    first = periods[periods.decision_date == cal.decision_date.iloc[0]]
    second = periods[periods.decision_date == cal.decision_date.iloc[1]]
    assert len(first) == len(second) == 26
    assert (first.cost == 0).all()
    assert first.turnover.isna().all()
    assert first.tau_eff.isna().all() and first.turnover_dual.isna().all() and not first.tau_relaxed.any()
    np.testing.assert_allclose(first.ret_net, first.ret_gross, rtol=0, atol=1e-15)
    w1 = weights[weights.decision_date == cal.decision_date.iloc[0]]
    assert w1.w_prev_drifted.isna().all() and w1.trade.isna().all() and (w1.cost_i == 0).all()
    # From the second period on, turnover and cost are recorded, and set C is constrained.
    assert second.turnover.notna().all()
    np.testing.assert_allclose(
        second.cost.to_numpy(),
        weights[weights.decision_date == cal.decision_date.iloc[1]].groupby("strategy_id", sort=False)
        .cost_i.sum()[second.strategy_id].to_numpy(),
        rtol=0, atol=1e-15)
    set_c = second[second.strategy_id.str.endswith("|C")]
    assert len(set_c) == 9 and set_c.tau_eff.notna().all()
    assert (set_c.turnover <= set_c.tau_eff + 1e-7).all()


def test_ruin_rule_stops_wealth_path(cfg, monkeypatch):
    # BBB doubles inside holding period 3 (decision 2018-03-30, held 2018-04-02 to 2018-05-01)
    # while a fixed target is short 1.5 of it: w'r is about -1.5, so net <= -1.
    prices, rf_daily, scfg = synthetic(cfg, jump=("BBB", pd.Timestamp("2018-04-16"), 2.0))
    target = pd.Series([2.0, -1.5, 0.5], index=SYN)

    def fixed(mu, Sigma, w_prev, cons):
        return AllocResult(target.copy(), "none", "optimal", False, np.nan, np.nan, False, np.nan)

    monkeypatch.setitem(backtest.ALLOCATORS, "equal_weight", fixed)
    sid = "equal_weight|none|none|none"
    weights, periods = run_walk_forward(specs_by_id(scfg, [sid]), prices, rf_daily, scfg)
    p = periods.set_index("decision_date")
    dates = list(p.index)
    assert len(dates) == 5
    assert p.ret_gross.iloc[2] < -1
    assert p.ret_net.iloc[2] == -1.0
    assert p.ruined.tolist() == [False, False, True, True, True]
    assert p.ret_net.iloc[:2].notna().all() and p.ret_net.iloc[3:].isna().all()
    assert (p.status.iloc[3:] == "not_solved").all()
    assert sorted(weights.decision_date.unique()) == dates[:3]
    assert np.prod(1 + p.ret_net.dropna().to_numpy()) == 0.0
