# Section 6 review decisions (session 7)

From `instructions/07_section_7.md`, step 7.0.

1. **Open decision 11: option 1.** A ticker the target buys but the positions file does not list is held at quantity 0 and priced at the panel close on `--asof`, as built in `pc.cli.complete_book`. It is the price the CLI already uses for its price warnings, and the `--help` text already says the CLI runs on the pinned snapshot.
2. **Review Deviations 6 to 9 of Section 6:** accepted. That covers the signed notional, the extra exit 2 cases, negative `--cash` with a warning, and `current_weights(…, tickers=None)`.
3. **`test_demo_reproduces_trades_demo` stays as a byte comparison.** It passed on Linux.
4. `decisions/OPEN.md` is cleared.
