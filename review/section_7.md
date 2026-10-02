# Review — Section 7: Write-up and reproducibility

## Section

Section 7 — Write-up and reproducibility, as amended by `instructions/07_section_7.md` (step 7.0, then amendments to 7.1 to 7.5).

## Steps completed

- 7.0 `f795bbc` reviewer decisions for section 6: `decisions/section_7_review.md`, `decisions/OPEN.md` cleared
- 7.1 `fb7e9bc` `scripts/run_all.py` (every writer in section order, per-writer runtime, the 6.5 demo through `pc.cli.main`), `tests/test_run_all.py`
- 7.2 `f72c51f` `pc/report.py::write_readme_tables`, the 5 `outputs/tables/readme_*.md` snippets, `README.md`, `tests/test_report.py`, and the README tables call added to `run_all.py`
- 7.3 `31a04b6` `docs/DESIGN_NOTE.md`
- 7.4 `336533d` `docs/METHODS.md`
- 7.5 `5dffbb3` `scripts/find_unused.py`, `tests/test_placeholder.py` removed, README runtime sentence set from the measured runs; fresh-clone check

## Evidence

### 1. `run_all` twice, with per-writer runtime and `git status --porcelain` after each

Both runs were made after the 7.4 commit, so they cover the full script including the README tables. stdout is shown in full. stderr held only cvxpy's `UserWarning: Solution may be inaccurate` (1,352 warnings per run, each on 2 lines, 2,704 lines), the CLARABEL `optimal_inaccurate` cases that the solver policy retries on SCS (`decisions/section_4_review.md`, 6); nothing else. stdout includes the demo's printed summary, which matches `docs/cli_demo.md`, and the `exit` line is the script's exit code.

Run 1:

```
data.write_data_issues: 0.1 s
data.write_data_summary: 0.0 s
cov_eval.write_cov_eval: 3.5 s
backtest.write_walk_forward: 76.6 s
stats.write_metrics: 0.1 s
stats.write_sharpe_intervals: 2.6 s
stats.write_results_primary: 0.0 s
charts.write_charts: 1.5 s
sensitivity.write_sensitivity: 163.4 s
experiments.write_turnover_frontier: 41.4 s
experiments.write_cost_sensitivity: 76.6 s
experiments.write_monthly_cov: 3.5 s
experiments.write_levered: 2.9 s
experiments.write_answers: 0.3 s
report.write_readme_tables: 0.1 s
strategy: mv_constrained|lw_cc|sample|C
decision date: 2026-07-31 (allocator inputs from the pinned data snapshot)
solver: CLARABEL+CLARABEL  status: optimal  fallback: False
turnover limit: 0.3, not relaxed
turnover shadow price: 0.946883 bp of monthly return per 1% of turnover
NAV: 10,000,000.00
cash before: 500,790.07 (5.0079% of NAV)
trades: 3  buys 1,749,179.25  sells 1,249,369.26
turnover before rounding: 0.300000
turnover after rounding: 0.299855
total estimated cost: 899.56 (0.8996 bp of NAV)
residual cash: 80.52 (0.0008% of NAV)
max |weight_after - weight_target|: 0.000121578
lots cut to keep cash >= 0: 6

ticker side  quantity      price      notional   est_cost  weight_before  weight_target  weight_after
   XLK  BUY    9987.0 175.145615  1.749179e+06 524.753776       0.000000       0.175040      0.174918
   TLT SELL    3058.0  81.607300 -2.495551e+05  74.866537       0.099993       0.075033      0.075038
   GLD SELL    2691.0 371.540000 -9.998141e+05 299.944242       0.400000       0.300000      0.300019

wrote examples/trades_demo.csv
cli.main (6.5 demo): 0.2 s
total: 372.8 s
exit 0
```

`git status --porcelain` after run 1 (empty):

```

```

Run 2:

```
data.write_data_issues: 0.1 s
data.write_data_summary: 0.0 s
cov_eval.write_cov_eval: 3.3 s
backtest.write_walk_forward: 68.6 s
stats.write_metrics: 0.4 s
stats.write_sharpe_intervals: 2.1 s
stats.write_results_primary: 0.0 s
charts.write_charts: 1.3 s
sensitivity.write_sensitivity: 160.9 s
experiments.write_turnover_frontier: 40.0 s
experiments.write_cost_sensitivity: 64.5 s
experiments.write_monthly_cov: 3.2 s
experiments.write_levered: 2.5 s
experiments.write_answers: 0.2 s
report.write_readme_tables: 0.0 s
strategy: mv_constrained|lw_cc|sample|C
decision date: 2026-07-31 (allocator inputs from the pinned data snapshot)
solver: CLARABEL+CLARABEL  status: optimal  fallback: False
turnover limit: 0.3, not relaxed
turnover shadow price: 0.946883 bp of monthly return per 1% of turnover
NAV: 10,000,000.00
cash before: 500,790.07 (5.0079% of NAV)
trades: 3  buys 1,749,179.25  sells 1,249,369.26
turnover before rounding: 0.300000
turnover after rounding: 0.299855
total estimated cost: 899.56 (0.8996 bp of NAV)
residual cash: 80.52 (0.0008% of NAV)
max |weight_after - weight_target|: 0.000121578
lots cut to keep cash >= 0: 6

ticker side  quantity      price      notional   est_cost  weight_before  weight_target  weight_after
   XLK  BUY    9987.0 175.145615  1.749179e+06 524.753776       0.000000       0.175040      0.174918
   TLT SELL    3058.0  81.607300 -2.495551e+05  74.866537       0.099993       0.075033      0.075038
   GLD SELL    2691.0 371.540000 -9.998141e+05 299.944242       0.400000       0.300000      0.300019

wrote examples/trades_demo.csv
cli.main (6.5 demo): 0.1 s
total: 347.2 s
exit 0
```

`git status --porcelain` after run 2 (empty):

```

```

No PNG or parquet differed between runs. An earlier run of `run_all.py`, made before the 7.1 commit and without the README tables, also left every output byte-identical (total 359.9 s).

### 2. Trace of every figure in README section 2 and in prose elsewhere

Each figure as written, with its source, row, column and the value there. Ratios are computed from the 2 rows of `sensitivity_summary.csv` they divide, as `answers.csv` does. "10,911%" is 109.1117 × 100. The README tables themselves are generated from the CSVs by `pc/report.py` and checked against the README by `test_readme_tables_match_snippets`, so they are not traced here.

```
                        where                                         written                      source                                                    row                                                column                              value
0                README 2, Q1                                            1.72     frontier_max_sharpe.csv                                                      A                                            max_sharpe                             1.7175
1                README 2, Q1                                        supremum     frontier_max_sharpe.csv                                                      A                                                status              supremum_not_attained
2                README 2, Q1                                            1.10     frontier_max_sharpe.csv                                                      B                                            max_sharpe                           1.098266
3                README 2, Q1                                   30% per asset                 config.toml                                                   [mv]                                                 upper                                0.3
4                README 2, Q1                             0.67 (0.36 to 1.03)        sharpe_intervals.csv                          mv_constrained|lw_cc|sample|C                                                sharpe                           0.673838
5                README 2, Q1                             0.67 (0.36 to 1.03)        sharpe_intervals.csv                          mv_constrained|lw_cc|sample|C                                            sharpe_p05                           0.363273
6                README 2, Q1                             0.67 (0.36 to 1.03)        sharpe_intervals.csv                          mv_constrained|lw_cc|sample|C                                            sharpe_p95                           1.026701
7                README 2, Q1                             0.71 (0.39 to 1.11)        sharpe_intervals.csv                            equal_weight|none|none|none                                                sharpe                             0.7051
8                README 2, Q1                             0.71 (0.39 to 1.11)        sharpe_intervals.csv                            equal_weight|none|none|none                                            sharpe_p05                           0.387164
9                README 2, Q1                             0.71 (0.39 to 1.11)        sharpe_intervals.csv                            equal_weight|none|none|none                                            sharpe_p95                            1.11021
10               README 2, Q1                           0.45 (-0.003 to 1.01)        sharpe_intervals.csv                              min_variance|lw_cc|none|B                                                sharpe                           0.452632
11               README 2, Q1                           0.45 (-0.003 to 1.01)        sharpe_intervals.csv                              min_variance|lw_cc|none|B                                            sharpe_p05                          -0.002685
12               README 2, Q1                           0.45 (-0.003 to 1.01)        sharpe_intervals.csv                              min_variance|lw_cc|none|B                                            sharpe_p95                           1.010246
13               README 2, Q1                        HRP below EW under all 4        sharpe_intervals.csv                                   hrp|sample|none|none               diff_p95_vs_equal_weight|none|none|none                          -0.012881
14               README 2, Q1                        HRP below EW under all 4        sharpe_intervals.csv                                    hrp|lw_cc|none|none               diff_p95_vs_equal_weight|none|none|none                          -0.014276
15               README 2, Q1                        HRP below EW under all 4        sharpe_intervals.csv                                     hrp|ewma|none|none               diff_p95_vs_equal_weight|none|none|none                          -0.108249
16               README 2, Q1                        HRP below EW under all 4        sharpe_intervals.csv                                     hrp|pca3|none|none               diff_p95_vs_equal_weight|none|none|none                          -0.001242
17               README 2, Q1                                        only HRP        sharpe_intervals.csv                                      every non-HRP row  count of diff_p95_vs_equal_weight|none|none|none < 0                                  0
18               README 2, Q1                            no allocator beat EW        sharpe_intervals.csv                                               all rows  count of diff_p05_vs_equal_weight|none|none|none > 0                                  0
19               README 2, Q1                                            0.55        sharpe_intervals.csv                                   hrp|sample|none|none                   diff_vs_equal_weight|none|none|none                          -0.548725
20               README 2, Q1                                           -1.02        sharpe_intervals.csv                                   hrp|sample|none|none               diff_p05_vs_equal_weight|none|none|none                          -1.023344
21               README 2, Q1                                           -0.01        sharpe_intervals.csv                                   hrp|sample|none|none               diff_p95_vs_equal_weight|none|none|none                          -0.012881
22               README 2, Q1                                      3 of the 4                 answers.csv                          ruined set A strategies, of 4                                                 value                                3.0
23               README 2, Q1                                             98%             metrics_all.csv                        mv_unconstrained|lw_cc|sample|A                                                max_dd                           -0.98178
24               README 2, Q1                                      not ruined             metrics_all.csv                        mv_unconstrained|lw_cc|sample|A                                                ruined                              False
25               README 2, Q2                                             7.9       turnover_frontier.csv                                                    0.3                          exante_return_given_up_bp_pa                           7.879745
26               README 2, Q2                                            0.95       turnover_frontier.csv                                                    0.3                                      cost_saved_bp_pa                           0.952416
27               README 2, Q2                            -7.8 (-41.8 to 24.9)       turnover_frontier.csv                                                    0.3                            realised_net_vs_none_bp_pa                          -7.843103
28               README 2, Q2                            -7.8 (-41.8 to 24.9)       turnover_frontier.csv                                                    0.3                              realised_net_vs_none_p05                         -41.757963
29               README 2, Q2                            -7.8 (-41.8 to 24.9)       turnover_frontier.csv                                                    0.3                              realised_net_vs_none_p95                          24.899885
30               README 2, Q2                          125.9 (-87.7 to 332.7)       turnover_frontier.csv                                                   0.05                            realised_net_vs_none_bp_pa                           125.9373
31               README 2, Q2                          125.9 (-87.7 to 332.7)       turnover_frontier.csv                                                   0.05                              realised_net_vs_none_p05                         -87.684641
32               README 2, Q2                          125.9 (-87.7 to 332.7)       turnover_frontier.csv                                                   0.05                              realised_net_vs_none_p95                         332.714377
33               README 2, Q2  each binding limit gives up more than it saves       turnover_frontier.csv                                          n_binding > 0                     count given_up > cost_saved, of 6                                  6
34               README 2, Q2               no limit below the 45 degree line                 answers.csv  largest tau whose point lies below the 45 degree line                                                 value                                NaN
35               README 2, Q3                                  109.1, 10,911%     sensitivity_summary.csv           2026-07-31, mv_unconstrained|sample|sample|A                                       mean_abs_change                         109.111688
36               README 2, Q3                                            0.94     sensitivity_summary.csv              2026-07-31, mv_constrained|lw_cc|sample|B                                       mean_abs_change                           0.941065
37               README 2, Q3                               Bayes-Stein ratio     sensitivity_summary.csv                                             2012-12-31                        mean_abs_change ratio BS / MVC                            0.97594
38               README 2, Q3                           Black-Litterman ratio     sensitivity_summary.csv                                             2012-12-31                        mean_abs_change ratio BL / MVC                           1.313081
39               README 2, Q3                               Bayes-Stein ratio     sensitivity_summary.csv                                             2020-02-28                        mean_abs_change ratio BS / MVC                           0.947103
40               README 2, Q3                           Black-Litterman ratio     sensitivity_summary.csv                                             2020-02-28                        mean_abs_change ratio BL / MVC                           0.500114
41               README 2, Q3                               Bayes-Stein ratio     sensitivity_summary.csv                                             2026-07-31                        mean_abs_change ratio BS / MVC                           1.016801
42               README 2, Q3                           Black-Litterman ratio     sensitivity_summary.csv                                             2026-07-31                        mean_abs_change ratio BL / MVC                           0.222619
43               README 2, Q4                         -0.24 (-0.58 to -0.005)     cov_eval_qlike_diff.csv                                               ewma, ew                                         diff_vs_lw_cc                          -0.239488
44               README 2, Q4                         -0.24 (-0.58 to -0.005)     cov_eval_qlike_diff.csv                                               ewma, ew                                                   p05                          -0.575984
45               README 2, Q4                         -0.24 (-0.58 to -0.005)     cov_eval_qlike_diff.csv                                               ewma, ew                                                   p95                          -0.005369
46               README 2, Q4                            0.45 (-0.07 to 1.24)     cov_eval_qlike_diff.csv                                              ewma, gmv                                         diff_vs_lw_cc                           0.449875
47               README 2, Q4                            0.45 (-0.07 to 1.24)     cov_eval_qlike_diff.csv                                              ewma, gmv                                                   p05                          -0.068463
48               README 2, Q4                            0.45 (-0.07 to 1.24)     cov_eval_qlike_diff.csv                                              ewma, gmv                                                   p95                           1.240137
49               README 2, Q4                                            1.38                cov_eval.csv                                              ewma, gmv                                            bias_ratio                           1.380937
50               README 2, Q4                                            1.01                cov_eval.csv                                             lw_cc, gmv                                            bias_ratio                           1.011114
51            README 3, Setup                                         18 ETFs                 config.toml                                             [universe]                                          len(tickers)                                 18
52            README 3, Setup                        2007-04-11 to 2026-09-15                 config.toml                                               [sample]                                price_start, price_end             2007-04-11, 2026-09-15
53            README 3, Setup                        2010-04-30 to 2026-07-31                 config.toml                                               [sample]                         first_decision, last_decision             2010-04-30, 2026-07-31
54            README 3, Setup                                       36 months                 config.toml                                               [sample]                                         window_months                                 36
55            README 3, Setup                             196 holding periods             periods.parquet                            equal_weight|none|none|none                                             row count                                196
56            README 3, Setup                                     3 bp / 6 bp                 config.toml                                     [costs.one_way_bp]                                                values  EEM 6, TIP 6, HYG 6, DBC 6, VNQ 6
57            README 3, Setup                           turnover at most 0.30                 config.toml                                                   [mv]                                          max_turnover                                0.3
58       README 5 to 8, prose                             1,000 perturbations                 config.toml                                          [sensitivity]                                                 draws                               1000
59       README 5 to 8, prose                             cost scales 0 and 3                 config.toml                                                [costs]                                           cost_scales                    [0.0, 1.0, 3.0]
60       README 5 to 8, prose                          Sharpe order unchanged        cost_sensitivity.csv                                         scales 0, 1, 3                                  rank order identical                               True
61       README 5 to 8, prose                  blows up far sooner on monthly  monthly_cov_strategies.csv                daily, mv_unconstrained|sample|sample|A                                            ruin_month                            2026-02
62       README 5 to 8, prose                  blows up far sooner on monthly  monthly_cov_strategies.csv              monthly, mv_unconstrained|sample|sample|A                                            ruin_month                            2010-12
63       README 5 to 8, prose                                    50 bp a year                 config.toml                                              [levered]                                financing_spread_bp_pa                                 50
64       README 5 to 8, prose                                      196 months        weights_long.parquet                              hrp|sample|none|none, SHY                                        count w_target                                196
65       README 5 to 8, prose                           87% in SHY on average        weights_long.parquet                              hrp|sample|none|none, SHY                                         mean w_target                           0.874403
66       README 5 to 8, prose                             never less than 69%        weights_long.parquet                              hrp|sample|none|none, SHY                                          min w_target                           0.693778
67  README 9, Trade generator                                            $10m                   pc/cli.py                                               DEMO_NAV                                                 value                        10000000.00
68  README 9, Trade generator                                      5% in cash            docs/cli_demo.md                                         printed output                                           cash before        500,790.07 (5.0079% of NAV)
69  README 9, Trade generator                                0.30 limit binds            docs/cli_demo.md                                         printed output                              turnover before rounding                           0.300000
70  README 9, Trade generator                         GLD sold to its 30% cap    examples/trades_demo.csv                                                    GLD                                         weight_target                                0.3
71  README 9, Trade generator                         XLK trimmed by 6 shares            docs/cli_demo.md                                         printed output                            lots cut to keep cash >= 0                                  6
72       README 10, Reproduce                                 about 6 minutes           review evidence 1                                                run_all                                                 total                 see run_all output
```

Figures in `docs/DESIGN_NOTE.md` prose, traced the same way (the demo figures 40%, 0.2501, $1,000, 0.300000 to 0.299855, 0.00012, 6 shares and $80.52 are in `docs/cli_demo.md`; 1e-6 is the kickoff 5.3 constant; 26 strategies is the registry):

```
                     written                 source                               row              column       value
0              4.6 positions        metrics_all.csv     mv_constrained|lw_cc|sample|C      mean_positions    4.556122
1                   27 times        periods.parquet  mv_unconstrained|sample|sample|A  min gross_leverage   26.698856
2                  129 times        periods.parquet  mv_unconstrained|sample|sample|A  max gross_leverage  129.225054
3                 3 of the 4        metrics_all.csv                        set A rows          sum ruined    3.000000
4                  62 months  turnover_frontier.csv                               0.3           n_binding   62.000000
5        turnover at scale 0   cost_sensitivity.csv  mv_constrained|lw_cc|sample|C, 0       mean_turnover    0.220689
6        turnover at scale 1   cost_sensitivity.csv  mv_constrained|lw_cc|sample|C, 1       mean_turnover    0.176746
7        turnover at scale 3   cost_sensitivity.csv  mv_constrained|lw_cc|sample|C, 3       mean_turnover    0.124980
8   4 months relaxed at 0.05  turnover_frontier.csv                              0.05           n_relaxed    4.000000
9            873 SCS retries        metrics_all.csv                            all 26     sum scs_retries  873.000000
10     hold rule never fired        metrics_all.csv                            all 26       sum fallbacks    0.000000
11                       98%        metrics_all.csv   mv_unconstrained|lw_cc|sample|A              max_dd   -0.981780
```

### 3. Writing-rule grep

`grep -n -E " — | – | - |robust|resilient|rigorous|leverag|grounded|delve|crucial|landscape|notably" README.md docs/DESIGN_NOTE.md docs/METHODS.md`:

```
README.md:103:<!-- readme_robustness.md -->
README.md:124:<!-- /readme_robustness.md -->
exit 0
```

- The 2 hits are the marker comments `<!-- readme_robustness.md -->` and `<!-- /readme_robustness.md -->`. The file name and the marker format are fixed by amendment 7.2, so they stay. The README section heading was reworded from "Robustness" to "Checks on the assumptions", and "robustness test" in METHODS to "step 5.4".
- Every other candidate was fixed while writing: no clause is joined by a dash, the levered table header says "Mean k" rather than "Mean leverage k", and METHODS writes a minus without spaces inside LaTeX.

### 4. Word counts

Counted with `str.split` after removing the 5 embedded snippets and every Markdown table line (the repo map included). Code blocks are counted.

| file | words |
|---|---|
| README.md, excluding tables | 1,785 |
| README.md section 3, Setup | 174 |
| docs/DESIGN_NOTE.md | 850 |
| docs/METHODS.md | 1,381 |

### 5. `scripts/find_unused.py` and the disposition of each hit

The script follows the spec: a top-level function or class of `pc/` whose name, as a whole word, appears in no other file under `pc/`, `scripts/` or `tests/`. It also prints how many more times the name appears in its own module.

```
pc/allocators.py: fallback_weights (other uses in its own module: 1)
pc/allocators.py: _bounds (other uses in its own module: 2)
pc/backtest.py: StrategySpec (other uses in its own module: 7)
pc/backtest.py: _ruined_row (other uses in its own module: 1)
pc/backtest.py: _sort (other uses in its own module: 2)
pc/charts.py: y_limits (other uses in its own module: 2)
pc/charts.py: outside_axes (other uses in its own module: 1)
pc/charts.py: outside_text (other uses in its own module: 1)
pc/charts.py: label_offset (other uses in its own module: 1)
pc/charts.py: overlapping_labels (other uses in its own module: 1)
pc/cli.py: read_positions (other uses in its own module: 1)
pc/cli.py: resolve_strategy (other uses in its own module: 1)
pc/cli.py: resolve_asof (other uses in its own module: 1)
pc/cli.py: complete_book (other uses in its own module: 1)
pc/config.py: RunConfig (other uses in its own module: 2)
pc/config.py: UniverseConfig (other uses in its own module: 2)
pc/config.py: SampleConfig (other uses in its own module: 2)
pc/config.py: DataConfig (other uses in its own module: 2)
pc/config.py: CovConfig (other uses in its own module: 2)
pc/config.py: MvConfig (other uses in its own module: 2)
pc/config.py: CostsConfig (other uses in its own module: 2)
pc/config.py: BlConfig (other uses in its own module: 2)
pc/config.py: CovEvalConfig (other uses in its own module: 2)
pc/config.py: SensitivityConfig (other uses in its own module: 2)
pc/config.py: TurnoverGridConfig (other uses in its own module: 2)
pc/config.py: PositionsConfig (other uses in its own module: 2)
pc/config.py: LeveredConfig (other uses in its own module: 2)
pc/config.py: CliConfig (other uses in its own module: 2)
pc/config.py: OutputsConfig (other uses in its own module: 2)
pc/config.py: _ticker_ordered (other uses in its own module: 3)
pc/config.py: _tuples (other uses in its own module: 7)
pc/cov.py: _frame (other uses in its own module: 5)
pc/cov.py: _cond (other uses in its own module: 1)
pc/cov_eval.py: run_cov_eval (other uses in its own module: 1)
pc/data.py: _read_prices_csv (other uses in its own module: 1)
pc/experiments.py: load_panel (other uses in its own module: 5)
pc/experiments.py: after_first (other uses in its own module: 3)
pc/experiments.py: bp_pa (other uses in its own module: 4)
pc/experiments.py: paired_diff_interval (other uses in its own module: 1)
pc/experiments.py: plot_turnover_frontier (other uses in its own module: 1)
pc/experiments.py: scale_costs (other uses in its own module: 1)
pc/experiments.py: monthly_cov_robustness (other uses in its own module: 2)
pc/experiments.py: read_tables (other uses in its own module: 1)
pc/experiments.py: levered_k (other uses in its own module: 2)
pc/report.py: is_true (other uses in its own module: 3)
pc/report.py: markdown_table (other uses in its own module: 6)
pc/report.py: primary_table (other uses in its own module: 1)
pc/report.py: qlike_table (other uses in its own module: 1)
pc/report.py: cost_table (other uses in its own module: 1)
pc/report.py: monthly_cov_table (other uses in its own module: 1)
pc/report.py: robustness_table (other uses in its own module: 1)
pc/report.py: readme_tables (other uses in its own module: 1)
pc/sensitivity.py: DateDraws (other uses in its own module: 5)
pc/sensitivity.py: momentum_months (other uses in its own module: 2)
pc/sensitivity.py: strategy_solvers (other uses in its own module: 1)
pc/sensitivity.py: plot_sensitivity (other uses in its own module: 1)
pc/sensitivity.py: load_inputs (other uses in its own module: 1)
pc/sensitivity.py: run_sensitivity (other uses in its own module: 1)
pc/solver.py: _options (other uses in its own module: 1)
pc/stats.py: bootstrap_config (other uses in its own module: 1)
pc/stats.py: interval_columns (other uses in its own module: 2)
pc/stats.py: boot_sharpe (other uses in its own module: 1)
pc/trades.py: universe_tickers (other uses in its own module: 1)
pc/trades.py: book_arrays (other uses in its own module: 2)
pc/trades.py: round_to_lot (other uses in its own module: 1)
65 names used in no other file; 0 used nowhere
```

Disposition: **all 65 stay.** Every hit is a helper used inside its own module, and none is used nowhere. A second check walked each module's AST: every one of the 65 names occurs as an `ast.Name` or `ast.Attribute` in its own module, so no count comes from a comment or docstring alone. By group:

- `pc/config.py`: the 15 nested config dataclasses, built by `load_config`, and its 2 parsing helpers.
- `pc/cli.py`: `read_positions`, `resolve_strategy`, `resolve_asof` and `complete_book`, the steps of `plan`, which `pctrade` (`pc.cli:main`) runs.
- `pc/report.py`: the per-table builders called by `readme_tables`.
- The rest are private steps of the module's public writer or allocator (`_bounds`, `_sort`, `run_sensitivity`, `boot_sharpe`, `round_to_lot` and so on), each listed in the "helpers outside kickoff Section 6" deviation of the section that built it.

### 6. Fresh clone

Cloned from GitHub at `5dffbb3` into `%TEMP%\pcs7`; `.venv` built as in amendment 2 (`uv venv --seed --python 3.11 .venv`, `pip install -r requirements-lock.txt`, `pip install -e . --no-deps`); then `.venv\Scripts\python scripts/run_all.py`, `git status --porcelain`, `.venv\Scripts\python -m pytest --disable-socket -q`, `git status --porcelain`. The folder was deleted afterwards. `run_all`'s stderr was discarded (the same cvxpy warnings as evidence 1), and the cvxpy warning lines inside pytest's warnings summary are filtered out below; the 35 warnings are the same `solver.py:77` `UserWarning` as in section 6.

```
=== run_all
data.write_data_issues: 0.1 s
data.write_data_summary: 0.0 s
cov_eval.write_cov_eval: 3.2 s
backtest.write_walk_forward: 68.4 s
stats.write_metrics: 0.6 s
stats.write_sharpe_intervals: 2.1 s
stats.write_results_primary: 0.0 s
charts.write_charts: 1.4 s
sensitivity.write_sensitivity: 162.8 s
experiments.write_turnover_frontier: 41.1 s
experiments.write_cost_sensitivity: 61.2 s
experiments.write_monthly_cov: 3.3 s
experiments.write_levered: 2.7 s
experiments.write_answers: 0.2 s
report.write_readme_tables: 0.1 s
strategy: mv_constrained|lw_cc|sample|C
decision date: 2026-07-31 (allocator inputs from the pinned data snapshot)
solver: CLARABEL+CLARABEL  status: optimal  fallback: False
turnover limit: 0.3, not relaxed
turnover shadow price: 0.946883 bp of monthly return per 1% of turnover
NAV: 10,000,000.00
cash before: 500,790.07 (5.0079% of NAV)
trades: 3  buys 1,749,179.25  sells 1,249,369.26
turnover before rounding: 0.300000
turnover after rounding: 0.299855
total estimated cost: 899.56 (0.8996 bp of NAV)
residual cash: 80.52 (0.0008% of NAV)
max |weight_after - weight_target|: 0.000121578
lots cut to keep cash >= 0: 6

ticker side  quantity      price      notional   est_cost  weight_before  weight_target  weight_after
   XLK  BUY    9987.0 175.145615  1.749179e+06 524.753776       0.000000       0.175040      0.174918
   TLT SELL    3058.0  81.607300 -2.495551e+05  74.866537       0.099993       0.075033      0.075038
   GLD SELL    2691.0 371.540000 -9.998141e+05 299.944242       0.400000       0.300000      0.300019

wrote examples/trades_demo.csv
cli.main (6.5 demo): 0.1 s
total: 347.4 s
=== git status --porcelain after run_all
=== end status
=== pytest
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 82%]
..............................................                           [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
262 passed, 35 warnings in 29.51s
=== git status --porcelain after pytest
=== end
```

Both `git status --porcelain` outputs are empty.

### 7. `git grep -n -E "TODO|FIXME|XXX"`

Not empty. Full output (lines cut at 160 characters):

```
PLAN.md:113:**7.5 Final check and tidy.** Fresh clone into a temp folder, `pip install -e ".[dev]"`, run `scripts/run_all.py` and `pytest -p socket --disable-so
instructions/00_kickoff.md:372:- 7.5 Final fresh-clone run of `scripts/run_all.py` and the test suite with sockets disabled; tidy (no stray files, no TODOs, no 
instructions/07_section_7.md:137:- **Grep.** `git grep -n -E "TODO|FIXME|XXX"` returns nothing.
Binary file outputs/results/weights_long.parquet matches
review/section_6.md:344:pctrade: error: positions: unknown ticker(s) ['XXX']; the universe is ['SPY', 'IWM', 'EFA', 'EEM', 'XLE', 'XLF', 'XLK', 'XLU', 'XLV', 'S
tests/test_cli.py:32:    ("unknown_ticker", ["SPY,10,745", "XXX,10,10"], "unknown ticker"),
tests/test_cli.py:46:    code, _, err = run(["--positions", write_positions(tmp_path / "p.csv", ["SPY,10,745", "XXX,1,1"])], capsys)
tests/test_cli.py:47:    assert code == 2 and "unknown ticker" in err and "XXX" in err
tests/test_trades.py:157:    (dict(ticker=["SPY", "XXX"]), "unknown ticker"),
```

- `PLAN.md`, `instructions/00_kickoff.md` and `instructions/07_section_7.md` quote the words in the checks themselves. These files may not be edited.
- `outputs/results/weights_long.parquet` matches on its binary bytes.
- `tests/test_cli.py` and `tests/test_trades.py` use `XXX` as the deliberately unknown ticker of the exit-2 tests, and `review/section_6.md` records that test's printed error. They are not markers.
- There is no TODO, FIXME or XXX marker in `pc/`, `scripts/`, `docs/`, `README.md`, `examples/` or `decisions/`. See open question 1.

`git grep -n -i "results pending" -- . ':!instructions' ':!PLAN.md'` returns nothing (exit 1). The phrase survives only in `PLAN.md` and the kickoff, which describe session 0.

## Tests run

The 2 new test files:

```
.venv\Scripts\python -m pytest --disable-socket -q tests/test_run_all.py tests/test_report.py
....                                                                     [100%]
4 passed in 2.70s
```

The full suite (262 tests: 263 at the 7.2 commit, less the removed placeholder):

```
.venv\Scripts\python -m pytest --disable-socket -q
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 82%]
..............................................                           [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
262 passed, 35 warnings in 20.31s
```

## Fresh-clone check

See evidence 6.

## Runtime per step

| step | runtime |
|---|---|
| 7.0 | none |
| 7.1 | `run_all.py` before the README tables existed: 359.9 s |
| 7.2 | `write_readme_tables` 0.0 to 0.1 s; full `run_all.py` 372.8 s and 347.2 s (evidence 1) |
| 7.3, 7.4 | none |
| 7.5 | fresh clone: `run_all.py` 347.4 s, pytest 29.5 s; `find_unused.py` under 1 s |

## Deviations from PLAN.md

1. **The README tables call joined `run_all.py` in the 7.2 commit,** because `pc/report.py` is step 7.2 and did not exist at 7.1. The 7.1 commit ran end to end without it, and the determinism runs of evidence 1 were made with the complete script.
2. **`readme_robustness.md` holds 2 tables,** the cost scales and the 36-monthly-return covariance, each under a bold caption written by the code. Amendment 7.2 fixes 5 snippets and asks for a callout before each table, so the 2 callouts are 2 consecutive paragraphs immediately before the snippet, each naming its table ("the first table below", "the second table").
3. **`readme_qlike.md` ends with a code-written note** giving the bias-ratio band (0.92 to 1.08 over 196 months) and the sign convention of the QLIKE difference.
4. **`readme_turnover.md` leaves out the `none` row,** the reference whose entries are 0 or NaN by construction.
5. **The primary table's ruin month comes from `metrics_all.csv`,** joined by strategy id, because `results_primary.csv` has no `ruin_month` column.
6. **`test_readme_tables_match_snippets` reads committed files under `outputs/tables/`.** Rule 7 says no test may depend on `outputs/` already existing, but amendment 7.2 defines the test as a comparison of the README against the snippet files. The snippets are committed, so the test passes in a fresh clone before `run_all` (evidence 6). Amendment 1 gives the instruction file precedence.
7. **The Bayes-Stein and Black-Litterman ratios in README section 5 are a typed list,** not a generated table, since the amendment fixes the 5 snippets. Each ratio is traced in evidence 2.
8. **README section 8 is titled "Checks on the assumptions",** to keep the banned stem out of the prose (evidence 3).
9. **`find_unused.py` also prints each name's use count in its own module.** The list itself is exactly the specified one.
10. **The trade generator section and the Reproduce section** cite the demo's 6 cut shares and the measured runtime of about 6 minutes; both are traced in evidence 2.

## Not verified

- The README, DESIGN_NOTE and METHODS were not viewed rendered on GitHub. The escaped pipes inside code spans in table cells and the `$$` LaTeX blocks follow GitHub's Markdown rules but were checked only as text.
- The Linux and macOS line in Reproduce (`.venv/bin/python`) was not run on those systems in this session; the reviewer's Linux runs of earlier sections used the same layout.

## Open questions

1. **The `git grep -n -E "TODO|FIXME|XXX"` check cannot return nothing** while the instruction files and `PLAN.md` quote the pattern and the binary parquet matches. The only hits that could be changed are the `XXX` unknown-ticker strings in `tests/test_cli.py` and `tests/test_trades.py`. Renaming them (for example to `ZZZ`) does not change what the tests check, but rule 5 forbids rewriting tests, so they were left. Options: (1) accept the hits as listed in evidence 7; (2) rename the 2 tests' fake ticker to `ZZZ` and scope the check to `-- pc scripts tests docs README.md`.

`decisions/OPEN.md` has no items.

## Files changed

- Added: `decisions/section_7_review.md`, `scripts/run_all.py`, `scripts/find_unused.py`, `pc/report.py`, `tests/test_run_all.py`, `tests/test_report.py`, `docs/DESIGN_NOTE.md`, `docs/METHODS.md`, `outputs/tables/readme_primary.md`, `outputs/tables/readme_qlike.md`, `outputs/tables/readme_turnover.md`, `outputs/tables/readme_levered.md`, `outputs/tables/readme_robustness.md`, `review/section_7.md`, `instructions/07_section_7.status.md`
- Modified: `decisions/OPEN.md`, `README.md`
- Deleted: `tests/test_placeholder.py`
- Regenerated by `run_all.py` and byte-identical: every other file under `outputs/`, and `examples/trades_demo.csv`

## Reviewer reads

1. `README.md`
2. Evidence 2 (trace) and evidence 3 (grep) above
3. `docs/DESIGN_NOTE.md`
4. `docs/METHODS.md`
5. `pc/report.py` and `tests/test_report.py`
6. `scripts/run_all.py` and evidence 1 and 6
7. Open question 1

### Session 7b

From `instructions/07b_final_edits.md`. Commits: `3c9f559` step 7.6 (the 4 wording fixes), `f0a153f` step 7.7 (`decisions/section_7b_review.md`). Each of the 4 old strings occurred exactly once before it was replaced.

#### The 4 diffs (`git diff` before the 7.6 commit)

```diff
diff --git a/README.md b/README.md
index 7cd9169..63a778d 100644
--- a/README.md
+++ b/README.md
@@ -5,13 +5,13 @@ It also ships `pctrade`, a command-line tool that turns a positions file and any
 
 ## What it found
 
-**Question 1: how much of the in-sample gap survives out of sample?** Very little. In sample, the budget-only frontier offers a maximum Sharpe ratio of 1.72 (a supremum the frontier approaches but never reaches) and the long-only frontier capped at 30% per asset offers 1.10. Out of sample, `mv_constrained|lw_cc|sample|C` earned a Sharpe of 0.67 (90% interval 0.36 to 1.03), equal weight 0.71 (0.39 to 1.11) and `min_variance|lw_cc|none|B` 0.45 (−0.003 to 1.01). No allocator beat equal weight by a margin the bootstrap can tell apart from 0. HRP, under all 4 covariance estimators, is the only allocator whose Sharpe is reliably below equal weight's: on the primary row, `hrp|sample|none|none` trails it by 0.55 with a 90% interval of −1.02 to −0.01. 3 of the 4 unconstrained mean-variance funds went to 0, and the 4th, on the Ledoit-Wolf covariance, was not ruined but lost 98% from peak to trough.
+**Question 1: how much of the in-sample gap survives out of sample?** Capped mean-variance kept 61% of the long-only frontier's Sharpe ratio and 39% of the unconstrained frontier's. In sample, the budget-only frontier offers a maximum Sharpe ratio of 1.72 (a supremum the frontier approaches but never reaches) and the long-only frontier capped at 30% per asset offers 1.10. Out of sample, `mv_constrained|lw_cc|sample|C` earned a Sharpe of 0.67 (90% interval 0.36 to 1.03), equal weight 0.71 (0.39 to 1.11) and `min_variance|lw_cc|none|B` 0.45 (−0.003 to 1.01). No allocator beat equal weight by a margin the bootstrap can tell apart from 0. HRP, under all 4 covariance estimators, is the only allocator whose Sharpe is reliably below equal weight's: on the primary row, `hrp|sample|none|none` trails it by 0.55 with a 90% interval of −1.02 to −0.01. 3 of the 4 unconstrained mean-variance funds went to 0, and the 4th, on the Ledoit-Wolf covariance, was not ruined but lost 98% from peak to trough.
 
 **Question 2: what does a turnover limit cost and save?** At the default limit of τ = 0.30, the fund gives up 7.9 bp a year of ex-ante expected return to save 0.95 bp a year of trading cost. Each limit that binds gives up more expected return than it saves in cost, so no limit in the grid lies below the 45° line. After the fact, the realised effect cannot be told apart from 0: τ = 0.30 returned −7.8 bp a year against no limit (90% interval −41.8 to 24.9), and even the tightest limit, τ = 0.05, returned 125.9 bp a year with an interval of −87.7 to 332.7.
 
 **Question 3: how sensitive are mean-variance weights to noise in expected returns?** Extremely, until a constraint steps in. Perturbing the means by their own sampling error at 2026-07-31 moved the unconstrained weights by a mean absolute change of 109.1 (10,911% of the fund), against 0.94 for the long-only capped version. Bayes-Stein shrinkage of the mean does not steady the weights: its mean absolute change divided by that of the plain capped fund is 0.98 at 2012-12-31, 0.95 at 2020-02-28 and 1.02 at 2026-07-31. Black-Litterman steadies them at 2 of the 3 dates, with ratios of 0.50 and 0.22, but not at 2012-12-31, where its ratio is 1.31.
 
-**Question 4: which covariance estimator forecasts risk best?** It depends on the portfolio. For equal weight, EWMA beats Ledoit-Wolf constant correlation: its QLIKE difference is −0.24 (90% interval −0.58 to −0.005), and lower is better. For the global minimum variance portfolio, the one an optimiser builds, EWMA is worse by 0.45 (interval −0.07 to 1.24) and under-forecasts the risk: its bias ratio is 1.38, against 1.01 for Ledoit-Wolf, where a calibrated forecast sits near 1.
+**Question 4: which covariance estimator forecasts risk best?** It depends on the portfolio. For equal weight, EWMA beats Ledoit-Wolf constant correlation: its QLIKE difference is −0.24 (90% interval −0.58 to −0.005), and lower is better. For the global minimum variance portfolio, the one an optimiser builds, EWMA scores 0.45 worse, though that interval (−0.07 to 1.24) includes 0. The clearer signal is the bias: EWMA under-forecasts that portfolio's risk with a bias ratio of 1.38, outside the 0.92 to 1.08 band for a calibrated forecast, against 1.01 for Ledoit-Wolf.
 
 ## Setup
 
@@ -98,7 +98,7 @@ Bias ratio 90% band for a correct forecast over 196 months: 0.92 to 1.08. A QLIK
 
 Scaling every cost by 0 and by 3 tells us whether the ranking depends on the cost model. In the first table below, look for any change in the order of the Sharpe columns: there is none.
 
-Estimating the covariance from 36 monthly returns instead of daily ones puts 18 assets against 36 observations. The second table compares the 2 strategies most exposed to that. Unconstrained mean-variance blows up far sooner on the monthly estimate, while capped minimum variance barely notices.
+Estimating the covariance from 36 monthly returns instead of daily ones puts 18 assets against 36 observations. The second table compares the 2 strategies most exposed to that. Unconstrained mean-variance blows up far sooner on the monthly estimate. Capped minimum variance keeps a similar Sharpe ratio but trades about twice as much.
 
 <!-- readme_robustness.md -->
 **Cost scales.** Every one-way cost multiplied by the scale.
diff --git a/docs/DESIGN_NOTE.md b/docs/DESIGN_NOTE.md
index 2e375c2..4294faf 100644
--- a/docs/DESIGN_NOTE.md
+++ b/docs/DESIGN_NOTE.md
@@ -10,7 +10,7 @@ A portfolio implementation desk turns a model's target weights into orders a fun
 
 **The turnover limit.** A turnover budget caps how much of the fund trades each month. It protects against an optimiser that chases noise, and it keeps orders within what the desk can execute without moving prices. At τ = 0.30 the limit bound in 62 months. In this backtest, every binding limit gave up more ex-ante expected return than it saved in modelled cost, and the realised effect cannot be told apart from 0. The limit earns its place as a guard on execution and on model error rather than as a source of return.
 
-**Flat basis-point costs in the objective.** Putting cost into the objective makes the optimiser trade only when the expected gain beats the spread. With costs scaled to 0, 1 and 3 times their base level, the capped mean-variance fund's mean turnover fell from 0.22 to 0.18 to 0.12, while its Sharpe ratio barely moved. Flat costs ignore market impact, so the objective understates the cost of large trades; for a $10m book in these ETFs that is a small error.
+**Flat basis-point costs in the objective.** Putting cost into the objective makes the optimiser trade only when the expected gain beats the spread. With costs scaled to 0, 1 and 3 times their base level, the capped mean-variance fund's mean turnover fell from 0.22 to 0.18 to 0.12, while its Sharpe ratio barely moved. Flat costs ignore market impact, so the objective understates the cost of large trades, an error this repo does not measure.
 
 **The feasibility relaxation.** A drifted weight can sit above its cap. If the turnover budget is too small to bring it back, the problem has no solution, so the rule solves with the smallest turnover that restores the cap, plus 1e-6, and records that the limit was relaxed. The ordering is deliberate: a mandate breach outranks a turnover budget, because a breach is a compliance event and an overspent budget is not. The demo book holds GLD at 40% against a 30% cap, and merely reaching the feasible set takes turnover of 0.2501. At τ = 0.05 the backtest relaxed the limit in 4 months.
 
```

#### `run_all` after both commits

stdout below without the demo's printed summary, which is unchanged from evidence 1. stderr held only the cvxpy `UserWarning` lines.

```
data.write_data_issues: 0.1 s
data.write_data_summary: 0.1 s
cov_eval.write_cov_eval: 2.9 s
backtest.write_walk_forward: 78.6 s
stats.write_metrics: 0.5 s
stats.write_sharpe_intervals: 2.2 s
stats.write_results_primary: 0.1 s
charts.write_charts: 1.2 s
sensitivity.write_sensitivity: 140.3 s
experiments.write_turnover_frontier: 36.1 s
experiments.write_cost_sensitivity: 48.8 s
experiments.write_monthly_cov: 2.2 s
experiments.write_levered: 2.1 s
experiments.write_answers: 0.2 s
report.write_readme_tables: 0.1 s
total estimated cost: 899.56 (0.8996 bp of NAV)
cli.main (6.5 demo): 0.1 s
total: 315.5 s
exit 0
```

`git status --porcelain` after the run (empty: the prose edits touch no generated file):

```

```

#### Style grep on the 2 edited files

`grep -n -E " — | – | - |robust|resilient|rigorous|leverag|grounded|delve|crucial|landscape|notably" README.md docs/DESIGN_NOTE.md`:

```
README.md:103:<!-- readme_robustness.md -->
README.md:124:<!-- /readme_robustness.md -->
exit 0
```

The 2 hits are the `readme_robustness.md` marker comments, as in evidence 3. None of the 4 new sentences match.

#### Tests

`.venv\Scripts\python -m pytest --disable-socket -q`:

```
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 82%]
..............................................                           [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
262 passed, 35 warnings in 18.20s
```

#### Fresh clone

Cloned from GitHub at `f0a153f` into `%TEMP%\pcs7b`; `.venv` built as in amendment 2; `.venv\Scripts\python -m pytest --disable-socket -q` (amendment 3); the folder was then deleted. The cvxpy warning lines inside the warnings summary are filtered out, as in evidence 6.

```
f0a153f section 7: reviewer decisions and close-out
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 82%]
..............................................                           [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
262 passed, 35 warnings in 31.22s
deleted: True
```
