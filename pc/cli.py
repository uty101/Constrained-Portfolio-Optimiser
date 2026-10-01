"""pctrade: the target weights of one registry strategy at a decision date, and the trades that
take a positions file there (PLAN 6.3, instruction 06 amendment 6.3).

Exit codes: 0 on success, 2 on an input error, 1 on anything else. An error is printed in one
line; --debug adds the stack trace.
"""

from __future__ import annotations

import argparse
import math
import sys
import traceback
from dataclasses import replace
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

import pandas as pd

from pc.backtest import ALLOCATORS, DateInputs, build_registry, constraint_sets, monthly_total_returns
from pc.calendar import build_calendar
from pc.config import Config, load_config
from pc.data import load_prices, load_rf_daily
from pc.returns import daily_returns, monthly_excess_returns
from pc.solver import CONFIG_PATH
from pc.trades import (
    POSITION_COLUMNS,
    TradeInputError,
    check_cash,
    current_weights,
    format_summary,
    generate_trades,
    price_warnings,
    validate_positions,
)

ROOT = CONFIG_PATH.parent
DEFAULT_STRATEGY = "mv_constrained|lw_cc|sample|C"
TRADES_CSV_KWARGS = dict(index=False, float_format="%.10g", lineterminator="\n")
SET_A_MESSAGE = "set A is research only; it shorts and levers"

# Step 6.5: the demo book, target weights of a $10,000,000 NAV at the 2026-07-31 closes; cash is
# the rest of the NAV.
DEMO_WEIGHTS = {"GLD": 0.40, "SPY": 0.20, "IEF": 0.20, "TLT": 0.10, "HYG": 0.05}
DEMO_NAV = Decimal("10000000.00")
DEMO_ASOF = "2026-07-31"
DEMO_PRICE_DECIMALS = 4


def repo_config() -> Config:
    """The repo's config.toml with the data paths made absolute, so pctrade runs from any folder."""
    cfg = load_config(CONFIG_PATH)
    data = replace(cfg.data, prices_csv=str(ROOT / cfg.data.prices_csv), rf_csv=str(ROOT / cfg.data.rf_csv),
                   manifest=str(ROOT / cfg.data.manifest))
    return replace(cfg, data=data)


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pctrade",
        description=(
            "Solve one registry strategy at a decision date and print the trades that take the book in "
            "--positions (columns ticker, quantity, price) plus --cash to its target weights. "
            "The allocator inputs are computed from the pinned data snapshot committed in data/raw, "
            "not from live prices: --asof must be a decision date of that snapshot's calendar, and a "
            "live run needs a fresh pull (scripts/pull_data.py) first."
        ),
        epilog="Exit codes: 0 success, 2 input error, 1 any other error.",
    )
    parser.add_argument("--positions", required=True, help="positions CSV with columns ticker, quantity, price")
    parser.add_argument("--cash", type=float, default=0.0, help="cash in the book (default 0)")
    parser.add_argument("--strategy", default=DEFAULT_STRATEGY,
                        help=f"a registry id, not set A (default {DEFAULT_STRATEGY})")
    parser.add_argument("--asof", default=None,
                        help="decision date YYYY-MM-DD in the calendar (default the last, "
                             f"{cfg.sample.last_decision})")
    parser.add_argument("--max-turnover", type=float, default=None,
                        help=f"turnover limit for a set C strategy, replacing mv.max_turnover ({cfg.mv.max_turnover:g})")
    parser.add_argument("--lot-size", type=float, default=cfg.cli.default_lot_size,
                        help=f"lot size in shares (default {cfg.cli.default_lot_size})")
    parser.add_argument("--min-notional", type=float, default=cfg.cli.default_min_notional,
                        help=f"drop trades below this notional (default {cfg.cli.default_min_notional:g})")
    parser.add_argument("--out", default="trades.csv", help="trades CSV to write (default trades.csv)")
    parser.add_argument("--dry-run", action="store_true", help="print only, write nothing")
    parser.add_argument("--debug", action="store_true", help="print the stack trace on an error")
    return parser


def read_positions(path: str | Path) -> pd.DataFrame:
    """The positions CSV as read, every column as text; validation is validate_positions'."""
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    except FileNotFoundError:
        raise TradeInputError(f"positions file not found: {path}") from None
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        raise TradeInputError(f"positions file {path} cannot be read as CSV: {e}") from None


def resolve_strategy(cfg: Config, strategy_id: str, max_turnover: float | None):
    """(spec, cfg with --max-turnover applied). Input errors: not a registry id, a set A
    strategy, --max-turnover on a strategy outside set C, a negative or non-finite limit."""
    by_id = {s.id: s for s in build_registry(cfg)}
    if strategy_id not in by_id:
        raise TradeInputError(f"--strategy {strategy_id!r} is not a registry id")
    spec = by_id[strategy_id]
    if spec.cons_set == "A":
        raise TradeInputError(f"--strategy {strategy_id}: {SET_A_MESSAGE}")
    if max_turnover is not None:
        if spec.cons_set != "C":
            raise TradeInputError(f"--max-turnover applies to set C strategies only; {strategy_id} is not in set C")
        if not (math.isfinite(max_turnover) and max_turnover >= 0):
            raise TradeInputError(f"--max-turnover {max_turnover} is not a non-negative number")
        cfg = replace(cfg, mv=replace(cfg.mv, max_turnover=max_turnover))
    return spec, cfg


def resolve_asof(asof: str | None, cal: pd.DataFrame) -> pd.Timestamp:
    dates = pd.DatetimeIndex(cal["decision_date"])
    if asof is None:
        return dates[-1]
    try:
        t = pd.Timestamp(asof)
    except ValueError:
        raise TradeInputError(f"--asof {asof!r} is not a date") from None
    if t not in dates:
        raise TradeInputError(f"--asof {asof} is not a decision date in the calendar "
                              f"({dates[0]:%Y-%m-%d} to {dates[-1]:%Y-%m-%d}, last trading day of each month)")
    return t


def complete_book(positions: pd.DataFrame, closes: pd.Series, tickers: list[str]) -> pd.DataFrame:
    """The validated positions plus a row (quantity 0, price = the panel close on the decision
    date) for every universe ticker not in the file, in config order (decisions/OPEN.md, item 11)."""
    p = positions.set_index("ticker")
    rows = [(t, float(p.at[t, "quantity"]), float(p.at[t, "price"])) if t in p.index
            else (t, 0.0, float(closes[t])) for t in tickers]
    return pd.DataFrame(rows, columns=POSITION_COLUMNS)


def plan(args: argparse.Namespace, cfg: Config) -> dict:
    """Everything pctrade prints and writes, from parsed arguments."""
    tickers = list(cfg.universe.tickers)
    spec, run_cfg = resolve_strategy(cfg, args.strategy, args.max_turnover)
    cash = check_cash(args.cash)
    if not args.lot_size > 0:
        raise TradeInputError(f"--lot-size {args.lot_size} is not positive")
    if not args.min_notional >= 0:
        raise TradeInputError(f"--min-notional {args.min_notional} is negative")
    positions = validate_positions(read_positions(args.positions), tickers)

    prices = load_prices(run_cfg)
    rf_daily = load_rf_daily(run_cfg, prices.index)
    asof = resolve_asof(args.asof, build_calendar(prices.index, run_cfg))
    closes = prices.loc[asof]
    book = complete_book(positions, closes, tickers)

    # w_prev is w_before of the book (amendment 6.1), not the backtest's drifted weights.
    w_prev, _ = current_weights(book, cash, tickers)
    inputs = DateInputs(asof, daily_returns(prices), monthly_excess_returns(prices, rf_daily),
                        monthly_total_returns(prices), run_cfg)
    mu, Sigma, _, _ = inputs.for_spec(spec)
    cons = constraint_sets(run_cfg)[spec.cons_set]
    res = ALLOCATORS[spec.allocator](mu, Sigma, w_prev, cons)
    trades, summary = generate_trades(book, cash, res.weights, run_cfg, args.lot_size, args.min_notional)
    return {
        "spec": spec, "asof": asof, "res": res, "trades": trades, "summary": summary,
        "tau": cons.max_turnover if spec.cons_set == "C" else None,
        "warnings": price_warnings(positions, closes, run_cfg.cli.price_warn_pct, asof),
    }


def report(result: dict) -> str:
    """The summary, then the trades table."""
    text = format_summary(result["summary"], result["res"], result["spec"].id, result["asof"], result["tau"],
                          result["warnings"])
    trades = result["trades"]
    table = "no trades" if trades.empty else trades.to_string(index=False)
    return f"{text}\n\n{table}"


def main(argv: list[str] | None = None) -> int:
    debug = "--debug" in (sys.argv[1:] if argv is None else argv)
    try:
        cfg = repo_config()
        parser = build_parser(cfg)
        try:
            args = parser.parse_args(argv)
        except SystemExit as e:  # --help (0) or an argparse usage error (2)
            return 0 if e.code is None else int(e.code)
        result = plan(args, cfg)
        print(report(result))
        if args.dry_run:
            print("\ndry run: nothing written")
        else:
            result["trades"].to_csv(args.out, **TRADES_CSV_KWARGS)
            print(f"\nwrote {args.out}")
        return 0
    except TradeInputError as e:
        print(f"pctrade: error: {e}", file=sys.stderr)
        if debug:
            traceback.print_exc()
        return e.code
    except Exception as e:  # noqa: BLE001 - every other failure is exit 1, one line
        print(f"pctrade: error: {type(e).__name__}: {e}", file=sys.stderr)
        if debug:
            traceback.print_exc()
        return 1


# --- 6.5 demo book -------------------------------------------------------------------------------


def demo_book(cfg: Config) -> tuple[pd.DataFrame, Decimal]:
    """(positions, cash) of the step 6.5 demo book: price_i = the DEMO_ASOF close rounded to 4
    decimals, quantity_i = floor(weight_i x NAV / price_i), cash = NAV - sum quantity x price,
    exact in decimal so the NAV is exactly $10,000,000.00. Rows in config order."""
    closes = load_prices(cfg).loc[pd.Timestamp(DEMO_ASOF)]
    rows, held = [], Decimal(0)
    for t in cfg.universe.tickers:
        if t not in DEMO_WEIGHTS:
            continue
        price = Decimal(repr(round(float(closes[t]), DEMO_PRICE_DECIMALS)))
        qty = int((Decimal(repr(DEMO_WEIGHTS[t])) * DEMO_NAV / price).to_integral_value(rounding=ROUND_FLOOR))
        held += qty * price
        rows.append((t, qty, float(price)))
    return pd.DataFrame(rows, columns=POSITION_COLUMNS), DEMO_NAV - held
