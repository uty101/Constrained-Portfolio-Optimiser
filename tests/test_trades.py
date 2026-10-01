import numpy as np
import pandas as pd
import pytest

from pc.backtest import cost_vector
from pc.trades import TRADE_COLUMNS, TradeInputError, current_weights, generate_trades, validate_positions


def book(cfg, rng):
    """Every universe ticker with a price in [20, 500) and a quantity worth up to about $400k."""
    tickers = list(cfg.universe.tickers)
    price = np.round(rng.uniform(20, 500, len(tickers)), 4)
    qty = np.floor(rng.uniform(0, 400_000, len(tickers)) / price)
    qty[rng.random(len(tickers)) < 0.3] = 0
    return pd.DataFrame({"ticker": tickers, "quantity": qty, "price": price})


def target(cfg, rng):
    w = rng.dirichlet(np.ones(len(cfg.universe.tickers)))
    w[rng.random(len(w)) < 0.3] = 0
    return pd.Series(w / w.sum(), index=list(cfg.universe.tickers))


def apply(positions, trades):
    after = positions.set_index("ticker")["quantity"].copy()
    signed = np.where(trades["side"] == "BUY", 1, -1) * trades["quantity"].to_numpy()
    after[trades["ticker"].to_numpy()] += signed
    return after


def test_current_weights_include_universe_zeros(cfg):
    positions = pd.DataFrame({"ticker": ["GLD", "SPY"], "quantity": [10.0, 4.0], "price": [200.0, 500.0]})
    w, nav = current_weights(positions, 1000.0)
    assert nav == 10 * 200 + 4 * 500 + 1000
    assert list(w.index) == list(cfg.universe.tickers)
    assert w["GLD"] == 0.4 and w["SPY"] == 0.4 and (w.drop(["GLD", "SPY"]) == 0).all()
    # Cash is not a weight: w_before sums to 1 - cash / NAV.
    assert abs(w.sum() - (1 - 1000 / nav)) <= 1e-15


def test_round_trip_synthetic_book(cfg):
    rng = np.random.default_rng(cfg.run.seed_master)
    positions, w_target = book(cfg, rng), target(cfg, rng)
    cash = 250_000.0
    trades, s = generate_trades(positions, cash, w_target, cfg, 1, 0.0)
    assert list(trades.columns) == TRADE_COLUMNS
    # Config order, only tickers with a trade.
    order = {t: i for i, t in enumerate(cfg.universe.tickers)}
    assert trades["ticker"].map(order).is_monotonic_increasing and (trades["quantity"] > 0).all()
    after = apply(positions, trades)
    price = positions.set_index("ticker")["price"]
    nav = s["nav"]
    np.testing.assert_allclose((after * price / nav)[list(cfg.universe.tickers)].to_numpy(), s["w_after"].to_numpy(),
                               rtol=0, atol=1e-15)
    # Cash: the trades and their costs, and the NAV after is the NAV before less the cost.
    c = cost_vector(cfg)[trades["ticker"]].to_numpy()
    np.testing.assert_allclose(trades["est_cost"], trades["notional"].abs() * c, rtol=1e-15, atol=0)
    residual = cash - trades["notional"].sum() - trades["est_cost"].sum()
    assert abs(residual - s["residual_cash"]) <= 1e-6 and s["residual_cash"] >= 0
    assert abs(float((after * price).sum()) + residual - (nav - s["total_est_cost"])) <= 1e-6
    # The re-read book: its weights are weight_after rescaled to the NAV after.
    w_new, nav_new = current_weights(pd.DataFrame({"ticker": after.index, "quantity": after.to_numpy(),
                                                   "price": price[after.index].to_numpy()}), residual)
    np.testing.assert_allclose(w_new.to_numpy() * nav_new / nav, s["w_after"].to_numpy(), rtol=0, atol=1e-12)
    # Lot 1, no notional floor: every weight lands within one share of its target, except the buys
    # cut to keep cash >= 0.
    gap = (s["w_target"] - s["w_after"]).abs() * nav / price[list(cfg.universe.tickers)]
    assert (gap <= 1 + 1e-9).sum() >= len(gap) - 1
    assert s["turnover_before_rounding"] == pytest.approx(float((w_target - s["w_before"]).abs().sum()), abs=1e-15)


@pytest.mark.parametrize("lot", [1, 10, 100])
def test_rounding_never_overshoots(cfg, lot):
    rng = np.random.default_rng(cfg.run.seed_master + lot)
    positions, w_target = book(cfg, rng), target(cfg, rng)
    trades, s = generate_trades(positions, 1e6, w_target, cfg, lot, 0.0)
    qty = positions.set_index("ticker")["quantity"]
    price = positions.set_index("ticker")["price"]
    target_qty = w_target * s["nav"] / price
    after = apply(positions, trades)
    for row in trades.itertuples():
        t = row.ticker
        assert row.quantity % lot == 0
        if row.side == "BUY":
            assert after[t] <= target_qty[t] + 1e-9, t
        else:
            assert target_qty[t] - 1e-9 <= after[t] <= qty[t], t
            assert after[t] >= 0
    # Rounding goes toward zero: no ticker is left a full lot or more short of its target unless
    # the cash repair cut it.
    short = (target_qty - after).abs() >= lot
    assert short.sum() <= s["lots_cut_for_cash"]


def test_min_notional_filter(cfg):
    rng = np.random.default_rng(cfg.run.seed_master)
    positions, w_target = book(cfg, rng), target(cfg, rng)
    cash = 1e6
    trades0, s0 = generate_trades(positions, cash, w_target, cfg, 1, 0.0)
    floor = float(trades0["notional"].abs().median())
    trades, _ = generate_trades(positions, cash, w_target, cfg, 1, floor)
    assert (trades["notional"].abs() >= floor).all()
    small = trades0.loc[trades0["notional"].abs() < floor, "ticker"]
    assert len(small) > 0 and not set(small) & set(trades["ticker"])
    # A trade under the floor leaves its ticker where it was.
    w_after = trades0.set_index("ticker")["weight_before"]
    _, s = generate_trades(positions, cash, w_target, cfg, 1, floor)
    np.testing.assert_allclose(s["w_after"][small].to_numpy(), w_after[small].to_numpy(), rtol=0, atol=1e-15)


def test_negative_cash_repair(cfg):
    # Fully invested in SPY, target half TLT: the buy equals the sell, so its cost leaves cash at
    # -30 and one lot of TLT is cut.
    positions = pd.DataFrame({"ticker": ["SPY", "TLT"], "quantity": [1000.0, 0.0], "price": [100.0, 50.0]})
    w_target = pd.Series(0.0, index=list(cfg.universe.tickers))
    w_target[["SPY", "TLT"]] = 0.5
    trades, s = generate_trades(positions, 0.0, w_target, cfg, 1, 0.0)
    t = trades.set_index("ticker")
    assert t.loc["SPY", "side"] == "SELL" and t.loc["SPY", "quantity"] == 500
    assert t.loc["TLT", "side"] == "BUY" and t.loc["TLT", "quantity"] == 999
    assert s["lots_cut_for_cash"] == 1
    assert s["residual_cash"] == pytest.approx(50_000 - 49_950 - 15 - 14.985, abs=1e-9)
    # Ties go to config order: an all-cash book buys two equal $50,000 legs, cash ends at -30, and
    # SPY (before TLT in config order) is the one cut.
    positions = pd.DataFrame({"ticker": ["TLT", "SPY"], "quantity": [0.0, 0.0], "price": [100.0, 100.0]})
    w_target = pd.Series(0.0, index=list(cfg.universe.tickers))
    w_target[["SPY", "TLT"]] = 0.5
    trades, s = generate_trades(positions, 100_000.0, w_target, cfg, 1, 0.0)
    q = trades.set_index("ticker")["quantity"]
    assert q["SPY"] == 499 and q["TLT"] == 500 and s["lots_cut_for_cash"] == 1
    assert s["residual_cash"] == pytest.approx(100_000 - 99_900 - 29.97, abs=1e-9)
    # Minimal: putting the last lot back would make cash negative.
    assert s["residual_cash"] - 100 * (1 + 3e-4) < 0


def test_sell_never_below_zero(cfg):
    tickers = list(cfg.universe.tickers)
    positions = pd.DataFrame({"ticker": ["SPY", "TLT", "GLD"], "quantity": [105.0, 33.0, 7.5],
                              "price": [100.0, 50.0, 200.0]})
    # Exit SPY and GLD; solver noise puts tiny negatives on the exits.
    w_target = pd.Series(0.0, index=tickers)
    w_target["TLT"] = 1.0
    w_target[["SPY", "GLD"]] = -1e-12
    for lot in (1, 10, 0.5):
        trades, s = generate_trades(positions, 0.0, w_target, cfg, lot, 0.0)
        after = apply(positions, trades)
        assert (after >= 0).all(), (lot, after)
        sells = trades[trades["side"] == "SELL"].set_index("ticker")["quantity"]
        held = positions.set_index("ticker")["quantity"]
        assert (sells <= held[sells.index]).all()
    trades, _ = generate_trades(positions, 0.0, w_target, cfg, 10, 0.0)
    after = apply(positions, trades)
    assert after["SPY"] == 5 and after["GLD"] == 7.5  # 105 sells 100; 7.5 is under a lot of 10


@pytest.mark.parametrize("bad, message", [
    (dict(ticker=["SPY", "XXX"]), "unknown ticker"),
    (dict(quantity=[1.0, -1.0]), "negative quantity"),
    (dict(price=[100.0, 0.0]), "non-positive price"),
    (dict(ticker=["SPY", "SPY"]), "duplicate ticker"),
    (dict(quantity=["1", "abc"]), "non-numeric quantity"),
    (dict(price=[100.0, None]), "non-numeric price"),
])
def test_validate_positions_errors(cfg, bad, message):
    p = pd.DataFrame({"ticker": ["SPY", "TLT"], "quantity": [1.0, 2.0], "price": [100.0, 50.0], **bad})
    with pytest.raises(TradeInputError, match=message) as e:
        validate_positions(p, cfg.universe.tickers)
    assert e.value.code == 2
    with pytest.raises(TradeInputError, match="missing column"):
        validate_positions(p.drop(columns="price"), cfg.universe.tickers)
