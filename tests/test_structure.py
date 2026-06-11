from autogpumd.config import StructureConfig
from autogpumd.structure import build_structure


def test_build_al_fcc_supercell() -> None:
    atoms = build_structure(
        StructureConfig(
            builder="ase_bulk",
            symbol="Al",
            crystalstructure="fcc",
            lattice_constant=4.05,
            supercell=(2, 2, 2),
        )
    )
    assert len(atoms) == 32
    assert atoms.get_chemical_symbols()[0] == "Al"
