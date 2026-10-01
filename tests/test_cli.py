from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pc.cli import SET_A_MESSAGE, TRADES_CSV_KWARGS, build_parser, demo_book, main, plan, repo_config
from pc.data import load_prices

ROOT = Path(__file__).resolve().parents[1]
DEMO_POSITIONS = ROOT / "examples" / "positions_demo.csv"
DEMO_TRADES = ROOT / "examples" / "trades_demo.csv"
LAST = "2026-07-31"


def write_positions(path, rows):
    path.write_text("ticker,quantity,price\n" + "".join(f"{r}\n" for r in rows), encoding="utf-8")
    return str(path)


def good_book(tmp_path):
    return write_positions(tmp_path / "positions.csv", ["SPY,1000,745.18", "TLT,5000,81.61", "GLD,800,371.54"])


def run(argv, capsys):
    code = main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


@pytest.mark.parametrize("name, rows, message", [
    ("unknown_ticker", ["SPY,10,745", "XXX,10,10"], "unknown ticker"),
    ("negative_quantity", ["SPY,10,745", "TLT,-5,81"], "negative quantity"),
    ("nonpositive_price", ["SPY,10,745", "TLT,5,0"], "non-positive price"),
    ("duplicate_ticker", ["SPY,10,745", "SPY,5,745"], "duplicate ticker"),
    ("non_numeric", ["SPY,ten,745"], "non-numeric quantity"),
])
def test_error_positions_one_line_exit_2(tmp_path, capsys, name, rows, message):
    out = tmp_path / "trades.csv"
    code, stdout, err = run(["--positions", write_positions(tmp_path / f"{name}.csv", rows), "--out", str(out)], capsys)
    assert code == 2 and message in err and not out.exists()
    assert len(err.strip().splitlines()) == 1  # one line, no stack trace without --debug


def test_error_unknown_ticker_exit_2(tmp_path, capsys):
    code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", ["SPY,10,745", "XXX,1,1"])], capsys)
    assert code == 2 and "unknown ticker" in err and "XXX" in err


def test_error_negative_quantity_exit_2(tmp_path, capsys):
    code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", ["TLT,-5,81"])], capsys)
    assert code == 2 and "negative quantity" in err


def test_error_nonpositive_price_exit_2(tmp_path, capsys):
    for price in ("0", "-81"):
        code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", [f"TLT,5,{price}"])], capsys)
        assert code == 2 and "non-positive price" in err


def test_error_duplicate_ticker_exit_2(tmp_path, capsys):
    code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", ["TLT,5,81", "TLT,1,81"])], capsys)
    assert code == 2 and "duplicate ticker" in err


def test_error_missing_column_exit_2(tmp_path, capsys):
    path = tmp_path / "p.csv"
    path.write_text("ticker,quantity\nSPY,10\n", encoding="utf-8")
    code, _, err = run(["--positions", str(path)], capsys)
    assert code == 2 and "missing column" in err


def test_debug_prints_stack_trace(tmp_path, capsys):
    code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", ["TLT,-5,81"]), "--debug"], capsys)
    assert code == 2 and "Traceback" in err


def test_set_a_strategy_exit_2(tmp_path, capsys):
    for sid in ("mv_unconstrained|sample|sample|A", "mv_unconstrained|lw_cc|sample|A"):
        code, _, err = run(["--positions", good_book(tmp_path), "--strategy", sid, "--dry-run"], capsys)
        assert code == 2 and SET_A_MESSAGE in err
    code, _, err = run(["--positions", good_book(tmp_path), "--strategy", "not|a|registry|id"], capsys)
    assert code == 2 and "not a registry id" in err


def test_asof_not_a_decision_date_exit_2(tmp_path, capsys):
    # 2026-07-30 is a trading day but not a month end; 2026-08-31 is past the last decision date.
    for asof in ("2026-07-30", "2026-08-31", "2009-12-31", "yesterday"):
        code, _, err = run(["--positions", good_book(tmp_path), "--asof", asof, "--dry-run"], capsys)
        assert code == 2, asof
        assert "--asof" in err


def test_max_turnover_on_non_c_strategy_exit_2(tmp_path, capsys):
    for sid in ("min_variance|lw_cc|none|B", "risk_parity|ewma|none|none", "equal_weight|none|none|none"):
        code, _, err = run(["--positions", good_book(tmp_path), "--strategy", sid, "--max-turnover", "0.1"], capsys)
        assert code == 2 and "set C" in err, sid


def test_dry_run_writes_no_file(tmp_path, capsys):
    out = tmp_path / "trades.csv"
    code, stdout, _ = run(["--positions", good_book(tmp_path), "--out", str(out), "--dry-run"], capsys)
    assert code == 0 and not out.exists() and "dry run: nothing written" in stdout
    assert list(tmp_path.iterdir()) == [tmp_path / "positions.csv"]
    code, stdout, _ = run(["--positions", good_book(tmp_path), "--out", str(out)], capsys)
    assert code == 0 and out.exists()


def args_for(argv):
    cfg = repo_config()
    return build_parser(cfg).parse_args(argv), cfg


def equal_book(tmp_path, cash_frac):
    """Close to 1/18 of a $10m book in every ticker at the last decision date's closes."""
    cfg = repo_config()
    closes = load_prices(cfg).loc[LAST]
    nav = 10_000_000.0
    rows = [f"{t},{int(nav * (1 - cash_frac) / 18 / closes[t])},{closes[t]:.4f}" for t in cfg.universe.tickers]
    return write_positions(tmp_path / "equal.csv", rows), nav * cash_frac


def test_max_turnover_005_respected(tmp_path, capsys):
    path, cash = equal_book(tmp_path, 0.01)
    argv = ["--positions", path, "--cash", str(cash), "--max-turnover", "0.05", "--out", str(tmp_path / "t.csv")]
    result = plan(*args_for(argv))
    res, s = result["res"], result["summary"]
    assert result["tau"] == 0.05 and not res.tau_relaxed and res.tau_eff == 0.05
    assert s["turnover_before_rounding"] <= 0.05 + 1e-7
    # The limit binds here: without it the same book trades more.
    assert s["turnover_before_rounding"] >= 0.05 - 1e-6
    assert s["turnover_after_rounding"] <= 0.05 + s["rounding_slack"] + 1e-7
    code, stdout, _ = run(argv, capsys)
    assert code == 0 and "turnover limit: 0.05, not relaxed" in stdout
    unlimited = plan(*args_for(argv[:4] + ["--max-turnover", "10"]))["summary"]
    assert unlimited["turnover_before_rounding"] > 0.05 + 1e-3


def test_cash_is_fully_invested_by_budget(tmp_path, capsys):
    cfg = repo_config()
    path = write_positions(tmp_path / "cash.csv", [])
    cash = 10_000_000.0
    args, _ = args_for(["--positions", path, "--cash", str(cash), "--dry-run"])
    result = plan(args, cfg)
    res, s, trades = result["res"], result["summary"], result["trades"]
    assert abs(res.weights.sum() - 1) <= 1e-9
    # The first trade from cash is the whole target: tau_min is 1 here, so the limit is relaxed.
    assert res.tau_relaxed and (trades["side"] == "BUY").all()
    closes = load_prices(cfg).loc[LAST]
    bound = float((closes * args.lot_size + args.min_notional).sum())
    assert 0 <= s["residual_cash"] <= bound
    np.testing.assert_allclose(trades["price"].to_numpy(), closes[trades["ticker"]].to_numpy(), rtol=0, atol=0)


def test_demo_reproduces_trades_demo(tmp_path, capsys):
    cfg = repo_config()
    positions, cash = demo_book(cfg)
    # The committed book is the step 6.5 formula applied to the committed data.
    rebuilt = tmp_path / "positions_demo.csv"
    positions.to_csv(rebuilt, **TRADES_CSV_KWARGS)
    assert rebuilt.read_bytes() == DEMO_POSITIONS.read_bytes()
    assert str(cash) == "500790.0747"
    out = tmp_path / "trades_demo.csv"
    code, _, _ = run(["--positions", str(rebuilt), "--cash", str(cash), "--asof", LAST, "--out", str(out)], capsys)
    assert code == 0
    assert out.read_bytes() == DEMO_TRADES.read_bytes()
    assert pd.read_csv(out)["ticker"].tolist() == pd.read_csv(DEMO_TRADES)["ticker"].tolist()
