# Review — Section 1: Data, calendar and returns

## Section

1, Data, calendar and returns (`PLAN.md` Section 1). Stopped at step 1.6 under rule 1: 1.1 to 1.5 are built, 1.6 is not.

## Steps completed

- 1.1 `cd30b4f` `pc/config.py`: `Config` (one frozen dataclass per table) and `load_config`; `tests/test_config.py`.
- 1.2 `897f22c` `scripts/pull_data.py`, the three `data/raw/` files, `.gitattributes`; `tests/test_manifest.py`.
- 1.3 `8cb0bce` `pc/data.py`: `load_prices`, `load_rf_daily`, `validate_prices`; `outputs/tables/data_issues.csv`; `tests/test_data.py`.
- 1.4 `45efc5d` `pc/calendar.py`: `build_calendar`; `tests/test_calendar.py`.
- 1.5 `dc80e08` `pc/returns.py`: `daily_returns`, `monthly_excess_returns`, `holding_returns`, `holding_rf`; `tests/test_returns.py`.
- 1.6 not built. Blocked by open decision 1 in `decisions/OPEN.md` (annualisation convention, first raised as item 3a of `instructions/00_kickoff.status.md`).
- `f11ee89` `decisions/OPEN.md`: open decisions 1 and 2.

## Evidence

### 1.1 Loaded Config (dict fields in config ticker order)

`pprint(load_config(), sort_dicts=False)`:

```
Config(run=RunConfig(seed_master=20260930,
                     bootstrap_seed=20260930,
                     cov_eval_seed=20260931,
                     sensitivity_seed=20260932),
       universe=UniverseConfig(tickers=('SPY', 'IWM', 'EFA', 'EEM', 'XLE', 'XLF', 'XLK', 'XLU', 'XLV', 'SHY',
                                        'IEF', 'TLT', 'TIP', 'LQD', 'HYG', 'GLD', 'DBC', 'VNQ'),
                               asset_class={'SPY': 'US equity',
                                            'IWM': 'US equity',
                                            'EFA': 'International equity',
                                            'EEM': 'International equity',
                                            'XLE': 'US sectors',
                                            'XLF': 'US sectors',
                                            'XLK': 'US sectors',
                                            'XLU': 'US sectors',
                                            'XLV': 'US sectors',
                                            'SHY': 'Treasuries',
                                            'IEF': 'Treasuries',
                                            'TLT': 'Treasuries',
                                            'TIP': 'Inflation linked',
                                            'LQD': 'Credit',
                                            'HYG': 'Credit',
                                            'GLD': 'Real assets',
                                            'DBC': 'Real assets',
                                            'VNQ': 'Real assets'}),
       sample=SampleConfig(price_start='2007-04-11',
                           price_end='2026-09-15',
                           first_decision='2010-04-30',
                           last_decision='2026-07-31',
                           window_months=36,
                           days_per_month=21,
                           expected_n_decisions=196),
       data=DataConfig(prices_csv='data/raw/prices_adjclose.csv',
                       rf_csv='data/raw/rf_dgs3mo.csv',
                       manifest='data/raw/MANIFEST.json',
                       max_abs_daily_return_flag=0.25,
                       max_gap_days_flag=4),
       cov=CovConfig(estimators=('sample', 'lw_cc', 'ewma', 'pca3'),
                     ewma_lambda=0.97,
                     pca_k=3,
                     max_cond=1000000.0),
       mv=MvConfig(gamma=2.5, upper=0.3, lower=0.0, max_turnover=0.3),
       costs=CostsConfig(cost_scales=(0.0, 1.0, 3.0),
                         one_way_bp={'SPY': 3,
                                     'IWM': 3,
                                     'EFA': 3,
                                     'EEM': 6,
                                     'XLE': 3,
                                     'XLF': 3,
                                     'XLK': 3,
                                     'XLU': 3,
                                     'XLV': 3,
                                     'SHY': 3,
                                     'IEF': 3,
                                     'TLT': 3,
                                     'TIP': 6,
                                     'LQD': 3,
                                     'HYG': 6,
                                     'GLD': 3,
                                     'DBC': 6,
                                     'VNQ': 6}),
       bl=BlConfig(delta=2.5,
                   tau=0.0277777777777778,
                   mom_lookback=12,
                   mom_skip=1,
                   n_long_short=6,
                   equity_basket=('SPY', 'IWM', 'EFA', 'EEM'),
                   bond_basket=('SHY', 'IEF', 'TLT'),
                   w_mkt={'SPY': 0.19,
                          'IWM': 0.04,
                          'EFA': 0.12,
                          'EEM': 0.05,
                          'XLE': 0.02,
                          'XLF': 0.02,
                          'XLK': 0.02,
                          'XLU': 0.02,
                          'XLV': 0.02,
                          'SHY': 0.05,
                          'IEF': 0.09,
                          'TLT': 0.08,
                          'TIP': 0.04,
                          'LQD': 0.08,
                          'HYG': 0.04,
                          'GLD': 0.04,
                          'DBC': 0.03,
                          'VNQ': 0.05}),
       solver=SolverConfig(primary='CLARABEL',
                           fallback='SCS',
                           scs_eps=1e-09,
                           rp_ftol=1e-15,
                           rp_gtol=1e-12,
                           rp_maxiter=10000),
       cov_eval=CovEvalConfig(n_random=100),
       bootstrap=BootstrapConfig(mean_block=6, reps=10000, ci=(0.05, 0.95)),
       sensitivity=SensitivityConfig(dates=('2012-12-31', '2020-02-28', '2026-07-31'), draws=1000),
       turnover_grid=TurnoverGridConfig(taus=(0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0), include_none=True),
       positions=PositionsConfig(threshold=0.005),
       cli=CliConfig(default_lot_size=1, default_min_notional=1000.0, price_warn_pct=0.05),
       outputs=OutputsConfig(results_dir='outputs/results',
                             tables_dir='outputs/tables',
                             figures_dir='outputs/figures'))
```

`pytest tests/test_config.py -v`:

```
tests/test_config.py::test_config_keys_match_fields PASSED               [ 33%]
tests/test_config.py::test_w_mkt_sums_to_one PASSED                      [ 66%]
tests/test_config.py::test_one_way_bp_tickers PASSED                     [100%]
======================== 3 passed, 1 warning in 0.03s =========================
```

### 1.2 MANIFEST.json in full

```
{
  "pulled_at_utc": "2026-09-30T14:52:35Z",
  "yfinance_version": "1.7.0",
  "sources": {
    "prices": "yfinance download, auto_adjust=True, Close",
    "rf": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO"
  },
  "range": {
    "start": "2007-04-11",
    "end": "2026-09-15"
  },
  "row_counts": {
    "prices_adjclose.csv": 4889,
    "rf_dgs3mo.csv": 5070
  },
  "tickers": {
    "SPY": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "IWM": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "EFA": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "EEM": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "XLE": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "XLF": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "XLK": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "XLU": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "XLV": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "SHY": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "IEF": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "TLT": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "TIP": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "LQD": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "HYG": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "GLD": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "DBC": {"first_date": "2007-04-11", "last_date": "2026-09-15"},
    "VNQ": {"first_date": "2007-04-11", "last_date": "2026-09-15"}
  },
  "sha256": {
    "prices_adjclose.csv": "eec844cad43481d8567ff8e06a63b1b758e9a30baac6223093e023547e6bc3db",
    "rf_dgs3mo.csv": "af623ba0928595927199cecd6f11afe78a95a1d4831717dd85c549f23269dedc"
  }
}
```

The file on disk is 2-space indented with one key per line; the `tickers` block is shown with each ticker on one line here for length. The values are unchanged.

### 1.2 Per-ticker first and last dates

```
        first_date   last_date
ticker                        
SPY     2007-04-11  2026-09-15
IWM     2007-04-11  2026-09-15
EFA     2007-04-11  2026-09-15
EEM     2007-04-11  2026-09-15
XLE     2007-04-11  2026-09-15
XLF     2007-04-11  2026-09-15
XLK     2007-04-11  2026-09-15
XLU     2007-04-11  2026-09-15
XLV     2007-04-11  2026-09-15
SHY     2007-04-11  2026-09-15
IEF     2007-04-11  2026-09-15
TLT     2007-04-11  2026-09-15
TIP     2007-04-11  2026-09-15
LQD     2007-04-11  2026-09-15
HYG     2007-04-11  2026-09-15
GLD     2007-04-11  2026-09-15
DBC     2007-04-11  2026-09-15
VNQ     2007-04-11  2026-09-15
```

### 1.2 First and last 5 rows of prices_adjclose.csv

```
         date         SPY        IWM        EFA        EEM        XLE        XLF       XLK        XLU        XLV        SHY        IEF        TLT        TIP        LQD        HYG        GLD        DBC        VNQ
0  2007-04-11  100.871841  61.885883  43.530628  26.826193  17.246683  19.770695  9.161511  10.420311  24.636581  57.274708  50.341267  47.685375  56.019489  49.468285  31.223076  67.080002  20.637653  35.188858
1  2007-04-12  101.320145  62.302052  43.821274  27.274704  17.510653  19.737383  9.258479  10.374465  24.914837  57.267502  50.390163  47.696285  56.019489  49.542789  31.244022  66.989998  20.759478  34.949398
2  2007-04-13  101.782356  62.702778  43.966610  27.408587  17.518986  19.820665  9.266236  10.371915  25.278717  57.238914  50.304607  47.548904  55.879772  49.459023  31.187187  67.839996  20.873188  35.344070
3  2007-04-16  102.748924  63.565952  44.430519  27.734381  17.621796  20.303688  9.343808  10.433044  25.521301  57.231785  50.359585  47.810886  56.058685  49.500896  31.175205  68.400002  20.710749  35.388435
4  2007-04-17  103.022079  63.373295  44.436115  27.584873  17.521770  20.298136  9.363206  10.481444  25.599789  57.324738  50.573425  48.078335  56.092205  49.770760  31.160231  68.000000  20.499580  35.849636
            date         SPY         IWM         EFA        EEM        XLE        XLF         XLK        XLU         XLV        SHY        IEF        TLT         TIP         LQD        HYG         GLD        DBC        VNQ
4884  2026-09-09  760.511536  289.882904  106.559998  68.480003  64.924088  56.858768  187.651001  42.626568  165.944901  81.629997  91.900002  81.730003  106.800003  105.309998  78.980003  403.350006  32.849998  94.123657
4885  2026-09-10  755.952820  286.950562  105.660004  67.000000  64.546333  56.669437  185.004105  42.209637  165.028412  81.419998  91.180000  80.779999  106.330002  104.360001  78.620003  396.359985  33.619999  93.310707
4886  2026-09-11  762.396790  288.137482  106.699997  67.839996  64.755096  57.048096  187.451248  42.080585  164.729553  81.370003  91.010002  80.870003  105.839996  104.320000  78.599998  398.769989  33.160000  93.984856
4887  2026-09-14  758.995239  287.160004  105.849998  65.989998  64.148697  56.828873  184.065201  41.514744  167.110443  81.339996  90.930000  80.930000  105.820000  104.300003  78.529999  392.839996  33.150002  93.518898
4888  2026-09-15  755.513916  285.140015  105.400002  65.760002  65.540428  56.649506  183.525833  41.018394  167.020798  81.309998  90.820000  80.709999  105.790001  104.279999  78.379997  394.149994  33.680000  93.290871
```

NaN count per column in the raw price file: 0 for every ticker.

### 1.2 First and last 5 rows of rf_dgs3mo.csv

```
         date DGS3MO
0  2007-04-11   5.04
1  2007-04-12   5.03
2  2007-04-13   5.02
3  2007-04-16   5.01
4  2007-04-17   5.01
            date DGS3MO
5065  2026-09-09   3.95
5066  2026-09-10   4.00
5067  2026-09-11   4.07
5068  2026-09-14   4.11
5069  2026-09-15   4.11
```

Blank DGS3MO rows as published: 209. Blank rows that fall on equity trading days: 36.

### 1.3 Panel start

```
panel start: 2007-04-11  rows: 4889  last: 2026-09-15
```

### 1.3 data_issues.csv in full

```
         date ticker             issue  value
0  2012-10-31    ALL  gap_days_gt_flag      5
```

2012-10-26 to 2012-10-31 is the Hurricane Sandy market closure. No daily return exceeds 25% in absolute value, no price is non-positive and no date is duplicated.

### 1.3 rf around a FRED holiday gap (Veterans Day 2025-11-11: FRED blank, equities open)

`rf_x100x252` is the DGS3MO level that rf was built from.

```
           DGS3MO_published_on_d                rf  rf_x100x252
date                                                           
2025-11-06                  3.93 0.000157142857143         3.96
2025-11-07                  3.92 0.000155952380952         3.93
2025-11-10                  3.95 0.000155555555556         3.92
2025-11-11                       0.000156746031746         3.95
2025-11-12                  3.95 0.000156746031746         3.95
2025-11-13                  3.96 0.000156746031746         3.95
2025-11-14                  3.95 0.000157142857143         3.96
```

rf on 2025-11-12 uses the 2025-11-10 level of 3.95 because 2025-11-11 is blank. rf has 1 NaN, on the panel start 2007-04-11, which has no previous trading day.

### 1.3 The 4 days where the two readings of "d − 1" differ (open decision 2)

FRED published on 8 days when equities were closed: 2010-04-02, 2012-04-06, 2012-10-29, 2015-04-03, 2021-04-02, 2023-04-07, 2025-01-09, 2026-04-03. DGS3MO level used on the next trading day under each reading:

```
            prev_trading_day  prev_calendar_day
date                                           
2012-04-09              0.08               0.07
2012-10-31              0.12               0.14
2023-04-10              4.91               4.95
2026-04-06              3.70               3.71
```

Good Friday 2012 as a worked case. Raw FRED rows:

```
           DGS3MO
date             
2012-04-04   0.08
2012-04-05   0.08
2012-04-06   0.07
2012-04-09   0.09
2012-04-10   0.09
```

rf as implemented (option 1: the 2012-04-09 row uses the 2012-04-05 level, not the Good Friday level):

```
           DGS3MO_published_on_d                rf  rf_x100x252
date                                                           
2012-04-04                  0.08  3.1746031746e-06         0.08
2012-04-05                  0.08  3.1746031746e-06         0.08
2012-04-09                  0.09  3.1746031746e-06         0.08
2012-04-10                  0.09 3.57142857143e-06         0.09
```

### 1.4 First and last 5 calendar rows

```
  decision_date  exec_date next_exec_date  n_hold_days
0    2010-04-30 2010-05-03     2010-06-01           20
1    2010-05-28 2010-06-01     2010-07-01           22
2    2010-06-30 2010-07-01     2010-08-02           21
3    2010-07-30 2010-08-02     2010-09-01           22
4    2010-08-31 2010-09-01     2010-10-01           21
    decision_date  exec_date next_exec_date  n_hold_days
191    2026-03-31 2026-04-01     2026-05-01           21
192    2026-04-30 2026-05-01     2026-06-01           20
193    2026-05-29 2026-06-01     2026-07-01           21
194    2026-06-30 2026-07-01     2026-08-03           22
195    2026-07-31 2026-08-03     2026-09-01           21
```

`n_hold_days` over the 196 rows:

```
count    196.000000
mean      20.959184
std        1.131537
min       19.000000
25%       20.000000
50%       21.000000
75%       22.000000
max       23.000000
```

### 1.5 Monthly excess return for 2020-03, manual against pc

Month-end closes 2020-02-28 and 2020-03-31, read straight from the raw CSV rows. `rf_month` compounds DGS3MO(previous trading day)/100/252 over the 22 trading days of March 2020, read straight from the raw FRED rows. `pc_function` is `monthly_excess_returns(prices, rf)` at 2020-03-31.

```
     close_2020_02  close_2020_03      total_return          rf_month     excess_manual       pc_function          abs_diff
SPY    269.3777771   235.74029541   -0.124871034469 0.000304009985325   -0.125175044455   -0.125175044455                 0
IWM  134.758407593  105.816215515    -0.21477095637 0.000304009985325   -0.215074966356   -0.215074966356                 0
EFA   51.222114563  43.9963760376   -0.141066775299 0.000304009985325   -0.141370785284   -0.141370785284                 0
EEM  35.2976951599  29.7312526703   -0.157699885627 0.000304009985325   -0.158003895613   -0.158003895613 1.11022302463e-16
XLE  17.2260913849  11.3053178787   -0.343709630576 0.000304009985325   -0.344013640561   -0.344013640561                 0
XLF   23.483839035  18.5437889099   -0.210359563347 0.000304009985325   -0.210663573332   -0.210663573332                 0
XLK  41.8145179749  38.2276954651   -0.085779358067 0.000304009985325  -0.0860833680524  -0.0860833680524 2.22044604925e-16
XLU  25.2459697723  22.7224845886  -0.0999559615444 0.000304009985325    -0.10025997153    -0.10025997153                 0
XLV  83.0165863037  79.7894515991  -0.0388733727593 0.000304009985325  -0.0391773827446  -0.0391773827446                 0
SHY  73.4772796631  74.3914718628   0.0124418351346 0.000304009985325   0.0121378251493   0.0121378251493                 0
IEF  99.3820266724  103.081764221   0.0372274310829 0.000304009985325   0.0369234210976   0.0369234210976                 0
TLT  127.172546387  135.281890869   0.0637664709313 0.000304009985325   0.0634624609459   0.0634624609459 2.22044604925e-16
TIP  94.6199951172  92.9566726685  -0.0175789741552 0.000304009985325  -0.0178829841405  -0.0178829841405 1.11022302463e-16
LQD  103.944221497  97.3834228516  -0.0631184547881 0.000304009985325  -0.0634224647735  -0.0634224647735 2.22044604925e-16
HYG  60.3251953125  54.2757797241   -0.100280082925 0.000304009985325    -0.10058409291    -0.10058409291 1.11022302463e-16
GLD  148.380004883  148.050003052 -0.00222403167674 0.000304009985325 -0.00252804166207 -0.00252804166207                 0
DBC  11.8425779343  9.78905200958   -0.173401934619 0.000304009985325   -0.173705944605   -0.173705944605                 0
VNQ   67.671546936  54.5487823486   -0.193918495757 0.000304009985325   -0.194222505743   -0.194222505743                 0
```

```
monthly_excess rows: 232 first: 2007-05-31 last: 2026-08-31 NaN: 0
```

## Tests run

`.venv\Scripts\python -m pytest -p socket --disable-socket -v`

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser
configfile: pyproject.toml
testpaths: tests
plugins: socket-0.8.1, platformdirs-4.12.2
collecting ... collected 18 items

tests/test_calendar.py::test_calendar_has_196_rows PASSED                [  5%]
tests/test_calendar.py::test_first_decision_2010_04_30 PASSED            [ 11%]
tests/test_calendar.py::test_last_decision_2026_07_31 PASSED             [ 16%]
tests/test_calendar.py::test_exec_date_is_next_trading_day PASSED        [ 22%]
tests/test_calendar.py::test_decision_dates_are_trading_days PASSED      [ 27%]
tests/test_config.py::test_config_keys_match_fields PASSED               [ 33%]
tests/test_config.py::test_w_mkt_sums_to_one PASSED                      [ 38%]
tests/test_config.py::test_one_way_bp_tickers PASSED                     [ 44%]
tests/test_data.py::test_load_prices_shape_and_order PASSED              [ 50%]
tests/test_data.py::test_load_prices_no_nan_from_panel_start PASSED      [ 55%]
tests/test_data.py::test_panel_start_is_first_full_row PASSED            [ 61%]
tests/test_data.py::test_rf_uses_previous_day_and_ffill PASSED           [ 66%]
tests/test_data.py::test_validate_flags_each_issue_type PASSED           [ 72%]
tests/test_manifest.py::test_manifest_hashes_match PASSED                [ 77%]
tests/test_placeholder.py::test_placeholder PASSED                       [ 83%]
tests/test_returns.py::test_compounded_daily_equals_holding_return PASSED [ 88%]
tests/test_returns.py::test_rf_constant_5pct_gives_005_over_252 PASSED   [ 94%]
tests/test_returns.py::test_monthly_excess_2020_03_manual PASSED         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\5) Constrained Portfolio Optimiser\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 18 passed, 1 warning in 1.93s ========================
```

The warning comes from `-p socket` on the command line loading pytest-socket a second time after its entry point has already loaded it. It does not affect any test.

## Fresh-clone check

Cloned `https://github.com/uty101/Constrained-Portfolio-Optimiser.git` at `f11ee89` into `%TEMP%\pcs1`, then `uv venv --seed --python 3.11 .venv`, `.venv\Scripts\python -m pip install -e ".[dev]"`, `.venv\Scripts\python -m pytest -p socket --disable-socket -q`. A first attempt under the session scratchpad folder failed inside `pip install` with `OSError: [Errno 2]` on a numpy test file whose path exceeded the Windows 260-character limit. The rerun at a short path ran the same commands.

```
..................                                                       [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Users\astha\AppData\Local\Temp\pcs1\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
18 passed, 1 warning in 6.12s
```

This clone is checked out with `core.autocrlf=true`, so `test_manifest_hashes_match` passing here also confirms that `.gitattributes` keeps the raw files byte-identical.

## Runtime per step

| step | runtime |
|---|---|
| 1.1 | tests 0.03 s |
| 1.2 | `pull_data.py` 9.6 s; tests 0.05 s |
| 1.3 | tests 1.12 s; `write_data_issues` under 2 s |
| 1.4 | tests 0.61 s |
| 1.5 | tests 1.09 s |
| 1.6 | not built |
| full suite | 1.93 s (repo), 6.12 s (fresh clone) |

## Deviations from PLAN.md

1. **No Section 1 instruction file.** No `instructions/01_*.md` existed in the repo or on `origin`. Rule 11 says the session prompt names one. The session was started from a chat instruction, "do section 1", and followed `PLAN.md` Section 1. So no reviewer answers to the session 0 questions were available.
2. **Step 1.6 not built.** It depends on open decision 1. The whole step was skipped, `corr_full_sample.csv` included, because both files come from one function and one commit in `PLAN.md`.
3. **`.gitattributes` added** (`data/raw/** -text`). This machine's system git config has `core.autocrlf=true`. Without the attribute, a checkout could rewrite the line endings of the hashed raw files and fail `test_manifest_hashes_match`.
4. **`tests/conftest.py` added.** It provides a `cfg` fixture and runs every test from the repo root, because `config.toml` paths are relative to the root.
5. **`pc.data.write_data_issues(cfg)` added.** No signature in kickoff Section 6 writes `data_issues.csv`, and `scripts/run_all.py` is Section 7.
6. **The 252 in the rf rule is computed as `12 × sample.days_per_month`**, not written as a literal in `pc/`, because of rule 6. The value is 252 either way.
7. **Behaviour the plan leaves implicit:**
   - `daily_returns` drops the first row, which has no previous close.
   - `monthly_excess_returns` is indexed by each month's last trading day, so `.loc[:t]` at a decision date is correct. It drops the first month (April 2007, no prior month-end) and a final month that ends before its last business day (September 2026, data ends 2026-09-15). No estimation window reaches that month.
   - `validate_prices` labels gap and duplicate-date issues with ticker `ALL`. The issue names are `abs_daily_return_gt_flag`, `non_positive_price`, `gap_days_gt_flag` and `duplicate_date`.
   - `load_prices` raises if a NaN appears after the panel start, rather than filling it.
   - `build_calendar` raises if it does not produce `sample.expected_n_decisions` rows.
   - `load_rf_daily` leaves rf NaN on the first day of the index.
8. **Price precision.** `pull_data.py` writes prices at pandas' default full precision (no `float_format`), because this is the raw snapshot, not an `outputs/tables` CSV.
9. **Two pushes**, as in session 0. The step commits were pushed so the fresh clone could run, then this review and the status file were pushed.

## Not verified

- The yfinance adjusted closes are not cross-checked against a second source, because rule 1.2 forbids switching source. The only checks are the manifest hash, the validation table and the 2020-03 manual calculation, which uses the same raw file.
- Rule 9 (byte-identical outputs): `data_issues.csv` was regenerated once and `git status` showed no change. It was not run in a second clean session.
- Step 1.6 outputs do not exist.

## Open questions

Appended to `decisions/OPEN.md`:

1. **Step 1.6 annualisation (blocks 1.6).** Option 1: geometric, (Π(1 + r_d))^(252/n) − 1 and std × √252. Option 2: arithmetic, mean × 252 and std × √252.
2. **"d − 1" in the rf rule (built as option 1, please confirm).** Option 1: the previous trading day in the price index. Option 2: the previous calendar day, forward filled. They differ on 4 days (evidence above).

Session 0 items 3b to 3e, 4, 5 and 6 are still unanswered. None of them affects Section 1.

## Files changed

Added: `.gitattributes`, `pc/config.py`, `pc/data.py`, `pc/calendar.py`, `pc/returns.py`, `scripts/pull_data.py`, `data/raw/prices_adjclose.csv`, `data/raw/rf_dgs3mo.csv`, `data/raw/MANIFEST.json`, `outputs/tables/data_issues.csv`, `tests/conftest.py`, `tests/test_config.py`, `tests/test_manifest.py`, `tests/test_data.py`, `tests/test_calendar.py`, `tests/test_returns.py`, `review/section_1.md`, `instructions/01_section_1.status.md`.
Modified: `decisions/OPEN.md`.
Deleted: none.

## Reviewer reads

1. `decisions/OPEN.md`
2. This file, Deviations from PLAN.md
3. `pc/data.py` (`load_rf_daily`, `validate_prices`)
4. `pc/returns.py`
5. `pc/calendar.py`
6. `tests/test_returns.py` (`manual_2020_03`)
7. `pc/config.py`, `tests/test_config.py`
8. `scripts/pull_data.py`
