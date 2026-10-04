"""Prepare only the declared journal inputs; no agent or scientific execution."""

import argparse
from hashlib import sha256
from importlib.metadata import version
import io
import json
import logging
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

from pypdf import PdfReader

from ai_statistician.research_schema import load_open_research_questions
from ai_statistician.research_source_library import load_research_source_snapshot


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": sha256(raw).hexdigest(), "byte_size": len(raw)}


def archive_files(path, kind):
    if kind == "package":
        with tarfile.open(path) as archive:
            for member in archive.getmembers():
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError(f"not a regular archive file: {member.name}")
                with archive.extractfile(member) as stream:
                    yield member.name, stream.read(), member.mode
    else:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                mode = member.external_attr >> 16
                if mode & 0o170000 not in (0, 0o100000):
                    raise ValueError(f"not a regular archive file: {member.filename}")
                yield member.filename, archive.read(member), mode


def prepare(out):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError("use a fresh preparation directory; no overwrite")
    questions = {q.id for q in load_open_research_questions(HERE / "questions.json")}
    plan = json.loads((HERE / "input_plan.json").read_bytes())
    if {row["question_id"] for row in plan} != questions or len(plan) != len(questions):
        raise ValueError("input plan must bind every candidate exactly once")
    verified = {}
    for row in plan:
        for kind in ("paper", "package", "replication"):
            path = REPO / row[kind]["path"]
            ref = identity(path)
            if ref["sha256"] != row[kind]["sha256"]:
                raise ValueError(f"original input identity mismatch: {path}")
            verified[row["question_id"], kind] = ref
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for row in plan:
        destination = out / row["snapshot_id"]
        source_root = destination / "sources"
        source_root.mkdir(parents=True)
        documents, excluded = [], []

        def add(relative_path, raw, kind, asset, mode=0o644):
            relative = PurePosixPath(relative_path)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe source path")
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
            file_mode = "100755" if mode & 0o111 else "100644"
            path.chmod(0o755 if file_mode == "100755" else 0o644)
            try:
                raw.decode("utf-8")
                content_mode = "text"
            except UnicodeDecodeError:
                content_mode = "binary"
            if relative.suffix.lower() == ".pdf":
                content_mode, media = "binary", "application/pdf"
            else:
                media = "text/plain" if content_mode == "text" else "application/octet-stream"
            documents.append({"document_id": relative.as_posix(),
                "title": row["title"] + ": " + relative.as_posix(),
                "source_kind": kind, "relative_path": relative.as_posix(),
                "sha256": sha256(raw).hexdigest(), "byte_size": len(raw),
                "content_mode": content_mode, "media_type": media,
                "file_mode": file_mode, "model_visible": True,
                "citation": "doi:" + row["doi"], "url": asset["url"],
                "publication_date": row["publication_date"],
                "license": asset["license_context"]})

        paper_path = Path(verified[row["question_id"], "paper"]["path"])
        add("paper/article.pdf", paper_path.read_bytes(), "paper", row["paper"])
        messages = io.StringIO()
        handler = logging.StreamHandler(messages)
        logger = logging.getLogger("pypdf")
        logger.addHandler(handler)
        try:
            reader = PdfReader(paper_path)
            pages = [page.extract_text(extraction_mode="layout") for page in reader.pages]
        finally:
            logger.removeHandler(handler)
        if not all(isinstance(page, str) and page.strip() for page in pages):
            raise ValueError("paper extraction contains an empty page; no OCR or content repair")
        text = "\n\n".join(f"[PDF page {number}]\n{text}" for number, text in enumerate(pages, 1)) + "\n"
        add("paper/article.txt", text.encode("utf-8"), "paper_text_extraction", row["paper"])

        for kind in ("package", "replication"):
            asset = row[kind]
            for name, raw, mode in archive_files(Path(verified[row["question_id"], kind]["path"]), kind):
                original = PurePosixPath(name)
                if original.is_absolute() or ".." in original.parts or not name.startswith(asset["root"]):
                    raise ValueError(f"unexpected archive path: {name}")
                relative = name[len(asset["root"]):]
                if any(relative.startswith(prefix) for prefix in asset["excluded_prefixes"]):
                    excluded.append({"archive_kind": kind, "member": name,
                        "sha256": sha256(raw).hexdigest(), "byte_size": len(raw),
                        "reason": asset["exclusion_reason"]})
                    continue
                add(kind + "/" + relative, raw, "author_" + kind, asset, mode)

        manifest = destination / "research_sources.json"
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump({"schema_version": 1, "snapshot_id": row["snapshot_id"],
                "source_horizon": row["publication_date"], "source_root": "sources",
                "documents": sorted(documents, key=lambda item: item["document_id"])}, stream, indent=2)
            stream.write("\n")
        snapshot = load_research_source_snapshot(manifest)
        errors = snapshot.identity_errors()
        if errors:
            raise ValueError("; ".join(errors))
        read = snapshot.read("paper/article.txt", line_start=1, line_end=3)
        search = snapshot.search(row["title"], top_k=1)
        records.append({"question_id": row["question_id"], "manifest_ref": identity(manifest),
            "snapshot": snapshot.descriptor(),
            "original_assets": {kind: verified[row["question_id"], kind] for kind in ("paper", "package", "replication")},
            "exclusions": excluded,
            "extraction": {"parser": "pypdf", "version": version("pypdf"),
                "mode": "layout", "page_marker": "[PDF page N]", "pages": len(pages),
                "warnings": messages.getvalue(), "text_sha256": snapshot.document("paper/article.txt").sha256,
                "semantic_or_visual_fidelity_qualified": False},
            "static_tool_checks": {"identity_errors": errors, "paper_read_ok": read["ok"],
                "search_hit_count": len(search["hits"]),
                "registered_file_count": len(snapshot.documents),
                "binary_assets": [item.relative_path for item in snapshot.documents if item.content_mode == "binary"]}})
    record = {"scope": "candidate_source_input_preparation_only", "study_activated": False,
        "model_calls": 0, "scientific_scripts_executed": 0, "mathematical_assessments": 0,
        "plan_ref": identity(HERE / "input_plan.json"), "questions_ref": identity(HERE / "questions.json"),
        "preparer_ref": identity(Path(__file__)), "candidates": records,
        "authority": "Existing ResearchSourceSnapshot identity/read/search, not source execution, scientific validity, blind rediscovery, release rights or arm qualification."}
    with (out / "input_preparation.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    result = prepare(parser.parse_args().out)
    print(json.dumps({"scope": result["scope"], "model_calls": 0,
        "snapshots": [{"question_id": row["question_id"], "snapshot_hash": row["snapshot"]["snapshot_hash"],
            "document_count": row["snapshot"]["document_count"]} for row in result["candidates"]]}))
