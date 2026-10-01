# pctrade demo

A $10,000,000 book held off target, run through `pctrade` at the 2026-07-31 decision date with every default: strategy `mv_constrained|lw_cc|sample|C`, turnover limit τ = 0.30, lot size 1, minimum notional $1,000.

## How the book was built

`examples/positions_demo.csv` is `pc.cli.demo_book` applied to the committed data:

- target weights GLD 0.40, SPY 0.20, IEF 0.20, TLT 0.10, HYG 0.05, and cash for the rest;
- price_i = the 2026-07-31 adjusted close, rounded to 4 decimals;
- quantity_i = floor(weight_i × 10,000,000 / price_i);
- cash = 10,000,000 − Σ quantity_i × price_i = 500,790.0747, in exact decimal arithmetic, so the NAV is exactly $10,000,000.00.

Flooring on the unrounded closes gives the same 5 quantities.

```
ticker,quantity,price
SPY,2683,745.1796
IEF,21668,92.3004
TLT,12253,81.6073
HYG,6356,78.6649
GLD,10766,371.54
```

GLD at 0.40 is above the 0.30 cap, and 5% of the fund is cash, so the book is outside the feasible set. The smallest turnover that reaches it, τ_min from the feasibility LP, is 0.2501: 0.1000 out of GLD and 0.1501 into other assets, of which 0.0501 is the cash. That is below τ = 0.30, so the feasibility rule does not relax the limit.

## Command

Run from the repo root:

```
pctrade --positions examples/positions_demo.csv --cash 500790.0747 --asof 2026-07-31 --out examples/trades_demo.csv
```

## Printed output

```
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
```

`solver` lists both solves: the feasibility LP and the mean-variance problem, both on CLARABEL. The limit binds (turnover 0.300000 before rounding), and its shadow price is 0.95 bp of monthly expected return per 1% of extra turnover. No price warning is printed, because every price in the book is within 5% of the 2026-07-31 close. XLK is not in the book, so the CLI priced it at that close.

## Trades

`examples/trades_demo.csv`:

```
ticker,side,quantity,price,notional,est_cost,weight_before,weight_target,weight_after
XLK,BUY,9987,175.1456146,1749179.253,524.753776,0,0.1750395037,0.1749179253
TLT,SELL,3058,81.6073,-249555.1234,74.86653702,0.09999342469,0.07503289242,0.07503791235
GLD,SELL,2691,371.54,-999814.14,299.944242,0.399999964,0.3,0.30001855
```

The fund sells GLD down to the cap and trims TLT, and puts the proceeds and the cash into XLK. The XLK buy was cut by 6 shares to pay the estimated costs, which is why XLK is the weight furthest from its target. `tests/test_cli.py::test_demo_reproduces_trades_demo` rebuilds the book, reruns this command into a temporary folder and compares both files byte for byte.
