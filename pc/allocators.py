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

from pc.solver import SolveRecord, merge_records


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
