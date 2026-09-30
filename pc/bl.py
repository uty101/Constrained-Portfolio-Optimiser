"""Black-Litterman prior, mechanical momentum views and posterior (kickoff 5.4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pc.config import Config
from pc.returns_model import trailing_months


def implied_returns(Sigma: pd.DataFrame, w_mkt: pd.Series, delta: float) -> pd.Series:
    """Pi = delta Sigma w_mkt."""
    if list(w_mkt.index) != list(Sigma.index):
        raise ValueError("w_mkt and Sigma must share one ticker index")
    return pd.Series(delta * Sigma.to_numpy(dtype=float) @ w_mkt.to_numpy(dtype=float), index=Sigma.index)


def momentum_window(monthly: pd.DataFrame, t: pd.Timestamp, cfg: Config) -> pd.DataFrame:
    """The 12-1 window: the months in (t - mom_lookback months, t - mom_skip months], month t skipped.

    With mom_lookback 12 and mom_skip 1 these are the 11 month-ends from month(t) - 11 to
    month(t) - 1.
    """
    return trailing_months(monthly, t, cfg.bl.mom_lookback - 1, cfg.bl.mom_skip)


def momentum_views(
    monthly_total: pd.DataFrame, monthly_excess: pd.DataFrame, t: pd.Timestamp, cfg: Config
) -> tuple[pd.DataFrame, pd.Series]:
    """(P: views x tickers, Q). Row "momentum" and row "stocks_bonds", in that order.

    momentum: tickers are ranked by compounded total return over the 12-1 window, highest
    first, ties by config order (the earlier ticker ranks higher). +1/k on the first k,
    -1/k on the last k of that one ranking, k = bl.n_long_short.
    stocks_bonds: +1/4 on bl.equity_basket, -1/3 on bl.bond_basket.
    Q = P times the mean monthly excess return over the same window.
    """
    tickers = list(cfg.universe.tickers)
    for name, frame in (("monthly_total", monthly_total), ("monthly_excess", monthly_excess)):
        if list(frame.columns) != tickers:
            raise ValueError(f"{name} columns are not the configured tickers in config order")
    total = momentum_window(monthly_total, t, cfg)
    excess = momentum_window(monthly_excess, t, cfg)
    if not total.index.equals(excess.index):
        raise ValueError("monthly_total and monthly_excess windows differ")

    mom = ((1 + total).prod() - 1).to_numpy()
    ranking = sorted(range(len(tickers)), key=lambda i: (-mom[i], i))
    k = cfg.bl.n_long_short
    P = pd.DataFrame(0.0, index=["momentum", "stocks_bonds"], columns=tickers)
    P.loc["momentum", [tickers[i] for i in ranking[:k]]] = 1.0 / k
    P.loc["momentum", [tickers[i] for i in ranking[-k:]]] = -1.0 / k
    P.loc["stocks_bonds", list(cfg.bl.equity_basket)] = 1.0 / len(cfg.bl.equity_basket)
    P.loc["stocks_bonds", list(cfg.bl.bond_basket)] = -1.0 / len(cfg.bl.bond_basket)
    Q = pd.Series(P.to_numpy() @ excess.mean().to_numpy(), index=P.index)
    return P, Q


def omega(Sigma: pd.DataFrame, P: pd.DataFrame, tau: float) -> np.ndarray:
    """The diagonal of Omega = diag(P tau Sigma P'), as a vector."""
    p = P.to_numpy(dtype=float)
    return np.einsum("ij,jk,ik->i", p, tau * Sigma.to_numpy(dtype=float), p)


def posterior(
    Sigma: pd.DataFrame, Pi: pd.Series, P: pd.DataFrame, Q: pd.Series, tau: float, omega_diag: np.ndarray
) -> tuple[pd.Series, pd.DataFrame]:
    """(mu_BL, Sigma_BL) for a given diagonal Omega.

    A = (tau Sigma)^-1 + P' Omega^-1 P; mu_BL = A^-1 [(tau Sigma)^-1 Pi + P' Omega^-1 Q];
    Sigma_BL = Sigma + A^-1. Every A^-1 and (tau Sigma)^-1 product is an np.linalg.solve.
    With no views (P has 0 rows) A^-1 = tau Sigma, so mu_BL = Pi exactly and
    Sigma_BL = Sigma + tau Sigma.
    """
    index = Sigma.index
    if list(Pi.index) != list(index) or list(P.columns) != list(index) or list(Q.index) != list(P.index):
        raise ValueError("Sigma, Pi, P and Q must share one ticker index (and P and Q one view index)")
    S = Sigma.to_numpy(dtype=float)
    if len(P) == 0:
        return Pi.astype(float).copy(), pd.DataFrame(S + tau * S, index=index, columns=index)
    tS = tau * S
    p = P.to_numpy(dtype=float)
    pt_oinv = p.T / omega_diag
    n = len(S)
    A = np.linalg.solve(tS, np.eye(n)) + pt_oinv @ p
    rhs = np.linalg.solve(tS, Pi.to_numpy(dtype=float)) + pt_oinv @ Q.to_numpy(dtype=float)
    mu_bl = np.linalg.solve(A, rhs)
    A_inv = np.linalg.solve(A, np.eye(n))
    Sigma_bl = S + 0.5 * (A_inv + A_inv.T)
    return pd.Series(mu_bl, index=index), pd.DataFrame(Sigma_bl, index=index, columns=index)


def bl_posterior(Sigma, Pi, P, Q, tau) -> tuple[pd.Series, pd.DataFrame]:
    """(mu_BL, Sigma_BL) with Omega = diag(P tau Sigma P'), Sigma the conditioned monthly covariance."""
    return posterior(Sigma, Pi, P, Q, tau, omega(Sigma, P, tau))
