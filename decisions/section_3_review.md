# Section 3 review decisions

From `instructions/04_section_4.md`, step 4.0.

1. **Open decision 4: option 1 confirmed.** One ranking, highest first, ties by config order, so on a bottom tie the later ticker is short. It is the plain reading of "the 6 lowest" in a single ranking. The item is moved out of `decisions/OPEN.md`, which is now empty.
2. **`pc.solver.solver_config()` reading `config.toml` via a path relative to the package:** accepted. It does not depend on the working directory, which the Section 6 CLI needs.
3. **Solver strings joined by "+" and SCS retries counted with `count("SCS")`:** accepted, and carried into `periods.parquet`.
4. **risk_parity when L-BFGS-B fails:** keep scipy's message as the status and `fallback = False`, but add a boolean column `rp_converged` to `periods.parquet` (True for every non risk parity row). Section 4 evidence counts the False rows per strategy.
5. **`mu_sample` built at 3.3, the test inputs and tolerances in review Deviations 7 and 8, and the 24-minute first fresh-clone run:** accepted. The run was environmental, most likely a virus scan of a new venv.

## Convention added

Convention 23 in `docs/CONVENTIONS_RESOLVED.md`: monthly windows are calendar-month periods. `window_daily` is corrected to it in step 4.0.c.
