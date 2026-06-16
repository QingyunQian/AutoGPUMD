from pathlib import Path

import yaml

from autogpumd.analysis import analyze_workdir, read_analysis_summary
from autogpumd.import_examples import import_example
from autogpumd.plotting import plot_workdir
from autogpumd.report import generate_report


def test_import_si_diffusion_and_analyze_raw_outputs(tmp_path: Path) -> None:
    tutorial = tmp_path / "external" / "GPUMD-Tutorials" / "examples" / "09_Silicon_diffusion"
    tutorial.mkdir(parents=True)
    (tutorial / "run.in").write_text("# tutorial input\n", encoding="utf-8")
    (tutorial / "model.xyz").write_text("1\ncomment\nSi 0 0 0\n", encoding="utf-8")
    (tutorial / "thermo.out").write_text(
        "\n".join(
            [
                "# step time_ps temperature_K potential_energy_eV kinetic_energy_eV total_energy_eV",
                "0 0.0 300 -10.0 1.0 -9.0",
                "1 0.1 305 -10.1 1.1 -9.0",
                "2 0.2 299 -10.0 1.0 -9.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tutorial / "msd.out").write_text(
        "0.0 0.0 0.0 0.0 0.0 0.0 0.0\n"
        "0.1 1.0 2.0 3.0 4.0 5.0 6.0\n"
        "0.2 2.0 3.0 4.0 5.0 6.0 7.0\n",
        encoding="utf-8",
    )
    (tutorial / "sdc.out").write_text(
        "0.0 1.0 1.0 1.0 0.0 0.0 0.0\n"
        "0.1 2.0 3.0 4.0 6.0 7.0 8.0\n"
        "0.2 3.0 4.0 5.0 7.0 8.0 9.0\n",
        encoding="utf-8",
    )

    outputs = import_example("si-diffusion", source=tmp_path / "external" / "GPUMD-Tutorials", destination_root=tmp_path)
    workdir = outputs["workdir"]
    assert (workdir / "raw" / "thermo.out").exists()
    metadata = yaml.safe_load((workdir / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["data_mode"] == "REAL TUTORIAL OUTPUT"

    analysis_outputs = analyze_workdir(workdir, thermo=True, msd=True)
    figures = plot_workdir(workdir, thermo=True, rdf=False, msd=True)
    report = generate_report(workdir)
    summary = read_analysis_summary(workdir)

    assert analysis_outputs["analysis_summary_json"].exists()
    assert (workdir / "analysis" / "thermo.csv").exists()
    assert (workdir / "analysis" / "msd.csv").exists()
    assert (workdir / "analysis" / "sdc.csv").exists()
    assert (workdir / "analysis" / "msd.csv").read_text(encoding="utf-8").splitlines()[2].startswith("1,0.1,2.0,5.0")
    assert figures["temperature"].exists()
    assert figures["msd"].exists()
    assert figures["sdc"].exists()
    text = report.read_text(encoding="utf-8")
    assert "Data mode: REAL TUTORIAL OUTPUT" in text
    assert "official GPUMD-Tutorials / examples/09_Silicon_diffusion" in text
    assert "not original AutoGPUMD simulation results" in text
    assert summary["data_mode"] == "REAL TUTORIAL OUTPUT"
