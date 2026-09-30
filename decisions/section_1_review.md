# Section 1 review decisions

From `instructions/01b_section_1_completion.md`. Both items were open in `decisions/OPEN.md` after session 1.

1. **Annualisation in step 1.6: option 1, geometric.** ann_return = (Π(1 + r_d))^(D/n) − 1, ann_vol = std(r_d, ddof=1) × √D, D = 12 × `sample.days_per_month` (252), n the number of daily returns. Reason: this matches the geometric annual return in kickoff 5.8, so the data summary and the backtest tables use the same convention.
2. **"d − 1" in the rf rule: option 1 confirmed, as built.** d − 1 is the previous trading day in the price index. Reason: rf accrues from one trading close to the next, and the rate that applies over that period is the one known at its start, the previous trading day. A Good Friday or Hurricane Sandy print falls inside an accrual period rather than starting one. The difference is 4 days of 4,888 at 1 to 4 bp.

## Session 1 additions accepted by the reviewer

- `.gitattributes`.
- `tests/conftest.py`.
- `pc.data.write_data_issues`.
- 252 computed as 12 × `sample.days_per_month` (no new config key).
- Every implicit behaviour in `review/section_1.md` Deviations item 7.
- rf is NaN only on 2007-04-11, the panel start. No monthly excess return, holding return or holding rf uses that day, and `monthly_excess_returns` has 0 NaN over 232 rows. It stays NaN and the FRED pull is not rerun.
