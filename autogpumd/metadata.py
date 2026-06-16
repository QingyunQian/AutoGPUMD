"""Workdir metadata and provenance helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import yaml

MOCK_MODE = "MOCK"
REAL_TUTORIAL_MODE = "REAL TUTORIAL OUTPUT"
REAL_GPUMD_MODE = "REAL GPUMD RUN / USER-PROVIDED NEP"


@dataclass(frozen=True)
class WorkdirMetadata:
    data_mode: str
    example_type: str
    source_path: str
    original_simulation_results: bool
    parser_assumptions: list[str]
    generated_timestamp: str


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_metadata(workdir: str | Path, metadata: WorkdirMetadata) -> Path:
    path = Path(workdir) / "metadata.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_metadata(workdir)
    if existing is not None and _same_provenance(existing, metadata):
        metadata = replace(metadata, generated_timestamp=existing.generated_timestamp)
    path.write_text(yaml.safe_dump(asdict(metadata), sort_keys=False), encoding="utf-8")
    return path


def read_metadata(workdir: str | Path) -> WorkdirMetadata | None:
    path = Path(workdir) / "metadata.yaml"
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return WorkdirMetadata(
        data_mode=str(raw.get("data_mode", "")),
        example_type=str(raw.get("example_type", "md")),
        source_path=str(raw.get("source_path", "")),
        original_simulation_results=bool(raw.get("original_simulation_results", False)),
        parser_assumptions=[str(item) for item in raw.get("parser_assumptions", [])],
        generated_timestamp=str(raw.get("generated_timestamp", "")),
    )


def infer_metadata(workdir: str | Path) -> WorkdirMetadata:
    workdir = Path(workdir)
    metadata = read_metadata(workdir)
    if metadata is not None:
        return metadata
    if (workdir / "MOCK_MODE.md").exists() or (workdir / "thermo_mock.csv").exists():
        return WorkdirMetadata(
            data_mode=MOCK_MODE,
            example_type="md",
            source_path="AutoGPUMD deterministic mock generator",
            original_simulation_results=False,
            parser_assumptions=[
                "AutoGPUMD mock thermo CSV schema",
                "AutoGPUMD mock extended XYZ trajectory",
            ],
            generated_timestamp="",
        )
    return WorkdirMetadata(
        data_mode=REAL_GPUMD_MODE,
        example_type="md",
        source_path=str(workdir),
        original_simulation_results=True,
        parser_assumptions=[
            "User-provided or externally generated files in the workdir",
            "Only documented AutoGPUMD-supported parser formats are interpreted",
        ],
        generated_timestamp="",
    )


def mock_metadata() -> WorkdirMetadata:
    return WorkdirMetadata(
        data_mode=MOCK_MODE,
        example_type="md",
        source_path="AutoGPUMD deterministic mock generator",
        original_simulation_results=False,
        parser_assumptions=[
            "thermo_mock.csv uses AutoGPUMD mock thermo columns",
            "trajectory_mock.xyz uses simple extended XYZ frames",
        ],
        generated_timestamp=now_timestamp(),
    )


def _same_provenance(left: WorkdirMetadata, right: WorkdirMetadata) -> bool:
    return (
        left.data_mode == right.data_mode
        and left.example_type == right.example_type
        and left.source_path == right.source_path
        and left.original_simulation_results == right.original_simulation_results
        and left.parser_assumptions == right.parser_assumptions
    )
