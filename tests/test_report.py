from pathlib import Path

from autogpumd.analysis import analyze_workdir
from autogpumd.mock import generate_mock_outputs
from autogpumd.plotting import plot_workdir
from autogpumd.report import generate_report


def test_generate_mock_report(tmp_path: Path) -> None:
    (tmp_path / "MOCK_MODE.md").write_text("mock\n", encoding="utf-8")
    generate_mock_outputs(tmp_path, n_frames=8)
    analyze_workdir(tmp_path, thermo=True, rdf=True, msd=True)
    plot_workdir(tmp_path, thermo=True, rdf=True, msd=True)
    report = generate_report(tmp_path)
    text = report.read_text(encoding="utf-8")
    assert "**Data mode: MOCK.**" in text
    assert "synthetic mock data" in text
    assert "not physical GPUMD/NEP" in text
    assert "Limitations" in text
    assert "figures/temperature.png" in text
