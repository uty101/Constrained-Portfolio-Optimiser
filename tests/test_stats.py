import numpy as np

from pc.stats import stationary_bootstrap_indices


def test_bootstrap_indices_shape_and_determinism(cfg):
    n, block, reps, seed = 196, cfg.bootstrap.mean_block, 500, cfg.run.bootstrap_seed
    idx = stationary_bootstrap_indices(n, block, reps, seed)
    assert idx.shape == (reps, n)
    assert idx.dtype == np.int64
    assert idx.min() >= 0 and idx.max() < n
    np.testing.assert_array_equal(idx, stationary_bootstrap_indices(n, block, reps, seed))
    assert not np.array_equal(idx, stationary_bootstrap_indices(n, block, reps, seed + 1))
    # The first replication is a prefix of a longer run: paths are drawn in order.
    np.testing.assert_array_equal(idx[:3], stationary_bootstrap_indices(n, block, 3, seed))


def test_bootstrap_indices_follow_the_fixed_draw_order():
    n, block, seed = 10, 3, 7
    rng = np.random.default_rng(seed)
    expected = []
    for _ in range(4):
        path = [int(rng.integers(n))]
        for _ in range(1, n):
            path.append(int(rng.integers(n)) if rng.random() < 1 / block else (path[-1] + 1) % n)
        expected.append(path)
    np.testing.assert_array_equal(stationary_bootstrap_indices(n, block, 4, seed), expected)
