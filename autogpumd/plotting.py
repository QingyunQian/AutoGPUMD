"""Plotting helpers for AutoGPUMD analyses."""

from __future__ import annotations

import os
import tempfile
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
    ax.plot(df["time_ps"], df["potential_energy_eV"], label="Potential", color="#7a4f9a")
    ax.plot(df["time_ps"], df["kinetic_energy_eV"], label="Kinetic", color="#c56b43")
    ax.plot(df["time_ps"], df["total_energy_eV"], label="Total", color="#2e7d54")
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Energy (eV)")
    ax.set_title("Energy vs time")
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


def plot_workdir(workdir: Path, *, thermo: bool, rdf: bool, msd: bool) -> dict[str, Path]:
    from autogpumd.analysis import THERMO_CANDIDATES, find_first, read_thermo

    workdir = Path(workdir)
    figures = workdir / "figures"
    outputs: dict[str, Path] = {}
    if thermo:
        outputs.update(plot_thermo(read_thermo(find_first(workdir, THERMO_CANDIDATES)), figures))
    if rdf:
        rdf_csv = workdir / "analysis" / "rdf.csv"
        if rdf_csv.exists():
            outputs["rdf"] = plot_rdf(pd.read_csv(rdf_csv), figures)
    if msd:
        msd_csv = workdir / "analysis" / "msd.csv"
        if msd_csv.exists():
            outputs["msd"] = plot_msd(pd.read_csv(msd_csv), figures)
    return outputs
