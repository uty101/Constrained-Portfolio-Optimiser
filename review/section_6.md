# Review — Section 6: Trade generator and CLI

## Section

Section 6 — Trade generator and CLI, as amended by `instructions/06_section_6.md` (step 6.0, then amendments to 6.1 to 6.5).

## Steps completed

- 6.0 `b019473` reviewer decisions for section 5: `decisions/section_6_review.md`, `decisions/OPEN.md` cleared, bootstrap intervals on `turnover_frontier.csv`, Q2 and Q3 of `answers.csv` regenerated
- 6.1 `2c58da0` trade core in `pc/trades.py`: `current_weights`, `validate_positions`, `generate_trades` (lot rounding toward the target, min notional, cash repair), `TradeInputError`
- 6.2 `12b6a9d` printed summary and price warnings in `pc/trades.py`
- 6.3 `e19d1a4` `pc/cli.py`, console script `pctrade`
- 6.4 `f12ccf5` `tests/test_trades.py`, `tests/test_cli.py`
- 6.5 `4d36dde` `examples/positions_demo.csv`, `examples/trades_demo.csv`, `docs/cli_demo.md`, `pc.cli.demo_book`, `test_demo_reproduces_trades_demo`, open decision 11

The 6.4 tests were run against the 6.3 `pc/cli.py` before the 6.5 additions (31 passed), with `test_demo_reproduces_trades_demo` added in 6.5.

## Evidence

### 6.0 Reviewer decisions for Section 5

#### `turnover_frontier.csv`, old (`4e886f1`) and new

The 11 old columns are unchanged in every row. The 3 new columns are a stationary bootstrap of the 195 paired monthly differences ret_net(τ) − ret_net(none), months 2 to 196, mean × 12 × 1e4 per replication, on `stationary_bootstrap_indices(195, 6, 10000, 20260930)`, with `np.quantile` at (0.05, 0.95).

```
OLD
    tau  mean_mu_exante  exante_return_given_up_bp_pa  mean_cost  cost_saved_bp_pa  realised_net_ann_return  realised_net_vs_none_bp_pa  mean_turnover  mean_dual_bp_per_pct  n_binding  n_relaxed
0  0.05        0.012111                  2.068268e+02   0.000018      5.975974e+00                 0.106135                1.259373e+02       0.050175          3.766449e-01        194          4
1   0.1        0.013135                  8.396118e+01   0.000032      4.226140e+00                 0.096755                3.394099e+01       0.094225          1.733218e-01        176          0
2   0.2        0.013645                  2.278888e+01   0.000050      2.067300e+00                 0.090732               -2.349968e+01       0.149443          5.778808e-02        116          0
3   0.3        0.013769                  7.879745e+00   0.000059      9.524165e-01                 0.092619               -7.843103e+00       0.176746          1.955142e-02         62          0
4   0.5        0.013823                  1.378750e+00   0.000066      1.801937e-01                 0.093246               -3.435845e+00       0.196472          3.776752e-03         19          0
5  0.75        0.013834                  1.756654e-02   0.000067      6.628972e-03                 0.093807                8.318797e-01       0.200849          3.255431e-04          1          0
6   1.0        0.013835                 -1.208404e-07   0.000067     -7.092646e-08                 0.093722                2.227364e-07       0.201033          1.313371e-12          0          0
7  none        0.013835                  0.000000e+00   0.000067      0.000000e+00                 0.093722                0.000000e+00       0.201033                   NaN          0          0

NEW
    tau  mean_mu_exante  exante_return_given_up_bp_pa  mean_cost  cost_saved_bp_pa  realised_net_ann_return  realised_net_vs_none_bp_pa  mean_turnover  mean_dual_bp_per_pct  n_binding  n_relaxed  realised_net_vs_none_p05  realised_net_vs_none_p95  realised_net_vs_none_frac_le_0
0  0.05        0.012111                  2.068268e+02   0.000018      5.975974e+00                 0.106135                1.259373e+02       0.050175          3.766449e-01        194          4                -87.684641                332.714377                          0.1615
1   0.1        0.013135                  8.396118e+01   0.000032      4.226140e+00                 0.096755                3.394099e+01       0.094225          1.733218e-01        176          0               -101.888572                164.443245                          0.3348
2   0.2        0.013645                  2.278888e+01   0.000050      2.067300e+00                 0.090732               -2.349968e+01       0.149443          5.778808e-02        116          0                -80.972627                 28.929759                          0.7596
3   0.3        0.013769                  7.879745e+00   0.000059      9.524165e-01                 0.092619               -7.843103e+00       0.176746          1.955142e-02         62          0                -41.757963                 24.899885                          0.6574
4   0.5        0.013823                  1.378750e+00   0.000066      1.801937e-01                 0.093246               -3.435845e+00       0.196472          3.776752e-03         19          0                -12.810375                  4.990406                          0.7513
5  0.75        0.013834                  1.756654e-02   0.000067      6.628972e-03                 0.093807                8.318797e-01       0.200849          3.255431e-04          1          0                 -0.011617                  2.495642                          0.3049
6   1.0        0.013835                 -1.208404e-07   0.000067     -7.092646e-08                 0.093722                2.227364e-07       0.201033          1.313371e-12          0          0                 -0.000002                  0.000002                          0.4264
7  none        0.013835                  0.000000e+00   0.000067      0.000000e+00                 0.093722                0.000000e+00       0.201033                   NaN          0          0                       NaN                       NaN                             NaN
```

The reviewer's figures were τ = 0.05: (−88.6, +329.2), fraction ≤ 0 0.16; τ = 0.10: (−104.2, +163.2). The repo gives (−87.7, +332.7), 0.1615 and (−101.9, +164.4). The point estimates agree (125.9 bp at τ = 0.05). The intervals differ by up to 3.5 bp at the ends, which is what a different set of bootstrap index paths gives. The conclusion is the same: every interval contains 0, and no τ row is distinguishable from no limit (see Not verified).

#### `answers.csv`, old (`4e886f1`) and new

Q2 gains the τ = 0.05 realised difference, and the τ = 0.30 row gains its interval. The largest τ below the 45° line is now NaN (open decision 9, option 2): τ = 1.00 lies below the line by 5e-8 bp but has `n_binding` 0, and no other τ lies below it. Q3 carries the 2 ratios at each of the 3 dates (6 rows in place of 2). The other 18 old rows are unchanged.

```
OLD
   question                                                                                                 figure       value       p05       p95                                                                                                    source_row
0        Q1                                                                   in-sample max Sharpe, set A frontier    1.717500       NaN       NaN                                                                                               frontier == "A"
1        Q1                                                                   in-sample max Sharpe, set B frontier    1.098266       NaN       NaN                                                                                               frontier == "B"
2        Q1                                                    out-of-sample Sharpe, mv_constrained|lw_cc|sample|C    0.673838  0.363273  1.026701                                                                strategy_id == "mv_constrained|lw_cc|sample|C"
3        Q1                                                      out-of-sample Sharpe, equal_weight|none|none|none    0.705100  0.387164  1.110210                                                                  strategy_id == "equal_weight|none|none|none"
4        Q1                                                        out-of-sample Sharpe, min_variance|lw_cc|none|B    0.452632 -0.002685  1.010246                                                                    strategy_id == "min_variance|lw_cc|none|B"
5        Q1                                                                          ruined set A strategies, of 4    3.000000       NaN       NaN                                                                                strategy_id.str.endswith("|A")
6        Q2                                                              tau = 0.3: ex-ante return given up, bp pa    7.879745       NaN       NaN                                                                                                  tau == "0.3"
7        Q2                                                                   tau = 0.3: trading cost saved, bp pa    0.952416       NaN       NaN                                                                                                  tau == "0.3"
8        Q2                                                 tau = 0.3: realised net return against no limit, bp pa   -7.843103       NaN       NaN                                                                                                  tau == "0.3"
9        Q2                                                  largest tau whose point lies below the 45 degree line    1.000000       NaN       NaN                                             tau != "none" and exante_return_given_up_bp_pa < cost_saved_bp_pa
10       Q3                                          2026-07-31: mean_abs_change, mv_unconstrained|sample|sample|A  109.111688       NaN       NaN                                       date == "2026-07-31" and strategy == "mv_unconstrained|sample|sample|A"
11       Q3                                             2026-07-31: mean_abs_change, mv_constrained|lw_cc|sample|B    0.941065       NaN       NaN                                          date == "2026-07-31" and strategy == "mv_constrained|lw_cc|sample|B"
12       Q3                                        2026-07-31: mean_abs_change, mv_constrained|lw_cc|bayes_stein|B    0.956876       NaN       NaN                                     date == "2026-07-31" and strategy == "mv_constrained|lw_cc|bayes_stein|B"
13       Q3                                                2026-07-31: mean_abs_change, black_litterman|lw_cc|bl|B    0.209499       NaN       NaN                                             date == "2026-07-31" and strategy == "black_litterman|lw_cc|bl|B"
14       Q3  2026-07-31: mean_abs_change ratio, mv_constrained|lw_cc|bayes_stein|B / mv_constrained|lw_cc|sample|B    1.016801       NaN       NaN  date == "2026-07-31" and strategy in ["mv_constrained|lw_cc|bayes_stein|B", "mv_constrained|lw_cc|sample|B"]
15       Q3          2026-07-31: mean_abs_change ratio, black_litterman|lw_cc|bl|B / mv_constrained|lw_cc|sample|B    0.222619       NaN       NaN          date == "2026-07-31" and strategy in ["black_litterman|lw_cc|bl|B", "mv_constrained|lw_cc|sample|B"]
16       Q4                                                             QLIKE difference against lw_cc, ewma on ew   -0.239488 -0.575984 -0.005369                                                                 estimator == "ewma" and portfolio_set == "ew"
17       Q4                                                            QLIKE difference against lw_cc, ewma on gmv    0.449875 -0.068463  1.240137                                                                estimator == "ewma" and portfolio_set == "gmv"
18       Q4                                                                                bias ratio, ewma on gmv    1.380937       NaN       NaN                                                                estimator == "ewma" and portfolio_set == "gmv"
19       Q4                                                                               bias ratio, lw_cc on gmv    1.011114       NaN       NaN                                                               estimator == "lw_cc" and portfolio_set == "gmv"

NEW
   question                                                                                                 figure       value        p05         p95                                                                                                    source_row
0        Q1                                                                   in-sample max Sharpe, set A frontier    1.717500        NaN         NaN                                                                                               frontier == "A"
1        Q1                                                                   in-sample max Sharpe, set B frontier    1.098266        NaN         NaN                                                                                               frontier == "B"
2        Q1                                                    out-of-sample Sharpe, mv_constrained|lw_cc|sample|C    0.673838   0.363273    1.026701                                                                strategy_id == "mv_constrained|lw_cc|sample|C"
3        Q1                                                      out-of-sample Sharpe, equal_weight|none|none|none    0.705100   0.387164    1.110210                                                                  strategy_id == "equal_weight|none|none|none"
4        Q1                                                        out-of-sample Sharpe, min_variance|lw_cc|none|B    0.452632  -0.002685    1.010246                                                                    strategy_id == "min_variance|lw_cc|none|B"
5        Q1                                                                          ruined set A strategies, of 4    3.000000        NaN         NaN                                                                                strategy_id.str.endswith("|A")
6        Q2                                                              tau = 0.3: ex-ante return given up, bp pa    7.879745        NaN         NaN                                                                                                  tau == "0.3"
7        Q2                                                                   tau = 0.3: trading cost saved, bp pa    0.952416        NaN         NaN                                                                                                  tau == "0.3"
8        Q2                                                tau = 0.05: realised net return against no limit, bp pa  125.937300 -87.684641  332.714377                                                                                                 tau == "0.05"
9        Q2                                                 tau = 0.3: realised net return against no limit, bp pa   -7.843103 -41.757963   24.899885                                                                                                  tau == "0.3"
10       Q2                                                  largest tau whose point lies below the 45 degree line         NaN        NaN         NaN                           tau != "none" and n_binding > 0 and exante_return_given_up_bp_pa < cost_saved_bp_pa
11       Q3                                          2026-07-31: mean_abs_change, mv_unconstrained|sample|sample|A  109.111688        NaN         NaN                                       date == "2026-07-31" and strategy == "mv_unconstrained|sample|sample|A"
12       Q3                                             2026-07-31: mean_abs_change, mv_constrained|lw_cc|sample|B    0.941065        NaN         NaN                                          date == "2026-07-31" and strategy == "mv_constrained|lw_cc|sample|B"
13       Q3                                        2026-07-31: mean_abs_change, mv_constrained|lw_cc|bayes_stein|B    0.956876        NaN         NaN                                     date == "2026-07-31" and strategy == "mv_constrained|lw_cc|bayes_stein|B"
14       Q3                                                2026-07-31: mean_abs_change, black_litterman|lw_cc|bl|B    0.209499        NaN         NaN                                             date == "2026-07-31" and strategy == "black_litterman|lw_cc|bl|B"
15       Q3  2012-12-31: mean_abs_change ratio, mv_constrained|lw_cc|bayes_stein|B / mv_constrained|lw_cc|sample|B    0.975940        NaN         NaN  date == "2012-12-31" and strategy in ["mv_constrained|lw_cc|bayes_stein|B", "mv_constrained|lw_cc|sample|B"]
16       Q3          2012-12-31: mean_abs_change ratio, black_litterman|lw_cc|bl|B / mv_constrained|lw_cc|sample|B    1.313081        NaN         NaN          date == "2012-12-31" and strategy in ["black_litterman|lw_cc|bl|B", "mv_constrained|lw_cc|sample|B"]
17       Q3  2020-02-28: mean_abs_change ratio, mv_constrained|lw_cc|bayes_stein|B / mv_constrained|lw_cc|sample|B    0.947103        NaN         NaN  date == "2020-02-28" and strategy in ["mv_constrained|lw_cc|bayes_stein|B", "mv_constrained|lw_cc|sample|B"]
18       Q3          2020-02-28: mean_abs_change ratio, black_litterman|lw_cc|bl|B / mv_constrained|lw_cc|sample|B    0.500114        NaN         NaN          date == "2020-02-28" and strategy in ["black_litterman|lw_cc|bl|B", "mv_constrained|lw_cc|sample|B"]
19       Q3  2026-07-31: mean_abs_change ratio, mv_constrained|lw_cc|bayes_stein|B / mv_constrained|lw_cc|sample|B    1.016801        NaN         NaN  date == "2026-07-31" and strategy in ["mv_constrained|lw_cc|bayes_stein|B", "mv_constrained|lw_cc|sample|B"]
20       Q3          2026-07-31: mean_abs_change ratio, black_litterman|lw_cc|bl|B / mv_constrained|lw_cc|sample|B    0.222619        NaN         NaN          date == "2026-07-31" and strategy in ["black_litterman|lw_cc|bl|B", "mv_constrained|lw_cc|sample|B"]
21       Q4                                                             QLIKE difference against lw_cc, ewma on ew   -0.239488  -0.575984   -0.005369                                                                 estimator == "ewma" and portfolio_set == "ew"
22       Q4                                                            QLIKE difference against lw_cc, ewma on gmv    0.449875  -0.068463    1.240137                                                                estimator == "ewma" and portfolio_set == "gmv"
23       Q4                                                                                bias ratio, ewma on gmv    1.380937        NaN         NaN                                                                estimator == "ewma" and portfolio_set == "gmv"
24       Q4                                                                               bias ratio, lw_cc on gmv    1.011114        NaN         NaN                                                               estimator == "lw_cc" and portfolio_set == "gmv"
```

#### The `sensitivity_summary.csv` rows behind the 6 Q3 ratios

1.231825 / 0.938118 = 1.313081, 0.422492 / 0.844790 = 0.500114, 0.209499 / 0.941065 = 0.222619.

```
          date                            strategy  mean_abs_change  frac_top_asset_changes
1   2012-12-31       mv_constrained|lw_cc|sample|B         0.938118                   0.783
2   2012-12-31  mv_constrained|lw_cc|bayes_stein|B         0.915547                   0.615
3   2012-12-31          black_litterman|lw_cc|bl|B         1.231825                   0.949
8   2020-02-28       mv_constrained|lw_cc|sample|B         0.844790                   0.396
9   2020-02-28  mv_constrained|lw_cc|bayes_stein|B         0.800103                   0.467
10  2020-02-28          black_litterman|lw_cc|bl|B         0.422492                   0.676
15  2026-07-31       mv_constrained|lw_cc|sample|B         0.941065                   0.643
16  2026-07-31  mv_constrained|lw_cc|bayes_stein|B         0.956876                   0.642
17  2026-07-31          black_litterman|lw_cc|bl|B         0.209499                   0.413
```

#### Chart 4

`outputs/figures/turnover_frontier.png` was regenerated by `write_turnover_frontier` and is byte-identical to the committed file: the chart reads only the 2 plotted columns, and no annotation of the new columns was added.

### 6.1 Trade core: a worked synthetic book

5 tickers at made-up prices, cash 25,000, lot 10, min notional 1,000. The target is SPY 0.30, TLT 0.20, GLD 0.20, EEM 0.15, IEF 0.15. Cash is not a weight, so w_before sums to 1 − 25,000 / 990,000 = 0.974747. The cash repair cut 5 lots from the 2 buys, each cut taken from whichever buy was then the largest: EEM 3,300 → 3,270 and IEF 1,560 → 1,540. That is why EEM and IEF end 0.0014 and 0.0022 under their targets.

```
  ticker  quantity  price
0    SPY      1000  500.0
1    TLT      2500   90.0
2    GLD       800  300.0
3    EEM         0   45.0
4    IEF         0   95.0
NAV 990000.0  sum w_before 0.9747474747474748
  ticker  side  quantity  price  notional  est_cost  weight_before  weight_target  weight_after
0    SPY  SELL     400.0  500.0 -200000.0     60.00   0.5050505051           0.30  0.3030303030
1    EEM   BUY    3270.0   45.0  147150.0     88.29   0.0000000000           0.15  0.1486363636
2    IEF   BUY    1540.0   95.0  146300.0     43.89   0.0000000000           0.15  0.1477777778
3    TLT  SELL     300.0   90.0  -27000.0      8.10   0.2272727273           0.20  0.2000000000
4    GLD  SELL     140.0  300.0  -42000.0     12.60   0.2424242424           0.20  0.2000000000
nav                         990000.0000000000
cash_before                  25000.0000000000
n_trades                         5.0000000000
buy_notional                293450.0000000000
sell_notional               269000.0000000000
turnover_before_rounding         0.5747474747
turnover_after_rounding          0.5681313131
rounding_slack                   0.0066161616
total_est_cost                 212.8800000000
total_est_cost_bp                2.1503030303
residual_cash                  337.1200000000
residual_cash_pct                0.0003405253
max_abs_weight_dev               0.0030303030
lots_cut_for_cash                5.0000000000
         w_before  w_target       w_after
SPY  0.5050505051      0.30  0.3030303030
EEM  0.0000000000      0.15  0.1486363636
IEF  0.0000000000      0.15  0.1477777778
TLT  0.2272727273      0.20  0.2000000000
GLD  0.2424242424      0.20  0.2000000000
```

### 6.5 The demo book and the NAV check

quantity = floor(weight × 10,000,000 / price), price = the 2026-07-31 close rounded to 4 decimals. `weight_x_nav_over_price` is the number floored. Cash = 10,000,000 − Σ value, in exact decimals.

```
  ticker  quantity     price           close  weight  weight_x_nav_over_price         value
0    SPY      2683  745.1796  745.1796264648    0.20          2683.9167363143  1999316.8668
1    IEF     21668   92.3004   92.3003768921    0.20         21668.3784685657  1999965.0672
2    TLT     12253   81.6073   81.6072845459    0.10         12253.8057257133   999934.2469
3    HYG      6356   78.6649   78.6648941040    0.05          6356.0749457509   499994.1044
4    GLD     10766  371.5400  371.5400085449    0.40         10766.0009689401    3999999.64
sum value 9499209.9253  cash 500790.0747  NAV 10000000.0000
```

`examples/positions_demo.csv`:

```
ticker,quantity,price
SPY,2683,745.1796
IEF,21668,92.3004
TLT,12253,81.6073
HYG,6356,78.6649
GLD,10766,371.54
```

### 6.2 and 6.5 The demo command, its printed summary and `trades_demo.csv`

```
$ pctrade --positions examples/positions_demo.csv --cash 500790.0747 --asof 2026-07-31 --out examples/trades_demo.csv
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
exit code: 0
```

`examples/trades_demo.csv`:

```
ticker,side,quantity,price,notional,est_cost,weight_before,weight_target,weight_after
XLK,BUY,9987,175.1456146,1749179.253,524.753776,0,0.1750395037,0.1749179253
TLT,SELL,3058,81.6073,-249555.1234,74.86653702,0.09999342469,0.07503289242,0.07503791235
GLD,SELL,2691,371.54,-999814.14,299.944242,0.399999964,0.3,0.30001855
```

τ_min of the demo book from the feasibility LP is 0.2501 (`turnover_feasibility(w_before, 0.30, 0.0, 0.30, 1.0)` returned τ_min 0.25007893547013377, τ_eff 0.3, tau_relaxed False), so the limit is not relaxed at τ = 0.30. The same book at `--max-turnover 0.05` shows the relaxation in the summary:

```
$ pctrade --positions examples/positions_demo.csv --cash 500790.0747 --asof 2026-07-31 --max-turnover 0.05 --dry-run
strategy: mv_constrained|lw_cc|sample|C
decision date: 2026-07-31 (allocator inputs from the pinned data snapshot)
solver: CLARABEL+CLARABEL  status: optimal  fallback: False
turnover limit: 0.05, relaxed (tau_relaxed True): tau_min > tau, tau_eff = 0.2500799355
turnover shadow price: 0.966468 bp of monthly return per 1% of turnover
NAV: 10,000,000.00
cash before: 500,790.07 (5.0079% of NAV)
trades: 2  buys 1,499,771.90  sells 999,814.14
turnover before rounding: 0.250080
turnover after rounding: 0.249959
total estimated cost: 749.88 (0.7499 bp of NAV)
residual cash: 82.44 (0.0008% of NAV)
max |weight_after - weight_target|: 0.000102282
lots cut to keep cash >= 0: 5

ticker side  quantity      price      notional   est_cost  weight_before  weight_target  weight_after
   XLK  BUY    8563.0 175.145615  1.499772e+06 449.931569            0.0       0.150079      0.149977
   GLD SELL    2691.0 371.540000 -9.998141e+05 299.944242            0.4       0.300000      0.300019

dry run: nothing written
exit code: 0
```

### By-hand reconciliation of 3 demo rows

NAV = 10,000,000. target_qty = w_target × NAV / price, raw = target_qty − current_qty, rounded trade = sign(raw) × floor(|raw|), lot 1. XLK's rounded buy of 9,993 was cut by 6 lots in the cash repair (it is the only buy). notional = trade × price, est_cost = |notional| × 0.0003 (all 3 tickers are 3 bp), weight_after = (current_qty + trade) × price / NAV. w_target is read from the CSV at 10 significant figures, which does not move any floor.

```
                                       0                   1                2
ticker                               GLD                 XLK              TLT
current_qty                      10766.0                 0.0          12253.0
price                             371.54       175.145614624          81.6073
w_target (csv, 10 sig.)              0.3        0.1750395037     0.0750328924
target_qty               8074.5007267051     9993.9415597558  9194.3848675302
raw                     -2691.4992732949     9993.9415597558 -3058.6151324698
rounded trade                    -2691.0              9993.0          -3058.0
lots cut for cash                    0.0                 6.0              0.0
final trade                        -2691                9987            -3058
notional                      -999814.14  1749179.2532501221     -249555.1234
c_i                               0.0003              0.0003           0.0003
est_cost                      299.944242       524.753775975      74.86653702
weight_after                  0.30001855        0.1749179253     0.0750379123
--- the same rows in trades_demo.csv
        side  quantity        price      notional      est_cost  weight_before  weight_target  weight_after
ticker                                                                                                     
GLD     SELL      2691  371.5400000  -999814.1400  299.94424200   0.3999999640   0.3000000000  0.3000185500
XLK      BUY      9987  175.1456146  1749179.2530  524.75377600   0.0000000000   0.1750395037  0.1749179253
TLT     SELL      3058   81.6073000  -249555.1234   74.86653702   0.0999934247   0.0750328924  0.0750379123
```

### A price warning, and a strategy with no turnover limit

SPY and GLD are priced 6.06% and 7.66% away from the 2026-07-31 close. Risk parity has no turnover constraint, so the shadow price prints "n/a". Tickers absent from the file are priced at the close (open decision 11).

```
$ cat stale.csv
ticker,quantity,price
SPY,1000,700
TLT,5000,81.61
GLD,800,400
$ pctrade --positions stale.csv --cash 50000 --strategy "risk_parity|ewma|none|none" --lot-size 10 --dry-run
strategy: risk_parity|ewma|none|none
decision date: 2026-07-31 (allocator inputs from the pinned data snapshot)
solver: L-BFGS-B  status: optimal  fallback: False
turnover limit: none
turnover shadow price: n/a
NAV: 1,478,050.00
cash before: 50,000.00 (3.3828% of NAV)
trades: 18  buys 1,330,014.45  sells 1,281,256.10
turnover before rounding: 1.777468
turnover after rounding: 1.766700
total estimated cost: 910.80 (6.1622 bp of NAV)
residual cash: 330.85 (0.0224% of NAV)
max |weight_after - weight_target|: 0.00349559
lots cut to keep cash >= 0: 2
WARNING: SPY price 700.0000 differs from the 2026-07-31 close 745.1796 by -6.06% (limit 5%)
WARNING: GLD price 400.0000 differs from the 2026-07-31 close 371.5400 by +7.66% (limit 5%)

ticker side  quantity      price       notional   est_cost  weight_before  weight_target  weight_after
   SPY SELL     940.0 700.000000 -658000.000000 197.400000       0.473597       0.024920      0.028416
   IWM  BUY      90.0 290.441437   26139.729309   7.841919       0.000000       0.017964      0.017685
   EFA  BUY     230.0 105.580002   24283.400421   7.285020       0.000000       0.016734      0.016429
   EEM  BUY     300.0  64.089996   19226.998901  11.536199       0.000000       0.013408      0.013008
   XLE  BUY    1520.0  59.198124   89981.148376  26.994345       0.000000       0.061197      0.060878
   XLF  BUY    1050.0  56.739189   59576.148605  17.872845       0.000000       0.040629      0.040307
   XLK  BUY     120.0 175.145615   21017.473755   6.305242       0.000000       0.014495      0.014220
   XLU  BUY    1070.0  44.026276   47108.114929  14.132434       0.000000       0.031959      0.031872
   XLV  BUY     340.0 161.930267   55056.290894  16.516887       0.000000       0.037872      0.037249
   SHY  BUY    4460.0  81.505417  363514.159241 109.054248       0.000000       0.247349      0.245942
   IEF  BUY    1250.0  92.300377  115375.471115  34.612641       0.000000       0.078252      0.078059
   TLT SELL    4010.0  81.610000 -327256.100000  98.176830       0.276073       0.054660      0.054662
   TIP  BUY    1390.0 106.845993  148515.930328  89.109558       0.000000       0.100960      0.100481
   LQD  BUY     980.0 105.349747  103242.751770  30.972826       0.000000       0.069927      0.069851
   HYG  BUY    1560.0  78.664894  122717.234802  73.630341       0.000000       0.083513      0.083026
   GLD SELL     740.0 400.000000 -296000.000000  88.800000       0.216501       0.014771      0.016238
   DBC  BUY    2960.0  29.450001   87172.002258  52.303201       0.000000       0.059108      0.058978
   VNQ  BUY     480.0  98.099167   47087.600098  28.252560       0.000000       0.032282      0.031858

dry run: nothing written
exit code: 0
```

### Every error case: the command and its exit code

Each command was run from a scratch folder holding the named file. The last 3 are not error tests but show the `--debug` stack trace, a bad `--lot-size`, and an argparse usage error, which argparse exits with 2.

```
$ pctrade --positions unknown_ticker.csv
pctrade: error: positions: unknown ticker(s) ['XXX']; the universe is ['SPY', 'IWM', 'EFA', 'EEM', 'XLE', 'XLF', 'XLK', 'XLU', 'XLV', 'SHY', 'IEF', 'TLT', 'TIP', 'LQD', 'HYG', 'GLD', 'DBC', 'VNQ']
exit code: 2

$ pctrade --positions negative_quantity.csv
pctrade: error: positions: negative quantity for ['TLT']
exit code: 2

$ pctrade --positions nonpositive_price.csv
pctrade: error: positions: non-positive price for ['TLT']
exit code: 2

$ pctrade --positions duplicate_ticker.csv
pctrade: error: positions: duplicate ticker(s) ['TLT']
exit code: 2

$ pctrade --positions missing_column.csv
pctrade: error: positions: missing column(s) ['price']; expected ['ticker', 'quantity', 'price']
exit code: 2

$ pctrade --positions non_numeric.csv
pctrade: error: positions: non-numeric quantity for ['SPY']
exit code: 2

$ pctrade --positions does_not_exist.csv
pctrade: error: positions file not found: does_not_exist.csv
exit code: 2

$ pctrade --positions good.csv --strategy mv_unconstrained|sample|sample|A --dry-run
pctrade: error: --strategy mv_unconstrained|sample|sample|A: set A is research only; it shorts and levers
exit code: 2

$ pctrade --positions good.csv --strategy not|a|registry|id --dry-run
pctrade: error: --strategy 'not|a|registry|id' is not a registry id
exit code: 2

$ pctrade --positions good.csv --asof 2026-07-30 --dry-run
pctrade: error: --asof 2026-07-30 is not a decision date in the calendar (2010-04-30 to 2026-07-31, last trading day of each month)
exit code: 2

$ pctrade --positions good.csv --asof yesterday --dry-run
pctrade: error: --asof 'yesterday' is not a date
exit code: 2

$ pctrade --positions good.csv --strategy min_variance|lw_cc|none|B --max-turnover 0.1 --dry-run
pctrade: error: --max-turnover applies to set C strategies only; min_variance|lw_cc|none|B is not in set C
exit code: 2

$ pctrade --positions good.csv --lot-size 0 --dry-run
pctrade: error: --lot-size 0.0 is not positive
exit code: 2

$ pctrade --positions negative_quantity.csv --debug
pctrade: error: positions: negative quantity for ['TLT']
Traceback (most recent call last):
  File "C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\cli.py", line 190, in main
    result = plan(args, cfg)
             ^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\cli.py", line 149, in plan
    positions = validate_positions(read_positions(args.positions), tickers)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\trades.py", line 65, in validate_positions
    raise TradeInputError(f"positions: negative quantity for {neg}")
pc.trades.TradeInputError: positions: negative quantity for ['TLT']
exit code: 2

$ pctrade --positions good.csv --cash x
usage: pctrade [-h] --positions POSITIONS [--cash CASH] [--strategy STRATEGY]
               [--asof ASOF] [--max-turnover MAX_TURNOVER]
               [--lot-size LOT_SIZE] [--min-notional MIN_NOTIONAL] [--out OUT]
               [--dry-run] [--debug]
pctrade: error: argument --cash: invalid float value: 'x'
exit code: 2
```

### `pctrade --help`

```
usage: pctrade [-h] --positions POSITIONS [--cash CASH] [--strategy STRATEGY]
               [--asof ASOF] [--max-turnover MAX_TURNOVER]
               [--lot-size LOT_SIZE] [--min-notional MIN_NOTIONAL] [--out OUT]
               [--dry-run] [--debug]

Solve one registry strategy at a decision date and print the trades that take
the book in --positions (columns ticker, quantity, price) plus --cash to its
target weights. The allocator inputs are computed from the pinned data
snapshot committed in data/raw, not from live prices: --asof must be a
decision date of that snapshot's calendar, and a live run needs a fresh pull
(scripts/pull_data.py) first.

options:
  -h, --help            show this help message and exit
  --positions POSITIONS
                        positions CSV with columns ticker, quantity, price
  --cash CASH           cash in the book (default 0)
  --strategy STRATEGY   a registry id, not set A (default
                        mv_constrained|lw_cc|sample|C)
  --asof ASOF           decision date YYYY-MM-DD in the calendar (default the
                        last, 2026-07-31)
  --max-turnover MAX_TURNOVER
                        turnover limit for a set C strategy, replacing
                        mv.max_turnover (0.3)
  --lot-size LOT_SIZE   lot size in shares (default 1)
  --min-notional MIN_NOTIONAL
                        drop trades below this notional (default 1000)
  --out OUT             trades CSV to write (default trades.csv)
  --dry-run             print only, write nothing
  --debug               print the stack trace on an error

Exit codes: 0 success, 2 input error, 1 any other error.
```

### Determinism (rule 9)

`write_turnover_frontier` and `write_answers` were run a second time after the 6.0 commit. `git status --short` was empty afterwards: `turnover_frontier.csv`, `answers.csv` and Chart 4 are byte-identical. `test_demo_reproduces_trades_demo` reruns the demo and compares both example files byte for byte.

## Tests run

`.venv\Scripts\python -m pytest tests/test_trades.py tests/test_cli.py -v --disable-socket -p no:cacheprovider`

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\.venv\Scripts\python.exe
rootdir: C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser
configfile: pyproject.toml
plugins: platformdirs-4.12.2, socket-0.8.1
collecting ... collected 32 items

tests/test_trades.py::test_current_weights_include_universe_zeros PASSED [  3%]
tests/test_trades.py::test_round_trip_synthetic_book PASSED              [  6%]
tests/test_trades.py::test_rounding_never_overshoots[1] PASSED           [  9%]
tests/test_trades.py::test_rounding_never_overshoots[10] PASSED          [ 12%]
tests/test_trades.py::test_rounding_never_overshoots[100] PASSED         [ 15%]
tests/test_trades.py::test_min_notional_filter PASSED                    [ 18%]
tests/test_trades.py::test_negative_cash_repair PASSED                   [ 21%]
tests/test_trades.py::test_sell_never_below_zero PASSED                  [ 25%]
tests/test_trades.py::test_validate_positions_errors[bad0-unknown ticker] PASSED [ 28%]
tests/test_trades.py::test_validate_positions_errors[bad1-negative quantity] PASSED [ 31%]
tests/test_trades.py::test_validate_positions_errors[bad2-non-positive price] PASSED [ 34%]
tests/test_trades.py::test_validate_positions_errors[bad3-duplicate ticker] PASSED [ 37%]
tests/test_trades.py::test_validate_positions_errors[bad4-non-numeric quantity] PASSED [ 40%]
tests/test_trades.py::test_validate_positions_errors[bad5-non-numeric price] PASSED [ 43%]
tests/test_cli.py::test_error_positions_one_line_exit_2[unknown_ticker-rows0-unknown ticker] PASSED [ 46%]
tests/test_cli.py::test_error_positions_one_line_exit_2[negative_quantity-rows1-negative quantity] PASSED [ 50%]
tests/test_cli.py::test_error_positions_one_line_exit_2[nonpositive_price-rows2-non-positive price] PASSED [ 53%]
tests/test_cli.py::test_error_positions_one_line_exit_2[duplicate_ticker-rows3-duplicate ticker] PASSED [ 56%]
tests/test_cli.py::test_error_positions_one_line_exit_2[non_numeric-rows4-non-numeric quantity] PASSED [ 59%]
tests/test_cli.py::test_error_unknown_ticker_exit_2 PASSED               [ 62%]
tests/test_cli.py::test_error_negative_quantity_exit_2 PASSED            [ 65%]
tests/test_cli.py::test_error_nonpositive_price_exit_2 PASSED            [ 68%]
tests/test_cli.py::test_error_duplicate_ticker_exit_2 PASSED             [ 71%]
tests/test_cli.py::test_error_missing_column_exit_2 PASSED               [ 75%]
tests/test_cli.py::test_debug_prints_stack_trace PASSED                  [ 78%]
tests/test_cli.py::test_set_a_strategy_exit_2 PASSED                     [ 81%]
tests/test_cli.py::test_asof_not_a_decision_date_exit_2 PASSED           [ 84%]
tests/test_cli.py::test_max_turnover_on_non_c_strategy_exit_2 PASSED     [ 87%]
tests/test_cli.py::test_dry_run_writes_no_file PASSED                    [ 90%]
tests/test_cli.py::test_max_turnover_005_respected PASSED                [ 93%]
tests/test_cli.py::test_cash_is_fully_invested_by_budget PASSED          [ 96%]
tests/test_cli.py::test_demo_reproduces_trades_demo PASSED               [100%]

============================= 32 passed in 6.55s ==============================
```

Full suite, `.venv\Scripts\python -m pytest --disable-socket -q -p no:cacheprovider`:

```
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
259 passed, 35 warnings in 40.49s
```

## Fresh-clone check

Cloned from GitHub at `4d36dde` into `%TEMP%\pcs6`, `.venv` built as in amendment 2 (`uv venv --seed --python 3.11 .venv`, `pip install -r requirements-lock.txt`, `pip install -e . --no-deps`), then `.venv\Scripts\python -m pytest --disable-socket -q`. The folder was deleted afterwards.

```
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
============================== warnings summary ===============================
tests/test_backtest.py: 16 warnings
tests/test_experiments.py: 19 warnings
  C:\Users\astha\AppData\Local\Temp\pcs6\pc\solver.py:77: UserWarning: Solution may be inaccurate. Try another solver, adjusting the solver settings, or solve with verbose=True for more information.
    prob.solve(solver=name, **_options(name, scfg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
259 passed, 35 warnings in 60.37s (0:01:00)
```

`.venv\Scripts\pctrade --help` from the fresh clone's venv (exit code 0):

```
usage: pctrade [-h] --positions POSITIONS [--cash CASH] [--strategy STRATEGY]
               [--asof ASOF] [--max-turnover MAX_TURNOVER]
               [--lot-size LOT_SIZE] [--min-notional MIN_NOTIONAL] [--out OUT]
               [--dry-run] [--debug]

Solve one registry strategy at a decision date and print the trades that take
the book in --positions (columns ticker, quantity, price) plus --cash to its
target weights. The allocator inputs are computed from the pinned data
snapshot committed in data/raw, not from live prices: --asof must be a
decision date of that snapshot's calendar, and a live run needs a fresh pull
(scripts/pull_data.py) first.

options:
  -h, --help            show this help message and exit
  --positions POSITIONS
                        positions CSV with columns ticker, quantity, price
  --cash CASH           cash in the book (default 0)
  --strategy STRATEGY   a registry id, not set A (default
                        mv_constrained|lw_cc|sample|C)
  --asof ASOF           decision date YYYY-MM-DD in the calendar (default the
                        last, 2026-07-31)
  --max-turnover MAX_TURNOVER
                        turnover limit for a set C strategy, replacing
                        mv.max_turnover (0.3)
  --lot-size LOT_SIZE   lot size in shares (default 1)
  --min-notional MIN_NOTIONAL
                        drop trades below this notional (default 1000)
  --out OUT             trades CSV to write (default trades.csv)
  --dry-run             print only, write nothing
  --debug               print the stack trace on an error

Exit codes: 0 success, 2 input error, 1 any other error.
```

## Runtime per step

| step | runtime |
|---|---|
| 6.0 | `write_turnover_frontier` 48.5 s (second run 74.8 s), 10,000 bootstrap paths included; `write_answers` 0.23 s (second run 0.35 s) |
| 6.1 | the worked synthetic book, under 1 s |
| 6.2 | no separate run |
| 6.3 | one `pctrade` run on the demo book, 3.5 s wall clock (loading the panel, Σ_lw_cc at the decision date, 2 CLARABEL solves) |
| 6.4 | `tests/test_trades.py` and `tests/test_cli.py`, 6.6 s; full suite 40.5 s |
| 6.5 | the demo command, 3.5 s |

## Deviations from PLAN.md

1. **Section 5 tests changed with the step 6.0 decisions** (a change of spec, not of tolerance):
   - `test_turnover_frontier_monotone_turnover`: calls `turnover_frontier(runs, pcfg)`, and asserts the 3 new columns are NaN on the "none" row and ordered (p05 ≤ p95, fraction in [0, 1]) on the τ rows. Every earlier assertion is kept.
   - `test_answers_has_4_rows_with_sources`: row counts per question [6, 4, 6, 4] → [6, 5, 10, 4]. The synthetic `turnover_frontier.csv` gains `n_binding` and the 2 interval columns, with τ = 1.00 below the line but never binding, so the Q2 τ answer is still 0.5 and now also tests decision 9. The synthetic `sensitivity_summary.csv` gains the 3 dates, and the Black-Litterman ratio is asserted at each. The 2 Q2 realised rows are asserted to carry the source row's value and interval.
   - New `test_largest_tau_below_line_nan_when_none_binds`: the Q2 τ answer is NaN when the only points below the line never bind.
2. **`turnover_frontier(runs)` became `turnover_frontier(runs, cfg)`** for the bootstrap settings. `write_turnover_frontier` passes its cfg.
3. **Q2's interval rows** carry p05 and p95 in `answers.csv`, whose columns are fixed. The fraction ≤ 0 is in `turnover_frontier.csv` only. The τ = 0.30 realised row is kept in place and gains its interval, so Q2 has 5 rows, not 6. Q3's 4 `mean_abs_change` rows stay at the last date only. Item 6 of the decisions names only the ratios.
4. **`current_weights(positions, cash)` gained an optional keyword `tickers`**, default the configured universe read from the repo's `config.toml`, as `pc.solver` reads its settings. `generate_trades` passes `cfg.universe.tickers`.
5. **The trades frame is built in 6.1**, because the fixed signature of `generate_trades` returns it. 6.2 added the printed summary (`format_summary`) and `price_warnings`.
6. **Formats I set where none was given:**
   - `quantity` is the absolute number of shares, with `side` BUY or SELL. `notional` is signed, trade × price, negative for a sell. `est_cost` is |notional| × c_i.
   - The printed summary's layout and wording (`pc.trades.format_summary`), then the trades table via `to_string(index=False)` ("no trades" when empty), then "wrote <path>" or "dry run: nothing written".
   - `rounding_slack` = Σ|w_after − w_target|, the slack `test_max_turnover_005_respected` adds to 0.05, and `lots_cut_for_cash` are printed or returned.
   - Errors go to stderr as `pctrade: error: <message>`.
7. **Input errors that exit 2 beyond the 6 in amendment 6.1:** a positions file that is missing or cannot be read as CSV; a non-finite `--cash`; NAV ≤ 0; `--lot-size` ≤ 0; `--min-notional` < 0; a negative or non-finite `--max-turnover`; an `--asof` that is not a date; argparse usage errors, which argparse itself exits with 2. `--max-turnover 0` is accepted.
8. **Cash repair with no buy left.** If post-trade cash is still negative when no buy remains, the loop stops and the summary prints a warning line. This is reachable only with a negative `--cash`, which is accepted because the 6 listed errors do not include it.
9. **The CLI reads the repo's `config.toml` and makes the data paths absolute**, so `pctrade` runs from any folder. `--positions` and `--out` are relative to the working folder.
10. **Demo quantities are floored on the price in the file** (the close rounded to 4 decimals), so the book reproduces from its own columns. Flooring on the unrounded close gives the same 5 quantities: 2683, 21668, 12253, 6356 and 10766, checked in a separate run. The `close` column of the NAV check table shows how close each pair is.
11. **`pc.cli.complete_book` (6.3) cites `decisions/OPEN.md` item 11**, which was written in the 6.5 commit.
12. **Extra tests**, beyond PLAN 6.4 and amendment 6.4:
    - `test_current_weights_include_universe_zeros`;
    - `test_validate_positions_errors` (6 cases);
    - `test_error_positions_one_line_exit_2` (5 cases);
    - `test_error_missing_column_exit_2`;
    - `test_debug_prints_stack_trace`.
13. **`--lot-size` is parsed as a float**, with default 1 from `cli.default_lot_size`. Quantities are written by `%.10g`, so whole numbers print without a decimal point.

## Not verified

1. **`test_demo_reproduces_trades_demo` on Linux.** `weight_target` comes from CLARABEL and is written at 10 significant figures. A different BLAS or CLARABEL build can move it by about 1e-10, which can change the last digit of a weight in `trades_demo.csv` and fail the byte comparison. The quantities would not move: a 1e-10 change in a weight moves target_qty by about 6e-6 shares, and the nearest floor boundary of a traded row is XLK's, 0.058 shares away (raw 9,993.94). The test passed on Windows in the repo and in the fresh clone.
2. **The cause of the small difference between the reviewer's τ intervals and the repo's** (up to 3.5 bp at the ends). The repo's figures come from `pc.stats.stationary_bootstrap_indices` with the draw order in its docstring. How the reviewer drew their paths was not available to check.
3. **No automated test covers the price warning.** It is shown working above, on the stale book.
4. **`pctrade --help` wraps its text to the terminal width** (argparse reads `COLUMNS`), so its line breaks differ between terminals. The text itself does not change.

## Open questions

1. **Open decision 11 (step 6.3): the price of a ticker the target buys but the positions file does not list.** Amendment 6.1 prices every trade from the positions file, and the allocator can buy any of the 18. The demo buys XLK, which the book does not hold, and the all-cash book of `test_cash_is_fully_invested_by_budget` lists no ticker.
   - Option 1 (implemented): a missing ticker is held at quantity 0 and priced at the panel close on the `--asof` decision date, the price amendment 6.2 uses for the warning. `pc.cli.complete_book`.
   - Option 2: the positions file must list all 18 tickers, with quantity 0 where not held. A missing ticker exits 2, and the demo book gains 13 rows.
   No other step depends on the choice beyond the demo files and the all-cash test.

## Files changed

- Added: `decisions/section_6_review.md`, `pc/trades.py`, `pc/cli.py`, `tests/test_trades.py`, `tests/test_cli.py`, `examples/positions_demo.csv`, `examples/trades_demo.csv`, `docs/cli_demo.md`, `review/section_6.md`, `instructions/06_section_6.status.md`.
- Modified: `decisions/OPEN.md` (cleared, then item 11), `pc/experiments.py`, `tests/test_experiments.py`, `outputs/tables/turnover_frontier.csv`, `outputs/tables/answers.csv`.
- Not changed: `outputs/figures/turnover_frontier.png` (regenerated, byte-identical). `CLAUDE.md` and `PLAN.md` were not staged.

## Reviewer reads

1. `decisions/OPEN.md`: item 11.
2. `pc/trades.py`: `generate_trades`, then `format_summary`.
3. `pc/cli.py`: `plan`, `resolve_strategy`, `resolve_asof`, `complete_book`, `main`.
4. `docs/cli_demo.md`, and this file's reconciliation of the 3 demo rows.
5. `pc/experiments.py`: `paired_diff_interval`, `turnover_frontier`, and the Q2 and Q3 blocks of `answers`.
6. `tests/test_cli.py`, `tests/test_trades.py`, and the `test_experiments.py` diff at `b019473`.
