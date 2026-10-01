"""Trade generator (PLAN 6.1 and 6.2, instruction 06 amendments 6.1 and 6.2).

A book is a positions frame (ticker, quantity, price) plus cash. Weights are holdings value
over NAV = sum qty x price + cash; cash is not a weight, so w_before sums to 1 - cash/NAV and
the allocator's budget constraint invests it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from pc.backtest import BP_PER_UNIT, cost_vector
from pc.config import Config, load_config
from pc.solver import CONFIG_PATH

POSITION_COLUMNS = ["ticker", "quantity", "price"]
TRADE_COLUMNS = ["ticker", "side", "quantity", "price", "notional", "est_cost", "weight_before", "weight_target",
                 "weight_after"]
# bp of monthly return per 1% of turnover = turnover_dual x 1e4 bp x 0.01 (amendment 6.2).
BP_PER_PCT = BP_PER_UNIT / 100


class TradeInputError(ValueError):
    """A bad positions file, cash amount or command-line value; the CLI exits with code."""

    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def universe_tickers() -> tuple[str, ...]:
    """The configured tickers, from the repo's config.toml (current_weights has no Config argument)."""
    return load_config(CONFIG_PATH).universe.tickers


def validate_positions(positions: pd.DataFrame, tickers: Sequence[str]) -> pd.DataFrame:
    """The positions as (ticker, quantity float, price float), in file order.

    Raises TradeInputError for a missing column, a non-numeric or missing quantity or price,
    an unknown ticker, a duplicate ticker, a negative quantity or a non-positive price.
    """
    missing = [c for c in POSITION_COLUMNS if c not in positions.columns]
    if missing:
        raise TradeInputError(f"positions: missing column(s) {missing}; expected {POSITION_COLUMNS}")
    out = positions[POSITION_COLUMNS].copy()
    out["ticker"] = out["ticker"].astype(str)
    for col in ("quantity", "price"):
        values = pd.to_numeric(out[col], errors="coerce")
        bad = out.loc[values.isna() | ~np.isfinite(values.astype(float)), "ticker"].tolist()
        if bad:
            raise TradeInputError(f"positions: non-numeric {col} for {bad}")
        out[col] = values.astype(float)
    unknown = [t for t in out["ticker"] if t not in tickers]
    if unknown:
        raise TradeInputError(f"positions: unknown ticker(s) {unknown}; the universe is {list(tickers)}")
    dup = out.loc[out["ticker"].duplicated(), "ticker"].tolist()
    if dup:
        raise TradeInputError(f"positions: duplicate ticker(s) {sorted(set(dup))}")
    neg = out.loc[out["quantity"] < 0, "ticker"].tolist()
    if neg:
        raise TradeInputError(f"positions: negative quantity for {neg}")
    nonpos = out.loc[out["price"] <= 0, "ticker"].tolist()
    if nonpos:
        raise TradeInputError(f"positions: non-positive price for {nonpos}")
    return out.reset_index(drop=True)


def check_cash(cash: float) -> float:
    cash = float(cash)
    if not math.isfinite(cash):
        raise TradeInputError(f"cash {cash} is not a finite number")
    return cash


def book_arrays(positions: pd.DataFrame, tickers: Sequence[str]) -> tuple[pd.Series, pd.Series]:
    """(quantity, price) per ticker in config order; a ticker not in positions has quantity 0 and
    price NaN."""
    p = validate_positions(positions, tickers).set_index("ticker")
    qty = p["quantity"].reindex(tickers).fillna(0.0)
    price = p["price"].reindex(tickers)
    return qty.rename("quantity"), price.rename("price")


def current_weights(positions: pd.DataFrame, cash: float,
                    tickers: Sequence[str] | None = None) -> tuple[pd.Series, float]:
    """(w_before, NAV): w_before_i = qty_i x price_i / NAV for every universe ticker (0 where not
    held), NAV = sum qty x price + cash (amendment 6.1). tickers defaults to the configured universe.
    Raises TradeInputError for a bad book or NAV <= 0."""
    tickers = list(universe_tickers() if tickers is None else tickers)
    qty, price = book_arrays(positions, tickers)
    value = (qty * price.fillna(0.0)).astype(float)
    nav = float(value.sum()) + check_cash(cash)
    if not nav > 0:
        raise TradeInputError(f"NAV {nav} is not positive")
    return (value / nav).rename("w_before"), nav


def round_to_lot(raw: pd.Series, lot: float) -> pd.Series:
    """sign(raw) x floor(|raw| / lot) x lot: toward zero, so the trade never passes the target."""
    return np.sign(raw) * np.floor(raw.abs() / lot) * lot


def generate_trades(positions: pd.DataFrame, cash: float, target_w: pd.Series, cfg: Config, lot_size: float,
                    min_notional: float) -> tuple[pd.DataFrame, dict]:
    """(trades, summary) taking the book to target_w (amendments 6.1 and 6.2).

    target_qty = w_target x NAV / price; raw = target_qty - current_qty; trade = raw rounded
    toward zero to the lot. Trades with |trade x price| < min_notional are dropped. est_cost =
    |notional| x c_i. Cash repair: while post_cash = cash - sum trade x price - sum est_cost < 0,
    the buy with the largest notional (ties by config order) is cut by one lot, and dropped when it
    reaches 0 or falls below min_notional. Every ticker with a nonzero target or a trade needs a
    price in positions.

    trades holds the tickers with a trade, in config order: side BUY or SELL, quantity = |trade|,
    notional = trade x price (signed), weight_after = (current_qty + trade) x price / NAV.
    """
    tickers = list(cfg.universe.tickers)
    if not lot_size > 0:
        raise TradeInputError(f"lot size {lot_size} is not positive")
    if not min_notional >= 0:
        raise TradeInputError(f"min notional {min_notional} is negative")
    if list(target_w.index) != tickers:
        raise ValueError("target weights are not indexed by the configured tickers in config order")
    w_before, nav = current_weights(positions, cash, tickers)
    cash = check_cash(cash)
    qty, price = book_arrays(positions, tickers)
    w_target = target_w.astype(float)
    unpriced = [t for t in tickers if np.isnan(price[t]) and w_target[t] != 0]
    if unpriced:
        raise TradeInputError(f"no price for {unpriced}, which the target holds")
    px = price.fillna(0.0)
    c = cost_vector(cfg)

    target_qty = (w_target * nav / price).fillna(0.0)
    trade = round_to_lot(target_qty - qty, lot_size).fillna(0.0)
    trade[(trade * px).abs() < min_notional] = 0.0

    def post_cash(tr: pd.Series) -> float:
        notional = tr * px
        return cash - float(notional.sum()) - float((notional.abs() * c).sum())

    lots_cut = 0
    cash_after = post_cash(trade)
    while cash_after < 0:
        buys = (trade * px).where(trade > 0)
        if not buys.notna().any():
            break
        t = buys.idxmax()  # first of the largest in config order
        trade[t] -= lot_size
        lots_cut += 1
        if trade[t] <= 0 or trade[t] * px[t] < min_notional:
            trade[t] = 0.0
        cash_after = post_cash(trade)

    notional = trade * px
    est_cost = notional.abs() * c
    w_after = ((qty + trade) * px / nav).rename("w_after")
    traded = [t for t in tickers if trade[t] != 0]
    trades = pd.DataFrame({
        "ticker": traded,
        "side": ["BUY" if trade[t] > 0 else "SELL" for t in traded],
        "quantity": trade[traded].abs().to_numpy(),
        "price": px[traded].to_numpy(),
        "notional": notional[traded].to_numpy(),
        "est_cost": est_cost[traded].to_numpy(),
        "weight_before": w_before[traded].to_numpy(),
        "weight_target": w_target[traded].to_numpy(),
        "weight_after": w_after[traded].to_numpy(),
    }, columns=TRADE_COLUMNS)
    total_cost = float(est_cost.sum())
    summary = {
        "nav": nav,
        "cash_before": cash,
        "n_trades": len(traded),
        "buy_notional": float(notional[notional > 0].sum()),
        "sell_notional": float(-notional[notional < 0].sum()),
        "turnover_before_rounding": float((w_target - w_before).abs().sum()),
        "turnover_after_rounding": float((w_after - w_before).abs().sum()),
        "rounding_slack": float((w_after - w_target).abs().sum()),
        "total_est_cost": total_cost,
        "total_est_cost_bp": total_cost / nav * BP_PER_UNIT,
        "residual_cash": cash_after,
        "residual_cash_pct": cash_after / nav,
        "max_abs_weight_dev": float((w_after - w_target).abs().max()),
        "lots_cut_for_cash": lots_cut,
        "w_before": w_before,
        "w_target": w_target,
        "w_after": w_after,
    }
    return trades, summary


# --- 6.2 printed summary ------------------------------------------------------------------------


def price_warnings(positions: pd.DataFrame, closes: pd.Series, warn_pct: float, asof: pd.Timestamp) -> list[str]:
    """One line per positions price differing from the panel close on the decision date by more
    than warn_pct (relative to the close), in file order (amendment 6.2)."""
    lines = []
    for row in positions.itertuples(index=False):
        close = float(closes[row.ticker])
        diff = row.price / close - 1
        if abs(diff) > warn_pct:
            lines.append(f"WARNING: {row.ticker} price {row.price:.4f} differs from the {asof:%Y-%m-%d} close "
                         f"{close:.4f} by {diff:+.2%} (limit {warn_pct:.0%})")
    return lines


def format_summary(summary: dict, res, strategy_id: str, asof: pd.Timestamp, tau: float | None,
                   warnings: list[str]) -> str:
    """The printed summary (PLAN 6.2, amendment 6.2). res is the AllocResult; tau is the turnover
    limit given to the allocator, None when it has none."""
    nav = summary["nav"]
    if tau is None:
        limit = "turnover limit: none"
    elif res.tau_relaxed:
        limit = (f"turnover limit: {tau:g}, relaxed (tau_relaxed True): tau_min > tau, "
                 f"tau_eff = {res.tau_eff:.10g}")
    else:
        limit = f"turnover limit: {tau:g}, not relaxed"
    dual = res.turnover_dual
    shadow = ("n/a" if tau is None or math.isnan(dual)
              else f"{dual * BP_PER_PCT:.6g} bp of monthly return per 1% of turnover")
    lines = [
        f"strategy: {strategy_id}",
        f"decision date: {asof:%Y-%m-%d} (allocator inputs from the pinned data snapshot)",
        f"solver: {res.solver}  status: {res.status}  fallback: {res.fallback}",
        limit,
        f"turnover shadow price: {shadow}",
        f"NAV: {nav:,.2f}",
        f"cash before: {summary['cash_before']:,.2f} ({summary['cash_before'] / nav:.4%} of NAV)",
        f"trades: {summary['n_trades']}  buys {summary['buy_notional']:,.2f}  sells {summary['sell_notional']:,.2f}",
        f"turnover before rounding: {summary['turnover_before_rounding']:.6f}",
        f"turnover after rounding: {summary['turnover_after_rounding']:.6f}",
        f"total estimated cost: {summary['total_est_cost']:,.2f} ({summary['total_est_cost_bp']:.4f} bp of NAV)",
        f"residual cash: {summary['residual_cash']:,.2f} ({summary['residual_cash_pct']:.4%} of NAV)",
        f"max |weight_after - weight_target|: {summary['max_abs_weight_dev']:.6g}",
        f"lots cut to keep cash >= 0: {summary['lots_cut_for_cash']}",
    ]
    if summary["residual_cash"] < 0:
        lines.append("WARNING: residual cash is negative and no buy is left to cut")
    return "\n".join([*lines, *warnings])
