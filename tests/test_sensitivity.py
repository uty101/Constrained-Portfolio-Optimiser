from dataclasses import replace

import numpy as np
import pandas as pd

from pc.backtest import DateInputs
from pc.sensitivity import MU_STRATEGIES, REFERENCE_STRATEGIES, perturbations, sensitivity_at, summarise

DATE = "2020-02-28"
DRAWS = 20


def small(cfg):
    return replace(cfg, sensitivity=replace(cfg.sensitivity, draws=DRAWS))


def inputs_at(real, cfg):
    return DateInputs(pd.Timestamp(DATE), real.returns_d, real.monthly_excess, real.monthly_total, cfg)


def test_sensitivity_deterministic_under_seed(cfg, real):
    c = small(cfg)
    k = 1
    a = sensitivity_at(inputs_at(real, c), k, c)
    b = sensitivity_at(inputs_at(real, c), k, c)
    for sid in MU_STRATEGIES + REFERENCE_STRATEGIES:
        assert np.array_equal(a.base[sid], b.base[sid]), sid
        assert np.array_equal(a.draws[sid], b.draws[sid]), sid
    for fa, fb in zip(summarise(a), summarise(b)):
        pd.testing.assert_frame_equal(fa, fb, check_exact=True)

    # Amendment 5.1: one generator per date, default_rng(sensitivity_seed + k); Z first, then Z_Q.
    # eps = Z L', L = chol(Sigma_lw / 36); eps_Q = Z_Q L_Q', L_Q = chol(P Sigma_lw P' / 11).
    rng = np.random.default_rng(c.run.sensitivity_seed + k)
    Z = rng.standard_normal((DRAWS, 18))
    Z_q = rng.standard_normal((DRAWS, 2))
    S = real.sigma(DATE, "lw_cc").to_numpy(dtype=float)
    P = inputs_at(real, c).views()[0].to_numpy(dtype=float)
    assert np.array_equal(a.eps, Z @ np.linalg.cholesky(S / 36).T)
    assert np.array_equal(a.eps_q, Z_q @ np.linalg.cholesky(P @ S @ P.T / 11).T)

    # Another date index draws other numbers.
    other, _ = perturbations(real.sigma(DATE, "lw_cc"), inputs_at(real, c).views()[0], k + 1, c)
    assert not np.array_equal(other, a.eps)
    # The mu-based strategies do move under the draws.
    summary = summarise(a)[1].set_index("strategy")
    assert (summary.loc[MU_STRATEGIES, "mean_abs_change"] > 0).all()


def test_reference_strategies_zero_dispersion(cfg, real):
    c = small(cfg)
    dd = sensitivity_at(inputs_at(real, c), 0, c)
    sens, summary = summarise(dd)
    for sid in REFERENCE_STRATEGIES:
        # Every draw is given a different mu; the references do not read it.
        assert (dd.draws[sid] == dd.base[sid]).all(), sid
        rows = sens[sens["strategy"] == sid]
        assert (rows["iqr"] == 0).all()
        for q in ("p05", "p25", "p50", "p75", "p95"):
            assert (rows[q] == rows["w_base"]).all(), (sid, q)
        s = summary[summary["strategy"] == sid].iloc[0]
        assert s.mean_abs_change == 0.0
        assert s.frac_top_asset_changes == 0.0
