# Covariance frequency

All four covariance estimators run on daily simple returns over the trailing 36 months and are scaled to monthly by ×21.
EWMA λ = 0.97 is the RiskMetrics decay applied to daily data here (half-life about 23 trading days), stated as such.
Monthly data would give N = 18 against T = 36 and a near-singular sample covariance; it is run as a robustness test (step 5.4), not the baseline.
Every Σ is ridged to cond ≤ 1e6 before any allocator sees it.
