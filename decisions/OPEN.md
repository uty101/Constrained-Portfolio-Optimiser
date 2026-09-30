# Open decisions

## 3. Step 2.6: percentile rule for the bootstrap 90% interval (implemented as option 1, needs confirming)

`cov_eval_qlike_diff.csv` reports p05 and p95 of the 10,000 bootstrap mean QLIKE differences, at `bootstrap.ci` = [0.05, 0.95]. Kickoff 5.8 and `PLAN.md` 2.6 fix the bootstrap but not how a percentile is read from 10,000 values. The same rule will apply to the Sharpe intervals in step 4.4. The two options differ by at most 1.0e-4 on the 9 rows (ewma × gmv, p05); both columns are in `review/section_2.md`.

- Option 1 (implemented): `np.quantile(boot, ci)`, numpy's default linear interpolation between order statistics (Hyndman-Fan type 7).
- Option 2: `np.quantile(boot, ci, method="inverted_cdf")`, the empirical quantile with no interpolation (Hyndman-Fan type 1), always one of the 10,000 replicated values.
