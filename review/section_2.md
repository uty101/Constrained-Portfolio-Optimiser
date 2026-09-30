# Review — Section 2: Covariance estimators and forecast evaluation

## Section

2, Covariance estimators and forecast evaluation (`PLAN.md` Section 2), run from `instructions/02_section_2.md`. Every step, 2.1 to 2.6, is built. No rule 4 stop. One new open item (decision 3, the bootstrap percentile rule) is in `decisions/OPEN.md`; it is implemented as option 1 and both options are printed below.

## Steps completed

- 2.1 `3cd4ed6` `pc/cov.py`: `window_daily`, `cov_sample`, `condition_cov`; `tests/test_cov.py`.
- 2.2 `5e53d15` `pc/cov.py`: `cov_lw_cc`, `cov_lw_identity`; `tests/test_cov_lw.py`.
- 2.3 `9da86e5` `pc/cov.py`: `ewma_weights`, `cov_ewma`; 2 tests in `tests/test_cov.py`.
- 2.4 `a2096dc` `pc/cov.py`: `_pca_corr`, `cov_pca`; 3 tests in `tests/test_cov.py`.
- 2.5 `1795ed8` `pc/cov.py`: `estimate_cov`; `pc/risk.py`: `gmv_closed_form`; 2 tests in `tests/test_cov.py`, `tests/test_risk.py`.
- 2.6 `79bd9cb` `pc/stats.py`: `stationary_bootstrap_indices`; `pc/cov_eval.py`; the 4 CSVs; `tests/test_cov_eval.py`, `tests/test_stats.py`.
- `d80044b` `decisions/OPEN.md`: open decision 3.

## Evidence

### 2.1 Synthetic ridge (cond 1e9 matrix, 18 × 18, eigenvalues logspace(0, −9), seed `run.seed_master`)

```
       cond_before          cond_after          ridge  eig_min_after  eig_max_after  cond_after/1e6 - 1
1.000000000178e+09 999999.999995278777 0.000000999001 0.000001000001 1.000000999001     -0.000000000005
```

### 2.2 Cross-checks against PyPortfolioOpt 1.6.0 and sklearn 1.9.1

Panels: the real daily window at 2010-04-30 (757 rows), and a synthetic Gaussian panel (T = 100, N = 18, seed `run.seed_master`, covariance 1e-4 × (AA′/18 + 0.1 I), A standard normal). `max_rel_diff` is max |ours − ref| / |ref| over all entries. Test tolerances: `np.allclose(ours, ref, rtol=1e-10, atol=0)`; constants to absolute 1e-10.

```
          panel                           check   T       max_abs_diff       max_rel_diff     ours_const      ref_const     const_abs_diff
real_2010_04_30 lw_cc(ddof=1) vs PyPortfolioOpt 757 2.168404344971e-19 1.013476315435e-14 0.022845537636 0.022845537636 0.000000000000e+00
real_2010_04_30          lw_identity vs sklearn 757 1.694065894509e-21 2.020670131563e-16 0.015336294921 0.015336294921 3.469446951954e-18
 synthetic_T100 lw_cc(ddof=1) vs PyPortfolioOpt 100 5.421010862428e-20 1.417237432207e-14 0.180725155737 0.180725155737 2.775557561563e-17
 synthetic_T100          lw_identity vs sklearn 100 2.710505431214e-20 2.489064278082e-16 0.184528081718 0.184528081718 8.326672684689e-17
```

### 2.2 The 50 δ values (ddof 0, production), in draw order

`default_rng(run.seed_master).choice(196, size=50, replace=False)` over the calendar's decision dates, each window `window_daily(returns_d, t, 36)`.

```
   decision_date           delta
0     2022-10-31  0.054934272540
1     2019-10-31  0.021221737532
2     2019-08-30  0.022647752743
3     2026-07-31  0.066430485327
4     2021-07-30  0.057767142037
5     2017-11-30  0.018609589989
6     2015-05-29  0.016460254379
7     2014-06-30  0.019490126238
8     2018-04-30  0.019009460036
9     2017-06-30  0.017171313577
10    2013-11-29  0.017602871204
11    2023-09-29  0.026842615006
12    2016-12-30  0.015745620918
13    2020-04-30  0.075374693597
14    2012-08-31  0.011782362444
15    2012-05-31  0.011434373751
16    2013-03-28  0.012936155510
17    2018-11-30  0.020812686196
18    2017-07-31  0.017609732185
19    2023-12-29  0.026154189779
20    2023-05-31  0.026619015755
21    2026-03-31  0.072369733925
22    2023-11-30  0.026059872882
23    2013-02-28  0.012944324836
24    2012-11-30  0.012502588426
25    2017-05-31  0.017167472943
26    2023-02-28  0.056820288214
27    2021-05-28  0.058941548805
28    2015-01-30  0.014109631128
29    2020-07-31  0.062393749192
30    2024-06-28  0.027602504209
31    2016-01-29  0.016103248809
32    2010-08-31  0.021083562512
33    2018-01-31  0.020837884307
34    2016-06-30  0.015165144031
35    2014-10-31  0.015893023013
36    2019-06-28  0.024749818241
37    2025-10-31  0.067754467760
38    2011-06-30  0.024321399948
39    2014-02-28  0.017608814679
40    2018-06-29  0.019423591300
41    2020-08-31  0.062670368221
42    2025-03-31  0.033149331295
43    2024-02-29  0.026919497472
44    2012-12-31  0.012534956115
45    2020-05-29  0.070361343529
46    2013-10-31  0.017161567092
47    2010-05-28  0.021660959408
48    2012-04-30  0.011516255458
49    2022-05-31  0.057022306565
```

### 2.2 δ over all 196 dates (`cov_diagnostics.csv`, `lw_cc`)

```
  n           min         median          max
196 0.01127626535 0.021907127415 0.0897529854
    decision_date       lw_delta
105    2012-06-29  0.01127626535
477    2020-03-31  0.08975298540
```

### 2.3 EWMA (2010-04-30 window, λ = 0.97)

`lambda_1e-12_max_abs_diff` is max |`cov_ewma(X, 1e-12)` − outer(last row)|. The row before the last carries weight about 1e-12, so a difference near 1e-15 is the formula, not rounding.

```
 n_rows  weight_sum     weight_sum - 1         w_last        w_first  lambda_1e-12_max_abs_diff
    757         1.0 2.220446049250e-16 0.030000000003 0.000000000003         1.066421256857e-15
```

### 2.4 PCA (2010-04-30 window, daily units)

```
 k3_min_eig_daily  k3_max_eig_daily  k3_Rf_diag_max_abs_dev_from_1  kN_max_abs_diff_vs_sample  kN_max_rel_diff_vs_sample
   0.000000760827      0.0054165861                            0.0         8.673617379884e-19         2.072492701316e-14
```

### 2.5 `estimate_cov` log dict at the first decision date (2010-04-30)

```
estimator        cond_before         cond_after  ridge       lw_delta
   sample  9254.777547822507  9254.777547822507    0.0            NaN
    lw_cc  7961.615557735537  7961.615557735537    0.0 0.022906012315
     ewma 11390.369965097643 11390.369965097643    0.0            NaN
    pca3  7119.336709857510  7119.336709857510    0.0            NaN
```

### Conditioning over all 196 dates (`cov_diagnostics.csv`, 784 rows)

No date needed a ridge for any estimator. The largest condition number is 82,458 (ewma, 2011-11-30), against the 1e6 limit.

```
             n  n_ridged     max_cond_before      max_cond_after
estimator                                                       
sample     196         0  28048.937020000001  28048.937020000001
lw_cc      196         0  25201.282700000000  25201.282700000000
ewma       196         0  82457.569090000005  82457.569090000005
pca3       196         0  26693.118030000001  26693.118030000001
ridged rows: 0
Empty DataFrame
Columns: [decision_date, estimator, cond_before, cond_after, ridge, lw_delta]
Index: []
rows with max cond_before per estimator:
    decision_date estimator         cond_before          cond_after  ridge       lw_delta
200    2014-06-30    sample  28048.937020000001  28048.937020000001      0            NaN
201    2014-06-30     lw_cc  25201.282700000000  25201.282700000000      0  0.01949012624
78     2011-11-30      ewma  82457.569090000005  82457.569090000005      0            NaN
207    2014-07-31      pca3  26693.118030000001  26693.118030000001      0            NaN
```

### `cov_eval.csv` (12 rows)

```
   estimator portfolio_set    n    qlike_mean    bias_ratio       band_lo      band_hi    mean_cond_before  n_ridged
0     sample            ew  196  -5.854661547  0.9646851140  0.9169149532  1.083085047  10548.367930000000         0
1     sample           gmv  196 -10.942003120  1.0494752780  0.9169149532  1.083085047  10548.367930000000         0
2     sample        random  196  -5.843165867  0.9631098923  0.9169149532  1.083085047  10548.367930000000         0
3      lw_cc            ew  196  -5.854210941  0.9685827748  0.9169149532  1.083085047   8675.543245000001         0
4      lw_cc           gmv  196 -10.901352070  1.0115322080  0.9169149532  1.083085047   8675.543245000001         0
5      lw_cc        random  196  -5.843014832  0.9658382975  0.9169149532  1.083085047   8675.543245000001         0
6       ewma            ew  196  -6.093641089  1.0398864340  0.9169149532  1.083085047  17974.809340000000         0
7       ewma           gmv  196 -10.451709690  1.3809373180  0.9169149532  1.083085047  17974.809340000000         0
8       ewma        random  196  -6.062970573  1.0412851580  0.9169149532  1.083085047  17974.809340000000         0
9       pca3            ew  196  -5.862029684  0.9488220945  0.9169149532  1.083085047   8430.163060999999         0
10      pca3           gmv  196 -10.536558710  1.1516630020  0.9169149532  1.083085047   8430.163060999999         0
11      pca3        random  196  -5.849161804  0.9491293462  0.9169149532  1.083085047   8430.163060999999         0
```

### `cov_eval_qlike_diff.csv` (9 rows)

Per date, QLIKE_est − QLIKE_lw_cc on the same set; mean over dates; bootstrap from `stationary_bootstrap_indices(196, 6, 10000, run.bootstrap_seed)`. Negative means the estimator beats `lw_cc`.

```
  estimator portfolio_set   diff_vs_lw_cc             p05             p95  frac_le_0
0    sample            ew -0.000450605517 -0.005818476447  0.003253250541     0.5300
1    sample           gmv -0.040651048540 -0.084656670720  0.006012464275     0.9247
2    sample        random -0.000151034590 -0.003789467032  0.002424147890     0.4883
3      ewma            ew -0.239430147700 -0.575783130200 -0.005263228895     0.9566
4      ewma           gmv  0.449642387300 -0.068783463460  1.239742617000     0.1193
5      ewma        random -0.219955741200 -0.519770091400 -0.009363542933     0.9636
6      pca3            ew -0.007818742778 -0.039208256680  0.011578760580     0.6423
7      pca3           gmv  0.364793359500  0.267049939000  0.476043262500     0.0000
8      pca3        random -0.006146972381 -0.031731329940  0.009584543613     0.6418
```

### Open decision 3: p05 and p95 under both percentile rules

Option 1 (`linear`) is what the CSV holds.

```
  estimator portfolio_set    p05_linear  p05_inverted_cdf    p95_linear  p95_inverted_cdf
0    sample            ew -0.0058184765     -0.0058200163  0.0032532505      0.0032532443
1    sample           gmv -0.0846566706     -0.0846587856  0.0060124647      0.0060112601
2    sample        random -0.0037894670     -0.0037914342  0.0024241479      0.0024239508
3      ewma            ew -0.5757831302     -0.5759523133 -0.0052632289     -0.0052650406
4      ewma           gmv -0.0687834635     -0.0688853841  1.2397426166      1.2397298579
5      ewma        random -0.5197700913     -0.5198137221 -0.0093635429     -0.0093695239
6      pca3            ew -0.0392082567     -0.0392098706  0.0115787606      0.0115785802
7      pca3           gmv  0.2670499388      0.2670337771  0.4760432624      0.4760428822
8      pca3        random -0.0317313299     -0.0317382823  0.0095845436      0.0095845234
```

### Per-date QLIKE for `ew`, first and last 5 dates (from `cov_eval_by_date.csv`)

```
estimator           sample        lw_cc         ewma         pca3
decision_date                                                    
2010-04-30    -4.679031597 -4.678512836 -2.727141557 -4.679617710
2010-05-28    -5.079775829 -5.084673794 -5.246743109 -5.071589009
2010-06-30    -5.208911548 -5.214687734 -5.455947370 -5.199331320
2010-07-30    -5.324836067 -5.332246583 -5.792178791 -5.312501279
2010-08-31    -5.488040863 -5.496650070 -6.259275643 -5.473749669
2026-03-31    -6.635678420 -6.636424109 -6.567278845 -6.619828142
2026-04-30    -6.771486261 -6.772205921 -6.783397432 -6.750731828
2026-05-29    -6.184121221 -6.183948014 -6.119746384 -6.190359555
2026-06-30    -6.883900976 -6.884228710 -6.947626936 -6.850349260
2026-07-31    -6.951269043 -6.951489967 -7.161293625 -6.915526835
```

### `cov_eval_by_date.csv`, `ew` × `lw_cc`, first and last 5 rows

```
     decision_date estimator portfolio_set      sigma2_hat  sigma2_realised             r_h        qlike
3       2010-04-30     lw_cc            ew  0.003239495972   0.003413860835 -0.066808860130 -4.678512836
15      2010-05-28     lw_cc            ew  0.003647779838   0.001929539712 -0.004763454734 -5.084673794
27      2010-06-30     lw_cc            ew  0.003521714101   0.001528845515  0.065479562590 -5.214687734
39      2010-07-30     lw_cc            ew  0.003695592759   0.000991777848 -0.008573569444 -5.332246583
51      2010-08-31     lw_cc            ew  0.003514376876   0.000542067945  0.042995742200 -5.496650070
2295    2026-03-31     lw_cc            ew  0.000653646569   0.000455277685  0.041109003430 -6.636424109
2307    2026-04-30     lw_cc            ew  0.000624513546   0.000378662308  0.013569080060 -6.772205921
2319    2026-05-29     lw_cc            ew  0.000652510078   0.000750866811 -0.006461030670 -6.183948014
2331    2026-06-30     lw_cc            ew  0.000694599191   0.000269467584  0.010749838180 -6.884228710
2343    2026-07-31     lw_cc            ew  0.000654545600   0.000248779257  0.017624506520 -6.951489967
```

### 2020-03-31, `ew` × `lw_cc`, worked by hand from the raw daily returns

Computed without `pc`: prices read with `csv.DictReader` from `data/raw/prices_adjclose.csv`, daily returns as p_d/p_{d−1} − 1, window (2017-03-31, 2020-03-31], and LW constant correlation with ddof 0 written as explicit sums over i, j and t straight from the LW 2004 formulas (π̂_ij = (1/T)Σ_t((x_ti x_tj − s_ij)²), θ̂_ii,ij = (1/T)Σ_t(x_ti² − s_ii)(x_ti x_tj − s_ij), ρ̂ with the ½(…) symmetric form). Σ monthly = 21 × (δF + (1 − δ)S); no ridge (cond 8,183.5). σ̂² = (1/18)²1′Σ1 × 21/21.

```
window: 2017-04-03 .. 2020-03-31, T = 754; r_bar = 0.29834622674203887; pi_hat = 0.00011899628258651827; rho_hat = 4.3264395592342884e-05; gamma_hat = 1.1190732873880127e-06; delta = 0.08975298540252173
w'Sigma w (monthly) = 0.0011535105880842865; exec 2020-04-01, next_exec 2020-05-01, n_hold_days = 21 (calendar: 21)
          date  ew_daily_return         squared
0   2020-04-02   0.019791354196  0.000391697701
1   2020-04-03  -0.009705645075  0.000094199546
2   2020-04-06   0.040766311241  0.001661892132
3   2020-04-07   0.000694742061  0.000000482667
4   2020-04-08   0.023139253353  0.000535425046
5   2020-04-09   0.021722790914  0.000471879645
6   2020-04-13  -0.009066840735  0.000082207601
7   2020-04-14   0.012521034505  0.000156776305
8   2020-04-15  -0.016682687443  0.000278312060
9   2020-04-16  -0.002208195460  0.000004876127
10  2020-04-17   0.019377467633  0.000375486252
11  2020-04-20  -0.012622092558  0.000159317221
12  2020-04-21  -0.017405712604  0.000302958831
13  2020-04-22   0.014366467454  0.000206395387
14  2020-04-23   0.001154959411  0.000001333931
15  2020-04-24   0.004678383221  0.000021887270
16  2020-04-27   0.008560836190  0.000073287916
17  2020-04-28   0.002964440428  0.000008787907
18  2020-04-29   0.018167245462  0.000330048808
19  2020-04-30  -0.011343847215  0.000128682870
20  2020-05-01  -0.018685165419  0.000349135407
                 source      sigma2_hat  sigma2_realised             r_h           qlike
0               by hand  0.001153510588   0.005635070629  0.090185099562 -1.879796705828
1  cov_eval_by_date.csv  0.001153510588   0.005635070629  0.090185099560 -1.879796706000
abs diff: {'sigma2_hat': 8.42865274103266e-14, 'sigma2_realised': 2.4158539752017205e-13, 'r_h': 2.0118212651354384e-12, 'qlike': 1.7246248873448167e-10}
cov_diagnostics row:
    decision_date estimator  cond_before   cond_after  ridge      lw_delta
477    2020-03-31     lw_cc  8183.525874  8183.525874      0  0.0897529854
```

The differences are the `%.10g` rounding of the CSV. The hand δ equals the `cov_diagnostics.csv` δ for that date.

### `stationary_bootstrap_indices(196, 6, 10000, run.bootstrap_seed)`: first 3 replications × first 20 indices

```
(7.33 s, shape (10000, 196), dtype int64)
       0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17   18   19
rep0  114  115  116  117   81   82   83   84   85   86   87   88   89   90   91   38   39   38   39   40
rep1  132  133  134  135  136   96   17   18   19   20   21   22   23   24   25   26   27   28   29   59
rep2  153  154  155  156  157  158  159  184  185  186  187  188  189  190  191  192  193  194  132  175
```

### Determinism

`write_cov_eval` run twice in a row: the SHA-256 of all 4 CSVs was identical (`identical: True`).

## Tests run

`.venv\Scripts\python -m pytest --disable-socket -v`

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.12.2, socket-0.8.1
collecting ... collected 43 items

tests/test_calendar.py::test_calendar_has_196_rows PASSED                [  2%]
tests/test_calendar.py::test_first_decision_2010_04_30 PASSED            [  4%]
tests/test_calendar.py::test_last_decision_2026_07_31 PASSED             [  6%]
tests/test_calendar.py::test_exec_date_is_next_trading_day PASSED        [  9%]
tests/test_calendar.py::test_decision_dates_are_trading_days PASSED      [ 11%]
tests/test_config.py::test_config_keys_match_fields PASSED               [ 13%]
tests/test_config.py::test_w_mkt_sums_to_one PASSED                      [ 16%]
tests/test_config.py::test_one_way_bp_tickers PASSED                     [ 18%]
tests/test_cov.py::test_window_boundaries_exclusive_start_inclusive_end PASSED [ 20%]
tests/test_cov.py::test_ridge_sets_cond_to_1e6 PASSED                    [ 23%]
tests/test_cov.py::test_condition_cov_noop_when_well_conditioned PASSED  [ 25%]
tests/test_cov.py::test_condition_cov_nonpositive_eigenvalue_is_inf_and_ridged PASSED [ 27%]
tests/test_cov.py::test_ewma_weights_sum_to_one PASSED                   [ 30%]
tests/test_cov.py::test_ewma_lambda_near_zero_is_last_outer_product PASSED [ 32%]
tests/test_cov.py::test_pca_rf_unit_diagonal PASSED                      [ 34%]
tests/test_cov.py::test_pca_positive_definite PASSED                     [ 37%]
tests/test_cov.py::test_pca_full_rank_equals_sample PASSED               [ 39%]
tests/test_cov.py::test_monthly_is_daily_times_21_exactly PASSED         [ 41%]
tests/test_cov.py::test_conditioning_log_fields_always_present PASSED    [ 44%]
tests/test_cov_eval.py::test_random_portfolios_fixed_and_long_only PASSED [ 46%]
tests/test_cov_eval.py::test_qlike_on_synthetic_perfect_forecast PASSED  [ 48%]
tests/test_cov_eval.py::test_bias_band_formula PASSED                    [ 51%]
tests/test_cov_lw.py::test_lw_cc_matches_pypfopt[real_2010_04_30] PASSED [ 53%]
tests/test_cov_lw.py::test_lw_cc_matches_pypfopt[synthetic_T100] PASSED  [ 55%]
tests/test_cov_lw.py::test_lw_identity_matches_sklearn[real_2010_04_30] PASSED [ 58%]
tests/test_cov_lw.py::test_lw_identity_matches_sklearn[synthetic_T100] PASSED [ 60%]
tests/test_cov_lw.py::test_lw_cc_delta_in_unit_interval PASSED           [ 62%]
tests/test_data.py::test_load_prices_shape_and_order PASSED              [ 65%]
tests/test_data.py::test_load_prices_no_nan_from_panel_start PASSED      [ 67%]
tests/test_data.py::test_panel_start_is_first_full_row PASSED            [ 69%]
tests/test_data.py::test_rf_uses_previous_day_and_ffill PASSED           [ 72%]
tests/test_data.py::test_validate_flags_each_issue_type PASSED           [ 74%]
tests/test_data.py::test_data_summary_columns_and_rows PASSED            [ 76%]
tests/test_data.py::test_data_summary_annualisation PASSED               [ 79%]
tests/test_data.py::test_corr_full_sample_symmetric_unit_diagonal PASSED [ 81%]
tests/test_manifest.py::test_manifest_hashes_match PASSED                [ 83%]
tests/test_placeholder.py::test_placeholder PASSED                       [ 86%]
tests/test_returns.py::test_compounded_daily_equals_holding_return PASSED [ 88%]
tests/test_returns.py::test_rf_constant_5pct_gives_005_over_252 PASSED   [ 90%]
tests/test_returns.py::test_monthly_excess_2020_03_manual PASSED         [ 93%]
tests/test_risk.py::test_gmv_closed_form_sums_to_one PASSED              [ 95%]
tests/test_stats.py::test_bootstrap_indices_shape_and_determinism PASSED [ 97%]
tests/test_stats.py::test_bootstrap_indices_follow_the_fixed_draw_order PASSED [100%]

============================= 43 passed in 9.35s ==============================
```

## Fresh-clone check

Standing rule (amendment 3): `git clone https://github.com/uty101/Constrained-Portfolio-Optimiser.git %TEMP%\pcs2` at `d80044b`, `uv venv --seed --python 3.11 .venv`, `.venv\Scripts\python -m pip install -r requirements-lock.txt`, `.venv\Scripts\python -m pip install -e . --no-deps`, then `.venv\Scripts\python -m pytest --disable-socket -q`. Both installs printed nothing under `-q`. Full pytest output:

```
d80044b section 2: open decision 3 (bootstrap percentile rule)
...........................................                              [100%]
43 passed in 19.57s
```

The folder was deleted afterwards (`removed: True`).

## Runtime per step

| step | runtime |
|---|---|
| 2.1 | tests 0.7 s |
| 2.2 | tests 5.0 s |
| 2.3 | tests 0.9 s (with 2.1) |
| 2.4 | tests 0.7 s (with 2.1 to 2.3) |
| 2.5 | tests 1.2 s (`test_cov.py` and `test_risk.py`) |
| 2.6 | `write_cov_eval`, all 196 dates × 4 estimators plus the 10,000-rep bootstrap: 5.4 s on the first run, 8.4 s in the evidence run. `stationary_bootstrap_indices(196, 6, 10000)` alone: 7.3 s. The machine was under varying load; these are wall-clock times of single runs. |

## Deviations from PLAN.md

None in method. Points the reviewer should see:

1. **Helpers not in kickoff Section 6.** `pc/cov.py`: `ewma_weights` (the EWMA weights, used by the weight-sum test), `_pca_corr` (R_f, used by the unit-diagonal test), `_daily_estimate` and `_monthly_unconditioned` (the matrix before `condition_cov`, which `test_monthly_is_daily_times_21_exactly` compares with `==`, per amendment 2.5). `pc/cov_eval.py`: `random_portfolios`, `qlike`, `bias_band`, `holding_period_stats`, `run_cov_eval`, `write_cov_eval`. `estimate_cov` is the composition `condition_cov(_monthly_unconditioned(...))`.
2. **Extra tests.** `test_condition_cov_nonpositive_eigenvalue_is_inf_and_ridged` (amendment 2.1's λ_min ≤ 0 rule) and `test_bootstrap_indices_follow_the_fixed_draw_order` (amendment 2.6's draw order, replayed by hand on a small case). The two cross-check tests are parametrised over the 2 panels of amendment 2.2, so they appear as 4 test items.
3. **Tolerances I set where `PLAN.md` gives none.** EWMA λ = 1e-12 against the last outer product: `rtol=1e-10, atol=1e-14`. My first version had `rtol=0, atol=1e-15` and failed at 1.07e-15, which is the weight of about 1e-12 on the row before the last (see the 2.3 evidence), so the tolerance was set before the test was first committed. PCA k = N against sample: `rtol=1e-10, atol=0`. R_f diagonal: absolute 1e-14. GMV sum to 1: absolute 1e-12. Random portfolios sum to 1: absolute 1e-12.
4. **`BAND_Z = 1.645` is a literal in `pc/cov_eval.py`**, taken from the formula in kickoff 5.6 (1 ± 1.645√(1/(2n))), not from `config.toml`. It is not derived from `bootstrap.ci`; `norm.ppf(0.95)` is 1.6448536…, which would move the band in the 8th decimal. Flagged against rule 6 for the reviewer; not changed.
5. **Synthetic cross-check panel.** Amendment 2.2 asks for "a random positive definite covariance". Built as 1e-4 × (AA′/18 + 0.1 I), A 18 × 18 standard normal, drawn from the same `default_rng(run.seed_master)` stream before the 100 rows.
6. **`_pca_corr` symmetrises V_kΛ_kV_k′** as ½(L + L′) before adding the diagonal. Without it the product was asymmetric at about 1e-19 and `test_pca_positive_definite`, which asserts exact symmetry, failed. All evidence above was produced after the change.
7. **`cov_eval_by_date.csv` row order** is decision_date, then estimator in config order, then portfolio_set (ew, gmv, random). 2,352 rows.
8. **`cov_lw_cc` arithmetic.** Written from the formulas; it evaluates 2·M∘S (M = Xm′Xm/T) where PyPortfolioOpt evaluates 2·(Xm′Xm)∘S/T. The differences are the 1e-14 relative shown above.

## Not verified

- The ridge path of `condition_cov` never ran on real data: no date and estimator reached cond 1e6 (max 82,458). It is covered only by the two synthetic tests.
- `lw_identity` is cross-checked only against sklearn 1.9.1; it is not used anywhere else, as specified.
- The bias-ratio band assumes r_h/σ̂_h is iid over dates; this is the kickoff formula and was not tested against the bootstrap.

## Open questions

Appended to `decisions/OPEN.md`:

3. **Step 2.6: percentile rule for the bootstrap 90% interval** (implemented as option 1, needs confirming; the same rule will apply to step 4.4).
   - Option 1 (implemented): `np.quantile(boot, ci)`, linear interpolation (Hyndman-Fan type 7).
   - Option 2: `np.quantile(boot, ci, method="inverted_cdf")`, empirical quantile with no interpolation (type 1).

   Both sets of values are printed above; the largest difference is 1.0e-4 (ewma × gmv, p05).

Also for the reviewer, not appended because the kickoff fixes it: deviation 4 (`BAND_Z` literal).

## Files changed

Added:
- `pc/cov.py`
- `pc/risk.py`
- `pc/stats.py`
- `pc/cov_eval.py`
- `tests/test_cov.py`
- `tests/test_cov_lw.py`
- `tests/test_risk.py`
- `tests/test_cov_eval.py`
- `tests/test_stats.py`
- `outputs/tables/cov_eval.csv`
- `outputs/tables/cov_eval_qlike_diff.csv`
- `outputs/tables/cov_eval_by_date.csv`
- `outputs/tables/cov_diagnostics.csv`
- `review/section_2.md`
- `instructions/02_section_2.status.md`

Modified:
- `decisions/OPEN.md` (open decision 3)

Not touched, per `instructions/02_section_2.md`: `CLAUDE.md`, `PLAN.md`.

## Reviewer reads

1. `pc/cov.py`: `cov_lw_cc` (the ddof rule), `condition_cov`, `estimate_cov`.
2. `tests/test_cov_lw.py` and the 2.2 cross-check table above.
3. `pc/cov_eval.py`: `run_cov_eval` (the random set's per-portfolio then mean aggregation, and the QLIKE difference bootstrap).
4. `pc/stats.py`: `stationary_bootstrap_indices` against amendment 2.6.
5. The 2020-03-31 hand calculation above.
6. `outputs/tables/cov_eval.csv` and `cov_eval_qlike_diff.csv`.
7. `decisions/OPEN.md` item 3.
