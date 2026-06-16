"""Import official tutorial-output examples into AutoGPUMD workdirs."""

from __future__ import annotations

import shutil
from pathlib import Path

from autogpumd.metadata import REAL_TUTORIAL_MODE, WorkdirMetadata, now_timestamp, write_metadata


class ImportExampleError(RuntimeError):
    """Raised when an external tutorial example cannot be imported."""


SI_DIFFUSION_SOURCE = Path("examples") / "09_Silicon_diffusion"
SI_DIFFUSION_WORKDIR = Path("examples") / "si_diffusion_real"


def import_example(name: str, source: str | Path, destination_root: str | Path = ".") -> dict[str, Path]:
    if name != "si-diffusion":
        raise ImportExampleError("Only 'si-diffusion' is supported in v0.1.")
    return import_si_diffusion(source=source, destination_root=destination_root)


def import_si_diffusion(
    source: str | Path, destination_root: str | Path = "."
) -> dict[str, Path]:
    source_root = Path(source)
    tutorial_dir = source_root / SI_DIFFUSION_SOURCE
    if not tutorial_dir.exists():
        raise ImportExampleError(
            f"Official Si diffusion tutorial directory not found: {tutorial_dir}"
        )

    destination = Path(destination_root) / SI_DIFFUSION_WORKDIR
    raw_dir = destination / "raw"
    figures_dir = destination / "figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for file_name in ("run.in", "model.xyz", "thermo.out", "msd.out", "sdc.out"):
        src = tutorial_dir / file_name
        if src.exists():
            dst = raw_dir / file_name
            shutil.copy2(src, dst)
            copied.append(dst)

    if not copied:
        raise ImportExampleError(f"No supported Si diffusion tutorial files found in {tutorial_dir}")

    readme = destination / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Si Diffusion Real Tutorial Output",
                "",
                "This workdir imports selected files from the official GPUMD-Tutorials",
                "`examples/09_Silicon_diffusion` example.",
                "",
                "The imported files are tutorial outputs for workflow demonstration and",
                "are not original AutoGPUMD simulation results.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    source_md = destination / "source.md"
    source_md.write_text(
        "\n".join(
            [
                "# Source",
                "",
                "- Data mode: REAL TUTORIAL OUTPUT",
                "- Source repository: https://github.com/brucefan1983/GPUMD-Tutorials",
                "- Source path: `examples/09_Silicon_diffusion`",
                f"- Imported from local path: `{tutorial_dir}`",
                "",
                "These files are imported for learning and workflow demonstration.",
                "They are not original AutoGPUMD simulation results.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    metadata = WorkdirMetadata(
        data_mode=REAL_TUTORIAL_MODE,
        example_type="md",
        source_path="official GPUMD-Tutorials / examples/09_Silicon_diffusion",
        original_simulation_results=False,
        parser_assumptions=[
            "Searches raw/ and workdir root for supported files",
            "thermo.out must include recognizable named columns to be parsed",
            "Si diffusion msd.out follows official plot_results.m; time in column 1 and MSD as mean columns 2-4",
            "Si diffusion sdc.out follows official plot_results.m; time in column 1 and SDC from VAC as mean columns 5-7",
        ],
        generated_timestamp=now_timestamp(),
    )
    metadata_path = write_metadata(destination, metadata)
    report = destination / "report.md"
    if not report.exists():
        report.write_text(
            "# Si Diffusion Tutorial Report\n\nRun `autogpumd report examples/si_diffusion_real`.\n",
            encoding="utf-8",
        )

    return {
        "workdir": destination,
        "raw": raw_dir,
        "readme": readme,
        "source": source_md,
        "metadata": metadata_path,
    }
