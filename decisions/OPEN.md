# Open decisions

## 11. Step 6.3: the price of a ticker the target buys but the positions file does not list (implemented as option 1, needs confirming)

Amendment 6.1 sets target_qty = w_target × NAV / price, and PLAN 6.1 says the price comes from the positions file (columns ticker, quantity, price). Neither says what price to use for a universe ticker that is not in the file. The allocator can put weight on any of the 18, so the case is routine: the demo book holds 5 tickers and the target buys XLK, and the all-cash book of `test_cash_is_fully_invested_by_budget` lists none.

- Option 1 (implemented): a ticker missing from the file is held at quantity 0 and priced at the panel close on the `--asof` decision date, the price amendment 6.2 already uses for the price warning. `pc.cli.complete_book`. The demo's XLK row is priced at 175.1456146.
- Option 2: the positions file must list every universe ticker, with quantity 0 where not held. A missing ticker is a `TradeInputError` (exit 2), and the demo book gains 13 rows of quantity 0 at the 2026-07-31 closes.
