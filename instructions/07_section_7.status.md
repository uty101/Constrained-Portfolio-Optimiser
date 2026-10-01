# Status: session 7 (instructions/07_section_7.md)

## Outcome

Completed. Step 7.0 and steps 7.1 to 7.5 are built and committed, one commit per step. 262 tests pass in the repo and in the fresh clone at `%TEMP%\pcs7`. `scripts/run_all.py` was run twice in the repo (372.8 s and 347.2 s) and once in the fresh clone (347.4 s). `git status --porcelain` was empty after each run.

## Last step reached

Step 7.5 (`5dffbb3`), then the review file (`fcfc484`).

## Reason for any stop

None. No rule 4 stop. One check could not pass as written, and it is reported as an open question in the review (item 1 below).

## Questions and blockers for the reviewer

1. **`git grep -n -E "TODO|FIXME|XXX"` is not empty, and cannot be.**
   - Some hits are in files that may not be edited: `PLAN.md`, `instructions/00_kickoff.md` and `instructions/07_section_7.md` quote the pattern.
   - `outputs/results/weights_long.parquet` matches on its binary bytes.
   - `XXX` is the deliberately unknown ticker in `tests/test_cli.py` and `tests/test_trades.py`, and `review/section_6.md` records that test's output.
   - There is no marker in `pc/`, `scripts/`, `docs/`, `README.md`, `examples/` or `decisions/`.
   - Option 1: accept the hits as they are. Option 2: rename the fake ticker to `ZZZ` and scope the check to the code paths. The tests were left unchanged under rule 5.
2. **`test_readme_tables_match_snippets` reads committed files under `outputs/tables/`.** Amendment 7.2 defines the test that way, but rule 7 says no test may depend on `outputs/` existing. It passes in a fresh clone because the snippets are committed (review Deviations 6).
3. **README layout choices the amendment did not fix** (review Deviations 2 to 5, 7 and 8):
   - `readme_robustness.md` holds 2 tables. Each has a caption written by the code, and both callouts come right before the snippet.
   - The QLIKE snippet ends with a note giving the bias band.
   - The turnover table leaves out the `none` row.
   - The primary table's ruin month is joined from `metrics_all.csv`.
   - The section 5 ratios are a typed list, traced in evidence 2.
   - Section 8 is titled "Checks on the assumptions", because "robustness" contains a banned stem.
4. **`run_all.py` gained its README tables call in the 7.2 commit,** because `pc/report.py` did not exist at 7.1.
5. **`find_unused.py` lists 65 names. All of them stay.** Each is a helper used only inside its own module, and none is used nowhere (review evidence 5).
6. **Facts worth a look while reading the README:**
   - HRP held 87% of the fund in SHY on average, and never less than 69% (`weights_long.parquet`). This is the support for the causal sentence about HRP.
   - No ridge fired on the 36-monthly-return covariance either: 0 of 196 dates in `monthly_cov_robustness.csv`.
7. `CLAUDE.md` and `PLAN.md` were not staged or committed, as instructed.

## git log origin/main --oneline -3

```
fcfc484 section 7: review file, fresh-clone check
5dffbb3 step 7.5: find_unused.py, placeholder test removed, README runtime
336533d step 7.4: docs/METHODS.md
```
