from pathlib import Path

import yaml

from autogpumd.metadata import WorkdirMetadata, write_metadata


def test_write_metadata_preserves_timestamp_for_same_provenance(tmp_path: Path) -> None:
    first = WorkdirMetadata(
        data_mode="MOCK",
        example_type="md",
        source_path="generator",
        original_simulation_results=False,
        parser_assumptions=["mock schema"],
        generated_timestamp="2026-01-01T00:00:00+00:00",
    )
    second = WorkdirMetadata(
        data_mode="MOCK",
        example_type="md",
        source_path="generator",
        original_simulation_results=False,
        parser_assumptions=["mock schema"],
        generated_timestamp="2026-01-02T00:00:00+00:00",
    )

    write_metadata(tmp_path, first)
    path = write_metadata(tmp_path, second)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["generated_timestamp"] == "2026-01-01T00:00:00+00:00"
