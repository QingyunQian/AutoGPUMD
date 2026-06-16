"""NEP tutorial-output analysis helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autogpumd.metadata import infer_metadata


def analyze_nep_workdir(workdir: str | Path) -> dict[str, Path | dict[str, float]]:
    workdir = Path(workdir)
    analysis_dir = workdir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    metadata = infer_metadata(workdir)
    outputs: dict[str, Path | dict[str, float]] = {}
    skipped: list[str] = []
    assumptions = list(metadata.parser_assumptions)

    try:
        loss_path = _find_first(workdir, ("loss.out",))
        loss_df = read_loss(loss_path)
        loss_csv = analysis_dir / "loss.csv"
        loss_df.to_csv(loss_csv, index=False)
        outputs["loss_csv"] = loss_csv
        if not any("loss.out" in item for item in assumptions):
            assumptions.append("loss.out follows GPUMD-Tutorials PbTe plot_results.m columns")
    except (FileNotFoundError, ValueError) as exc:
        skipped.append(f"loss: {exc}")

    for split in ("train", "test"):
        try:
            energy_path = _find_first(workdir, (f"energy_{split}.out",))
            energy_df = read_energy_parity(energy_path)
            energy_csv = analysis_dir / f"energy_{split}_parity.csv"
            energy_df.to_csv(energy_csv, index=False)
            outputs[f"energy_{split}_parity_csv"] = energy_csv
            outputs[f"energy_{split}_rmse_eV_per_atom"] = _rmse(
                energy_df["nep_energy_eV_per_atom"], energy_df["dft_energy_eV_per_atom"]
            )
        except (FileNotFoundError, ValueError) as exc:
            skipped.append(f"energy_{split}: {exc}")

        try:
            force_path = _find_first(workdir, (f"force_{split}.out",))
            force_df = read_force_parity(force_path)
            force_csv = analysis_dir / f"force_{split}_parity.csv"
            force_df.to_csv(force_csv, index=False)
            outputs[f"force_{split}_parity_csv"] = force_csv
            outputs[f"force_{split}_rmse_eV_per_A"] = _rmse(
                force_df["nep_force_eV_per_A"], force_df["dft_force_eV_per_A"]
            )
        except (FileNotFoundError, ValueError) as exc:
            skipped.append(f"force_{split}: {exc}")

    summary_path = write_nep_summary(
        workdir,
        {
            "data_mode": metadata.data_mode,
            "example_type": metadata.example_type,
            "outputs": _json_ready(outputs),
            "skipped": skipped,
            "parser_assumptions": list(dict.fromkeys(assumptions)),
        },
    )
    outputs["analysis_summary_json"] = summary_path
    return outputs


def read_loss(path: str | Path) -> pd.DataFrame:
    raw = _numeric_table(path)
    if raw.shape[1] < 9:
        raise ValueError(f"loss.out must contain at least 9 numeric columns: {path}")
    columns = [
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
    ][: raw.shape[1]]
    raw.columns = columns
    return raw


def read_energy_parity(path: str | Path) -> pd.DataFrame:
    raw = _numeric_table(path)
    if raw.shape[1] < 2:
        raise ValueError(f"energy parity file must contain at least 2 columns: {path}")
    return pd.DataFrame(
        {
            "nep_energy_eV_per_atom": raw.iloc[:, 0],
            "dft_energy_eV_per_atom": raw.iloc[:, 1],
        }
    )


def read_force_parity(path: str | Path) -> pd.DataFrame:
    raw = _numeric_table(path)
    if raw.shape[1] < 6:
        raise ValueError(f"force parity file must contain 6 columns: {path}")
    nep = raw.iloc[:, 0:3].to_numpy().reshape(-1)
    dft = raw.iloc[:, 3:6].to_numpy().reshape(-1)
    return pd.DataFrame({"nep_force_eV_per_A": nep, "dft_force_eV_per_A": dft})


def write_nep_summary(workdir: str | Path, summary: dict[str, Any]) -> Path:
    path = Path(workdir) / "analysis" / "analysis_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _find_first(workdir: Path, names: tuple[str, ...]) -> Path:
    for directory in (workdir, workdir / "raw"):
        for name in names:
            path = directory / name
            if path.exists():
                return path
    raise FileNotFoundError(f"None of these files were found in {workdir}: {', '.join(names)}")


def _numeric_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    return pd.read_csv(path, sep=r"\s+", comment="#", header=None)


def _rmse(predicted: pd.Series, reference: pd.Series) -> float:
    return float(np.sqrt(np.mean((predicted.to_numpy() - reference.to_numpy()) ** 2)))


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]
    return value
