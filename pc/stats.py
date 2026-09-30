"""Statistics: stationary block bootstrap."""

from __future__ import annotations

import numpy as np


def stationary_bootstrap_indices(n: int, mean_block: float, reps: int, seed: int) -> np.ndarray:
    """Politis-Romano index paths, reps x n, int64.

    Draw order is fixed: for each replication in turn, index 0 is rng.integers(n); for
    j >= 1, u = rng.random(), and if u < 1/mean_block the index is rng.integers(n),
    otherwise (previous + 1) mod n.
    """
    rng = np.random.default_rng(seed)
    p = 1 / mean_block
    idx = np.empty((reps, n), dtype=np.int64)
    for r in range(reps):
        cur = int(rng.integers(n))
        idx[r, 0] = cur
        for j in range(1, n):
            cur = int(rng.integers(n)) if rng.random() < p else (cur + 1) % n
            idx[r, j] = cur
    return idx
