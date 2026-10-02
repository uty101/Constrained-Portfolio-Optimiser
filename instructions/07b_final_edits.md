# instructions/07b_final_edits.md — Session 7b: final wording fixes and close-out

Section 7 is approved, apart from 4 sentences. The reviewer ran the suite on Linux (262 passed) and checked the README against the outputs, and the claims hold except those 4:

- HRP's SHY weight: 87.4% on average, at least 69.4%, over 196 months.
- The cost-scale turnover for capped mean-variance: 0.22, 0.18 and 0.12.
- The ranking under each cost scale.
- Every figure in "What it found".
- The demo facts.
- The must-not and must-make lists in `07_section_7.md`.

The style grep is clean.

This session makes exactly the edits below, records the decisions, reruns the checks and closes the project. Nothing else changes. Where this file and anything earlier differ, this file wins. This file is already committed; do not edit it. Stage files by explicit path; never stage `CLAUDE.md` or `PLAN.md`.

---

## Step 7.6 — wording fixes (commit: `step 7.6: README and design note wording`)

Replace each old string with the new one exactly. Each old string occurs once; if one does not match exactly once, stop under rule 4.

**1. `README.md`, question 1.** "Very little" overstates it. The outputs say the capped strategy kept about 3/5 of the long-only promise.

Old:
```
**Question 1: how much of the in-sample gap survives out of sample?** Very little. In sample,
```
New:
```
**Question 1: how much of the in-sample gap survives out of sample?** Capped mean-variance kept 61% of the long-only frontier's Sharpe ratio and 39% of the unconstrained frontier's. In sample,
```

**2. `README.md`, question 4.** The 0.45 GMV difference has an interval that includes 0, so "worse" claims more than the bootstrap shows. The bias ratio is the clear finding.

Old:
```
For the global minimum variance portfolio, the one an optimiser builds, EWMA is worse by 0.45 (interval −0.07 to 1.24) and under-forecasts the risk: its bias ratio is 1.38, against 1.01 for Ledoit-Wolf, where a calibrated forecast sits near 1.
```
New:
```
For the global minimum variance portfolio, the one an optimiser builds, EWMA scores 0.45 worse, though that interval (−0.07 to 1.24) includes 0. The clearer signal is the bias: EWMA under-forecasts that portfolio's risk with a bias ratio of 1.38, outside the 0.92 to 1.08 band for a calibrated forecast, against 1.01 for Ledoit-Wolf.
```

**3. `README.md`, checks section.** On the monthly estimate, minimum variance's turnover goes from 3.4% to 6.6% a month, which is more than "barely notices".

Old:
```
Unconstrained mean-variance blows up far sooner on the monthly estimate, while capped minimum variance barely notices.
```
New:
```
Unconstrained mean-variance blows up far sooner on the monthly estimate. Capped minimum variance keeps a similar Sharpe ratio but trades about twice as much.
```

**4. `docs/DESIGN_NOTE.md`, costs paragraph.** The size of the market-impact error is not measured anywhere in the repo.

Old:
```
Flat costs ignore market impact, so the objective understates the cost of large trades; for a $10m book in these ETFs that is a small error.
```
New:
```
Flat costs ignore market impact, so the objective understates the cost of large trades, an error this repo does not measure.
```

---

## Step 7.7 — decisions and close-out (commit: `section 7: reviewer decisions and close-out`)

Write `decisions/section_7b_review.md`:

1. **Status question 1, the TODO grep: option 1.** The hits are quoted patterns in instruction files that may not be edited, bytes inside a parquet file, and the deliberately unknown ticker `XXX` in 2 tests and 1 review file. The check is satisfied for `pc/`, `scripts/`, `docs/`, `README.md`, `examples/` and `decisions/`, which is where a forgotten marker would matter. The tests stay unchanged.
2. **Status question 2, `test_readme_tables_match_snippets` reading committed `outputs/tables/`:** accepted as the one named exception to rule 7. Its job is to check the committed README against the committed snippets, so it has to read committed outputs. It passes in a fresh clone.
3. **Status questions 3 to 5:** accepted as reported. That includes the section title "Checks on the assumptions", the 2 captioned robustness tables, the turnover table without its `none` row, and the 65 module-internal helpers kept.
4. **The project is complete.** Sections 0 to 7 are built and reviewed. `decisions/OPEN.md` is empty.

Then:

- run `scripts/run_all.py` once and confirm `git status --porcelain` is empty, since prose edits touch no generated file;
- run the full suite;
- rerun the style grep from `07_section_7.md` on the 2 edited files;
- run the fresh-clone check under standing amendments 2 and 3.

## Review and status

Append a subsection `### Session 7b` to `review/section_7.md` with:

- the 4 diffs;
- the `run_all` timing and `git status` output;
- the grep output;
- the test output;
- the fresh-clone output.

Status file: `instructions/07b_final_edits.status.md`, per rule 11. Then push and stop.
