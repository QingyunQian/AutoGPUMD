"""Configuration models and validation for AutoGPUMD workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a workflow configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    workdir: Path


@dataclass(frozen=True)
class StructureConfig:
    builder: str
    symbol: str
    crystalstructure: str
    lattice_constant: float
    supercell: tuple[int, int, int]


@dataclass(frozen=True)
class PotentialConfig:
    type: str
    path: Path


@dataclass(frozen=True)
class SimulationConfig:
    ensemble: str
    temperature: float
    timestep_fs: float
    equilibration_steps: int
    production_steps: int
    dump_interval: int


@dataclass(frozen=True)
class AnalysisConfig:
    thermo: bool = True
    rdf: bool = True
    msd: bool = True
    diffusion: bool = True
    report: bool = True


@dataclass(frozen=True)
class WorkflowConfig:
    project: ProjectConfig
    structure: StructureConfig
    potential: PotentialConfig
    simulation: SimulationConfig
    analysis: AnalysisConfig
    source_path: Path | None = None

    @property
    def base_dir(self) -> Path:
        return Path.cwd()

    @property
    def workdir(self) -> Path:
        return resolve_relative(self.project.workdir, self.base_dir)

    @property
    def potential_path(self) -> Path:
        return resolve_relative(self.potential.path, self.base_dir)


def resolve_relative(path: Path, base_dir: Path) -> Path:
    return path if path.is_absolute() else (base_dir / path)


def load_config(path: str | Path) -> WorkflowConfig:
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Config file is not valid YAML: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping.")
    return parse_config(raw, source_path=config_path)


def parse_config(raw: dict[str, Any], source_path: Path | None = None) -> WorkflowConfig:
    required_sections = ("project", "structure", "potential", "simulation")
    for section in required_sections:
        if section not in raw:
            raise ConfigError(f"Missing required section: {section}")
        if not isinstance(raw[section], dict):
            raise ConfigError(f"Section '{section}' must be a mapping.")

    project = ProjectConfig(
        name=_required_str(raw["project"], "name"),
        workdir=Path(_required_str(raw["project"], "workdir")),
    )
    structure = StructureConfig(
        builder=_required_str(raw["structure"], "builder"),
        symbol=_required_str(raw["structure"], "symbol"),
        crystalstructure=_required_str(raw["structure"], "crystalstructure"),
        lattice_constant=_positive_float(raw["structure"], "lattice_constant"),
        supercell=_supercell(raw["structure"].get("supercell")),
    )
    potential = PotentialConfig(
        type=_required_str(raw["potential"], "type").lower(),
        path=Path(_required_str(raw["potential"], "path")),
    )
    simulation = SimulationConfig(
        ensemble=_required_str(raw["simulation"], "ensemble").lower(),
        temperature=_positive_float(raw["simulation"], "temperature"),
        timestep_fs=_positive_float(raw["simulation"], "timestep_fs"),
        equilibration_steps=_nonnegative_int(raw["simulation"], "equilibration_steps"),
        production_steps=_positive_int(raw["simulation"], "production_steps"),
        dump_interval=_positive_int(raw["simulation"], "dump_interval"),
    )
    analysis_raw = raw.get("analysis") or {}
    if not isinstance(analysis_raw, dict):
        raise ConfigError("Section 'analysis' must be a mapping when present.")
    analysis = AnalysisConfig(
        thermo=bool(analysis_raw.get("thermo", True)),
        rdf=bool(analysis_raw.get("rdf", True)),
        msd=bool(analysis_raw.get("msd", True)),
        diffusion=bool(analysis_raw.get("diffusion", True)),
        report=bool(analysis_raw.get("report", True)),
    )

    if structure.builder != "ase_bulk":
        raise ConfigError("Only structure.builder='ase_bulk' is supported in the MVP.")
    if potential.type != "nep":
        raise ConfigError("Only potential.type='nep' is supported in the MVP.")
    if simulation.ensemble != "nvt":
        raise ConfigError("Only simulation.ensemble='nvt' is supported in the MVP.")
    if simulation.dump_interval > simulation.production_steps:
        raise ConfigError("simulation.dump_interval must not exceed production_steps.")

    return WorkflowConfig(project, structure, potential, simulation, analysis, source_path)


def summarize_config(config: WorkflowConfig, mock: bool = False) -> str:
    mode = "mock" if mock else "real GPUMD"
    return "\n".join(
        [
            f"Project: {config.project.name}",
            f"Mode: {mode}",
            f"Workdir: {config.workdir}",
            "Structure: "
            f"{config.structure.symbol} {config.structure.crystalstructure}, "
            f"a={config.structure.lattice_constant}, "
            f"supercell={config.structure.supercell}",
            "Simulation: "
            f"{config.simulation.ensemble.upper()} at {config.simulation.temperature:g} K, "
            f"dt={config.simulation.timestep_fs:g} fs, "
            f"production={config.simulation.production_steps} steps",
            f"Potential: {config.potential.type.upper()} at {config.potential_path}",
            "Analysis: "
            f"thermo={config.analysis.thermo}, rdf={config.analysis.rdf}, "
            f"msd={config.analysis.msd}, report={config.analysis.report}",
        ]
    )


def _required_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing or invalid string field: {key}")
    return value


def _positive_float(section: dict[str, Any], key: str) -> float:
    value = section.get(key)
    if not isinstance(value, int | float) or float(value) <= 0:
        raise ConfigError(f"Field '{key}' must be a positive number.")
    return float(value)


def _positive_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"Field '{key}' must be a positive integer.")
    return value


def _nonnegative_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int) or value < 0:
        raise ConfigError(f"Field '{key}' must be a non-negative integer.")
    return value


def _supercell(value: Any) -> tuple[int, int, int]:
    if (
        not isinstance(value, list | tuple)
        or len(value) != 3
        or not all(isinstance(item, int) and item > 0 for item in value)
    ):
        raise ConfigError("structure.supercell must contain three positive integers.")
    return (int(value[0]), int(value[1]), int(value[2]))
