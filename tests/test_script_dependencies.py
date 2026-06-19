import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def touch_files(paths: list[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plot_a800_reports_missing_raw_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = load_script("plot_a800_nep4_results")
    monkeypatch.setattr(script, "IONIC_RUN", tmp_path / "missing_ionic")
    monkeypatch.setattr(script, "CODECHECK_RUN", tmp_path / "missing_codecheck")

    with pytest.raises(FileNotFoundError, match="Missing required A800 raw run inputs") as excinfo:
        script.check_required_inputs()

    message = str(excinfo.value)
    assert "LLZO ionic run directory" in message
    assert "Li3PS4 CodeCheck run directory" in message


def test_plot_a800_accepts_required_raw_run_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = load_script("plot_a800_nep4_results")
    ionic_run = tmp_path / "nep4_ionic_1000K_short"
    codecheck_run = tmp_path / "nep4_li3ps4_codecheck_short"
    monkeypatch.setattr(script, "IONIC_RUN", ionic_run)
    monkeypatch.setattr(script, "CODECHECK_RUN", codecheck_run)
    touch_files(
        [
            ionic_run / "run.in",
            ionic_run / "thermo.out",
            ionic_run / "msd.out",
            ionic_run / "gpumd.stdout",
            codecheck_run / "run.in",
            codecheck_run / "hac.out",
            codecheck_run / "gpumd.stdout",
        ]
    )

    script.check_required_inputs()


def test_plot_doas_reports_missing_reference_and_local_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = load_script("plot_doas_aedp_tutorial")
    monkeypatch.setattr(script, "SOURCE", tmp_path / "missing_external")
    monkeypatch.setattr(script, "OUT", tmp_path / "missing_local")

    with pytest.raises(FileNotFoundError, match="Missing required Tutorial 32 plotting inputs") as excinfo:
        script.check_required_inputs()

    message = str(excinfo.value)
    assert "official 600K DOAS table" in message
    assert "local 1000K site-energy CSV" in message
    assert "external/GPUMD-Tutorials" in message


def test_plot_doas_accepts_required_reference_and_local_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = load_script("plot_doas_aedp_tutorial")
    source = tmp_path / "external" / "GPUMD-Tutorials" / "examples" / "32_DOAS_and_AEDP"
    out = tmp_path / "examples" / "tutorial_32_doas_aedp"
    monkeypatch.setattr(script, "SOURCE", source)
    monkeypatch.setattr(script, "OUT", out)
    touch_files(
        [
            source / "600K" / "doas_600K.out",
            source / "600K" / "position_energy.out",
            source / "1000K" / "doas_1000K.out",
            source / "1000K" / "position_energy.out",
            out / "600K" / "data" / "local_li_site_energy.csv",
            out / "600K" / "data" / "local_li_position_energy.csv",
            out / "1000K" / "data" / "local_li_site_energy.csv",
            out / "1000K" / "data" / "local_li_position_energy.csv",
        ]
    )

    script.check_required_inputs()


def test_run_tutorial_reports_missing_source_and_gpumd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = load_script("run_tutorial_32_doas_aedp")
    monkeypatch.setattr(script, "SOURCE", tmp_path / "missing_external")
    monkeypatch.setattr(script.shutil, "which", lambda _: None)

    with pytest.raises(FileNotFoundError, match="Missing required Tutorial 32 run inputs") as excinfo:
        script.check_required_inputs()

    message = str(excinfo.value)
    assert "official Tutorial 32 directory" in message
    assert "gpumd executable on PATH" in message


def test_run_tutorial_accepts_required_source_and_gpumd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = load_script("run_tutorial_32_doas_aedp")
    source = tmp_path / "external" / "GPUMD-Tutorials" / "examples" / "32_DOAS_and_AEDP"
    monkeypatch.setattr(script, "SOURCE", source)
    monkeypatch.setattr(script.shutil, "which", lambda _: "/usr/local/bin/gpumd")
    touch_files(
        [
            source / "nep.txt",
            source / "600K" / "model.xyz",
            source / "1000K" / "model.xyz",
        ]
    )

    script.check_required_inputs()
