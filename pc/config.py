"""Typed, frozen view of config.toml.

One field per key, one nested frozen dataclass per table. Ticker-keyed tables
(universe.asset_class, costs.one_way_bp, bl.w_mkt) are held as dicts in config
ticker order; any key that is not a configured ticker is kept, after the
tickers, so that tests can see it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    seed_master: int
    bootstrap_seed: int
    cov_eval_seed: int
    sensitivity_seed: int


@dataclass(frozen=True)
class UniverseConfig:
    tickers: tuple[str, ...]
    asset_class: dict[str, str]


@dataclass(frozen=True)
class SampleConfig:
    price_start: str
    price_end: str
    first_decision: str
    last_decision: str
    window_months: int
    days_per_month: int
    expected_n_decisions: int


@dataclass(frozen=True)
class DataConfig:
    prices_csv: str
    rf_csv: str
    manifest: str
    max_abs_daily_return_flag: float
    max_gap_days_flag: int


@dataclass(frozen=True)
class CovConfig:
    estimators: tuple[str, ...]
    ewma_lambda: float
    pca_k: int
    max_cond: float


@dataclass(frozen=True)
class MvConfig:
    gamma: float
    upper: float
    lower: float
    max_turnover: float


@dataclass(frozen=True)
class CostsConfig:
    cost_scales: tuple[float, ...]
    one_way_bp: dict[str, float]


@dataclass(frozen=True)
class BlConfig:
    delta: float
    tau: float
    mom_lookback: int
    mom_skip: int
    n_long_short: int
    equity_basket: tuple[str, ...]
    bond_basket: tuple[str, ...]
    w_mkt: dict[str, float]


@dataclass(frozen=True)
class SolverConfig:
    primary: str
    fallback: str
    scs_eps: float
    clarabel_tol: float
    rp_ftol: float
    rp_gtol: float
    rp_maxiter: int


@dataclass(frozen=True)
class CovEvalConfig:
    n_random: int


@dataclass(frozen=True)
class BootstrapConfig:
    mean_block: float
    reps: int
    ci: tuple[float, ...]


@dataclass(frozen=True)
class SensitivityConfig:
    dates: tuple[str, ...]
    draws: int


@dataclass(frozen=True)
class TurnoverGridConfig:
    taus: tuple[float, ...]
    include_none: bool


@dataclass(frozen=True)
class PositionsConfig:
    threshold: float


@dataclass(frozen=True)
class LeveredConfig:
    strategies: tuple[str, ...]
    financing_spread_bp_pa: float


@dataclass(frozen=True)
class CliConfig:
    default_lot_size: int
    default_min_notional: float
    price_warn_pct: float


@dataclass(frozen=True)
class OutputsConfig:
    results_dir: str
    tables_dir: str
    figures_dir: str


@dataclass(frozen=True)
class Config:
    run: RunConfig
    universe: UniverseConfig
    sample: SampleConfig
    data: DataConfig
    cov: CovConfig
    mv: MvConfig
    costs: CostsConfig
    bl: BlConfig
    solver: SolverConfig
    cov_eval: CovEvalConfig
    bootstrap: BootstrapConfig
    sensitivity: SensitivityConfig
    turnover_grid: TurnoverGridConfig
    positions: PositionsConfig
    levered: LeveredConfig
    cli: CliConfig
    outputs: OutputsConfig


def _ticker_ordered(table: dict, tickers: tuple[str, ...]) -> dict:
    ordered = {t: table[t] for t in tickers if t in table}
    ordered.update({k: v for k, v in table.items() if k not in ordered})
    return ordered


def _tuples(table: dict) -> dict:
    return {k: tuple(v) if isinstance(v, list) else v for k, v in table.items()}


def load_config(path: str | Path = "config.toml") -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    tickers = tuple(raw["universe"]["tickers"])
    universe = dict(raw["universe"])
    universe["tickers"] = tickers
    universe["asset_class"] = _ticker_ordered(universe["asset_class"], tickers)
    costs = _tuples(raw["costs"])
    costs["one_way_bp"] = _ticker_ordered(costs["one_way_bp"], tickers)
    bl = _tuples(raw["bl"])
    bl["w_mkt"] = _ticker_ordered(bl["w_mkt"], tickers)

    return Config(
        run=RunConfig(**raw["run"]),
        universe=UniverseConfig(**universe),
        sample=SampleConfig(**raw["sample"]),
        data=DataConfig(**raw["data"]),
        cov=CovConfig(**_tuples(raw["cov"])),
        mv=MvConfig(**raw["mv"]),
        costs=CostsConfig(**costs),
        bl=BlConfig(**bl),
        solver=SolverConfig(**raw["solver"]),
        cov_eval=CovEvalConfig(**raw["cov_eval"]),
        bootstrap=BootstrapConfig(**_tuples(raw["bootstrap"])),
        sensitivity=SensitivityConfig(**_tuples(raw["sensitivity"])),
        turnover_grid=TurnoverGridConfig(**_tuples(raw["turnover_grid"])),
        positions=PositionsConfig(**raw["positions"]),
        levered=LeveredConfig(**_tuples(raw["levered"])),
        cli=CliConfig(**raw["cli"]),
        outputs=OutputsConfig(**raw["outputs"]),
    )
