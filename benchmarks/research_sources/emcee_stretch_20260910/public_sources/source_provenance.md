# Pinned emcee Numerical Reproduction

The public source is `dfm/emcee` release `v3.1.6`, commit
`9c5f59b6ca2fce111cc7348bda415253e0e1c1b0`, under its MIT license.
`paper.tex`, `stretch.py`, and `red_blue.py` are unmodified repository files.
The official versioned quickstart notebook was downloaded from
https://emcee.readthedocs.io/en/v3.1.6/_sources/tutorials/quickstart.ipynb.
Its content hash, not the mutable documentation URL alone, fixes the source.

The paper is Foreman-Mackey, Hogg, Lang and Goodman (2013), *emcee: The MCMC
Hammer*, PASP 125, 306-312, https://doi.org/10.1086/670067;
https://arxiv.org/abs/1202.3665v4. The source implements the Goodman-Weare stretch
move with the two-subensemble update described in the paper.

The operator launcher executes unchanged notebook computational cells with seed
42, dimension 5, 32 walkers, 100 initial steps and 10,000 retained steps. It omits
only display configuration and histogram rendering and exports a numerical JSON
summary. These omissions are explicit; this is not reproduction of every paper
figure, a speed comparison, a new sampler implementation or proof of convergence.

The installed release is emcee 3.1.6 with NumPy 2.4.6 and CPython 3.12.13. This
is a versioned contemporary environment, not the paper's historical environment.
Package versions and interpreter identity are recorded in `environment_lock.json`.
Execution is isolated without network or inherited credentials. Acceptance rates,
sample moments and autocorrelation estimates must be read from the actual run;
neither a zero exit status nor a plausible acceptance rate proves stationarity or
mixing. Correlated time samples cannot be counted as independent Monte Carlo
replicates.
