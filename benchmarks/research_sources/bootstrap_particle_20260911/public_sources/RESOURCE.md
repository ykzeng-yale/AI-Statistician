# Bootstrap Particle Filtering: Public Source

This is a source-assisted research task, not blind rediscovery. The computational
baseline is Nicolas Chopin's MIT-licensed `particles` package, version 0.4, at
commit `f71e94a21a11c73b58e2d694775b1b1d379b8854` (2026-02-19):
https://github.com/nchopin/particles/tree/f71e94a21a11c73b58e2d694775b1b1d379b8854

The package accompanies Chopin and Papaspiliopoulos (2020), *An Introduction to
Sequential Monte Carlo*, DOI 10.1007/978-3-030-47845-2. The selected unchanged
script is `book/filtering/comparing_bootstrap_guided_apf_stochvol.py`, associated
with Section 10.4.2 and Figure 10.3. It uses 201 observed GBP/USD returns,
250 independent runs of each of three filters at N=1000, and one SQMC baseline
at N=65536. The SQMC run is a numerical benchmark, not an exact posterior.
This task does not reproduce the entire book, the linear-Gaussian script,
parameter-inference algorithms, or all figures.

`run_particle_source.py` is an operator-authored launcher, not upstream scientific
code. It verifies installed package and data bytes, fixes the random seed and a
headless plotting/cache environment, executes the complete selected script
unchanged, and serializes its actual numerical output. Package versions are
recorded in `environment_lock.json`; this is a current compatible environment,
not a claim to reconstruct the authors' historical machine. The execution has
network and inherited secrets denied. Resource and source provenance alone do
not establish theory, generated-code correctness or confirmatory validation.

Additional theory background is Bérard, Del Moral and Doucet (2014), *A lognormal
central limit theorem for particle approximations of normalizing constants*,
Electronic Journal of Probability 19(94), DOI 10.1214/EJP.v19-3428:
https://www.stats.ox.ac.uk/~doucet/berard_delmoral_doucet_lognormalCLT_EJPfinalversion.pdf
The present task asks for finite-horizon bootstrap-filter results, not that
paper's growing-horizon lognormal limit theorem.
