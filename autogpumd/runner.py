"""Workflow preparation and execution interfaces."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from autogpumd.config import WorkflowConfig
from autogpumd.mock import generate_mock_outputs
from autogpumd.structure import build_structure, write_structure_files
from autogpumd.templates import write_mock_notes, write_run_in


class WorkflowError(RuntimeError):
    """Raised for preparation or execution failures."""


def prepare_workdir(config: WorkflowConfig, mock: bool = False) -> dict[str, Path]:
    workdir = config.workdir
    workdir.mkdir(parents=True, exist_ok=True)

    if not mock and not config.potential_path.exists():
        raise WorkflowError(
            f"NEP potential not found: {config.potential_path}. "
            "Provide a real nep.txt path or rerun with --mock."
        )

    atoms = build_structure(config.structure)
    outputs = write_structure_files(atoms, workdir)
    outputs["run_in"] = write_run_in(config, workdir, mock=mock)
    if mock:
        outputs["mock_notes"] = write_mock_notes(config, workdir)
    else:
        outputs["potential"] = config.potential_path
    return outputs


def run_workdir(workdir: Path, gpumd: str = "gpumd", mock: bool = False) -> dict[str, Path]:
    workdir = Path(workdir)
    if mock:
        return generate_mock_outputs(workdir)

    run_in = workdir / "run.in"
    if not run_in.exists():
        raise WorkflowError(f"Missing run.in in workdir: {workdir}")

    executable = shutil.which(gpumd)
    if executable is None:
        raise WorkflowError(
            f"GPUMD executable not found: {gpumd}. Install GPUMD, pass --gpumd, or use --mock."
        )

    stdout_path = workdir / "gpumd.stdout"
    stderr_path = workdir / "gpumd.stderr"
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        result = subprocess.run(
            [executable],
            cwd=workdir,
            check=False,
            stdout=stdout,
            stderr=stderr,
            text=True,
        )
    if result.returncode != 0:
        raise WorkflowError(
            f"GPUMD exited with code {result.returncode}. See {stdout_path} and {stderr_path}."
        )
    return {"stdout": stdout_path, "stderr": stderr_path}
