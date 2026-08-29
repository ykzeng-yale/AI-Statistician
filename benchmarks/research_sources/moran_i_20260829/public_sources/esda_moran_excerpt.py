# Excerpt from PySAL esda, commit dcd9c74bb2b78563c45d4f4a7977da9315d45c56.
# Source: esda/moran.py. License: BSD-3-Clause, copyright PySAL Developers.

def __moments(self):
    self.n = len(self.y)
    y = self.y
    z = y - y.mean()
    self.z = z
    self.z2ss = (z * z).sum()
    self.EI = -1.0 / (self.n - 1)


def __calc(self, z):
    zl = _slag(self.w, z)
    inum = (z * zl).sum()
    s0 = self.w.s0 if isinstance(self.w, W) else self.summary.s0
    return self.n / s0 * inum / self.z2ss
