"""Allocators with the uniform signature allocate(mu, Sigma, w_prev, cons) -> AllocResult.

mu, Sigma and w_prev share one ticker index, in config order; a mismatch raises
ValueError and nothing is reordered. w_prev = None is the first period (kickoff 4.4):
no turnover constraint and no cost term.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cvxpy as cp
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from pc.solver import SolveRecord, merge_records, solve, solver_config, symmetrise, turnover_feasibility

# Kickoff 5.3 allocator 4: L-BFGS-B bounds (1e-12, None) (convention 22).
RP_LOWER = 1e-12


@dataclass(frozen=True)
class Constraints:
    budget: float = 1.0
    lower: float | None = None  # None = unbounded
    upper: float | None = None
    max_turnover: float | None = None
    cost: pd.Series | None = None  # one-way decimal per ticker
    gamma: float = 2.5


@dataclass
class AllocResult:
    weights: pd.Series
    solver: str
    status: str
    fallback: bool
    objective: float
    turnover_dual: float  # NaN when no turnover constraint
    tau_relaxed: bool
    tau_eff: float  # NaN when no turnover constraint


def check_index(
    mu: pd.Series | None,
    Sigma: pd.DataFrame,
    w_prev: pd.Series | None,
    cons: Constraints | None = None,
) -> pd.Index:
    """The shared ticker index. Raises ValueError unless every input carries it in the same order."""
    index = Sigma.index
    if list(Sigma.columns) != list(index):
        raise ValueError("Sigma rows and columns differ")
    named = {"mu": mu, "w_prev": w_prev, "cons.cost": None if cons is None else cons.cost}
    for name, s in named.items():
        if s is not None and list(s.index) != list(index):
            raise ValueError(f"{name} index {list(s.index)} does not match Sigma {list(index)}")
    return index


def fallback_weights(w_prev: pd.Series | None, index: pd.Index) -> pd.Series:
    """Hold drifted w_prev; with no w_prev (first period), 1/N."""
    if w_prev is not None:
        return w_prev.astype(float).copy()
    return pd.Series(1.0 / len(index), index=index)


def solved_result(
    w: cp.Variable,
    prob: cp.Problem,
    records: list[SolveRecord],
    index: pd.Index,
    w_prev: pd.Series | None,
    turnover_con: cp.Constraint | None = None,
    tau_relaxed: bool = False,
    tau_eff: float = math.nan,
) -> AllocResult:
    """AllocResult from the solves of one allocator call; holds w_prev (or 1/N) on fallback."""
    record = merge_records(records)
    if record.fallback:
        return AllocResult(
            weights=fallback_weights(w_prev, index),
            solver=record.solver,
            status=record.status,
            fallback=True,
            objective=math.nan,
            turnover_dual=math.nan,
            tau_relaxed=tau_relaxed,
            tau_eff=tau_eff,
        )
    dual = math.nan if turnover_con is None else float(np.asarray(turnover_con.dual_value))
    return AllocResult(
        weights=pd.Series(np.asarray(w.value, dtype=float), index=index),
        solver=record.solver,
        status=record.status,
        fallback=False,
        objective=float(prob.value),
        turnover_dual=dual,
        tau_relaxed=tau_relaxed,
        tau_eff=tau_eff,
    )


def _bounds(w: cp.Variable, cons: Constraints) -> dict[str, cp.Constraint]:
    """Budget, and each bound that is not None, keyed budget / lower / upper."""
    out = {"budget": cp.sum(w) == cons.budget}
    if cons.lower is not None:
        out["lower"] = w >= cons.lower
    if cons.upper is not None:
        out["upper"] = w <= cons.upper
    return out


def mv_unconstrained(mu, Sigma, w_prev, cons) -> AllocResult:
    """Set A closed form: w = (1/gamma) Sigma^-1 (mu - eta 1), eta = (1' Sigma^-1 mu - gamma budget) / (1' Sigma^-1 1).

    No solver. cons.gamma and cons.budget are read; bounds, turnover and cost are not.
    """
    index = check_index(mu, Sigma, w_prev, cons)
    m = mu.to_numpy(dtype=float)
    S = Sigma.to_numpy(dtype=float)
    ab = np.linalg.solve(S, np.column_stack([m, np.ones(len(m))]))
    a, b = ab[:, 0], ab[:, 1]
    eta = (a.sum() - cons.gamma * cons.budget) / b.sum()
    w = (a - eta * b) / cons.gamma
    objective = float(m @ w - cons.gamma / 2 * w @ S @ w)
    return AllocResult(
        weights=pd.Series(w, index=index),
        solver="closed_form",
        status="optimal",
        fallback=False,
        objective=objective,
        turnover_dual=math.nan,
        tau_relaxed=False,
        tau_eff=math.nan,
    )


def min_variance(mu, Sigma, w_prev, cons) -> AllocResult:
    """Set B: min w' Sigma w (Sigma symmetrised) s.t. 1'w = budget, lower <= w <= upper. mu is not read.

    objective is the monthly variance w' Sigma w.
    """
    index = check_index(mu, Sigma, w_prev, cons)
    w = cp.Variable(len(index))
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, symmetrise(Sigma))), list(_bounds(w, cons).values()))
    return solved_result(w, prob, [solve(prob)], index, w_prev)


def mv_problem(
    mu: pd.Series,
    Sigma: pd.DataFrame,
    w_prev: pd.Series | None,
    cons: Constraints,
    tau_eff: float | None,
) -> tuple[cp.Problem, cp.Variable, dict[str, cp.Constraint]]:
    """max mu'w - gamma/2 quad_form(w, Sigma) - cost @ |w - w_prev| over the bounds of cons.

    With w_prev given, the cost term is built even when cons.cost is None (cost 0), and
    tau_eff not None adds norm1(w - w_prev) <= tau_eff. With w_prev None there is neither.
    The constraints are returned keyed budget / lower / upper / turnover.
    """
    w = cp.Variable(len(Sigma))
    constraints = _bounds(w, cons)
    objective = mu.to_numpy(dtype=float) @ w - cons.gamma / 2 * cp.quad_form(w, symmetrise(Sigma))
    if w_prev is not None:
        prev = w_prev.to_numpy(dtype=float)
        cost = np.zeros(len(prev)) if cons.cost is None else cons.cost.to_numpy(dtype=float)
        objective = objective - cost @ cp.abs(w - prev)
        if tau_eff is not None:
            constraints["turnover"] = cp.norm1(w - prev) <= tau_eff
    prob = cp.Problem(cp.Maximize(objective), list(constraints.values()))
    return prob, w, constraints


def mv_constrained(mu, Sigma, w_prev, cons) -> AllocResult:
    """Set C, or set B when turnover and costs are off (kickoff 5.3, allocator 2).

    With w_prev and cons.max_turnover both given, the feasibility LP runs first and the
    turnover limit is tau_eff (tau, or tau_min + 1e-6 when tau_min > tau). turnover_dual is
    the dual of that constraint: monthly return per unit of turnover.
    """
    index = check_index(mu, Sigma, w_prev, cons)
    records = []
    tau_eff, tau_relaxed = math.nan, False
    if w_prev is not None and cons.max_turnover is not None:
        _, tau_eff, tau_relaxed, record = turnover_feasibility(
            w_prev, cons.max_turnover, cons.lower, cons.upper, cons.budget
        )
        records.append(record)
        if record.fallback:
            return solved_result(None, None, records, index, w_prev, None, tau_relaxed, tau_eff)
    limit = None if math.isnan(tau_eff) else tau_eff
    prob, w, constraints = mv_problem(mu, Sigma, w_prev, cons, limit)
    records.append(solve(prob))
    return solved_result(w, prob, records, index, w_prev, constraints.get("turnover"), tau_relaxed, tau_eff)


def risk_parity(mu, Sigma, w_prev, cons) -> AllocResult:
    """Spinu: min 1/2 x'Sigma x - sum_i b_i log x_i, b_i = 1/N, by L-BFGS-B; w = x / 1'x.

    Long-only, no caps; mu and cons are not read, w_prev only for the index check.
    Gradient Sigma x - b/x, bounds (1e-12, None), x0 = 1/sqrt(diag Sigma), ftol, gtol and
    maxiter from [solver]. status is "optimal" when scipy reports success, else scipy's
    message; the weights are x / 1'x either way. objective is NaN.
    """
    index = check_index(mu, Sigma, w_prev, cons)
    S = symmetrise(Sigma)
    n = len(S)
    b = np.full(n, 1.0 / n)
    scfg = solver_config()

    def f(x):
        Sx = S @ x
        return 0.5 * x @ Sx - b @ np.log(x), Sx - b / x

    res = minimize(
        f,
        1.0 / np.sqrt(np.diag(S)),
        jac=True,
        method="L-BFGS-B",
        bounds=[(RP_LOWER, None)] * n,
        options={"ftol": scfg.rp_ftol, "gtol": scfg.rp_gtol, "maxiter": scfg.rp_maxiter},
    )
    x = res.x
    return AllocResult(
        weights=pd.Series(x / x.sum(), index=index),
        solver="L-BFGS-B",
        status="optimal" if res.success else str(res.message),
        fallback=False,
        objective=math.nan,
        turnover_dual=math.nan,
        tau_relaxed=False,
        tau_eff=math.nan,
    )
