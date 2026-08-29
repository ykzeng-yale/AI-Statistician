# Excerpt from PySAL esda, commit dcd9c74bb2b78563c45d4f4a7977da9315d45c56.
# Source: esda/tests/test_moran.py. License: BSD-3-Clause.

def test_variance(self, w):
    y = np.arange(1, 10)
    mi = moran.Moran(y, w, transformation="B")
    np.testing.assert_allclose(
        mi.VI_rand, 0.059687500000000004, atol=ATOL, rtol=RTOL
    )
    np.testing.assert_allclose(
        mi.VI_norm, 0.053125000000000006, atol=ATOL, rtol=RTOL
    )
