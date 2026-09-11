"""Execute the unchanged book experiment and serialize observed results."""

import hashlib
import json
import os
from pathlib import Path
import runpy

os.environ['NUMBA_CACHE_DIR'] = str(Path.home() / 'numba_cache')
import matplotlib
matplotlib.use('Agg')
import numpy as np
import particles

ROOT = Path(__file__).resolve().parent
INSTALLED = Path(particles.__file__).resolve().parent
for source in sorted((ROOT / 'upstream/particles').rglob('*')):
    if source.is_file():
        installed = INSTALLED / source.relative_to(ROOT / 'upstream/particles')
        assert installed.is_file(), str(installed)
        assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(installed.read_bytes()).digest()

np.random.seed(91180411)
namespace = runpy.run_path(str(ROOT / 'upstream/book/filtering/comparing_bootstrap_guided_apf_stochvol.py'))
baseline = np.array([float(row['mean']) for row in namespace['bigpf'].summaries.moments])
summaries = {}
for name in namespace['models']:
    outputs = [row['output'] for row in namespace['results'] if row['fk'] == name]
    log_likelihoods = np.array([output.logLt for output in outputs])
    means = np.array([[float(row['mean']) for row in output.summaries.moments] for output in outputs])
    errors = means - baseline
    summaries[name] = dict(
        runs=len(outputs), log_likelihoods=log_likelihoods.tolist(),
        mean_log_likelihood=float(np.mean(log_likelihoods)),
        sd_log_likelihood=float(np.std(log_likelihoods, ddof=1)),
        mean_filtering_means=np.mean(means, axis=0).tolist(),
        rmse_to_sqmc_by_time=np.sqrt(np.mean(errors**2, axis=0)).tolist(),
        first_run_ess=np.asarray(outputs[0].summaries.ESSs).tolist(),
    )
result = dict(
    source_commit='f71e94a21a11c73b58e2d694775b1b1d379b8854', seed=91180411,
    observations=np.asarray(namespace['data']).reshape(-1).tolist(),
    T=namespace['T'], N=1000, runs_per_filter=250,
    parameters=dict(mu=float(namespace['my_ssm'].mu), sigma=namespace['my_ssm'].sigma, rho=namespace['my_ssm'].rho),
    sqmc_N=namespace['bigN'], sqmc_log_likelihood=float(namespace['bigpf'].logLt),
    sqmc_filtering_means=baseline.tolist(), filters=summaries,
    figure='stochvol_filtering_error_boot_vs_guided_vs_apf.pdf',
)
Path('particle_source_result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
print(json.dumps(dict(T=result['T'], N=result['N'], runs_per_filter=250,
                     filters=list(summaries), sqmc_N=result['sqmc_N'])))
