"""Original project layout, not scientific execution or numerical acceptance."""

import hashlib
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest


def test_original_empty_output_layout_is_restored_without_cached_results(tmp_path):
    script = Path(__file__).resolve().parents[1] / "benchmarks/publication_reference_qualification_20261016/prepare_reference_applications.py"
    spec = importlib.util.spec_from_file_location("reference_application_staging", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.APPLICATIONS = {"Opaque": {"inputs": ("Inputs/opaque.bin",), "alias": ("old.R", "requested.R")}}
    files = {
        module.ROOT_MARKER: b"Version: 1.0\n",
        "Code/Opaque-Scripts/Opaque-Analysis.R": b"# Unexecuted opaque source\n",
        "Code/Opaque-Scripts/old.R": b"# Same-byte alias\n",
        "Inputs/opaque.bin": b"opaque input",
        "Outputs/Opaque/cached.rds": b"must not be copied",
    }
    archive = tmp_path / "source.zip"
    with ZipFile(archive, "w") as output:
        for name, data in files.items():
            output.writestr(module.PREFIX + name, data)
        output.writestr(module.PREFIX + "Outputs/Opaque/", b"")
    module.ARCHIVE_SHA256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    options = dict(applications=("Opaque",), destination_name="fresh", restore_output_layout=True)
    module.main(tmp_path, **options)
    workspace = tmp_path / "fresh/Opaque"
    assert list((workspace / "Outputs/Opaque").iterdir()) == []
    assert (workspace / "Code/Opaque-Scripts/requested.R").read_bytes() == files["Code/Opaque-Scripts/old.R"]
    assert (workspace / "Inputs/opaque.bin").read_bytes() == files["Inputs/opaque.bin"]
    manifest = json.loads((tmp_path / "fresh/staged_inputs.json").read_text())
    assert "Outputs/Opaque" in manifest["applications"]["Opaque"]["empty_original_output_directories"]
    with pytest.raises(FileExistsError):
        module.main(tmp_path, **options)
