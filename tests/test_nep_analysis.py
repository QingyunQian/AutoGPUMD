from pathlib import Path

import pandas as pd
import yaml

from autogpumd.import_examples import import_example
from autogpumd.nep_analysis import (
    analyze_nep_workdir,
    read_energy_parity,
    read_force_parity,
    read_loss,
)
from autogpumd.plotting import plot_nep_workdir
from autogpumd.report import generate_report


def test_pbte_nep_import_analysis_and_report(tmp_path: Path) -> None:
    tutorial = tmp_path / "external" / "GPUMD-Tutorials" / "examples" / "11_NEP_potential_PbTe"
    tutorial.mkdir(parents=True)
    (tutorial / "nep.in").write_text("# nep input\n", encoding="utf-8")
    (tutorial / "nep.txt").write_text("# tutorial potential\n", encoding="utf-8")
    (tutorial / "train.xyz").write_text("1\ncomment\nPb 0 0 0\n", encoding="utf-8")
    (tutorial / "test.xyz").write_text("1\ncomment\nTe 0 0 0\n", encoding="utf-8")
    (tutorial / "loss.out").write_text(
        "100 1.0 0.1 0.2 0.03 0.4 0.0 0.04 0.5 0.0\n"
        "200 0.8 0.1 0.2 0.02 0.3 0.0 0.03 0.4 0.0\n",
        encoding="utf-8",
    )
    (tutorial / "energy_test.out").write_text("-3.7 -3.8\n-3.8 -3.9\n", encoding="utf-8")
    (tutorial / "energy_train.out").write_text("-3.6 -3.7\n", encoding="utf-8")
    (tutorial / "force_test.out").write_text(
        "0.1 0.2 0.3 0.1 0.1 0.4\n0.0 0.1 0.0 0.0 0.2 0.0\n",
        encoding="utf-8",
    )
    (tutorial / "force_train.out").write_text("0.1 0.2 0.3 0.1 0.1 0.4\n", encoding="utf-8")

    outputs = import_example("pbte-nep", source=tmp_path / "external" / "GPUMD-Tutorials", destination_root=tmp_path)
    workdir = outputs["workdir"]
    metadata = yaml.safe_load((workdir / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["example_type"] == "nep"

    analysis_outputs = analyze_nep_workdir(workdir)
    figures = plot_nep_workdir(workdir)
    report = generate_report(workdir)

    assert analysis_outputs["loss_csv"].exists()
    assert analysis_outputs["energy_test_parity_csv"].exists()
    assert analysis_outputs["force_test_parity_csv"].exists()
    assert figures["loss_curve"].exists()
    assert figures["energy_test_parity"].exists()
    assert figures["force_test_parity"].exists()
    text = report.read_text(encoding="utf-8")
    assert "AutoGPUMD NEP Workflow Report" in text
    assert "Data mode: REAL TUTORIAL OUTPUT" in text
    assert "Test energy RMSE" in text
    assert "Test force RMSE" in text


def test_pbte_nep_column_conventions(tmp_path: Path) -> None:
    loss = tmp_path / "loss.out"
    loss.write_text("100 1 2 3 4 5 6 7 8 9\n", encoding="utf-8")
    loss_df = read_loss(loss)
    assert list(loss_df.columns) == [
        "generation",
        "total",
        "l1_reg",
        "l2_reg",
        "energy_train",
        "force_train",
        "virial_train",
        "energy_test",
        "force_test",
        "virial_test",
    ]

    energy = tmp_path / "energy_test.out"
    energy.write_text("-3.7 -3.8\n", encoding="utf-8")
    energy_df = read_energy_parity(energy)
    assert energy_df.iloc[0].to_dict() == {
        "nep_energy_eV_per_atom": -3.7,
        "dft_energy_eV_per_atom": -3.8,
    }

    force = tmp_path / "force_test.out"
    force.write_text("1 2 3 4 5 6\n", encoding="utf-8")
    force_df = read_force_parity(force)
    assert force_df.equals(
        pd.DataFrame(
            {
                "nep_force_eV_per_A": [1, 2, 3],
                "dft_force_eV_per_A": [4, 5, 6],
            }
        )
    )
