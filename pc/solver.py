"""Solver policy for every cvxpy problem in pc/, and the set C feasibility LP.

Policy (kickoff 5.3): solve with `solver.primary` (CLARABEL, at `solver.clarabel_tol`
for tol_gap_abs, tol_gap_rel and tol_feas). On any status other than "optimal",
including "optimal_inaccurate" and a raised SolverError, retry once with
`solver.fallback` (SCS, eps = `solver.scs_eps`). If SCS is not "optimal" either, the
record carries fallback = True and the caller holds w_prev.

Allocators take (mu, Sigma, w_prev, cons) and no Config, so the solver settings are
read here from the repo's config.toml.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd

from pc.config import SolverConfig, load_config

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.toml"

# Kickoff 5.3 feasibility rule: tau_eff = tau_min + 1e-6 (convention 22).
TAU_RELAX = 1e-6


@lru_cache(maxsize=1)
def solver_config() -> SolverConfig:
    return load_config(CONFIG_PATH).solver


@dataclass(frozen=True)
class SolveRecord:
    solvers: tuple[str, ...]  # every solver called, in call order
    status: str  # status of the last call
    fallback: bool  # True when no call ended "optimal"

    @property
    def solver(self) -> str:
        return "+".join(self.solvers)


def merge_records(records: list[SolveRecord]) -> SolveRecord:
    """One record for several solves in one allocator call (the LP, then the QP).

    solvers are concatenated in order, so the number of SCS retries in a call is
    record.solvers.count("SCS"). status is the first failing status, else "optimal".
    """
    solvers = tuple(s for r in records for s in r.solvers)
    failed = [r for r in records if r.fallback]
    status = failed[0].status if failed else records[-1].status
    return SolveRecord(solvers, status, bool(failed))


def _options(name: str, scfg: SolverConfig) -> dict:
    if name == "CLARABEL":
        tol = scfg.clarabel_tol
        return {"tol_gap_abs": tol, "tol_gap_rel": tol, "tol_feas": tol}
    if name == "SCS":
        return {"eps": scfg.scs_eps}
    return {}


def solve(prob: cp.Problem) -> SolveRecord:
    """Solve prob in place under the policy above and return what happened."""
    scfg = solver_config()
    called = []
    status = "not_solved"
    for name in (scfg.primary, scfg.fallback):
        called.append(name)
        try:
            prob.solve(solver=name, **_options(name, scfg))
            status = prob.status
        except cp.error.SolverError:
            status = "solver_error"
        if status == cp.OPTIMAL:
            return SolveRecord(tuple(called), status, False)
    return SolveRecord(tuple(called), status, True)


def turnover_feasibility(
    w_prev: pd.Series,
    tau: float,
    lower: float | None,
    upper: float | None,
    budget: float = 1.0,
) -> tuple[float, float, bool, SolveRecord]:
    """(tau_min, tau_eff, tau_relaxed, record).

    tau_min = min ||w - w_prev||_1 s.t. 1'w = budget, lower <= w <= upper (a bound that is
    None is left off). If tau_min > tau, tau_eff = tau_min + 1e-6 and tau_relaxed is True;
    otherwise tau_eff = tau. When the LP falls back, tau_min and tau_eff are NaN.
    """
    w = cp.Variable(len(w_prev))
    constraints = [cp.sum(w) == budget]
    if lower is not None:
        constraints.append(w >= lower)
    if upper is not None:
        constraints.append(w <= upper)
    prob = cp.Problem(cp.Minimize(cp.norm1(w - w_prev.to_numpy(dtype=float))), constraints)
    record = solve(prob)
    if record.fallback:
        return math.nan, math.nan, False, record
    tau_min = float(prob.value)
    if tau_min > tau:
        return tau_min, tau_min + TAU_RELAX, True, record
    return tau_min, float(tau), False, record


def symmetrise(Sigma: pd.DataFrame) -> np.ndarray:
    A = Sigma.to_numpy(dtype=float)
    return 0.5 * (A + A.T)
