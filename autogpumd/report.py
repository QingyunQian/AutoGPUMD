"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from autogpumd.analysis import read_analysis_summary
from autogpumd.metadata import MOCK_MODE, REAL_TUTORIAL_MODE, infer_metadata


def generate_report(workdir: str | Path) -> Path:
    workdir = Path(workdir)
    metadata = infer_metadata(workdir)
    summary = read_analysis_summary(workdir)
    if metadata.example_type == "nep":
        lines = _nep_report_lines(metadata, summary)
    else:
        lines = _md_report_lines(workdir, metadata, summary)
    report_path = workdir / "report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _md_report_lines(workdir: Path, metadata: Any, summary: dict[str, Any]) -> list[str]:
    thermo_summary = _load_thermo_summary(workdir, summary)
    diffusion = _load_diffusion(workdir)
    skipped = summary.get("skipped", [])
    assumptions = metadata.parser_assumptions or summary.get("parser_assumptions", [])

    lines = [
        "# AutoGPUMD Workflow Report",
        "",
        f"**Data mode: {metadata.data_mode}**",
    ]
    if metadata.data_mode == REAL_TUTORIAL_MODE:
        lines.append(f"**Source: {metadata.source_path}**")
    lines.extend(
        [
            "",
            "## Overview",
            "",
            "AutoGPUMD is an unofficial learning/demo workflow layer around GPUMD/NEP.",
            "It automates setup, execution or import, analysis, plotting, and Markdown reporting.",
            "",
            "## Data provenance",
            "",
            _provenance_text(metadata),
            "",
            "## System and inputs",
            "",
            f"- Example type: `{metadata.example_type}`",
            f"- Source path: `{metadata.source_path}`",
            f"- Original AutoGPUMD simulation results: `{metadata.original_simulation_results}`",
            f"- Workdir: `{workdir}`",
            "",
            "## Thermodynamic stability",
            "",
        ]
    )
    if thermo_summary:
        lines.extend(
            [
                f"- Samples: {thermo_summary['n_samples']:.0f}",
                f"- Mean temperature: {thermo_summary['temperature_mean_K']:.2f} K",
                f"- Temperature standard deviation: {thermo_summary['temperature_std_K']:.2f} K",
                f"- Total energy drift: {thermo_summary['total_energy_drift_eV']:.4f} eV",
                "",
            ]
        )
        if (workdir / "figures" / "temperature.png").exists():
            lines.extend(["![Temperature](figures/temperature.png)", ""])
        if (workdir / "figures" / "energy.png").exists():
            lines.extend(["![Energy](figures/energy.png)", ""])
    else:
        lines.extend(["Thermodynamic output was not available or could not be parsed.", ""])

    lines.extend(["## RDF observations", ""])
    if (workdir / "analysis" / "rdf.csv").exists():
        if metadata.data_mode == MOCK_MODE:
            lines.append(
                "RDF data were generated from the mock XYZ trajectory and illustrate the pipeline, "
                "not a physical pair-correlation result."
            )
        else:
            lines.append("RDF data were generated from a supported XYZ trajectory parser.")
    else:
        lines.append("RDF analysis was not available.")
    lines.append("")
    if (workdir / "figures" / "rdf.png").exists():
        lines.extend(["![RDF](figures/rdf.png)", ""])

    lines.extend(["## MSD and diffusion observations", ""])
    if diffusion is not None:
        lines.append(f"- Estimated diffusion slope proxy: {diffusion:.6f} Angstrom^2/ps")
        if metadata.data_mode == MOCK_MODE:
            lines.append("- Mock-mode MSD is synthetic and should not be read as a real diffusivity.")
        elif metadata.data_mode == REAL_TUTORIAL_MODE:
            lines.append("- Tutorial-output MSD is imported for workflow demonstration.")
        if (workdir / "analysis" / "sdc.csv").exists():
            lines.append("- SDC data were parsed from the tutorial `sdc.out` file when available.")
    else:
        lines.append("MSD/diffusion analysis was not available.")
    lines.append("")
    if (workdir / "figures" / "msd.png").exists():
        lines.extend(["![MSD](figures/msd.png)", ""])
    if (workdir / "figures" / "sdc.png").exists():
        lines.extend(["![SDC](figures/sdc.png)", ""])

    if skipped:
        lines.extend(["## Skipped analyses", ""])
        lines.extend(f"- {item}" for item in skipped)
        lines.append("")

    lines.extend(
        [
            "## Parser assumptions",
            "",
            *(f"- {item}" for item in assumptions),
            "",
            "## Limitations",
            "",
            "- This is not a replacement for GPUMD, gpyumd, GPUMDkit, or official GPUMD tooling.",
            "- Mock data are synthetic and intended only for workflow validation.",
            "- Official tutorial outputs are used only for learning and workflow demonstration.",
            "- Real NEP potentials are never fabricated by this project.",
            "",
            "## Next steps",
            "",
            "- A800 real GPUMD run with a traceable user-provided potential.",
            "- Compact NEP training mini-demo with documented input data provenance.",
            "- High-temperature diffusion and confined-system case studies.",
        ]
    )
    return lines


def _nep_report_lines(metadata: Any, summary: dict[str, Any]) -> list[str]:
    outputs = summary.get("outputs", {})
    skipped = summary.get("skipped", [])
    assumptions = summary.get("parser_assumptions", metadata.parser_assumptions)
    lines = [
        "# AutoGPUMD NEP Workflow Report",
        "",
        f"**Data mode: {metadata.data_mode}**",
        f"**Source: {metadata.source_path}**",
        "",
        "## Overview",
        "",
        (
            "This report summarizes imported NEP tutorial-output files. It does not retrain a "
            "potential and does not claim that the tutorial potential was produced by AutoGPUMD."
        ),
        "",
        "## Data provenance",
        "",
        _provenance_text(metadata),
        "",
        "## Loss curve",
        "",
    ]
    if "loss_csv" in outputs:
        lines.append("Loss data were parsed from `loss.out` using the official tutorial plotting convention.")
        lines.append("")
        lines.append("![Loss curve](figures/loss_curve.png)")
    else:
        lines.append("Loss output was not available or could not be parsed.")
    lines.extend(["", "## Energy and force evaluation", ""])
    if "energy_train_rmse_eV_per_atom" in outputs:
        lines.append(f"- Train energy RMSE: {outputs['energy_train_rmse_eV_per_atom']:.6f} eV/atom")
    if "energy_test_rmse_eV_per_atom" in outputs:
        lines.append(f"- Test energy RMSE: {outputs['energy_test_rmse_eV_per_atom']:.6f} eV/atom")
    if "force_train_rmse_eV_per_A" in outputs:
        lines.append(f"- Train force RMSE: {outputs['force_train_rmse_eV_per_A']:.6f} eV/Angstrom")
    if "force_test_rmse_eV_per_A" in outputs:
        lines.append(f"- Test force RMSE: {outputs['force_test_rmse_eV_per_A']:.6f} eV/Angstrom")
    if "energy_test_parity_csv" in outputs:
        lines.extend(["", "![Energy parity](figures/energy_test_parity.png)"])
    if "force_test_parity_csv" in outputs:
        lines.extend(["", "![Force parity](figures/force_test_parity.png)"])
    if skipped:
        lines.extend(["", "## Skipped analyses", ""])
        lines.extend(f"- {item}" for item in skipped)
    lines.extend(
        [
            "",
            "## Parser assumptions",
            "",
            *(f"- {item}" for item in assumptions),
            "",
            "## Limitations",
            "",
            "- This is not a replacement for GPUMD, GPUMDkit, NEP training tools, or official tutorials.",
            "- Tutorial outputs are used for learning and workflow demonstration.",
            "- Real NEP training decisions require careful dataset, hyperparameter, and validation review.",
            "",
            "## Next steps",
            "",
            "- Extend the same workflow to a small real GPUMD run with a traceable user-provided NEP potential.",
            "- Add a compact NEP training mini-demo only after input data provenance and runtime assumptions are clear.",
            "- Compare tutorial-output diagnostics with future A800-generated outputs.",
        ]
    )
    return lines


def _provenance_text(metadata: Any) -> str:
    if metadata.data_mode == MOCK_MODE:
        return (
            "These are synthetic mock data generated for workflow testing and are not physical "
            "GPUMD simulation results."
        )
    if metadata.data_mode == REAL_TUTORIAL_MODE:
        return (
            "These files are imported from official GPUMD tutorial outputs for learning and "
            "workflow demonstration. They are not original AutoGPUMD simulation results."
        )
    return (
        "This report uses files present in the workdir as user-provided or externally generated "
        "simulation outputs. Verify GPUMD, input, potential, and output provenance before citation."
    )


def _load_thermo_summary(workdir: Path, summary: dict[str, Any]) -> dict[str, float] | None:
    raw = summary.get("outputs", {}).get("thermo_summary")
    if isinstance(raw, dict):
        return {str(key): float(value) for key, value in raw.items()}
    path = workdir / "analysis" / "thermo_summary.csv"
    if not path.exists():
        return None
    return pd.read_csv(path).iloc[0].to_dict()


def _load_diffusion(workdir: Path) -> float | None:
    path = workdir / "analysis" / "diffusion.csv"
    if not path.exists():
        return None
    return float(pd.read_csv(path)["diffusion_A2_per_ps"].iloc[0])
