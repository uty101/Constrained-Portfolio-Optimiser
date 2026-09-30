"""Hierarchical risk parity (Lopez de Prado), written by hand (kickoff 5.3, allocator 6)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import squareform

from pc.allocators import AllocResult, check_index


def quasi_diag_order(Sigma: pd.DataFrame) -> list[int]:
    """Leaf order of the single-linkage tree on d_ij = sqrt(clip((1 - rho_ij)/2, 0, 1)).

    rho is derived from Sigma. Linkage is applied to d directly (convention 14); the
    diagonal of d is not read (squareform with checks=False).
    """
    S = Sigma.to_numpy(dtype=float)
    sd = np.sqrt(np.diag(S))
    rho = S / np.outer(sd, sd)
    d = np.sqrt(np.clip((1.0 - rho) / 2.0, 0.0, 1.0))
    link = linkage(squareform(d, checks=False), "single")
    return to_tree(link, rd=False).pre_order()


def cluster_var(S: np.ndarray, items: list[int]) -> float:
    """Variance of the inverse-variance portfolio of `items`."""
    sub = S[np.ix_(items, items)]
    ivp = 1.0 / np.diag(sub)
    ivp /= ivp.sum()
    return float(ivp @ sub @ ivp)


def bisect_weights(S: np.ndarray, order: list[int]) -> np.ndarray:
    """Recursive bisection of `order` in halves; alpha = 1 - V1/(V1 + V2) goes to the first half."""
    w = np.ones(len(order))
    clusters = [list(order)]
    while clusters:
        clusters = [c[j:k] for c in clusters for j, k in ((0, len(c) // 2), (len(c) // 2, len(c))) if len(c) > 1]
        for first, second in zip(clusters[0::2], clusters[1::2]):
            v1, v2 = cluster_var(S, first), cluster_var(S, second)
            alpha = 1 - v1 / (v1 + v2)
            w[first] *= alpha
            w[second] *= 1 - alpha
    return w


def hrp(mu, Sigma, w_prev, cons) -> AllocResult:
    """Long-only, no caps. mu and cons are not read; w_prev only for the index check. objective is NaN."""
    index = check_index(mu, Sigma, w_prev, cons)
    S = Sigma.to_numpy(dtype=float)
    w = bisect_weights(S, quasi_diag_order(Sigma))
    return AllocResult(
        weights=pd.Series(w, index=index),
        solver="none",
        status="optimal",
        fallback=False,
        objective=math.nan,
        turnover_dual=math.nan,
        tau_relaxed=False,
        tau_eff=math.nan,
    )
