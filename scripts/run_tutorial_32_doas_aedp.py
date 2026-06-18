"""Run GPUMD-Tutorials example 32 locally and extract DOAS/AEDP tables."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "external" / "GPUMD-Tutorials" / "examples" / "32_DOAS_and_AEDP"
RUNS = ROOT / "runs" / "tutorial_32_doas_aedp"
OUT = ROOT / "examples" / "tutorial_32_doas_aedp"

TEMPERATURES = {"600K": 600, "1000K": 1000}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_command(
    command: list[str], workdir: Path, *, name: str, cuda_visible_devices: str
) -> None:
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices
    with (
        (workdir / f"{name}.stdout").open("w", encoding="utf-8") as stdout,
        (workdir / f"{name}.stderr").open("w", encoding="utf-8") as stderr,
    ):
        result = subprocess.run(
            command, cwd=workdir, env=env, stdout=stdout, stderr=stderr, check=False
        )
    (workdir / f"{name}.exitcode").write_text(f"{result.returncode}\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"{name} failed in {workdir}; see {name}.stderr")


def write_md_input(workdir: Path, temperature: int, *, pre_steps: int, prod_steps: int, dump_interval: int) -> None:
    shutil.copy2(SOURCE / f"{temperature}K" / "model.xyz", workdir / "model.xyz")
    shutil.copy2(SOURCE / "nep.txt", workdir / "nep.txt")
    write_text(
        workdir / "run.in",
        f"""potential ./nep.txt
velocity    {temperature}

ensemble    nvt_nhc {temperature} {temperature} 100
run        {pre_steps}

ensemble    nvt_nhc {temperature} {temperature} 100
dump_thermo 100
dump_exyz  {dump_interval}
run        {prod_steps}
""",
    )


def frame_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            atoms = int(line.strip())
            handle.readline()
            for _ in range(atoms):
                handle.readline()
            count += 1
    return count


def sampled_indices(total: int, sample_count: int) -> set[int]:
    if sample_count >= total:
        return set(range(total))
    if sample_count <= 1:
        return {total - 1}
    return {round(i * (total - 1) / (sample_count - 1)) for i in range(sample_count)}


def sample_dump_frames(dump_path: Path, sample_root: Path, sample_count: int) -> int:
    total = frame_count(dump_path)
    selected = sampled_indices(total, sample_count)
    sample_root.mkdir(parents=True, exist_ok=True)

    written = 0
    with dump_path.open("r", encoding="utf-8", errors="replace") as handle:
        frame_idx = 0
        while True:
            header = handle.readline()
            if not header:
                break
            atoms = int(header.strip())
            comment = handle.readline()
            atom_lines = [handle.readline() for _ in range(atoms)]
            if frame_idx in selected:
                sample_dir = sample_root / f"sample_{written:03d}"
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "model.xyz").write_text(
                    header + comment + "".join(atom_lines), encoding="utf-8"
                )
                written += 1
            frame_idx += 1
    return written


def write_minimize_input(sample_dir: Path) -> None:
    write_text(
        sample_dir / "run.in",
        """potential ./nep.txt

minimize sd 1.0e-6 10000

ensemble    nve
time_step   0
dump_xyz    -1 0 1 relaxed.xyz potential
run         1
""",
    )


def run_minimizations(
    temperature_run: Path, sample_count: int, *, cuda_visible_devices: str
) -> None:
    sample_root = temperature_run / "samples"
    sample_dirs = sorted(sample_root.glob("sample_*"))[:sample_count]
    for sample_dir in sample_dirs:
        shutil.copy2(SOURCE / "nep.txt", sample_dir / "nep.txt")
        write_minimize_input(sample_dir)
        if not (sample_dir / "relaxed.xyz").exists():
            run_command(
                ["gpumd"],
                sample_dir,
                name="gpumd_minimize",
                cuda_visible_devices=cuda_visible_devices,
            )


def parse_relaxed_xyz(path: Path) -> list[tuple[float, float, float, float]]:
    rows: list[tuple[float, float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        atoms = int(handle.readline().strip())
        handle.readline()
        for _ in range(atoms):
            parts = handle.readline().split()
            if parts and parts[0] == "Li":
                rows.append((float(parts[1]), float(parts[2]), float(parts[3]), float(parts[-1])))
    return rows


def extract_tables(temperature: str) -> dict[str, float | int]:
    sample_root = RUNS / temperature / "samples"
    rows: list[tuple[float, float, float, float]] = []
    for relaxed in sorted(sample_root.glob("sample_*/relaxed.xyz")):
        rows.extend(parse_relaxed_xyz(relaxed))

    data_dir = OUT / temperature / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "local_li_position_energy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x_A", "y_A", "z_A", "site_energy_eV"])
        writer.writerows(rows)
    with (data_dir / "local_li_site_energy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["site_energy_eV"])
        writer.writerows([[row[3]] for row in rows])

    energies = [row[3] for row in rows]
    return {
        "li_samples": len(energies),
        "mean_site_energy_eV": sum(energies) / len(energies),
        "min_site_energy_eV": min(energies),
        "max_site_energy_eV": max(energies),
    }


def run_temperature(
    temperature: str,
    sample_count: int,
    *,
    skip_md: bool,
    pre_steps: int,
    prod_steps: int,
    dump_interval: int,
    cuda_visible_devices: str,
) -> dict[str, float | int]:
    kelvin = TEMPERATURES[temperature]
    workdir = RUNS / temperature / "md"
    workdir.mkdir(parents=True, exist_ok=True)
    write_md_input(workdir, kelvin, pre_steps=pre_steps, prod_steps=prod_steps, dump_interval=dump_interval)

    dump_path = workdir / "dump.xyz"
    if not skip_md and not dump_path.exists():
        run_command(
            ["gpumd"], workdir, name="gpumd_md", cuda_visible_devices=cuda_visible_devices
        )
    if not dump_path.exists():
        raise FileNotFoundError(f"Missing {dump_path}; run MD first or omit --skip-md")

    sampled = sample_dump_frames(dump_path, RUNS / temperature / "samples", sample_count)
    run_minimizations(RUNS / temperature, sampled, cuda_visible_devices=cuda_visible_devices)
    stats = extract_tables(temperature)
    stats["sampled_frames"] = sampled
    stats["pre_equilibration_steps"] = pre_steps
    stats["production_steps"] = prod_steps
    stats["dump_interval"] = dump_interval
    return stats


def main() -> None:
    global RUNS, OUT

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, default=10)
    parser.add_argument("--pre-steps", type=int, default=100000)
    parser.add_argument("--prod-steps", type=int, default=500000)
    parser.add_argument("--dump-interval", type=int, default=1000)
    parser.add_argument("--skip-md", action="store_true")
    parser.add_argument("--temperature", choices=sorted(TEMPERATURES), action="append")
    parser.add_argument("--cuda-visible-devices", default="0")
    parser.add_argument("--runs-dir", type=Path, default=RUNS)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()

    if not SOURCE.exists():
        raise FileNotFoundError("Clone GPUMD-Tutorials into external/GPUMD-Tutorials first.")

    RUNS = args.runs_dir
    OUT = args.out_dir

    temperatures = args.temperature or list(TEMPERATURES)
    summary = {
        "source": "official GPUMD-Tutorials example 32_DOAS_and_AEDP",
        "reproduction_scope": "local GPUMD MD, frame sampling, minimization, extraction, and official-reference comparison",
        "sample_count": args.sample_count,
        "temperatures": {},
    }
    for temperature in temperatures:
        summary["temperatures"][temperature] = run_temperature(
            temperature,
            args.sample_count,
            skip_md=args.skip_md,
            pre_steps=args.pre_steps,
            prod_steps=args.prod_steps,
            dump_interval=args.dump_interval,
            cuda_visible_devices=args.cuda_visible_devices,
        )

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "local_run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
