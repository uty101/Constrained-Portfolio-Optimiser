import math

import numpy as np
import pandas as pd

from pc.stats import sharpe_intervals, stationary_bootstrap_indices, strategy_metrics


def test_bootstrap_indices_shape_and_determinism(cfg):
    n, block, reps, seed = 196, cfg.bootstrap.mean_block, 500, cfg.run.bootstrap_seed
    idx = stationary_bootstrap_indices(n, block, reps, seed)
    assert idx.shape == (reps, n)
    assert idx.dtype == np.int64
    assert idx.min() >= 0 and idx.max() < n
    np.testing.assert_array_equal(idx, stationary_bootstrap_indices(n, block, reps, seed))
    assert not np.array_equal(idx, stationary_bootstrap_indices(n, block, reps, seed + 1))
    # The first replication is a prefix of a longer run: paths are drawn in order.
    np.testing.assert_array_equal(idx[:3], stationary_bootstrap_indices(n, block, 3, seed))


def test_bootstrap_indices_follow_the_fixed_draw_order():
    n, block, seed = 10, 3, 7
    rng = np.random.default_rng(seed)
    expected = []
    for _ in range(4):
        path = [int(rng.integers(n))]
        for _ in range(1, n):
            path.append(int(rng.integers(n)) if rng.random() < 1 / block else (path[-1] + 1) % n)
        expected.append(path)
    np.testing.assert_array_equal(stationary_bootstrap_indices(n, block, 4, seed), expected)


def synthetic_periods(sid, ret_net, rf=0.001, turnover=None, positions=None, solver="CLARABEL", ruined=None,
                      fallback=None, ridge=None, rp_converged=None, fcst=None):
    n = len(ret_net)
    ret_net = np.asarray(ret_net, dtype=float)
    dates = pd.date_range("2020-01-31", periods=n, freq="ME")
    return pd.DataFrame({
        "strategy_id": sid,
        "decision_date": dates,
        "ret_net": ret_net,
        "rf_hold": rf,
        "excess_net": ret_net - rf,
        "forecast_vol_ann": fcst if fcst is not None else np.full(n, 0.10),
        "turnover": turnover if turnover is not None else [np.nan] + [0.2] * (n - 1),
        "n_positions": positions if positions is not None else np.full(n, 5.0),
        "solver": solver,
        "fallback": fallback if fallback is not None else np.zeros(n, dtype=bool),
        "ridge": ridge if ridge is not None else np.zeros(n),
        "ruined": ruined if ruined is not None else np.zeros(n, dtype=bool),
        "rp_converged": rp_converged if rp_converged is not None else np.ones(n, dtype=bool),
    })


def test_metrics_on_synthetic_series():
    r = [0.02, -0.01, 0.03, -0.04, 0.01, 0.02]
    p = synthetic_periods(
        "a", r, turnover=[np.nan, 0.1, 0.2, 0.3, 0.4, 0.5], positions=[4, 5, 6, 7, 8, 9],
        solver=["CLARABEL", "CLARABEL+SCS", "CLARABEL+SCS+CLARABEL+SCS", "CLARABEL", "CLARABEL", "CLARABEL"],
        fallback=[False, False, True, False, False, False], ridge=[0, 1e-9, 0, 0, 2e-9, 0],
        rp_converged=[True, True, True, False, True, True], fcst=[0.08, 0.09, 0.10, 0.11, 0.12, 0.13])
    p = pd.concat([p, synthetic_periods("b", [0.01] * 3 + [0.03] * 3)], ignore_index=True)
    m = strategy_metrics(p).set_index("strategy_id")
    assert list(m.index) == ["a", "b"]
    a = m.loc["a"]

    # By hand.
    growth = 1.0
    for x in r:
        growth *= 1 + x
    ann_return = growth ** (12 / 6) - 1
    mean = sum(r) / 6
    sd = math.sqrt(sum((x - mean) ** 2 for x in r) / 5)
    ex = [x - 0.001 for x in r]
    ex_mean = sum(ex) / 6
    ex_sd = math.sqrt(sum((x - ex_mean) ** 2 for x in ex) / 5)
    # Peak 1.02 * 0.99 * 1.03 after month 3, then -4%: the drawdown is exactly -0.04.
    assert a.n_months == 6 and not a.ruined
    assert abs(a.ann_return - ann_return) <= 1e-15
    assert abs(a.ann_vol - sd * math.sqrt(12)) <= 1e-15
    assert abs(a.sharpe - ex_mean / ex_sd * math.sqrt(12)) <= 1e-12
    assert abs(a.max_dd - (-0.04)) <= 1e-15
    assert abs(a.forecast_vol_ann - 0.105) <= 1e-15
    assert abs(a.fcst_realised_ratio - 0.105 / (sd * math.sqrt(12))) <= 1e-12
    assert abs(a.mean_turnover - 0.3) <= 1e-15
    assert abs(a.mean_positions - 6.5) <= 1e-15
    assert (a.scs_retries, a.fallbacks, a.rp_not_converged, a.ridged_months) == (3, 1, 1, 2)
    # A series that never falls has no drawdown.
    assert m.loc["b"].max_dd == 0.0


def test_metrics_respect_ruin_truncation():
    nan = np.nan
    p = synthetic_periods(
        "x", [0.10, 0.05, -1.0, nan, nan], turnover=[nan, 0.3, 0.5, nan, nan],
        positions=[3, 4, 5, nan, nan], ruined=[False, False, True, True, True],
        fcst=[0.2, 0.2, 0.2, nan, nan], solver=["CLARABEL", "CLARABEL", "CLARABEL", "none", "none"])
    p.loc[3:, "rf_hold"] = nan
    p.loc[3:, "excess_net"] = nan
    m = strategy_metrics(p).iloc[0]
    assert m.n_months == 3
    assert m.ruined
    assert m.ann_return == -1.0
    assert m.max_dd == -1.0
    r = np.array([0.10, 0.05, -1.0])
    assert abs(m.ann_vol - np.std(r, ddof=1) * math.sqrt(12)) <= 1e-15
    ex = r - 0.001
    assert abs(m.sharpe - ex.mean() / np.std(ex, ddof=1) * math.sqrt(12)) <= 1e-12
    assert abs(m.mean_turnover - 0.4) <= 1e-15
    assert abs(m.mean_positions - 4.0) <= 1e-15


def interval_inputs(cfg, n=60, reps=500):
    rng = np.random.default_rng(cfg.run.seed_master)
    a = rng.normal(0.006, 0.03, n)
    c = rng.normal(0.004, 0.02, n)
    p = pd.concat([
        synthetic_periods("a", a, rf=0.0),
        synthetic_periods("b", 2 * a, rf=0.0),  # the same Sharpe ratio on every path
        synthetic_periods("c", c, rf=0.0),
    ], ignore_index=True)
    idx = stationary_bootstrap_indices(n, cfg.bootstrap.mean_block, reps, cfg.run.bootstrap_seed)
    return p, idx, a, c


def test_sharpe_intervals_paired_paths(cfg):
    p, idx, a, c = interval_inputs(cfg)
    out = sharpe_intervals(p, idx, ["a"]).set_index("strategy_id")

    def path_sharpe(x):
        return np.array([x[i].mean() / x[i].std(ddof=1) * math.sqrt(12) for i in idx])

    lo, hi = cfg.bootstrap.ci
    sa, sc = path_sharpe(a), path_sharpe(c)
    np.testing.assert_allclose(out.loc["a", ["sharpe_p05", "sharpe_p95"]].to_numpy(dtype=float),
                               np.quantile(sa, [lo, hi]), rtol=0, atol=1e-12)
    # c against a: path by path on the same indices.
    d = sc - sa
    np.testing.assert_allclose(out.loc["c", ["diff_p05_vs_a", "diff_p95_vs_a"]].to_numpy(dtype=float),
                               np.quantile(d, [lo, hi]), rtol=0, atol=1e-12)
    assert out.loc["c", "frac_le_0_vs_a"] == np.mean(d <= 0)
    # b = 2a has a's Sharpe ratio on every path, so the paired difference is 0 on every path.
    assert abs(out.loc["b", "diff_vs_a"]) <= 1e-12
    assert abs(out.loc["b", "diff_p05_vs_a"]) <= 1e-12 and abs(out.loc["b", "diff_p95_vs_a"]) <= 1e-12
    # Unpaired paths would not give 0: the same difference on shifted paths is spread out.
    shifted = path_sharpe(2 * a)[np.roll(np.arange(len(idx)), 1)] - sa
    assert np.quantile(shifted, hi) - np.quantile(shifted, lo) > 0.1


def test_sharpe_diff_against_self_is_zero(cfg):
    p, idx, _, _ = interval_inputs(cfg)
    ruined = synthetic_periods("r", [0.01] * 59 + [-1.0], rf=0.0, ruined=[False] * 59 + [True])
    out = sharpe_intervals(pd.concat([p, ruined], ignore_index=True), idx, ["a", "c"]).set_index("strategy_id")
    for b in ("a", "c"):
        row = out.loc[b]
        assert row[f"diff_vs_{b}"] == 0.0
        assert row[f"diff_p05_vs_{b}"] == 0.0 and row[f"diff_p95_vs_{b}"] == 0.0
        assert row[f"frac_le_0_vs_{b}"] == 1.0
    # A ruined strategy gets NaN intervals (amendment 4.2.8).
    assert out.loc["r"].ruined
    assert out.loc["r", ["sharpe_p05", "sharpe_p95", "diff_vs_a", "diff_p05_vs_c", "frac_le_0_vs_c"]].isna().all()
    x = np.array([0.01] * 59 + [-1.0])
    assert abs(out.loc["r", "sharpe"] - x.mean() / x.std(ddof=1) * math.sqrt(12)) <= 1e-12
