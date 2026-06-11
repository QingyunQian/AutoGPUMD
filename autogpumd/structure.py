"""Structure generation helpers."""

from __future__ import annotations

from pathlib import Path

from ase import Atoms
from ase.build import bulk
from ase.io import write

from autogpumd.config import StructureConfig


def build_structure(config: StructureConfig) -> Atoms:
    """Build an ASE bulk supercell for the MVP structure builder."""
    atoms = bulk(
        name=config.symbol,
        crystalstructure=config.crystalstructure,
        a=config.lattice_constant,
        cubic=True,
    )
    return atoms.repeat(config.supercell)


def write_structure_files(atoms: Atoms, workdir: Path) -> dict[str, Path]:
    """Write portable structure files for inspection and mock analysis."""
    workdir.mkdir(parents=True, exist_ok=True)
    xyz_path = workdir / "structure.xyz"
    gpumd_note_path = workdir / "structure_note.md"
    write(xyz_path, atoms, format="extxyz")
    gpumd_note_path.write_text(
        "\n".join(
            [
                "# Structure note",
                "",
                "AutoGPUMD writes `structure.xyz` using ASE extended XYZ for the MVP.",
                "Real GPUMD production use may require conversion to the exact input format",
                "expected by your installed GPUMD version or companion tooling.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"xyz": xyz_path, "note": gpumd_note_path}
