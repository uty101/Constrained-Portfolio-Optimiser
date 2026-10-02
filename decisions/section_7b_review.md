# Section 7 review decisions (session 7b)

From `instructions/07b_final_edits.md`, step 7.7.

1. **Status question 1, the TODO grep: option 1.** The hits are quoted patterns in instruction files that may not be edited, bytes inside a parquet file, and the deliberately unknown ticker `XXX` in 2 tests and 1 review file. The check is satisfied for `pc/`, `scripts/`, `docs/`, `README.md`, `examples/` and `decisions/`, which is where a forgotten marker would matter. The tests stay unchanged.
2. **Status question 2, `test_readme_tables_match_snippets` reading committed `outputs/tables/`:** accepted as the one named exception to rule 7. Its job is to check the committed README against the committed snippets, so it has to read committed outputs. It passes in a fresh clone.
3. **Status questions 3 to 5:** accepted as reported. That includes the section title "Checks on the assumptions", the 2 captioned robustness tables, the turnover table without its `none` row, and the 65 module-internal helpers kept.
4. **The project is complete.** Sections 0 to 7 are built and reviewed. `decisions/OPEN.md` is empty.
