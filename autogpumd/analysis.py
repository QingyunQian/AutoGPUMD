"""Conservative parsers and analysis routines for AutoGPUMD outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autogpumd.metadata import MOCK_MODE, infer_metadata

THERMO_CANDIDATES = ("thermo_mock.csv", "thermo.csv", "thermo.out")
TRAJECTORY_CANDIDATES = ("trajectory_mock.xyz", "trajectory.xyz", "dump.xyz")
MSD_CANDIDATES = ("msd.csv", "msd.out")
SDC_CANDIDATES = ("sdc.csv", "sdc.out")


@dataclass(frozen=True)
class XyzTrajectory:
    symbols: list[str]
    positions: np.ndarray
    cell: np.ndarray | None


def read_thermo(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".out":
        return _read_named_thermo_out(path)
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


def read_msd(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = _read_numeric_table(path)
        if df.empty or df.shape[1] < 2:
            raise ValueError(f"MSD file must contain at least two numeric columns: {path}")
        if df.shape[1] >= 7 and "time_ps" not in df.columns:
            # GPUMD Si diffusion tutorial: plot_results.m uses mean(msd(:,2:4),2)
            # for MSD and mean(msd(:,5:7),2) for SDC from MSD.
            return pd.DataFrame(
                {
                    "frame": np.arange(len(df)),
                    "time_ps": df.iloc[:, 0],
                    "msd_A2": df.iloc[:, 1:4].mean(axis=1),
                    "sdc_from_msd_A2_per_ps": df.iloc[:, 4:7].mean(axis=1),
                }
            )
        if "time_ps" not in df.columns or "msd_A2" not in df.columns:
            df = df.rename(columns={df.columns[0]: "time_ps", df.columns[1]: "msd_A2"})
    missing = {"time_ps", "msd_A2"}.difference(df.columns)
    if missing:
        raise ValueError(f"MSD file is missing required columns: {sorted(missing)}")
    out = df[["time_ps", "msd_A2"]].copy()
    out.insert(0, "frame", np.arange(len(out)))
    return out


def read_sdc(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = _read_numeric_table(path)
        if df.empty or df.shape[1] < 4:
            raise ValueError(f"SDC file must contain at least four numeric columns: {path}")
        if df.shape[1] >= 7 and "time_ps" not in df.columns:
            # GPUMD Si diffusion tutorial: plot_results.m uses mean(sdc(:,2:4),2)
            # for VAC and mean(sdc(:,5:7),2) for SDC from VAC.
            return pd.DataFrame(
                {
                    "frame": np.arange(len(df)),
                    "time_ps": df.iloc[:, 0],
                    "vac_A2_per_ps2": df.iloc[:, 1:4].mean(axis=1),
                    "sdc_from_vac_A2_per_ps": df.iloc[:, 4:7].mean(axis=1),
                }
            )
        if "time_ps" not in df.columns or "sdc_from_vac_A2_per_ps" not in df.columns:
            df = df.rename(columns={df.columns[0]: "time_ps", df.columns[1]: "sdc_from_vac_A2_per_ps"})
    missing = {"time_ps", "sdc_from_vac_A2_per_ps"}.difference(df.columns)
    if missing:
        raise ValueError(f"SDC file is missing required columns: {sorted(missing)}")
    out = df[[column for column in ("time_ps", "vac_A2_per_ps2", "sdc_from_vac_A2_per_ps") if column in df.columns]].copy()
    out.insert(0, "frame", np.arange(len(out)))
    return out


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
    metadata = infer_metadata(workdir)
    skipped: list[str] = []
    parser_assumptions = list(metadata.parser_assumptions)

    if thermo:
        try:
            thermo_path = find_first(workdir, THERMO_CANDIDATES)
            df = read_thermo(thermo_path)
            thermo_csv = analysis_dir / "thermo.csv"
            df.to_csv(thermo_csv, index=False)
            out = analysis_dir / "thermo_summary.csv"
            summary = summarize_thermo(df)
            pd.DataFrame([summary]).to_csv(out, index=False)
            outputs["thermo_csv"] = thermo_csv
            outputs["thermo_summary_csv"] = out
            outputs["thermo_summary"] = summary
            parser_assumptions.append(f"Thermo parsed from {thermo_path.name}")
        except (FileNotFoundError, ValueError) as exc:
            skipped.append(f"thermo: {exc}")

    traj_path: Path | None = None
    if rdf:
        try:
            traj_path = find_first(workdir, TRAJECTORY_CANDIDATES)
            rdf_df = compute_rdf_from_xyz(traj_path)
            out = analysis_dir / "rdf.csv"
            rdf_df.to_csv(out, index=False)
            outputs["rdf_csv"] = out
            parser_assumptions.append(f"RDF parsed from {traj_path.name}")
        except (FileNotFoundError, ValueError) as exc:
            skipped.append(f"rdf: {exc}")

    if msd:
        try:
            msd_source = None
            if traj_path is None:
                try:
                    traj_path = find_first(workdir, TRAJECTORY_CANDIDATES)
                except FileNotFoundError:
                    traj_path = None
            if traj_path is not None:
                msd_df = compute_msd_from_xyz(traj_path)
                msd_source = traj_path
            else:
                msd_source = find_first(workdir, MSD_CANDIDATES)
                msd_df = read_msd(msd_source)
            msd_out = analysis_dir / "msd.csv"
            msd_df.to_csv(msd_out, index=False)
            diffusion = estimate_diffusion_from_msd(msd_df)
            diffusion_out = analysis_dir / "diffusion.csv"
            pd.DataFrame([{"diffusion_A2_per_ps": diffusion}]).to_csv(diffusion_out, index=False)
            outputs["msd_csv"] = msd_out
            outputs["diffusion_csv"] = diffusion_out
            if msd_source is not None:
                parser_assumptions.append(f"MSD parsed from {msd_source.name}")
            try:
                sdc_source = find_first(workdir, SDC_CANDIDATES)
                sdc_df = read_sdc(sdc_source)
                sdc_out = analysis_dir / "sdc.csv"
                sdc_df.to_csv(sdc_out, index=False)
                outputs["sdc_csv"] = sdc_out
                parser_assumptions.append(f"SDC parsed from {sdc_source.name}")
            except (FileNotFoundError, ValueError) as exc:
                if metadata.data_mode != MOCK_MODE:
                    skipped.append(f"sdc: {exc}")
        except (FileNotFoundError, ValueError) as exc:
            skipped.append(f"msd: {exc}")
    summary_path = write_analysis_summary(
        workdir,
        {
            "data_mode": metadata.data_mode,
            "example_type": metadata.example_type,
            "outputs": _json_ready(outputs),
            "skipped": skipped,
            "parser_assumptions": parser_assumptions,
        },
    )
    outputs["analysis_summary_json"] = summary_path
    return outputs


def find_first(workdir: Path, names: Iterable[str]) -> Path:
    for directory in (Path(workdir), Path(workdir) / "raw"):
        for name in names:
            path = directory / name
            if path.exists():
                return path
    raise FileNotFoundError(f"None of these files were found in {workdir}: {', '.join(names)}")


def write_analysis_summary(workdir: str | Path, summary: dict[str, Any]) -> Path:
    path = Path(workdir) / "analysis" / "analysis_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_analysis_summary(workdir: str | Path) -> dict[str, Any]:
    path = Path(workdir) / "analysis" / "analysis_summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_named_thermo_out(path: Path) -> pd.DataFrame:
    df = _read_numeric_table(path)
    normalized = {_normalize_name(column): column for column in df.columns}
    column_map: dict[str, str] = {}
    candidates = {
        "step": ("step", "n", "index"),
        "time_ps": ("time_ps", "time", "t_ps"),
        "temperature_K": ("temperature_k", "temperature", "temp", "t"),
        "potential_energy_eV": ("potential_energy_ev", "potential_energy", "pe", "u"),
        "kinetic_energy_eV": ("kinetic_energy_ev", "kinetic_energy", "ke", "ek"),
        "total_energy_eV": ("total_energy_ev", "total_energy", "etot", "e"),
    }
    for target, names in candidates.items():
        for name in names:
            if name in normalized:
                column_map[target] = normalized[name]
                break
    missing = set(candidates).difference(column_map)
    if missing:
        raise ValueError(
            "thermo.out requires recognizable named columns for "
            f"{sorted(missing)}; unsupported anonymous thermo.out was skipped"
        )
    out = pd.DataFrame({target: df[source] for target, source in column_map.items()})
    return out


def _read_numeric_table(path: Path) -> pd.DataFrame:
    first = _first_content_line(path)
    if first is None:
        raise ValueError(f"Empty numeric table: {path}")
    if first.startswith("#"):
        names = first[1:].split()
        df = pd.read_csv(path, sep=r"\s+", comment="#", header=None)
        if len(names) == df.shape[1]:
            df.columns = names
        return df
    return pd.read_csv(path, sep=r"\s+", comment="#", header=None)


def _first_content_line(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _normalize_name(name: object) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]
    return value


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
