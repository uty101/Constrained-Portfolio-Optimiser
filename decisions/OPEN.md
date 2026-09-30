# Open decisions

## 4. Step 3.7: which ticker leaves the short leg on a tie at the bottom boundary (implemented as option 1, needs confirming)

Kickoff 5.4 view 1 puts +1/6 on the 6 highest-momentum tickers and −1/6 on the 6 lowest, "ties broken by ticker order in config". At the top boundary both readings agree: of 2 tickers tied for 6th place, the earlier one in config is long. At the bottom boundary they differ. No tie occurs on the real data (18 compounded 11-month returns, all distinct), so this only changes `test_momentum_views_ties_by_config_order`, which asserts option 1: with XLK (config position 7) and GLD (position 16) tied for the last short slot, GLD is short.

- Option 1 (implemented): one ranking, highest momentum first, ties by config order (the earlier ticker ranks higher). Long = first 6, short = last 6 of that ranking. On a bottom tie the later ticker is short.
- Option 2: config order wins each selection. Long = the 6 highest with ties to the earlier ticker; short = the 6 lowest with ties to the earlier ticker. On a bottom tie the earlier ticker is short.
