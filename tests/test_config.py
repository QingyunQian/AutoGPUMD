from pathlib import Path

import pytest

from autogpumd.config import ConfigError, load_config, parse_config


def test_load_example_config() -> None:
    config = load_config(Path("configs/al_nvt.yaml"))
    assert config.project.name == "al_nvt_demo"
    assert config.workdir == Path.cwd() / "examples/al_nvt_mock"
    assert config.structure.supercell == (4, 4, 4)
    assert config.simulation.temperature == 300.0


def test_missing_required_section_raises() -> None:
    with pytest.raises(ConfigError, match="Missing required section"):
        parse_config({"project": {"name": "x", "workdir": "w"}})


def test_invalid_supercell_raises() -> None:
    raw = {
        "project": {"name": "x", "workdir": "w"},
        "structure": {
            "builder": "ase_bulk",
            "symbol": "Al",
            "crystalstructure": "fcc",
            "lattice_constant": 4.05,
            "supercell": [1, 2],
        },
        "potential": {"type": "nep", "path": "nep.txt"},
        "simulation": {
            "ensemble": "nvt",
            "temperature": 300,
            "timestep_fs": 1.0,
            "equilibration_steps": 1,
            "production_steps": 10,
            "dump_interval": 1,
        },
    }
    with pytest.raises(ConfigError, match="supercell"):
        parse_config(raw)
