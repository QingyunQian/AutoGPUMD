from pathlib import Path

import pytest

from autogpumd.analysis import analyze_workdir
from autogpumd.config import load_config
from autogpumd.plotting import plot_workdir
from autogpumd.runner import WorkflowError, prepare_workdir, run_workdir


def test_prepare_and_run_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "al_nvt.yaml"
    config_file.write_text(
        """
project:
  name: al_nvt_demo
  workdir: examples/al_nvt_mock
structure:
  builder: ase_bulk
  symbol: Al
  crystalstructure: fcc
  lattice_constant: 4.05
  supercell: [2, 2, 2]
potential:
  type: nep
  path: potentials/Al/nep.txt
simulation:
  ensemble: nvt
  temperature: 300
  timestep_fs: 1.0
  equilibration_steps: 10
  production_steps: 100
  dump_interval: 10
analysis:
  thermo: true
  rdf: true
  msd: true
  diffusion: true
  report: true
""",
        encoding="utf-8",
    )
    config = load_config(config_file)
    prepared = prepare_workdir(config, mock=True)
    assert prepared["run_in"].exists()
    assert (config.workdir / "MOCK_MODE.md").exists()

    outputs = run_workdir(config.workdir, mock=True)
    assert outputs["thermo"].exists()
    thermo_lines = outputs["thermo"].read_text(encoding="utf-8").splitlines()
    trajectory_lines = outputs["trajectory"].read_text(encoding="utf-8").splitlines()
    assert trajectory_lines[0] == "32"
    assert thermo_lines[1].split(",")[3] == "-107.2"
    analysis_outputs = analyze_workdir(config.workdir, thermo=True, rdf=True, msd=True)
    figures = plot_workdir(config.workdir, thermo=True, rdf=True, msd=True)
    assert analysis_outputs["thermo_summary_csv"].exists()
    msd_text = (config.workdir / "analysis" / "msd.csv").read_text(encoding="utf-8")
    assert max(float(line.split(",")[2]) for line in msd_text.splitlines()[1:]) < 5.0
    assert figures["temperature"].exists()
    assert figures["rdf"].exists()


def test_real_prepare_requires_potential(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    raw = Path("config.yaml")
    raw.write_text(
        """
project:
  name: x
  workdir: work
structure:
  builder: ase_bulk
  symbol: Al
  crystalstructure: fcc
  lattice_constant: 4.05
  supercell: [1, 1, 1]
potential:
  type: nep
  path: missing/nep.txt
simulation:
  ensemble: nvt
  temperature: 300
  timestep_fs: 1.0
  equilibration_steps: 0
  production_steps: 10
  dump_interval: 1
""",
        encoding="utf-8",
    )
    with pytest.raises(WorkflowError, match="NEP potential not found"):
        prepare_workdir(load_config(raw), mock=False)
