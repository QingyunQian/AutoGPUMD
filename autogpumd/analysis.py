"""Conservative parsers and analysis routines for AutoGPUMD outputs."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

THERMO_CANDIDATES = ("thermo_mock.csv", "thermo.csv")
TRAJECTORY_CANDIDATES = ("trajectory_mock.xyz", "trajectory.xyz", "dump.xyz")


@dataclass(frozen=True)
class XyzTrajectory:
    symbols: list[str]
    positions: np.ndarray
    cell: np.ndarray | None


def read_thermo(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "step",
        "time_ps",
        "temperature_K",
        "potential_energy_eV",
        "kinetic_energy_eV",
        "total_energy_eV",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Thermo file is missing required columns: {sorted(missing)}")
    return df


def summarize_thermo(df: pd.DataFrame) -> dict[str, float]:
    return {
        "n_samples": float(len(df)),
        "temperature_mean_K": float(df["temperature_K"].mean()),
        "temperature_std_K": float(df["temperature_K"].std(ddof=0)),
        "total_energy_drift_eV": float(df["total_energy_eV"].iloc[-1] - df["total_energy_eV"].iloc[0]),
        "potential_energy_mean_eV": float(df["potential_energy_eV"].mean()),
    }


def read_xyz_trajectory(path: str | Path) -> XyzTrajectory:
    """Read a minimal XYZ/extended XYZ trajectory.

    Supported format: repeated XYZ frames with atom count, a comment line, then
    `symbol x y z` rows. If the comment contains a standard extended-XYZ
    `Lattice="..."` field, the 3x3 cell is parsed for simple orthorhombic RDF.
    This parser is intentionally small and currently targets ASE-written or
    AutoGPUMD mock trajectories.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    idx = 0
    frames: list[np.ndarray] = []
    symbols: list[str] | None = None
    cell: np.ndarray | None = None

    while idx < len(lines):
        if not lines[idx].strip():
            idx += 1
            continue
        try:
            n_atoms = int(lines[idx].strip())
        except ValueError as exc:
            raise ValueError(f"Expected atom count at line {idx + 1}") from exc
        frame_end = idx + 2 + n_atoms
        if frame_end > len(lines):
            raise ValueError("XYZ trajectory ended before a complete frame was read.")
        comment = lines[idx + 1]
        parsed_cell = _parse_lattice(comment)
        if parsed_cell is not None:
            cell = parsed_cell
        frame_symbols: list[str] = []
        frame_positions: list[list[float]] = []
        for atom_line in lines[idx + 2 : frame_end]:
            parts = atom_line.split()
            if len(parts) < 4:
                raise ValueError(f"Invalid XYZ atom row: {atom_line}")
            frame_symbols.append(parts[0])
            frame_positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
        if symbols is None:
            symbols = frame_symbols
        elif frame_symbols != symbols:
            raise ValueError("All XYZ frames must contain the same atom order for MSD analysis.")
        frames.append(np.asarray(frame_positions, dtype=float))
        idx = frame_end

    if not frames or symbols is None:
        raise ValueError(f"No XYZ frames found in {path}")
    return XyzTrajectory(symbols=symbols, positions=np.stack(frames), cell=cell)


def compute_rdf_from_xyz(path: str | Path, r_max: float = 8.0, bins: int = 100) -> pd.DataFrame:
    traj = read_xyz_trajectory(path)
    positions = traj.positions
    n_frames, n_atoms, _ = positions.shape
    distances: list[float] = []
    box_lengths = _orthorhombic_lengths(traj.cell)

    for frame in positions:
        for i in range(n_atoms - 1):
            delta = frame[i + 1 :] - frame[i]
            if box_lengths is not None:
                delta -= box_lengths * np.round(delta / box_lengths)
            distances.extend(np.linalg.norm(delta, axis=1).tolist())

    hist, edges = np.histogram(distances, bins=bins, range=(0.0, r_max))
    r = 0.5 * (edges[:-1] + edges[1:])
    dr = edges[1] - edges[0]
    volume = float(np.prod(box_lengths)) if box_lengths is not None else _estimate_volume(positions)
    density = n_atoms / volume
    shell_volume = 4.0 * np.pi * r**2 * dr
    ideal_pairs = 0.5 * n_atoms * density * shell_volume * n_frames
    g_r = np.divide(hist, ideal_pairs, out=np.zeros_like(r), where=ideal_pairs > 0)
    return pd.DataFrame({"r_angstrom": r, "g_r": g_r})


def compute_msd_from_xyz(path: str | Path) -> pd.DataFrame:
    traj = read_xyz_trajectory(path)
    displacement = traj.positions - traj.positions[0][None, :, :]
    msd = np.mean(np.sum(displacement**2, axis=2), axis=1)
    return pd.DataFrame({"frame": np.arange(len(msd)), "time_ps": np.arange(len(msd)) * 0.1, "msd_A2": msd})


def estimate_diffusion_from_msd(
    msd_df: pd.DataFrame, fit_range: tuple[float, float] | None = None
) -> float:
    if fit_range is None:
        start = len(msd_df) // 2
        fit = msd_df.iloc[start:]
    else:
        lo, hi = fit_range
        fit = msd_df[(msd_df["time_ps"] >= lo) & (msd_df["time_ps"] <= hi)]
    if len(fit) < 2:
        raise ValueError("Need at least two MSD samples for diffusion estimate.")
    slope, _ = np.polyfit(fit["time_ps"], fit["msd_A2"], 1)
    return float(max(slope / 6.0, 0.0))


def analyze_workdir(
    workdir: Path,
    *,
    thermo: bool = False,
    rdf: bool = False,
    msd: bool = False,
) -> dict[str, Path | dict[str, float]]:
    workdir = Path(workdir)
    analysis_dir = workdir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path | dict[str, float]] = {}

    if thermo:
        thermo_path = find_first(workdir, THERMO_CANDIDATES)
        df = read_thermo(thermo_path)
        out = analysis_dir / "thermo_summary.csv"
        summary = summarize_thermo(df)
        pd.DataFrame([summary]).to_csv(out, index=False)
        outputs["thermo_summary_csv"] = out
        outputs["thermo_summary"] = summary

    traj_path = None
    if rdf or msd:
        traj_path = find_first(workdir, TRAJECTORY_CANDIDATES)

    if rdf and traj_path is not None:
        rdf_df = compute_rdf_from_xyz(traj_path)
        out = analysis_dir / "rdf.csv"
        rdf_df.to_csv(out, index=False)
        outputs["rdf_csv"] = out

    if msd and traj_path is not None:
        msd_df = compute_msd_from_xyz(traj_path)
        msd_out = analysis_dir / "msd.csv"
        msd_df.to_csv(msd_out, index=False)
        diffusion = estimate_diffusion_from_msd(msd_df)
        diffusion_out = analysis_dir / "diffusion.csv"
        pd.DataFrame([{"diffusion_A2_per_ps": diffusion}]).to_csv(diffusion_out, index=False)
        outputs["msd_csv"] = msd_out
        outputs["diffusion_csv"] = diffusion_out
    return outputs


def find_first(workdir: Path, names: Iterable[str]) -> Path:
    for name in names:
        path = workdir / name
        if path.exists():
            return path
    raise FileNotFoundError(f"None of these files were found in {workdir}: {', '.join(names)}")


def _parse_lattice(comment: str) -> np.ndarray | None:
    match = re.search(r'Lattice="([^"]+)"', comment)
    if not match:
        return None
    values = [float(value) for value in match.group(1).split()]
    if len(values) != 9:
        return None
    return np.asarray(values, dtype=float).reshape(3, 3)


def _orthorhombic_lengths(cell: np.ndarray | None) -> np.ndarray | None:
    if cell is None:
        return None
    offdiag = cell.copy()
    np.fill_diagonal(offdiag, 0.0)
    if np.any(np.abs(offdiag) > 1e-8):
        return None
    lengths = np.diag(cell)
    if np.any(lengths <= 0):
        return None
    return lengths


def _estimate_volume(positions: np.ndarray) -> float:
    mins = positions.reshape(-1, 3).min(axis=0)
    maxs = positions.reshape(-1, 3).max(axis=0)
    lengths = np.maximum(maxs - mins, 1.0)
    return float(np.prod(lengths))
