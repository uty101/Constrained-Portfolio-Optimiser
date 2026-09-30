import numpy as np
import pandas as pd
import pytest
import scipy.cluster.hierarchy as sch
from pypfopt import HRPOpt

from pc.allocators import Constraints
from pc.cov import window_daily
from pc.hrp import bisect_weights, cluster_var, hrp, quasi_diag_order


@pytest.mark.parametrize("t", ["2010-04-30", "2020-02-28"])
def test_hrp_matches_pypfopt(real, cfg, t):
    X = window_daily(real.returns_d, pd.Timestamp(t), cfg.sample.window_months)
    ours = hrp(None, X.cov(), None, Constraints())

    opt = HRPOpt(returns=X)
    ref = pd.Series(opt.optimize("single")).reindex(X.columns)
    ref_order = [X.columns[i] for i in sch.to_tree(opt.clusters, rd=False).pre_order()]
    our_order = [X.columns[i] for i in quasi_diag_order(X.cov())]
    assert our_order == ref_order, (our_order, ref_order)

    assert np.max(np.abs(ours.weights - ref)) <= 1e-10


def test_hrp_hand_worked_4_asset():
    """Four assets A, B, C, D, monthly vols 0.04, 0.05, 0.02, 0.03.

    Correlations rho_AB = 0.8, rho_CD = 0.6, rho_AC = 0.1, rho_AD = 0.2, rho_BC = 0.15,
    rho_BD = 0.1, so Sigma_ij = rho_ij s_i s_j:

            A        B        C        D
        A   0.0016   0.0016   0.00008  0.00024
        B   0.0016   0.0025   0.00015  0.00015
        C   0.00008  0.00015  0.0004   0.00036
        D   0.00024  0.00015  0.00036  0.0009

    Distances d = sqrt((1 - rho)/2): d_AB = sqrt(0.1) = 0.3162, d_CD = sqrt(0.2) = 0.4472,
    d_AD = sqrt(0.4) = 0.6325, d_BC = sqrt(0.425) = 0.6519, d_AC = d_BD = sqrt(0.45) = 0.6708.
    Single linkage merges {A, B} at 0.3162, then {C, D} at 0.4472, then the two at
    min(d_AC, d_AD, d_BC, d_BD) = 0.6325. The tree's leaf order is A, B, C, D, and the
    first bisection splits {A, B} from {C, D}.

    Cluster {A, B}: inverse-variance weights proportional to 1/0.0016 = 625 and
    1/0.0025 = 400, i.e. (25/41, 16/41). Its variance is
        V1 = (625 * 0.0016 + 256 * 0.0025 + 2 * 25 * 16 * 0.0016) / 41^2
           = (1.0 + 0.64 + 1.28) / 1681 = 2.92 / 1681 = 0.0017370612730517548.
    Cluster {C, D}: weights proportional to 1/0.0004 = 2500 and 1/0.0009 = 1111.1,
    i.e. (9/13, 4/13). Its variance is
        V2 = (81 * 0.0004 + 16 * 0.0009 + 2 * 9 * 4 * 0.00036) / 13^2
           = (0.0324 + 0.0144 + 0.02592) / 169 = 0.07272 / 169 = 0.0004302958579881656.
    alpha = 1 - V1 / (V1 + V2) = V2 / (V1 + V2) = 0.198534820046803 goes to {A, B},
    1 - alpha = 0.801465179953197 to {C, D}.

    Each pair is then split in halves of one asset each, and a single asset's inverse-
    variance portfolio is itself, so each split is again by inverse variance:
        A: alpha * 625 / 1025 = alpha * 25/41 = 0.12105781710170915
        B: alpha * 400 / 1025 = alpha * 16/41 = 0.07747700294509384
        C: (1 - alpha) * 9/13 = 0.5548605091983672
        D: (1 - alpha) * 4/13 = 0.24660467075482986
    """
    names = list("ABCD")
    vol = np.array([0.04, 0.05, 0.02, 0.03])
    rho = np.eye(4)
    for (i, j), r in {(0, 1): 0.8, (2, 3): 0.6, (0, 2): 0.1, (0, 3): 0.2, (1, 2): 0.15, (1, 3): 0.1}.items():
        rho[i, j] = rho[j, i] = r
    Sigma = pd.DataFrame(np.outer(vol, vol) * rho, index=names, columns=names)
    S = Sigma.to_numpy()

    assert quasi_diag_order(Sigma) == [0, 1, 2, 3]
    V1, V2 = cluster_var(S, [0, 1]), cluster_var(S, [2, 3])
    alpha = 1 - V1 / (V1 + V2)
    assert abs(V1 - 0.0017370612730517548) <= 1e-12
    assert abs(V2 - 0.0004302958579881656) <= 1e-12
    assert abs(alpha - 0.198534820046803) <= 1e-12

    expected = pd.Series(
        [0.12105781710170915, 0.07747700294509384, 0.5548605091983672, 0.24660467075482986], index=names
    )
    w = hrp(None, Sigma, None, Constraints()).weights
    assert np.max(np.abs(w - expected)) <= 1e-12
    np.testing.assert_array_equal(w.to_numpy(), bisect_weights(S, [0, 1, 2, 3]))
