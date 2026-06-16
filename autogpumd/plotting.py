"""Plotting helpers for AutoGPUMD analyses."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from pathlib import Path

import pandas as pd


def _pyplot():
    _mpl_config = Path(tempfile.gettempdir()) / "autogpumd-matplotlib"
    _mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(_mpl_config))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_thermo(df: pd.DataFrame, outdir: str | Path) -> dict[str, Path]:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    temp_path = outdir / "temperature.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["time_ps"], df["temperature_K"], color="#2f6f8f")
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Temperature (K)")
    ax.set_title("Temperature vs time")
    fig.tight_layout()
    fig.savefig(temp_path, dpi=180)
    plt.close(fig)

    energy_path = outdir / "energy.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    energy_columns = {
        "Potential": ("potential_energy_eV", "#7a4f9a"),
        "Kinetic": ("kinetic_energy_eV", "#c56b43"),
        "Total": ("total_energy_eV", "#2e7d54"),
    }
    for label, (column, color) in energy_columns.items():
        ax.plot(df["time_ps"], df[column] - df[column].iloc[0], label=label, color=color)
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Energy change from initial value (eV)")
    ax.set_title("Energy drift vs time")
    ax.legend()
    fig.tight_layout()
    fig.savefig(energy_path, dpi=180)
    plt.close(fig)
    return {"temperature": temp_path, "energy": energy_path}


def plot_rdf(rdf_df: pd.DataFrame, outdir: str | Path) -> Path:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "rdf.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rdf_df["r_angstrom"], rdf_df["g_r"], color="#4d6f3a")
    ax.set_xlabel("r (Angstrom)")
    ax.set_ylabel("g(r)")
    ax.set_title("Radial distribution function")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_msd(msd_df: pd.DataFrame, outdir: str | Path) -> Path:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "msd.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(msd_df["time_ps"], msd_df["msd_A2"], color="#8a6f2f")
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("MSD (Angstrom^2)")
    ax.set_title("Mean squared displacement")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_sdc(sdc_df: pd.DataFrame, outdir: str | Path) -> Path:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "sdc.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    if "sdc_from_vac_A2_per_ps" in sdc_df.columns:
        ax.plot(
            sdc_df["time_ps"],
            sdc_df["sdc_from_vac_A2_per_ps"],
            label="SDC from VAC",
            color="#5b6f9f",
        )
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("SDC (Angstrom^2/ps)")
    ax.set_title("Self-diffusion coefficient estimate")
    if ax.get_legend_handles_labels()[0]:
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_loss(loss_df: pd.DataFrame, outdir: str | Path) -> Path:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "loss_curve.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    for column in (
        "total",
        "l1_reg",
        "l2_reg",
        "energy_train",
        "force_train",
        "energy_test",
        "force_test",
    ):
        if column in loss_df.columns:
            ax.loglog(loss_df["generation"], loss_df[column], label=column)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Loss")
    ax.set_title("NEP loss curve")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_parity(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    outdir: str | Path,
    name: str,
    *,
    x_label: str = "DFT reference",
    y_label: str = "NEP prediction",
) -> Path:
    plt = _pyplot()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{name}.png"
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(df[x_col], df[y_col], s=8, alpha=0.45)
    lo = min(float(df[x_col].min()), float(df[y_col].min()))
    hi = max(float(df[x_col].max()), float(df[y_col].max()))
    ax.plot([lo, hi], [lo, hi], color="#333333", linewidth=1)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(name.replace("_", " ").title())
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_workdir(workdir: Path, *, thermo: bool, rdf: bool, msd: bool) -> dict[str, Path]:
    from autogpumd.analysis import THERMO_CANDIDATES, find_first, read_thermo

    workdir = Path(workdir)
    figures = workdir / "figures"
    outputs: dict[str, Path] = {}
    if thermo:
        thermo_csv = workdir / "analysis" / "thermo.csv"
        if thermo_csv.exists():
            outputs.update(plot_thermo(pd.read_csv(thermo_csv), figures))
        else:
            with suppress(FileNotFoundError, ValueError):
                outputs.update(plot_thermo(read_thermo(find_first(workdir, THERMO_CANDIDATES)), figures))
    if rdf:
        rdf_csv = workdir / "analysis" / "rdf.csv"
        if rdf_csv.exists():
            outputs["rdf"] = plot_rdf(pd.read_csv(rdf_csv), figures)
    if msd:
        msd_csv = workdir / "analysis" / "msd.csv"
        if msd_csv.exists():
            outputs["msd"] = plot_msd(pd.read_csv(msd_csv), figures)
        sdc_csv = workdir / "analysis" / "sdc.csv"
        if sdc_csv.exists():
            outputs["sdc"] = plot_sdc(pd.read_csv(sdc_csv), figures)
    return outputs


def plot_nep_workdir(workdir: str | Path) -> dict[str, Path]:
    workdir = Path(workdir)
    figures = workdir / "figures"
    analysis = workdir / "analysis"
    outputs: dict[str, Path] = {}
    loss_csv = analysis / "loss.csv"
    if loss_csv.exists():
        outputs["loss_curve"] = plot_loss(pd.read_csv(loss_csv), figures)
    energy_test = analysis / "energy_test_parity.csv"
    if energy_test.exists():
        outputs["energy_test_parity"] = plot_parity(
            pd.read_csv(energy_test),
            "dft_energy_eV_per_atom",
            "nep_energy_eV_per_atom",
            figures,
            "energy_test_parity",
            x_label="DFT energy (eV/atom)",
            y_label="NEP energy (eV/atom)",
        )
    force_test = analysis / "force_test_parity.csv"
    if force_test.exists():
        outputs["force_test_parity"] = plot_parity(
            pd.read_csv(force_test),
            "dft_force_eV_per_A",
            "nep_force_eV_per_A",
            figures,
            "force_test_parity",
            x_label="DFT force (eV/Angstrom)",
            y_label="NEP force (eV/Angstrom)",
        )
    return outputs
