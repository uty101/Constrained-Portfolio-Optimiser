# Status: session 4b (instructions/04b_section_4_completion.md)

## Outcome

Completed. Step 4.2 is finished (part (b) of `test_no_look_ahead` rewritten on the information set, `rp_max_rc_dev` added, both parquet outputs committed). Steps 4.3 to 4.6 are built and committed. 217 tests pass in the repo and in the fresh clone at `%TEMP%\pcs4b`. A second full run reproduced every output byte for byte: both parquet files, `metrics_all.csv`, `sharpe_intervals.csv`, `results_primary.csv` and both PNGs, compared by MD5.

## Last step reached

Step 4.6 (`e5e84cf`), then open decision 6 (`7d88eda`) and the review file (`ab83c85`, `251c9a1`).

## Reason for any stop

None. No rule 4 stop.

## Questions and blockers for the reviewer

1. **Open decision 6 (`decisions/OPEN.md`): the ddof of the Sharpe std.** Kickoff 5.8 gives ddof 1 for annualised vol but no ddof for the Sharpe std, and Chart 1's x coordinate has the same gap. Implemented as option 1, ddof 1, through `pc.stats.SHARPE_DDOF`. Option 2 is ddof 0. Over 196 months the two differ by a factor of √(196/195) = 1.0026 on every Sharpe ratio, and the bootstrap fractions are unaffected.
2. **Ruined strategies keep their point Sharpe in `sharpe_intervals.csv`,** computed over the months of their wealth path, the same value as in `metrics_all.csv`. Their intervals and every difference involving them are NaN. Amendment 4.2.8 asked for NaN intervals, not a NaN point. Please confirm (review Deviations 9).
3. **Formats I set where none was given** (review Deviations 10 to 14):
   - `sharpe_intervals.csv` is wide, with columns named by the full benchmark id.
   - The `metrics_all.csv` column list.
   - `max_dd` counts the starting wealth of 1 as the first peak.
   - Chart 1: the set A curve is drawn at 50 points, the y-axis spans everything plotted with vol from 0 to 30% plus 5% padding, and "outside the axes" follows from those limits.
4. **`pc.stats` reads `[bootstrap] ci` from the repo's `config.toml`** via a package-relative path, as `pc.solver` does, because `sharpe_intervals` has no Config argument (review Deviations 15).
5. **Risk parity non-converged months differ from the reviewer's run.** Here they are `ewma` at 2012-06-29 and `pca3` at 2023-01-31; the reviewer saw `ewma` at 2010-08-31. Both have `rp_max_rc_dev` of about 6e-9, inside the converged months' range (max 7.1e-8).
6. **Chart 1:** only `mv_unconstrained|sample|sample|A` (ruined; 109.1% vol, 67.9% excess return) is outside the axes and listed in the text box. All 50 set B frontier points are CLARABEL `optimal`.
7. `CLAUDE.md` and `PLAN.md` were not staged or committed, as instructed.

## git log origin/main --oneline -3

```
251c9a1 section 4: review file, determinism checked in session 4b
ab83c85 section 4: review file, session 4b
7d88eda section 4: open decision 6 (Sharpe ddof)
```
