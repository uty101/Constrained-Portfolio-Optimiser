"""Walk-forward engine (kickoff 5.7): the strategy registry and the monthly backtest."""

from __future__ import annotations

from dataclasses import dataclass

from pc.config import Config


@dataclass(frozen=True)
class StrategySpec:
    allocator: str
    cov: str  # an estimator in cov.estimators, or "none"
    mu_model: str  # "sample", "bayes_stein", "bl" or "none"
    cons_set: str  # "A", "B", "C" or "none"
    id: str


def spec(allocator: str, cov: str, mu_model: str, cons_set: str) -> StrategySpec:
    return StrategySpec(allocator, cov, mu_model, cons_set, f"{allocator}|{cov}|{mu_model}|{cons_set}")


def build_registry(cfg: Config) -> list[StrategySpec]:
    """The 26 strategies of kickoff 5.7, in the order listed there; estimators in config order."""
    est = cfg.cov.estimators
    return [
        *(spec("mv_unconstrained", e, "sample", "A") for e in est),
        *(spec("mv_constrained", e, "sample", "C") for e in est),
        spec("mv_constrained", "lw_cc", "bayes_stein", "C"),
        *(spec("min_variance", e, "none", "B") for e in est),
        *(spec("risk_parity", e, "none", "none") for e in est),
        *(spec("black_litterman", e, "bl", "C") for e in est),
        *(spec("hrp", e, "none", "none") for e in est),
        spec("equal_weight", "none", "none", "none"),
    ]
