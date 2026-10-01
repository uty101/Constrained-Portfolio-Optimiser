# Section 4 review decisions (session 5)

From `instructions/05_section_5.md`, step 5.0.a.

1. **Open decision 6: option 1, ddof 1,** the same as annualised vol. `pc.stats.SHARPE_DDOF = 1` stays as built. The item is moved out of `decisions/OPEN.md`, which is now empty.
2. **Ruined strategies get a NaN point Sharpe as well as NaN intervals,** in `metrics_all.csv`, `sharpe_intervals.csv` and `results_primary.csv`.
   - Reason: `mv_unconstrained|ewma|sample|A` lost everything in month 37 and showed a Sharpe of 1.15. A mean over standard deviation of monthly returns says nothing about a path that ends at 0.
   - `ann_return` −1 and `max_dd` −1 stay, as they are the truthful figures.
   - `ruin_month` is added to `metrics_all.csv`.
3. **Review Deviations 9 to 15 of section 4:** accepted.
4. **Risk parity convergence differing across platforms:** accepted. `rp_max_rc_dev` is about 6e-9 in every flagged month, so it is noise, and results may differ across operating systems at that level.
5. **Chart 1 corrections** (step 5.0.b):
   - Each label has a fixed offset in points, kept in a dict in `pc/charts.py` keyed by allocator, chosen so no 2 labels overlap.
   - A ruined strategy's text box entry reads `<allocator> (<id>): ruined <YYYY-MM>, wealth 0` in place of its mean and vol.
