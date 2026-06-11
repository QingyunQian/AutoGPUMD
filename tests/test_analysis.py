from pathlib import Path

import numpy as np

from autogpumd.analysis import (
    compute_msd_from_xyz,
    compute_rdf_from_xyz,
    read_thermo,
    read_xyz_trajectory,
    summarize_thermo,
)
from autogpumd.mock import generate_mock_outputs


def test_read_and_summarize_mock_thermo(tmp_path: Path) -> None:
    outputs = generate_mock_outputs(tmp_path, n_frames=8)
    df = read_thermo(outputs["thermo"])
    summary = summarize_thermo(df)
    assert len(df) == 8
    assert 290 < summary["temperature_mean_K"] < 310
    assert np.isfinite(summary["total_energy_drift_eV"])


def test_xyz_rdf_and_msd(tmp_path: Path) -> None:
    outputs = generate_mock_outputs(tmp_path, n_frames=8)
    traj = read_xyz_trajectory(outputs["trajectory"])
    assert traj.positions.shape == (8, 64, 3)
    rdf = compute_rdf_from_xyz(outputs["trajectory"], r_max=6.0, bins=24)
    msd = compute_msd_from_xyz(outputs["trajectory"])
    assert list(rdf.columns) == ["r_angstrom", "g_r"]
    assert list(msd.columns) == ["frame", "time_ps", "msd_A2"]
    assert len(rdf) == 24
    assert len(msd) == 8
    assert msd["msd_A2"].iloc[0] == 0.0
