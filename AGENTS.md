# AGENTS.md

Guidance for AI coding agents and human contributors working on AutoGPUMD.

## Project Summary

AutoGPUMD is an unofficial v0.1 research-demo workflow layer around GPUMD/NEP. It demonstrates agent-assisted molecular dynamics workflow steps: config validation, structure preparation, mock execution, analysis, plotting, and report generation.

The main success path is the mock workflow. It must run on a laptop without GPUMD, without a GPU, and without a real NEP potential.

## Non-Negotiable Scientific Boundaries

- Do not claim mock outputs are real physical results.
- Do not invent, bundle, or fabricate NEP potentials.
- Do not claim to replace GPUMD, gpyumd, GPUMDkit, or official GPUMD tooling.
- Do not hard-code undocumented GPUMD file formats.
- Keep real GPUMD support as a clean external interface around a user-provided `gpumd` executable and `nep.txt`.
- Keep tests lightweight and independent of GPUMD, GPUs, cluster schedulers, and large simulation files.

## Required Smoke Workflow

This sequence should work after installation in a Python >=3.10 environment:

```bash
pip install -e .
autogpumd init examples/al_nvt_mock --template al-nvt
autogpumd prepare configs/al_nvt.yaml --mock
autogpumd run examples/al_nvt_mock --mock
autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
autogpumd report examples/al_nvt_mock
pytest
```

Expected generated outputs:

- `examples/al_nvt_mock/figures/temperature.png`
- `examples/al_nvt_mock/figures/energy.png`
- `examples/al_nvt_mock/figures/rdf.png`
- `examples/al_nvt_mock/figures/msd.png`
- `examples/al_nvt_mock/report.md`

Generated simulation outputs are ignored by git and can be recreated.

## Environment

Prefer uv for development:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

The plain `pip install -e .` path is kept for simple demo use and should remain valid.

## Repository Map

- `autogpumd/cli.py`: Typer CLI commands.
- `autogpumd/config.py`: YAML config loading and validation.
- `autogpumd/structure.py`: ASE structure generation.
- `autogpumd/templates.py`: project and `run.in` template writers.
- `autogpumd/runner.py`: mock or external GPUMD execution interface.
- `autogpumd/mock.py`: deterministic synthetic data generation.
- `autogpumd/analysis.py`: thermo, XYZ trajectory, RDF, MSD, diffusion helpers.
- `autogpumd/plotting.py`: matplotlib figure generation.
- `autogpumd/report.py`: Markdown report generation with mock/real provenance.
- `configs/`: example YAML workflow configs.
- `examples/`: demo workdirs and documentation.
- `agent/`: agent tool descriptions and prompt templates.
- `tests/`: lightweight pytest coverage for the mock workflow.

## Coding Guidelines

- Python >=3.10.
- Keep type hints and small focused functions.
- Prefer dataclasses and explicit validation over implicit global state.
- Use `pathlib.Path` for paths.
- Keep parsers conservative and document supported formats.
- Add tests for new behavior, especially anything touching config parsing, mock outputs, analysis, or reports.
- Keep generated outputs, potentials, large trajectories, caches, and local environments out of git.

## Documentation Guidelines

README should stay readable in about three minutes by a potential PhD supervisor. It should answer:

- What is this?
- Why does AI-assisted workflow automation matter here?
- What works today?
- How do I run the demo?
- What is mock versus real GPUMD mode?
- What are the limitations and next steps?

Reports must clearly state whether data are mock or real/user-provided.

## Before Finishing Changes

Run:

```bash
uv run ruff check .
uv run pytest
```

If uv is unavailable in the local shell, use the active Python environment:

```bash
ruff check .
pytest
```

For workflow-impacting changes, also rerun the full mock workflow listed above.
