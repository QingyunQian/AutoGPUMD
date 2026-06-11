"""Deterministic synthetic outputs for tests and laptop demos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_mock_outputs(
    workdir: Path,
    *,
    n_atoms: int = 64,
    n_frames: int = 60,
    dump_interval: int = 100,
    timestep_fs: float = 1.0,
    seed: int = 42,
) -> dict[str, Path]:
    """Generate synthetic thermodynamic data and a simple XYZ trajectory.

    The output is deterministic and intended only for workflow testing. It is not
    a GPUMD file-format claim and must not be interpreted as physical simulation data.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    steps = np.arange(n_frames) * dump_interval
    time_ps = steps * timestep_fs / 1000.0
    temperature = 300.0 + 8.0 * np.sin(np.linspace(0, 4 * np.pi, n_frames)) + rng.normal(
        0.0, 2.0, n_frames
    )
    potential = -3.35 * n_atoms + 0.03 * np.sin(np.linspace(0, 2 * np.pi, n_frames))
    kinetic = 1.5 * n_atoms * 8.617333262e-5 * temperature
    total = potential + kinetic
    thermo = pd.DataFrame(
        {
            "step": steps,
            "time_ps": time_ps,
            "temperature_K": temperature,
            "potential_energy_eV": potential,
            "kinetic_energy_eV": kinetic,
            "total_energy_eV": total,
        }
    )
    thermo_path = workdir / "thermo_mock.csv"
    thermo.to_csv(thermo_path, index=False)

    traj_path = workdir / "trajectory_mock.xyz"
    _write_mock_xyz(traj_path, rng, n_atoms=n_atoms, n_frames=n_frames)

    stdout = workdir / "gpumd.stdout"
    stderr = workdir / "gpumd.stderr"
    stdout.write_text("AutoGPUMD mock run completed. No GPUMD executable was called.\n", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    return {"thermo": thermo_path, "trajectory": traj_path, "stdout": stdout, "stderr": stderr}


def _write_mock_xyz(path: Path, rng: np.random.Generator, n_atoms: int, n_frames: int) -> None:
    side_count = round(n_atoms ** (1 / 3))
    if side_count**3 != n_atoms:
        raise ValueError("n_atoms must be a perfect cube for this mock generator.")
    lattice_constant = 4.05
    box = side_count * lattice_constant
    grid = np.array(
        [
            [i * lattice_constant, j * lattice_constant, k * lattice_constant]
            for i in range(side_count)
            for j in range(side_count)
            for k in range(side_count)
        ],
        dtype=float,
    )
    velocities = rng.normal(0.0, 0.015, size=grid.shape)
    positions = grid + rng.normal(0.0, 0.03, size=grid.shape)

    with path.open("w", encoding="utf-8") as handle:
        for frame in range(n_frames):
            positions = (positions + velocities + rng.normal(0.0, 0.01, size=positions.shape)) % box
            handle.write(f"{n_atoms}\n")
            handle.write(
                f'Lattice="{box:.6f} 0 0 0 {box:.6f} 0 0 0 {box:.6f}" '
                f'Properties=species:S:1:pos:R:3 Time={frame}\n'
            )
            for xyz in positions:
                handle.write(f"Al {xyz[0]:.8f} {xyz[1]:.8f} {xyz[2]:.8f}\n")
