"""Plot local Tutorial 32 DOAS/AEDP results against official references."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "external" / "GPUMD-Tutorials" / "examples" / "32_DOAS_and_AEDP"
OUT = ROOT / "examples" / "tutorial_32_doas_aedp"
TUTORIAL_URL = "https://github.com/brucefan1983/GPUMD-Tutorials/tree/main/examples/32_DOAS_and_AEDP"

COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "red": "#D55E00",
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
    required = []
    for temperature in ["600K", "1000K"]:
        suffix = temperature.replace("K", "")
        required.extend(
            [
                (f"official {temperature} DOAS table", SOURCE / temperature / f"doas_{suffix}K.out"),
                (
                    f"official {temperature} position-energy table",
                    SOURCE / temperature / "position_energy.out",
                ),
                (
                    f"local {temperature} site-energy CSV",
                    OUT / temperature / "data" / "local_li_site_energy.csv",
                ),
                (
                    f"local {temperature} position-energy CSV",
                    OUT / temperature / "data" / "local_li_position_energy.csv",
                ),
            ]
        )
    missing = [(label, path) for label, path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            _missing_message(
                "Missing required Tutorial 32 plotting inputs.",
                missing,
                "Clone external/GPUMD-Tutorials and run scripts/run_tutorial_32_doas_aedp.py first.",
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
        }
    )
    return plt


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
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=600, bbox_inches="tight", facecolor="white")


def read_official_doas(temperature: str) -> np.ndarray:
    suffix = temperature.replace("K", "")
    return np.loadtxt(SOURCE / temperature / f"doas_{suffix}K.out", comments="#")


def read_official_position_energy(temperature: str) -> pd.DataFrame:
    data = np.loadtxt(SOURCE / temperature / "position_energy.out")
    return pd.DataFrame(data, columns=["x_A", "y_A", "z_A", "site_energy_eV"])


def read_local_doas(temperature: str) -> np.ndarray:
    path = OUT / temperature / "data" / "local_li_site_energy.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing local result {path}. Run scripts/run_tutorial_32_doas_aedp.py first."
        )
    return pd.read_csv(path)["site_energy_eV"].to_numpy()


def read_local_position_energy(temperature: str) -> pd.DataFrame:
    path = OUT / temperature / "data" / "local_li_position_energy.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing local result {path}. Run scripts/run_tutorial_32_doas_aedp.py first."
        )
    return pd.read_csv(path)


def stats(values: np.ndarray) -> dict[str, float | int]:
    return {
        "li_samples": int(values.size),
        "mean_site_energy_eV": float(values.mean()),
        "std_site_energy_eV": float(values.std(ddof=0)),
        "p05_site_energy_eV": float(np.percentile(values, 5)),
        "median_site_energy_eV": float(np.median(values)),
        "p95_site_energy_eV": float(np.percentile(values, 95)),
        "min_site_energy_eV": float(values.min()),
        "max_site_energy_eV": float(values.max()),
    }


def compare_stats(local: np.ndarray, official: np.ndarray) -> dict[str, float]:
    return {
        "mean_abs_delta_eV": float(abs(local.mean() - official.mean())),
        "std_abs_delta_eV": float(abs(local.std(ddof=0) - official.std(ddof=0))),
        "median_abs_delta_eV": float(abs(np.median(local) - np.median(official))),
    }


def plot_doas_comparisons(
    local_doas: dict[str, np.ndarray], official_doas: dict[str, np.ndarray]
) -> None:
    plt = pyplot()
    bins = np.linspace(
        min(min(values.min() for values in local_doas.values()), min(values.min() for values in official_doas.values())),
        max(max(values.max() for values in local_doas.values()), max(values.max() for values in official_doas.values())),
        95,
    )

    for panel, temperature, color in [
        ("a", "600K", COLORS["blue"]),
        ("b", "1000K", COLORS["orange"]),
    ]:
        fig, ax = plt.subplots(figsize=(3.45, 2.35))
        ax.hist(
            official_doas[temperature],
            bins=bins,
            density=True,
            histtype="step",
            color=COLORS["gray"],
            linewidth=1.4,
            label="Official bundled",
        )
        ax.hist(
            local_doas[temperature],
            bins=bins,
            density=True,
            histtype="stepfilled",
            color=color,
            alpha=0.35,
            label="Local GPUMD run",
        )
        ax.set_xlabel("Li atomistic energy (eV)")
        ax.set_ylabel("Density")
        ax.set_title(f"LLZO DOAS at {temperature}")
        style_axis(ax, panel=panel)
        ax.legend(frameon=False)
        save_figure(fig, OUT / temperature / "figures" / f"doas_{temperature}_local_vs_official.png")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    ax.hist(
        local_doas["600K"],
        bins=bins,
        density=True,
        histtype="step",
        color=COLORS["blue"],
        linewidth=1.5,
        label="600 K local",
    )
    ax.hist(
        local_doas["1000K"],
        bins=bins,
        density=True,
        histtype="step",
        color=COLORS["orange"],
        linewidth=1.5,
        label="1000 K local",
    )
    ax.hist(
        official_doas["600K"],
        bins=bins,
        density=True,
        histtype="step",
        color=COLORS["blue"],
        linewidth=0.8,
        linestyle=(0, (3, 2)),
        label="600 K official",
    )
    ax.hist(
        official_doas["1000K"],
        bins=bins,
        density=True,
        histtype="step",
        color=COLORS["orange"],
        linewidth=0.8,
        linestyle=(0, (3, 2)),
        label="1000 K official",
    )
    ax.set_xlabel("Li atomistic energy (eV)")
    ax.set_ylabel("Density")
    ax.set_title("LLZO Li DOAS local vs official")
    style_axis(ax, panel="c")
    ax.legend(frameon=False)
    save_figure(fig, OUT / "figures" / "doas_local_vs_official.png")
    plt.close(fig)


def visibility_order(energy: np.ndarray) -> np.ndarray:
    lower, upper = np.percentile(energy, [8, 92])
    middle = np.where((energy >= lower) & (energy <= upper))[0]
    high = np.where(energy > upper)[0]
    low = np.where(energy < lower)[0]
    return np.concatenate([middle, high, low])


def plot_local_aedp(local_positions: dict[str, pd.DataFrame]) -> None:
    plt = pyplot()
    vmin = min(frame["site_energy_eV"].min() for frame in local_positions.values())
    vmax = max(frame["site_energy_eV"].max() for frame in local_positions.values())
    projections = [
        ("c-a projection", "z_A", "x_A", "Lattice c (A)", "Lattice a (A)"),
        ("a-b projection", "x_A", "y_A", "Lattice a (A)", "Lattice b (A)"),
        ("b-c projection", "y_A", "z_A", "Lattice b (A)", "Lattice c (A)"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(7.1, 4.8), constrained_layout=True)
    scatter = None
    for row, temperature in enumerate(["600K", "1000K"]):
        frame = local_positions[temperature]
        ordered = frame.iloc[visibility_order(frame["site_energy_eV"].to_numpy())]
        for col, (title, x_col, y_col, x_label, y_label) in enumerate(projections):
            ax = axes[row, col]
            scatter = ax.scatter(
                ordered[x_col],
                ordered[y_col],
                c=ordered["site_energy_eV"],
                cmap="viridis",
                vmin=vmin,
                vmax=vmax,
                s=9,
                alpha=0.55,
                edgecolors="none",
                rasterized=True,
            )
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_aspect("equal", adjustable="box")
            ax.tick_params(direction="out", length=2.5, width=0.7, pad=1)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            if row == 0:
                ax.set_title(title)
            ax.text(
                0.04,
                0.94,
                temperature.replace("K", " K"),
                transform=ax.transAxes,
                ha="left",
                va="top",
                color=COLORS["black"],
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 1.5},
            )
    if scatter is not None:
        colorbar = fig.colorbar(scatter, ax=axes, shrink=0.84, pad=0.02)
        colorbar.set_label("Li atomistic energy (eV)")
    save_figure(fig, OUT / "figures" / "aedp_local_projections.png")
    plt.close(fig)


def write_docs(summary: dict[str, object]) -> None:
    source_text = f"""# Source Tutorial

- Official repository: https://github.com/brucefan1983/GPUMD-Tutorials
- Official tutorial: {TUTORIAL_URL}
- Official path: `examples/32_DOAS_and_AEDP`
- Local raw run path: `runs/tutorial_32_doas_aedp`

This example is successful only when local GPUMD outputs have been generated from the tutorial workflow and compared with the official bundled DOAS/AEDP references.
"""
    (OUT / "source.md").write_text(source_text, encoding="utf-8")

    readme = f"""# Tutorial 32: DOAS and AEDP

This folder is for reproducing the official GPUMD-Tutorials `examples/32_DOAS_and_AEDP` workflow:

{TUTORIAL_URL}

## Reproduction Standard

This example should not be considered reproduced by simply replotting official `doas_*.out` or `position_energy.out` files. A successful reproduction must:

1. run the GPUMD MD stage locally for 600 K and 1000 K;
2. sample frames from the local `dump.xyz`;
3. minimize sampled frames locally with GPUMD;
4. extract local Li site-energy and position-energy tables;
5. compare local DOAS/AEDP plots with the official bundled reference.

## Local Data

- `600K/data/local_li_site_energy.csv`
- `600K/data/local_li_position_energy.csv`
- `1000K/data/local_li_site_energy.csv`
- `1000K/data/local_li_position_energy.csv`
- `summary.json`

## Reference Comparison

- 600 K local mean: {summary['local']['600K']['mean_site_energy_eV']:.3f} eV; official mean: {summary['official']['600K']['mean_site_energy_eV']:.3f} eV.
- 1000 K local mean: {summary['local']['1000K']['mean_site_energy_eV']:.3f} eV; official mean: {summary['official']['1000K']['mean_site_energy_eV']:.3f} eV.

| Local vs official DOAS | Local AEDP projections |
| --- | --- |
| ![Tutorial 32 local vs official DOAS](figures/doas_local_vs_official.png)<br><sub>Local GPUMD-derived DOAS distributions compared with official bundled references.</sub> | ![Tutorial 32 local AEDP projections](figures/aedp_local_projections.png)<br><sub>AEDP projections generated from locally minimized frames.</sub> |

| 600 K local vs official DOAS | 1000 K local vs official DOAS |
| --- | --- |
| ![Tutorial 32 600 K local vs official DOAS](600K/figures/doas_600K_local_vs_official.png)<br><sub>600 K local result compared with the official bundled DOAS table.</sub> | ![Tutorial 32 1000 K local vs official DOAS](1000K/figures/doas_1000K_local_vs_official.png)<br><sub>1000 K local result compared with the official bundled DOAS table.</sub> |
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    check_required_inputs()
    local_doas = {temperature: read_local_doas(temperature) for temperature in ["600K", "1000K"]}
    official_doas = {temperature: read_official_doas(temperature) for temperature in ["600K", "1000K"]}
    local_positions = {
        temperature: read_local_position_energy(temperature) for temperature in ["600K", "1000K"]
    }

    OUT.mkdir(parents=True, exist_ok=True)
    plot_doas_comparisons(local_doas, official_doas)
    plot_local_aedp(local_positions)

    summary: dict[str, object] = {
        "source": "official GPUMD-Tutorials example 32_DOAS_and_AEDP",
        "source_url": TUTORIAL_URL,
        "reproduction_scope": "local GPUMD workflow with official-reference comparison",
        "local": {temperature: stats(values) for temperature, values in local_doas.items()},
        "official": {temperature: stats(values) for temperature, values in official_doas.items()},
        "comparison": {
            temperature: compare_stats(local_doas[temperature], official_doas[temperature])
            for temperature in ["600K", "1000K"]
        },
    }
    write_docs(summary)


if __name__ == "__main__":
    main()
