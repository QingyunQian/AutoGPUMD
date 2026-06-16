"""Import official tutorial-output examples into AutoGPUMD workdirs."""

from __future__ import annotations

import shutil
from pathlib import Path

from autogpumd.metadata import REAL_TUTORIAL_MODE, WorkdirMetadata, now_timestamp, write_metadata


class ImportExampleError(RuntimeError):
    """Raised when an external tutorial example cannot be imported."""


SI_DIFFUSION_SOURCE = Path("examples") / "09_Silicon_diffusion"
SI_DIFFUSION_WORKDIR = Path("examples") / "si_diffusion_real"
PBTE_NEP_SOURCE = Path("examples") / "11_NEP_potential_PbTe"
PBTE_NEP_WORKDIR = Path("examples") / "pbte_nep_real"


def import_example(name: str, source: str | Path, destination_root: str | Path = ".") -> dict[str, Path]:
    if name == "si-diffusion":
        return import_si_diffusion(source=source, destination_root=destination_root)
    if name == "pbte-nep":
        return import_pbte_nep(source=source, destination_root=destination_root)
    raise ImportExampleError("Supported examples: 'si-diffusion', 'pbte-nep'.")


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


def import_pbte_nep(source: str | Path, destination_root: str | Path = ".") -> dict[str, Path]:
    source_root = Path(source)
    tutorial_dir = source_root / PBTE_NEP_SOURCE
    if not tutorial_dir.exists():
        raise ImportExampleError(f"Official PbTe NEP tutorial directory not found: {tutorial_dir}")

    destination = Path(destination_root) / PBTE_NEP_WORKDIR
    raw_dir = destination / "raw"
    figures_dir = destination / "figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for file_name in (
        "nep.in",
        "nep.txt",
        "train.xyz",
        "test.xyz",
        "loss.out",
        "energy_train.out",
        "energy_test.out",
        "force_train.out",
        "force_test.out",
    ):
        src = tutorial_dir / file_name
        if src.exists():
            dst = raw_dir / file_name
            shutil.copy2(src, dst)
            copied.append(dst)

    if not copied:
        raise ImportExampleError(f"No supported PbTe NEP tutorial files found in {tutorial_dir}")

    readme = destination / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# PbTe NEP Real Tutorial Output",
                "",
                "This workdir imports selected files from the official GPUMD-Tutorials",
                "`examples/11_NEP_potential_PbTe` example.",
                "",
                "The imported files are tutorial outputs for workflow demonstration and",
                "are not original AutoGPUMD training results.",
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
                "- Source path: `examples/11_NEP_potential_PbTe`",
                f"- Imported from local path: `{tutorial_dir}`",
                "",
                "These files are imported for learning and workflow demonstration.",
                "They are not original AutoGPUMD training results.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    metadata = WorkdirMetadata(
        data_mode=REAL_TUTORIAL_MODE,
        example_type="nep",
        source_path="official GPUMD-Tutorials / examples/11_NEP_potential_PbTe",
        original_simulation_results=False,
        parser_assumptions=[
            "loss.out follows official plot_results.m columns",
            "energy_*.out columns are NEP energy then DFT energy",
            "force_*.out columns 1-3 are NEP force components and columns 4-6 are DFT force components",
        ],
        generated_timestamp=now_timestamp(),
    )
    metadata_path = write_metadata(destination, metadata)
    report = destination / "report.md"
    if not report.exists():
        report.write_text(
            "# PbTe NEP Tutorial Report\n\nRun `autogpumd analyze-nep examples/pbte_nep_real`.\n",
            encoding="utf-8",
        )

    return {
        "workdir": destination,
        "raw": raw_dir,
        "readme": readme,
        "source": source_md,
        "metadata": metadata_path,
    }
