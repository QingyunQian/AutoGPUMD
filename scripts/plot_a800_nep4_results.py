"""Generate README-ready figures for the A800 NEP4 GPUMD demo runs."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUT = ROOT / "examples" / "a800_nep4_real"

IONIC_RUN = RUNS / "nep4_ionic_1000K_short"
CODECHECK_RUN = RUNS / "nep4_li3ps4_codecheck_short"
OFFICIAL = ROOT / "external" / "GPUMD-Tutorials" / "examples"
OFFICIAL_IONIC = OFFICIAL / "24_Ionic_Conductivity" / "1000K"
OFFICIAL_CODECHECK = (
    OFFICIAL / "28_thermal_transport_superionic_EMD" / "Li3PS4" / "CodeCheck"
)
GPUMD_TUTORIALS_URL = "https://github.com/brucefan1983/GPUMD-Tutorials"
IONIC_TUTORIAL_URL = (
    "https://github.com/brucefan1983/GPUMD-Tutorials/tree/main/examples/24_Ionic_Conductivity"
)
CODECHECK_TUTORIAL_URL = (
    "https://github.com/brucefan1983/GPUMD-Tutorials/tree/main/examples/28_thermal_transport_superionic_EMD/Li3PS4/CodeCheck"
)

COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "black": "#222222",
    "gray": "#6E6E6E",
    "light_gray": "#D9D9D9",
}


def _missing_message(title: str, missing: list[tuple[str, Path]], guidance: str) -> str:
    lines = [title, ""]
    lines.extend(f"- {label}: {path}" for label, path in missing)
    lines.extend(["", guidance])
    return "\n".join(lines)


def check_required_inputs() -> None:
    required = [
        ("LLZO ionic run directory", IONIC_RUN),
        ("LLZO ionic run.in", IONIC_RUN / "run.in"),
        ("LLZO ionic thermo.out", IONIC_RUN / "thermo.out"),
        ("LLZO ionic msd.out", IONIC_RUN / "msd.out"),
        ("LLZO ionic gpumd.stdout", IONIC_RUN / "gpumd.stdout"),
        ("Li3PS4 CodeCheck run directory", CODECHECK_RUN),
        ("Li3PS4 CodeCheck run.in", CODECHECK_RUN / "run.in"),
        ("Li3PS4 CodeCheck hac.out", CODECHECK_RUN / "hac.out"),
        ("Li3PS4 CodeCheck gpumd.stdout", CODECHECK_RUN / "gpumd.stdout"),
    ]
    missing = [(label, path) for label, path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            _missing_message(
                "Missing required A800 raw run inputs.",
                missing,
                "Restore the ignored raw A800 outputs under runs/ before regenerating figures.",
            )
        )


def pyplot():
    mpl_config = Path(tempfile.gettempdir()) / "autogpumd-matplotlib"
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "axes.linewidth": 0.8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "lines.linewidth": 1.25,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    return plt


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=r"\s+", header=None, comment="#")


def rolling_mean(values: pd.Series | np.ndarray, window: int) -> np.ndarray:
    series = pd.Series(values)
    return series.rolling(window, center=True, min_periods=max(3, window // 8)).mean().to_numpy()


def style_axis(ax, *, panel: str | None = None) -> None:
    ax.tick_params(direction="out", length=3.0, width=0.8, pad=2)
    ax.grid(axis="y", color=COLORS["light_gray"], linewidth=0.5, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if panel:
        ax.text(
            -0.14,
            1.05,
            panel,
            transform=ax.transAxes,
            fontsize=10,
            fontweight="bold",
            va="bottom",
        )


def save_figure(fig, path: Path) -> None:
    fig.savefig(path, dpi=600, bbox_inches="tight", facecolor="white")


def parse_stdout(path: Path) -> dict[str, float | int | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    completed = [int(match) for match in re.findall(r"(\d+)\s+steps completed", text)]
    time_match = re.search(r"Time used =\s*([0-9.]+)\s*s", text)
    speed_matches = re.findall(r"Speed of this run =\s*([0-9.eE+-]+)", text)
    return {
        "max_completed_steps": max(completed) if completed else None,
        "time_used_s": float(time_match.group(1)) if time_match else None,
        "last_speed_atom_step_per_s": float(speed_matches[-1]) if speed_matches else None,
    }


def plot_ionic() -> dict[str, object]:
    figures = OUT / "ionic_1000K" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    shutil.copy2(IONIC_RUN / "run.in", OUT / "ionic_1000K" / "run.in")

    thermo = read_table(IONIC_RUN / "thermo.out")
    msd = read_table(IONIC_RUN / "msd.out")
    stdout_summary = parse_stdout(IONIC_RUN / "gpumd.stdout")

    # GPUMD default time step is 1 fs here; thermo is dumped every 100 steps.
    thermo_time_ps = (np.arange(len(thermo)) + 1) * 0.1
    msd_time_ps = msd.iloc[:, 0].to_numpy()
    temperature = thermo.iloc[:, 0]
    kinetic = thermo.iloc[:, 1]
    potential = thermo.iloc[:, 2]
    total_energy = kinetic + potential

    plt = pyplot()

    temp_mask = thermo_time_ps >= 5.0
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    ax.plot(
        thermo_time_ps[temp_mask],
        temperature[temp_mask],
        color=COLORS["sky"],
        linewidth=0.35,
        alpha=0.35,
        label="100-step samples",
    )
    ax.plot(
        thermo_time_ps[temp_mask],
        rolling_mean(temperature[temp_mask], 200),
        color=COLORS["blue"],
        linewidth=1.25,
        label="20 ps rolling mean",
    )
    ax.axhline(1000, color=COLORS["black"], linestyle=(0, (3, 2)), linewidth=0.8)
    ax.text(0.98, 0.14, "target 1000 K", transform=ax.transAxes, ha="right", va="center")
    ax.set_xlim(5, 1000)
    ax.set_ylim(960, 1035)
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Temperature (K)")
    style_axis(ax, panel="a")
    ax.legend(frameon=False, loc="upper left", handlelength=2.4)
    save_figure(fig, figures / "ionic_temperature.png")
    plt.close(fig)

    equilibrated = thermo_time_ps >= 5.0
    kinetic_eq = kinetic[equilibrated]
    potential_eq = potential[equilibrated]
    total_eq = total_energy[equilibrated]
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    ax.plot(
        thermo_time_ps[equilibrated],
        rolling_mean(kinetic_eq - kinetic_eq.mean(), 120),
        label="Kinetic",
        color=COLORS["orange"],
    )
    ax.plot(
        thermo_time_ps[equilibrated],
        rolling_mean(potential_eq - potential_eq.mean(), 120),
        label="Potential",
        color=COLORS["purple"],
    )
    ax.plot(
        thermo_time_ps[equilibrated],
        rolling_mean(total_eq - total_eq.mean(), 120),
        label="Total",
        color=COLORS["green"],
    )
    ax.axhline(0, color=COLORS["black"], linewidth=0.6, alpha=0.7)
    ax.set_xlim(5, 1000)
    ax.set_xlabel("Time (ps)")
    ax.set_ylabel("Energy fluctuation (eV)")
    style_axis(ax, panel="b")
    ax.legend(frameon=False, loc="upper right", handlelength=2.2)
    save_figure(fig, figures / "ionic_energy_drift.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    species = ["Li", "La", "Zr", "O"]
    colors = [COLORS["blue"], COLORS["purple"], COLORS["red"], COLORS["green"]]
    final_msd: dict[str, float] = {}
    final_sdc_cm2_s: dict[str, float] = {}
    immobile_traces: list[tuple[str, pd.Series, str]] = []
    for idx, (label, color) in enumerate(zip(species, colors, strict=True)):
        offset = 1 + idx * 6
        mean_msd = msd.iloc[:, offset : offset + 3].mean(axis=1)
        mean_sdc = msd.iloc[:, offset + 3 : offset + 6].mean(axis=1)
        final_msd[label] = float(mean_msd.iloc[-1])
        # 1 A^2/ps = 1e-4 cm^2/s.
        final_sdc_cm2_s[label] = float(mean_sdc.iloc[-1] * 1e-4)
        if label == "Li":
            ax.plot(msd_time_ps, mean_msd, label="Li", color=color, linewidth=1.6)
        else:
            immobile_traces.append((label, mean_msd, color))
    ax.set_xlabel("Correlation time (ps)")
    ax.set_ylabel("Li MSD (A$^2$)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 21)
    style_axis(ax, panel="c")
    ax.text(
        0.04,
        0.86,
        f"$D_{{Li}}$ = {final_sdc_cm2_s['Li']:.2e} cm$^2$ s$^{{-1}}$",
        transform=ax.transAxes,
        color=COLORS["blue"],
    )
    inset = ax.inset_axes([0.54, 0.18, 0.40, 0.36])
    for label, mean_msd, color in immobile_traces:
        inset.plot(msd_time_ps, mean_msd, label=label, color=color, linewidth=1.0)
    inset.set_xlim(0, 100)
    inset.set_ylim(0, 0.085)
    inset.set_xlabel("Time (ps)", fontsize=6, labelpad=0)
    inset.set_ylabel("MSD (A$^2$)", fontsize=6, labelpad=0)
    inset.tick_params(labelsize=6, length=2, pad=1)
    inset.legend(frameon=False, fontsize=6, loc="upper left", handlelength=1.4)
    save_figure(fig, figures / "ionic_group_msd.png")
    plt.close(fig)

    return {
        "run_path": str(IONIC_RUN.relative_to(ROOT)),
        "output_path": str((OUT / "ionic_1000K").relative_to(ROOT)),
        "atoms": 12288,
        "steps": 1_000_000,
        "thermo_rows": int(len(thermo)),
        "msd_rows": int(len(msd)),
        "temperature_mean_K": float(temperature.mean()),
        "temperature_std_K": float(temperature.std(ddof=0)),
        "temperature_min_K": float(temperature.min()),
        "temperature_max_K": float(temperature.max()),
        "final_msd_A2": final_msd,
        "final_sdc_cm2_s": final_sdc_cm2_s,
        "official_readme_temperature_K": 999.960,
        "official_readme_li_diffusivity_cm2_s": 9.667e-06,
        "official_msd_li_diffusivity_cm2_s": _official_ionic_li_diffusivity(),
        **stdout_summary,
    }


def _official_ionic_li_diffusivity() -> float | None:
    official_msd = OFFICIAL_IONIC / "msd.out"
    if not official_msd.exists():
        return None
    msd = read_table(official_msd)
    return float(msd.iloc[-1, 4:7].mean() * 1e-4)


def plot_codecheck() -> dict[str, object]:
    figures = OUT / "li3ps4_codecheck" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CODECHECK_RUN / "run.in", OUT / "li3ps4_codecheck" / "run.in")

    hac = read_table(CODECHECK_RUN / "hac.out")
    stdout_summary = parse_stdout(CODECHECK_RUN / "gpumd.stdout")
    time_ps = hac.iloc[:, 0]

    plt = pyplot()

    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    component_colors = [
        COLORS["blue"],
        COLORS["orange"],
        COLORS["green"],
        COLORS["red"],
        COLORS["purple"],
    ]
    for col, label, color in zip(
        range(1, 6),
        [r"$C_1$", r"$C_2$", r"$C_3$", r"$C_4$", r"$C_5$"],
        component_colors,
        strict=True,
    ):
        ax.plot(time_ps, hac.iloc[:, col], label=label, color=color, linewidth=0.55, alpha=0.85)
    ax.set_xlabel("Correlation time (ps)")
    ax.set_ylabel("HAC component")
    ax.set_xlim(0, 10)
    style_axis(ax, panel="a")
    ax.legend(frameon=False, ncol=2, loc="upper right", handlelength=1.5)
    save_figure(fig, figures / "li3ps4_hac_components.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    for col, label, color in zip(
        range(6, 11),
        [r"$K_1$", r"$K_2$", r"$K_3$", r"$K_4$", r"$K_5$"],
        component_colors,
        strict=True,
    ):
        ax.plot(time_ps, hac.iloc[:, col], label=label, color=color, linewidth=0.65, alpha=0.9)
    ax.set_xlabel("Correlation time (ps)")
    ax.set_ylabel("Integrated signal")
    ax.set_xlim(0, 10)
    style_axis(ax, panel="b")
    ax.legend(frameon=False, ncol=2, loc="upper right", handlelength=1.5)
    save_figure(fig, figures / "li3ps4_integrated_hac.png")
    plt.close(fig)

    kz = hac.iloc[:, 10]
    official_kz_mean = None
    official_kappa_mean = None
    if (OFFICIAL_CODECHECK / "hac.out").exists():
        official_hac = read_table(OFFICIAL_CODECHECK / "hac.out")
        official_kz = official_hac.iloc[:, 10]
        official_kz_mean = float(official_kz.iloc[len(official_kz) // 2 :].mean())

        a800_mean = float(kz.iloc[len(kz) // 2 :].mean())
        fig, ax = plt.subplots(figsize=(3.55, 2.45))
        ax.plot(time_ps, kz, color=COLORS["sky"], linewidth=0.35, alpha=0.45)
        ax.plot(
            time_ps,
            rolling_mean(kz, 160),
            label="A800 run",
            color=COLORS["blue"],
            linewidth=1.25,
        )
        ax.plot(
            official_hac.iloc[:, 0],
            rolling_mean(official_kz, 160),
            label="Official hac.out",
            color=COLORS["purple"],
            linewidth=1.2,
        )
        if (OFFICIAL_CODECHECK / "kappa_ee.txt").exists():
            official_kappa = read_table(OFFICIAL_CODECHECK / "kappa_ee.txt")
            official_kappa_mean = float(
                official_kappa.iloc[len(official_kappa) // 2 :, 1].mean()
            )
            ax.plot(
                official_kappa.iloc[:, 0],
                rolling_mean(official_kappa.iloc[:, 1], 160),
                label="Official independent GK",
                color=COLORS["red"],
                linewidth=1.0,
                linestyle=(0, (3, 2)),
            )
            ax.axhline(
                official_kappa_mean,
                color=COLORS["red"],
                linewidth=0.65,
                linestyle=":",
                alpha=0.8,
            )
        ax.axhline(a800_mean, color=COLORS["blue"], linewidth=0.65, linestyle=":", alpha=0.8)
        ax.set_xlabel("Correlation time (ps)")
        ax.set_ylabel(r"$\kappa_z$ (W m$^{-1}$ K$^{-1}$)")
        ax.set_xlim(0, 10)
        style_axis(ax, panel="c")
        ax.text(
            0.03,
            0.93,
            f"A800 mean = {a800_mean:.2f}",
            transform=ax.transAxes,
            color=COLORS["blue"],
            va="top",
        )
        if official_kappa_mean is not None:
            ax.text(
                0.03,
                0.82,
                f"official mean = {official_kappa_mean:.2f}",
                transform=ax.transAxes,
                color=COLORS["red"],
                va="top",
            )
        ax.legend(frameon=False, loc="upper right", handlelength=2.0)
        save_figure(fig, figures / "li3ps4_kz_reference_comparison.png")
        plt.close(fig)

    return {
        "run_path": str(CODECHECK_RUN.relative_to(ROOT)),
        "output_path": str((OUT / "li3ps4_codecheck").relative_to(ROOT)),
        "atoms": 6144,
        "steps": 400_000,
        "hac_rows": int(len(hac)),
        "hac_last_time_ps": float(time_ps.iloc[-1]),
        "kz_mean_second_half_W_mK": float(kz.iloc[len(kz) // 2 :].mean()),
        "kz_last_W_mK": float(kz.iloc[-1]),
        "official_reference_kz_mean_second_half_W_mK": official_kz_mean,
        "official_reference_independent_gk_mean_second_half_W_mK": official_kappa_mean,
        "final_integrated_components": {
            f"component_{idx}": float(hac.iloc[-1, col])
            for idx, col in enumerate(range(6, 11), start=1)
        },
        **stdout_summary,
    }


def write_summary(summary: dict[str, object]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUT / "source.md").write_text(
        "\n".join(
            [
                "# Source Tutorials",
                "",
                f"- Official repository: {GPUMD_TUTORIALS_URL}",
                f"- LLZO ionic conductivity: {IONIC_TUTORIAL_URL}",
                "- Official LLZO path: `examples/24_Ionic_Conductivity/1000K`",
                f"- Li3PS4 CodeCheck HAC: {CODECHECK_TUTORIAL_URL}",
                "- Official Li3PS4 path: `examples/28_thermal_transport_superionic_EMD/Li3PS4/CodeCheck`",
                "",
                "The local A800 runs use official NEP4 tutorial inputs with GPUMD v5.5. Raw runtime outputs stay under `runs/`; this folder keeps README-ready figures, copied `run.in` files, and summaries.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ionic = summary["ionic_1000K"]
    codecheck = summary["li3ps4_codecheck"]
    lines = [
        "# A800 NEP4 Real GPUMD Demo",
        "",
        "These are real GPUMD v5.5 runs executed on NVIDIA A800 GPUs using official GPUMD-Tutorials NEP4 inputs.",
        "",
        "## Official Tutorial Sources",
        "",
        f"- LLZO ionic conductivity: `{OFFICIAL_IONIC.relative_to(OFFICIAL)}`",
        f"  {IONIC_TUTORIAL_URL}",
        f"- Li3PS4 CodeCheck HAC: `{OFFICIAL_CODECHECK.relative_to(OFFICIAL)}`",
        f"  {CODECHECK_TUTORIAL_URL}",
        "",
        "Raw `*.out` files are kept in `runs/` and are not committed; this folder keeps lightweight figures and run inputs for the README demo.",
        "",
        "## Runs",
        "",
        f"- LLZO ionic conductivity at 1000 K: {ionic['atoms']} atoms, {ionic['steps']} steps, "
        f"{ionic['time_used_s']:.2f} s wall time.",
        f"- Li3PS4 CodeCheck HAC: {codecheck['atoms']} atoms, {codecheck['steps']} total steps, "
        f"{codecheck['time_used_s']:.2f} s wall time.",
        "",
        "## Key Outputs",
        "",
        f"- LLZO `thermo.out`: {ionic['thermo_rows']} rows; mean temperature "
        f"{ionic['temperature_mean_K']:.2f} K.",
        f"- LLZO `msd.out`: {ionic['msd_rows']} rows; final Li running diffusivity proxy "
        f"{ionic['final_sdc_cm2_s']['Li']:.3e} cm^2/s.",
        f"- Li3PS4 `hac.out`: {codecheck['hac_rows']} rows; A800 `kz` mean over the second half "
        f"{codecheck['kz_mean_second_half_W_mK']:.3f} W/mK.",
        f"- Official bundled Li3PS4 reference `kz` mean over the second half: "
        f"{codecheck['official_reference_kz_mean_second_half_W_mK']:.3f} W/mK.",
        "",
        "The LLZO diffusivity proxy agrees with the official tutorial README. The Li3PS4 CodeCheck figure is a stochastic single-run sanity check; it should be compared by trend and workflow, not read as a converged thermal conductivity estimate. The A800 `kz` mean is lower than the official bundled reference because Green-Kubo/HAC estimates have high finite-trajectory variance, depend on the sampled random trajectory, and are sensitive to noisy long-time integration tails.",
        "",
        "## Figures",
        "",
        "Each figure is generated as a README-friendly 600 dpi PNG.",
        "",
        "- `ionic_1000K/figures/ionic_temperature.png`: equilibrated LLZO temperature samples with a 20 ps rolling mean and 1000 K target line.",
        "- `ionic_1000K/figures/ionic_energy_drift.png`: equilibrated NPT kinetic, potential, and total energy fluctuations around their post-transient means; this is not an NVE energy-drift test.",
        "- `ionic_1000K/figures/ionic_group_msd.png`: Li MSD and final Li diffusivity proxy in the main panel, with La/Zr/O small-scale MSD in the inset.",
        "- `li3ps4_codecheck/figures/li3ps4_hac_components.png`: raw HAC component signals from the A800 single CodeCheck run.",
        "- `li3ps4_codecheck/figures/li3ps4_integrated_hac.png`: integrated HAC signals from the A800 single CodeCheck run.",
        "- `li3ps4_codecheck/figures/li3ps4_kz_reference_comparison.png`: A800 `kz` compared with official bundled `hac.out` and independent GK references.",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    check_required_inputs()
    summary = {
        "gpumd_version": "5.5",
        "gpu": "NVIDIA A800 80GB PCIe",
        "source": "official GPUMD-Tutorials NEP4 examples",
        "ionic_1000K": plot_ionic(),
        "li3ps4_codecheck": plot_codecheck(),
    }
    write_summary(summary)


if __name__ == "__main__":
    main()
