# Section 5 review decisions (session 6)

From `instructions/06_section_6.md`, step 6.0.a.

1. **Open decision 7: option 1.** Σ_lw_cc for the 3 zero-dispersion references (`min_variance|lw_cc|none|B`, `risk_parity|lw_cc|none|none`, `hrp|lw_cc|none|none`), as built.
2. **Open decision 8: option 1.** The set A in-sample maximum Sharpe is the supremum √(A − B²/C) = 1.7175, flagged `supremum_not_attained`, as built. It is the correct statement because the budget-1 frontier never reaches it; option 2 depends on where a plot stops.
3. **Open decision 9: option 2.** A τ with `n_binding = 0` lies on the 45° line, not below it. The answer "largest τ whose point lies below the 45 degree line" becomes NaN, read as "no limit in the grid was worth it ex ante". Option 1 reported solver noise of 5e-8 bp as a result.
4. **Open decision 10: option 1,** the kickoff 4.6 form net = (1 − cost)(1 + gross) − 1 for the levered funds, as built, for consistency with every other net return in the repo.
5. **Review Deviations 1 to 9 of Section 5:** accepted, except item 7's "the 2 Q3 ratios at the last date only", which is replaced by item 6.
6. **Q3 ratios at all 3 sensitivity dates.** At 2012-12-31 Black-Litterman's mean_abs_change (1.23) is larger than `mv_constrained`'s (0.94): its ratio is 1.31 there, against 0.50 at 2020-02-28 and 0.22 at 2026-07-31. Reporting the last date only would overstate how reliably Black-Litterman calms weights. `answers.csv` carries both ratios at each of the 3 dates, 6 rows in place of 2.
7. `decisions/OPEN.md` is cleared.

From step 6.0.b: `turnover_frontier.csv` gains `realised_net_vs_none_p05`, `realised_net_vs_none_p95` and `realised_net_vs_none_frac_le_0`, a stationary bootstrap of the paired monthly differences ret_net(τ) − ret_net(none) over months 2 to 196, and Q2 in `answers.csv` gains the τ = 0.05 and τ = 0.30 realised differences with these intervals. None of the τ rows is distinguishable from 0, so the write-up must not claim that tight turnover limits paid off.
