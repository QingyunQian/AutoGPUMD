import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_png_links_exist() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"!\[[^\]]+\]\(([^)]+\.png)\)", readme)

    assert links
    for link in links:
        assert (ROOT / link).is_file(), f"README image is missing: {link}"


def test_a800_summary_matches_headline_values() -> None:
    summary = json.loads((ROOT / "examples/a800_nep4_real/summary.json").read_text())
    ionic = summary["ionic_1000K"]
    codecheck = summary["li3ps4_codecheck"]

    assert ionic["run_path"] == "runs/nep4_ionic_1000K_short"
    assert ionic["output_path"] == "examples/a800_nep4_real/ionic_1000K"
    assert "total_energy_drift_eV" not in ionic
    assert math.isclose(ionic["temperature_mean_K"], 999.8881089216429)
    assert math.isclose(ionic["final_sdc_cm2_s"]["Li"], 9.687343333333334e-06)
    assert math.isclose(codecheck["kz_mean_second_half_W_mK"], 0.3094666505867627)
    assert math.isclose(
        codecheck["official_reference_kz_mean_second_half_W_mK"],
        0.7800195350582589,
    )


def test_tutorial_32_summary_matches_headline_values() -> None:
    summary = json.loads((ROOT / "examples/tutorial_32_doas_aedp/summary.json").read_text())

    assert summary["reproduction_scope"] == "local GPUMD workflow with official-reference comparison"
    assert summary["local"]["600K"]["li_samples"] == 35840
    assert summary["local"]["1000K"]["li_samples"] == 35840
    assert math.isclose(summary["comparison"]["600K"]["mean_abs_delta_eV"], 0.0009857036060267887)
    assert math.isclose(summary["comparison"]["1000K"]["mean_abs_delta_eV"], 0.0004871621721540542)
