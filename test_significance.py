import math

import numpy as np
import pytest

from app.significance import binom_pvalue, cohens_h, summarize, wilson_ci


def test_pvalue_matches_scipy_when_available():
    stats = pytest.importorskip("scipy.stats")
    for k, n, p in [(468, 4460, 0.1), (30, 100, 0.5), (0, 20, 0.1), (362, 3620, 0.1), (10, 10, 0.5)]:
        assert math.isclose(binom_pvalue(k, n, p), stats.binomtest(k, n, p).pvalue, rel_tol=1e-6)


def test_pvalue_known_values():
    assert binom_pvalue(5, 10, 0.5) == pytest.approx(1.0)
    assert binom_pvalue(10, 10, 0.5) == pytest.approx(2 / 1024)


def test_wilson_contains_rate_and_in_unit_interval():
    lo, hi = wilson_ci(468, 4460)
    assert lo < 468 / 4460 < hi and 0 <= lo and hi <= 1
    assert wilson_ci(0, 10)[0] == 0.0


def test_cohens_h_zero_when_equal():
    assert cohens_h(0.1, 0.1) == 0


def test_summarize_random_data_contains_chance():
    rng = np.random.default_rng(0)
    n = 5000
    s = summarize(int((rng.random(n) < 0.1).sum()), n, 0.1)
    assert s["contains_chance"] and s["p_value"] > 0.01
    assert abs(s["cohens_h"]) < 0.05
