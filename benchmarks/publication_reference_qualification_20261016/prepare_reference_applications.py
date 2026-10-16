"""Stage the declared original application port, never cached author outcomes."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ARCHIVE_SHA256 = "de336cc76ee769d5a0d5d1246566b760475f266a6f8b9c4321991b38a01a20fa"
PREFIX = "HonestParallelTrends_RESTUD_ReplicationFiles/"
ROOT_MARKER = "HonestParallelTrends_RESTUD_ReplicationFiles.Rproj"
APPLICATIONS = {
    "BenzartiCarloni": {
        "inputs": (
            "Inputs/BenzartiCarloni/beta_l_r_plbt.dta",
            "Inputs/BenzartiCarloni/vcv_l_r_plbt.dta",
        ),
        "alias": ("BenzartiCarloni-estimateIDSets.R", "BenzartiCarloni-estimateIDsets.R"),
    },
    "LovenheimWillen": {
        "inputs": (
            "Inputs/LovenheimWillen/Data files/Estimation samples/Estimation_MALE.dta",
            "Inputs/LovenheimWillen/Data files/Estimation samples/Estimation_FEMALE.dta",
        ),
        "alias": ("LovenheimWillein-compareCIvsIDsets.R", "LovenheimWillen-compareCIvsIDsets.R"),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(root: Path) -> None:
    archive = root / "source.zip"
    if sha256(archive) != ARCHIVE_SHA256:
        raise ValueError("Original archive identity differs from the frozen plan")
    destination = root / "applications_path_port_20261016"
    destination.mkdir(exist_ok=False)
    manifest = {"archive_sha256": ARCHIVE_SHA256, "applications": {}}
    with ZipFile(archive) as source:
        for app, spec in APPLICATIONS.items():
            workspace = destination / app
            workspace.mkdir()
            code_dir = f"Code/{app}-Scripts/"
            names = sorted(name for name in source.namelist() if name.startswith(PREFIX)
                           and (name[len(PREFIX):] in (*spec["inputs"], ROOT_MARKER)
                                or (name.endswith(".R") and name[len(PREFIX):].startswith(
                                    (code_dir, "Code/UtilityFunctions/")))))
            files = []
            for name in names:
                relative = PurePosixPath(name[len(PREFIX):])
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError(f"Unsafe archive member: {name}")
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(name) as incoming, target.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                files.append({"path": str(relative), "sha256": sha256(target),
                              "bytes": target.stat().st_size, "archive_member": name})
            for required in (*spec["inputs"], ROOT_MARKER, f"{code_dir}{app}-Analysis.R"):
                if not (workspace / required).is_file():
                    raise ValueError(f"Missing original application input: {required}")
            old, new = (workspace / code_dir / name for name in spec["alias"])
            if new.exists():
                raise ValueError(f"Declared alias already exists: {new}")
            shutil.copyfile(old, new)
            assert sha256(old) == sha256(new)
            for directory in ("Temp", "Outputs", "Figures"):
                (workspace / directory).mkdir()
            manifest["applications"][app] = {
                "entry": f"{code_dir}{app}-Analysis.R", "files": files,
                "same_byte_alias": {"source": str(old.relative_to(workspace)),
                                    "target": str(new.relative_to(workspace)),
                                    "sha256": sha256(new)},
            }
    with (destination / "staged_inputs.json").open("x") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    print(f"Staged original sources and four input files: {destination}")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
