"""Evaluator mechanism fixtures only, never generated research or efficacy evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "benchmarks/agentic_scientist_hc0_bouchet_20261015/evaluate.py"
SPEC = importlib.util.spec_from_file_location("hc0_full_study_evaluator", EVALUATOR)
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)

REFERENCE_FIXTURE = '''\
# Public-library mechanism fixture, not an authored statistical solution.
import statsmodels.api as sm
def run_estimator(request):
    result = sm.OLS(request['outcomes'], request['design_matrix']).fit(cov_type='HC0', use_t=False)
    return {'coefficients': result.params.tolist(), 'covariance': result.cov_params().tolist(),
            'standard_errors': result.bse.tolist()}
'''


def read_json(path):
    return json.loads(path.read_text(), parse_constant=lambda value: pytest.fail(f"Nonfinite JSON token: {value}"))


def read_rows(output):
    return [json.loads(line) for line in (output / "replicates.jsonl").read_text().splitlines()]


@pytest.fixture
def pinned_reference():
    statsmodels = pytest.importorskip("statsmodels", reason="Requires existing statsmodels 0.14.6 evaluation environment")
    assert statsmodels.__version__ == "0.14.6"
    return statsmodels


@pytest.fixture
def program(tmp_path):
    source = tmp_path / "candidate/src/program.py"
    source.parent.mkdir(parents=True)
    source.write_text(REFERENCE_FIXTURE)
    return source


def test_frozen_grid_and_order_independent_rng():
    assert evaluator.MASTER_SEED == 2026101517
    assert evaluator.REPETITIONS == 5000
    assert len(evaluator.CELLS) == 12
    assert {(cell['n'], cell['beta1'], cell['variance']) for cell in evaluator.CELLS} == {
        (n, beta, variance) for n in (50, 200, 1000) for beta in (0.0, 0.2)
        for variance in ('homoskedastic', 'heteroskedastic')}
    forward = {(cell['cell_id'], r): evaluator.generate_dataset(cell, r)
               for cell in evaluator.CELLS for r in range(2)}
    fingerprints = set()
    for cell in reversed(evaluator.CELLS):
        for r in (1, 0):
            x, y = evaluator.generate_dataset(cell, r)
            expected_x, expected_y = forward[cell['cell_id'], r]
            np.testing.assert_array_equal(x, expected_x)
            np.testing.assert_array_equal(y, expected_y)
            np.testing.assert_array_equal(x[:, 0], np.ones(cell['n']))
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(2026101517, spawn_key=(cell['cell_id'], r))))
            draws = rng.standard_normal((cell['n'], 3))
            variance = 1 if cell['variance'] == 'homoskedastic' else (1 + 4 * draws[:, 0] ** 2) / 5
            np.testing.assert_allclose(y, cell['beta1'] * draws[:, 0] + draws[:, 1] + np.sqrt(variance) * draws[:, 2])
            fingerprints.add(hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest())
    assert len(fingerprints) == 24


def test_complete_tiny_study_reference_fixture_and_no_coverage_gate(tmp_path, program, pinned_reference):
    before = program.read_bytes()
    output = tmp_path / "results"
    metrics = evaluator.run_study(program, output, repetitions=3)
    assert metrics['completed_replicates'] == metrics['scheduled_replicates'] == 36
    assert metrics['candidate_compliant_replicates'] == 36
    assert metrics['study_complete'] == metrics['combined_score'] == 1
    assert all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values())
    assert read_json(output / 'correct.json') == {'correct': True}
    assert read_json(output / 'metrics.json') == metrics
    details = read_json(output / 'study.json')
    assert details['theory'] == 'UNASSESSED'
    assert details['statsmodels'] == '0.14.6'
    assert details['cli_design'] is False
    assert details['entrypoint_unchanged'] is True
    assert details['source_tree_unchanged'] is True
    assert details['candidate_source_sha256_before'] == details['candidate_source_sha256_after'] == {
        'program.py': hashlib.sha256(before).hexdigest()}
    assert read_json(output / 'source_before.json')['sha256'] == details['candidate_source_sha256_before']
    assert details['raw_sha256'] == hashlib.sha256((output / 'replicates.jsonl').read_bytes()).hexdigest()
    assert program.read_bytes() == before
    assert not list(program.parent.rglob('__pycache__'))
    rows = read_rows(output)
    assert len(rows) == 36
    assert len({(row['cell_id'], row['replicate']) for row in rows}) == 36
    assert all(row['methods']['candidate_hc0']['status'] == 'ok' for row in rows)
    assert all(all(check['allclose'] for check in row['methods']['candidate_hc0']['checks'].values()) for row in rows)
    summaries = read_json(output / 'summaries.json')
    for cell in summaries:
        for method in evaluator.METHODS:
            result = cell['methods'][method]
            assert result['attempted'] == result['usable'] == result['compliant'] == 3
            assert result['not_run'] == 0
            assert result['failure_rate'] == {'estimate': 0.0, 'mcse': 0.0}
            assert len(result['coefficients']) == 3
            for coefficient in result['coefficients']:
                assert all(coefficient[name]['mcse'] is not None for name in (
                    'bias', 'rmse', 'empirical_sd', 'rms_se', 'se_sd_ratio', 'coverage',
                    'mean_interval_length', 'rejection'))
    # With m=3, coverage cannot equal .95. This is still numerical compliance.
    assert all(cell['methods']['candidate_hc0']['coefficients'][1]['coverage']['estimate'] != .95 for cell in summaries)


@pytest.mark.parametrize('body, status, tag', [
    ("print('before failure'); raise RuntimeError('deliberate fixture error')", 'exception', 'deliberate fixture error'),
    ("raise SystemExit('candidate exit')", 'exception', 'candidate exit'),
    ("return {'coefficients': [float('nan')]*3, 'covariance': [[0]*3]*3, 'standard_errors': [1]*3}", 'invalid_output', 'nan'),
    ("return {'coefficients': [0,0], 'covariance': [[1,0,0],[0,1,0],[0,0,1]], 'standard_errors': [1,1,1]}", 'invalid_output', 'coefficients'),
    ("return None", 'invalid_output', 'mapping'),
])
def test_failed_outputs_preserved_without_reference_substitution(tmp_path, program, pinned_reference, body, status, tag):
    program.write_text('def run_estimator(request):\n    ' + body + '\n')
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=2)
    assert metrics['study_complete'] == 1
    assert metrics['combined_score'] == metrics['candidate_compliant_replicates'] == 0
    assert metrics['conventional_compliant_replicates'] == 24
    assert read_json(output / 'correct.json') == {'correct': False}
    rows = read_rows(output)
    assert len(rows) == 24
    assert tag in (output / 'replicates.jsonl').read_text()
    assert all(row['methods']['candidate_hc0']['status'] == status for row in rows)
    assert all(row['methods']['candidate_hc0']['interval_lower'] is None for row in rows)
    for cell in read_json(output / 'summaries.json'):
        result = cell['methods']['candidate_hc0']
        assert result['usable'] == result['compliant'] == 0
        assert result['failure_rate'] == {'estimate': 1.0, 'mcse': 0.0}
        assert result['coefficients'][1]['bias'] == {'estimate': None, 'mcse': None}


def test_reference_mismatch_is_retained_in_performance_not_replaced(tmp_path, program, pinned_reference):
    program.write_text(REFERENCE_FIXTURE.replace("return {'coefficients': result.params.tolist()", "return {'coefficients': (result.params + 1).tolist()"))
    output = tmp_path / 'results'
    evaluator.run_study(program, output, repetitions=2)
    for row in read_rows(output):
        candidate = row['methods']['candidate_hc0']
        assert candidate['status'] == 'reference_mismatch'
        assert candidate['usable'] and not candidate['compliant']
        np.testing.assert_allclose(np.array(candidate['raw_output']['coefficients']) - row['reference_hc0']['raw_output']['coefficients'], 1)
    summary = read_json(output / 'summaries.json')[0]
    candidate, conventional = (summary['methods'][key] for key in evaluator.METHODS)
    assert candidate['failure_rate']['estimate'] == 1
    assert candidate['unusable_rate']['estimate'] == 0
    assert candidate['performance_denominator'] == 2
    assert candidate['coefficients'][1]['bias']['estimate'] == pytest.approx(conventional['coefficients'][1]['bias']['estimate'] + 1)
    assert read_json(output / 'correct.json') == {'correct': False}


@pytest.mark.parametrize('key, replacement', [
    ('coefficients', [0, 0]), ('covariance', np.eye(2)), ('standard_errors', [1, 1]),
    ('coefficients', [0, float('inf'), 0]), ('covariance', np.full((3, 3), float('nan'))),
    ('standard_errors', [1, float('inf'), 1]), ('standard_errors', [-1, 1, 1]),
    ('standard_errors', [0, 1, 1]), ('coefficients', ['0', '0', '0']),
    ('coefficients', [1j, 0, 0]),
])
def test_all_output_fields_require_numeric_shape_finiteness(key, replacement):
    raw = {'coefficients': np.zeros(3), 'covariance': np.eye(3), 'standard_errors': np.ones(3)}
    raw[key] = replacement
    _, _, usable, _, _ = evaluator._check_output(raw)
    assert not usable


def test_exact_allclose_tolerance():
    reference = {'coefficients': np.ones(3), 'covariance': np.eye(3), 'standard_errors': np.ones(3)}
    for difference, expected in ((0.5e-6, True), (2e-6, False)):
        raw = {key: value.copy() for key, value in reference.items()}
        raw['coefficients'][0] += difference
        _, _, usable, agreement, _ = evaluator._check_output(raw, reference)
        assert usable and agreement is expected
    for difference, expected in ((0.5e-9, True), (2e-9, False)):
        raw = {key: value.copy() for key, value in reference.items()}
        raw['covariance'][0, 1] = difference
        assert evaluator._check_output(raw, reference)[3] is expected


def test_mcse_delta_matches_independent_moment_gradient_calculation():
    estimates = np.array([-2., -1., 1., 2.])
    ses = np.array([1., 2., 2., 3.])
    result = evaluator.summarize_performance(estimates, ses, 0.)
    assert result['bias']['estimate'] == 0
    assert result['rmse']['estimate'] == pytest.approx(math.sqrt(2.5))
    assert result['empirical_sd']['estimate'] == pytest.approx(math.sqrt(10 / 3))
    assert result['rms_se']['estimate'] == pytest.approx(math.sqrt(4.5))
    moments = np.column_stack((estimates, estimates**2, ses**2))
    center = moments.mean(axis=0)
    covariance = np.cov(moments, rowvar=False, ddof=1) / len(estimates)
    functions = {
        'rmse': lambda m: np.sqrt(m[1]),
        'empirical_sd': lambda m: np.sqrt(4 / 3 * (m[1] - m[0]**2)),
        'rms_se': lambda m: np.sqrt(m[2]),
        'se_sd_ratio': lambda m: np.sqrt(m[2]) / np.sqrt(4 / 3 * (m[1] - m[0]**2)),
    }
    for key, function in functions.items():
        step = 1e-5
        gradient = np.array([(function(center + np.eye(3)[j]*step) - function(center - np.eye(3)[j]*step)) / (2*step) for j in range(3)])
        assert result[key]['mcse'] == pytest.approx(math.sqrt(gradient @ covariance @ gradient), rel=1e-8)
    assert result['bias']['mcse'] == pytest.approx(np.std(estimates, ddof=1) / 2)
    assert result['coverage']['estimate'] == .75
    assert result['coverage']['mcse'] == pytest.approx(math.sqrt(.75*.25/4))
    assert result['rejection']['estimate'] == .25
    assert result['mean_interval_length']['mcse'] == pytest.approx(2*evaluator.CRITICAL_VALUE*np.std(ses, ddof=1)/2)


def test_degenerate_and_empty_summaries_do_not_invent_precision():
    empty = evaluator.summarize_performance([], [], 0)
    assert all(value == {'estimate': None, 'mcse': None} for value in empty.values())
    single = evaluator.summarize_performance([0.], [1.], 0.)
    assert single['bias']['mcse'] is None
    assert single['rmse'] == {'estimate': 0., 'mcse': None}
    assert single['empirical_sd'] == single['se_sd_ratio'] == {'estimate': None, 'mcse': None}
    constant = evaluator.summarize_performance([0., 0.], [1., 1.], 0.)
    assert constant['empirical_sd'] == {'estimate': 0., 'mcse': None}
    assert constant['se_sd_ratio'] == {'estimate': None, 'mcse': None}


def test_refuses_consumed_output_without_overwriting(tmp_path, program, pinned_reference):
    output = tmp_path / 'results'
    evaluator.run_study(program, output, repetitions=1)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError, match='Consumed'):
        evaluator.run_study(program, output, repetitions=1)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize('name', evaluator.OUTPUT_NAMES)
def test_refuses_existing_result_or_in_progress_marker(tmp_path, name):
    (tmp_path / name).write_text('immutable')
    with pytest.raises(FileExistsError):
        evaluator.run_study(tmp_path / 'missing.py', tmp_path, repetitions=1)
    assert (tmp_path / name).read_text() == 'immutable'


def test_partial_evaluator_failure_keeps_rows_and_not_run_denominators(tmp_path, program, pinned_reference, monkeypatch):
    original = evaluator.generate_dataset
    def stop(cell, replicate):
        assert read_json(tmp_path / 'results/source_before.json')['sha256']['program.py'] == hashlib.sha256(program.read_bytes()).hexdigest()
        if cell['cell_id'] == 1:
            raise RuntimeError('injected evaluator interruption')
        return original(cell, replicate)
    monkeypatch.setattr(evaluator, 'generate_dataset', stop)
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=2)
    assert metrics['completed_replicates'] == 2 and metrics['study_complete'] == 0
    assert len(read_rows(output)) == 2
    assert 'injected evaluator interruption' in read_json(output / 'study.json')['error']
    summaries = read_json(output / 'summaries.json')
    assert summaries[0]['methods']['candidate_hc0']['not_run'] == 0
    assert summaries[1]['methods']['candidate_hc0']['not_run'] == 2
    assert summaries[1]['methods']['candidate_hc0']['failure_rate'] == {'estimate': None, 'mcse': None}
    assert read_json(output / 'correct.json') == {'correct': False}
    with pytest.raises(FileExistsError):
        evaluator.run_study(program, output, repetitions=2)


def test_reference_version_mismatch_is_not_silently_accepted(tmp_path, program, pinned_reference, monkeypatch):
    monkeypatch.setattr(pinned_reference, '__version__', 'wrong-version')
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=1)
    assert metrics['study_complete'] == metrics['completed_replicates'] == 0
    assert 'Require statsmodels 0.14.6' in read_json(output / 'study.json')['error']
    assert read_json(output / 'correct.json') == {'correct': False}


def test_import_failure_has_a_record_for_every_scheduled_dataset(tmp_path, program, pinned_reference):
    program.write_text("print('import observation')\nraise RuntimeError('import failed')\n")
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=1)
    assert metrics['completed_replicates'] == 12
    assert metrics['candidate_compliant_replicates'] == 0
    for row in read_rows(output):
        failed = row['methods']['candidate_hc0']
        assert failed['raw_output'] is None
        assert 'import failed' in failed['error']
        assert failed['stdout'] == 'import observation\n'
    assert read_json(output / 'correct.json') == {'correct': False}


def test_reference_failure_does_not_replace_candidate_or_certify_agreement(tmp_path, program, pinned_reference, monkeypatch):
    def broken_reference(x, y):
        raise RuntimeError('reference fixture failure')
    monkeypatch.setattr(evaluator, '_reference_methods', broken_reference)
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=1)
    assert metrics['reference_failure_replicates'] == 12
    assert metrics['candidate_compliant_replicates'] == metrics['combined_score'] == 0
    for row in read_rows(output):
        assert row['methods']['candidate_hc0']['status'] == 'reference_unavailable'
        assert row['methods']['candidate_hc0']['usable'] is True
        assert row['reference_hc0']['raw_output'] is None
        assert 'reference fixture failure' in row['reference_hc0']['error']


def test_unserializable_failed_output_retains_diagnostic():
    raw = []
    raw.append(raw)
    record, values = evaluator._method_record(raw, {'error': None})
    assert values is None and not record['usable']
    assert record['raw_output'] == {'python_type': 'list', 'repr': '[[...]]'}
    assert 'RecursionError' in record['serialization_error']
    json.dumps(record, allow_nan=False)


@pytest.mark.parametrize('mutated', ['helper.py', 'theory.md', 'theory.tex', 'report.py'])
def test_multifile_source_mutation_invalidates_numerical_compliance(tmp_path, program, pinned_reference, mutated):
    source = program.parent
    for name in ('helper.py', 'theory.md', 'theory.tex', 'report.py'):
        (source / name).write_text('# Opaque mechanism fixture, not a scientific argument.\n')
    (source / '__pycache__').mkdir()
    (source / '__pycache__/ignored.pyc').write_bytes(b'not source')
    (source / 'ignored.pyo').write_bytes(b'not source')
    program.write_text(REFERENCE_FIXTURE.replace(
        '    result = sm.OLS',
        "    from pathlib import Path\n"
        f"    target = Path(__file__).parent / {mutated!r}\n"
        "    target.write_text(target.read_text() + '# changed during execution\\n')\n"
        '    result = sm.OLS'))
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.iterdir() if path.is_file() and path.suffix != '.pyo'}
    output = tmp_path / 'results'
    metrics = evaluator.run_study(program, output, repetitions=1)
    assert metrics['study_complete'] == 1
    assert metrics['candidate_compliant_replicates'] == 12
    assert metrics['combined_score'] == metrics['numerical_compliance'] == 0
    details = read_json(output / 'study.json')
    assert details['entrypoint_unchanged'] is True
    assert details['source_tree_unchanged'] is False
    assert details['theory'] == 'UNASSESSED'
    assert details['candidate_source_sha256_before'] == before
    after = details['candidate_source_sha256_after']
    assert set(after) == set(before) == {'program.py', 'helper.py', 'theory.md', 'theory.tex', 'report.py'}
    assert after[mutated] != before[mutated]
    assert all(after[name] == before[name] for name in before if name != mutated)
    assert read_json(output / 'correct.json') == {'correct': False}


def test_source_hashes_include_nested_files_and_detect_additions_deletions(tmp_path):
    nested = tmp_path / 'theory'
    nested.mkdir()
    (nested / 'argument.tex').write_text('opaque')
    initial = evaluator._source_hashes(tmp_path)
    assert initial == {'theory/argument.tex': hashlib.sha256(b'opaque').hexdigest()}
    (tmp_path / 'report.py').write_text('# opaque')
    added = evaluator._source_hashes(tmp_path)
    assert set(added) == {'theory/argument.tex', 'report.py'}
    (nested / 'argument.tex').unlink()
    assert set(evaluator._source_hashes(tmp_path)) == {'report.py'}


def test_cli_has_fixed_repetitions_and_only_two_required_arguments(monkeypatch, capsys):
    calls = []
    def stub(program_path, results_dir, *, repetitions):
        calls.append((program_path, results_dir, repetitions))
        return {'study_complete': 1}
    monkeypatch.setattr(evaluator, 'run_study', stub)
    assert evaluator.main(['--program_path', 'candidate.py', '--results_dir', 'output']) == 0
    assert calls == [('candidate.py', 'output', 5000)]
    assert json.loads(capsys.readouterr().out) == {'study_complete': 1}
    with pytest.raises(SystemExit) as error:
        evaluator.main(['--program_path', 'candidate.py', '--results_dir', 'output', '--repetitions', '2'])
    assert error.value.code == 2
    assert len(calls) == 1


@pytest.mark.parametrize('count', [0, -1, True, 1.5])
def test_invalid_helper_repetitions_do_not_consume_output(tmp_path, count):
    output = tmp_path / 'results'
    with pytest.raises(ValueError):
        evaluator.run_study(tmp_path / 'missing.py', output, repetitions=count)
    assert not output.exists()
