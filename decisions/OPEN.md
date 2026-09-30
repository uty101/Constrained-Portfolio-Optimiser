# Open decisions

## 1. Step 1.6: annualisation in data_summary.csv (blocks step 1.6)

`data_summary.csv` has ann_return and ann_vol of daily returns; the kickoff does not fix the convention. Raised in `instructions/00_kickoff.status.md` item 3a; unanswered, so step 1.6 was not built.

- Option 1: geometric. ann_return = (Π(1 + r_d))^(252/n) − 1, ann_vol = std(r_d, ddof=1) × √252, with 252 = 12 × `sample.days_per_month`.
- Option 2: arithmetic. ann_return = mean(r_d) × 252, ann_vol = std(r_d, ddof=1) × √252, with 252 = 12 × `sample.days_per_month`.

## 2. Step 1.3: which day is "d − 1" in the rf rule (implemented as option 1, needs confirming)

Kickoff 4.8: daily rf on trading day d = DGS3MO(d − 1)/100/252, forward filled across FRED gaps. FRED publishes on 8 days in the sample when the equity market is closed (Good Fridays, 2012-10-29, 2025-01-09), so the two readings differ on the next trading day. They differ on 4 of 4,888 days, by 1 to 4 bp of annual yield (about 1.6e-6 of daily rf at most). Rows are in `review/section_1.md`.

- Option 1 (implemented): d − 1 is the previous trading day in the price index; DGS3MO is the last published value on or before it.
- Option 2: d − 1 is the previous calendar day; DGS3MO is the last published value strictly before d.
