# AutoGPUMD

**Agent-assisted Molecular Dynamics Workflow with GPUMD/NEP**

AutoGPUMD is a small, unofficial Python v0.1 demo for reproducible molecular dynamics workflows around GPUMD and NEP. It shows how an agent-assisted layer can help with simulation setup, mock execution, output analysis, plotting, and report generation while preserving clear scientific provenance.

The first release is intentionally modest: the complete workflow runs in mock mode on a laptop without GPUMD, without a GPU, and without a real NEP potential. Real GPUMD support is exposed as a clean subprocess interface for users who provide their own executable and `nep.txt`.

## Why This Exists

Scientific simulation projects often lose time at workflow boundaries: preparing inputs, checking missing files, launching jobs, parsing outputs, making figures, and writing short reports. These are useful places for LLM-agent-style tools, but only if the tooling is conservative about provenance and physics.

AutoGPUMD demonstrates that idea with a small GPUMD/NEP-inspired workflow:

- validate a YAML simulation plan;
- generate an ASE structure and transparent `run.in` template;
- run deterministic synthetic outputs for CI and local demos;
- analyze thermo, RDF, and MSD data;
- save publication-style figures and a Markdown report;
- define agent tool prompts without calling a real LLM API.

AutoGPUMD does not invent potentials or claim physical conclusions from mock data.

## Mock Mode vs Real GPUMD Mode

| Mode | Purpose | Requirements | Scientific status |
| --- | --- | --- | --- |
| Mock mode | Demonstrate and test the full workflow | Python only | Synthetic data, not physical GPUMD/NEP results |
| Real GPUMD mode | Run an external GPUMD executable | GPUMD, valid user-provided `nep.txt`, reviewed inputs | User-provided simulation provenance |

Mock mode is the default v0.1 path. Real mode deliberately stays thin: AutoGPUMD writes conservative templates and calls `gpumd`, but users must verify GPUMD syntax, potential provenance, and output formats against official documentation.

## Quickstart

Use Python 3.10 or newer.

```bash
pip install -e .
autogpumd init examples/al_nvt_mock --template al-nvt
autogpumd prepare configs/al_nvt.yaml --mock
autogpumd run examples/al_nvt_mock --mock
autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
autogpumd report examples/al_nvt_mock
pytest
```

Expected outputs:

- figures in `examples/al_nvt_mock/figures/`
- report at `examples/al_nvt_mock/report.md`
- processed CSV files in `examples/al_nvt_mock/analysis/`
- mock thermo and trajectory files in `examples/al_nvt_mock/`

The generated report starts with a data-mode label such as `MOCK` or `REAL / USER-PROVIDED`.

## Installation and Development

For a simple editable install:

```bash
pip install -e .
```

For uv-managed development:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

The repository includes `uv.lock` for reproducible development setup. A conda environment file is also provided for users who prefer conda/mamba.

## Real GPUMD Sketch

Prepare `configs/al_nvt.yaml` so `potential.path` points to a real `nep.txt`, then run:

```bash
autogpumd validate configs/al_nvt.yaml
autogpumd prepare configs/al_nvt.yaml
autogpumd run examples/al_nvt_mock --gpumd gpumd
autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
autogpumd report examples/al_nvt_mock
```

Before using real outputs scientifically, inspect `run.in`, confirm GPUMD version compatibility, and verify the provenance of the potential and trajectory files.

## CLI Commands

```bash
autogpumd init PROJECT_DIR --template al-nvt
autogpumd validate CONFIG_PATH
autogpumd prepare CONFIG_PATH [--mock]
autogpumd run WORKDIR [--gpumd gpumd] [--mock]
autogpumd analyze WORKDIR [--thermo] [--rdf] [--msd]
autogpumd report WORKDIR
autogpumd agent-tools
autogpumd submit WORKDIR --scheduler slurm
```

## What v0.1 Includes

- Typer CLI for the full workflow.
- Dataclass-based YAML validation.
- ASE-based Al fcc structure generation.
- Deterministic mock thermo and XYZ trajectory generation.
- Conservative thermo CSV and simple XYZ/extended XYZ parsers.
- Temperature, energy, RDF, and MSD plotting with matplotlib.
- Markdown reports that explicitly distinguish mock from real/user-provided data.
- Agent tool definitions and prompts under `agent/`.
- Lightweight pytest coverage that does not require GPUMD or a GPU.

## Repository Structure

```text
autogpumd/       Python package and CLI implementation
configs/         example YAML workflow configs
examples/        mock and real-mode example folders
agent/           tool definitions and prompt templates for agent workflows
scripts/         Slurm submission template
tutorials/       planned tutorial notes
tests/           lightweight pytest suite
```

## Limitations

- Mock outputs are synthetic and should not be interpreted as physical results.
- Real NEP potentials are never fabricated, bundled, or guessed.
- Current parsers support AutoGPUMD mock thermo CSV and simple XYZ/extended XYZ trajectories.
- The generated `run.in` is a conservative template, not official GPUMD syntax validation.
- Large trajectories, real potentials, and local generated outputs are kept out of git by default.

## Roadmap

- Real GPUMD/NEP tutorial-level run.
- NEP training mini-demo.
- High-temperature diffusion case study.
- Confined-system case study.
- Slurm/A800 cluster integration.
- MCP server integration.

## Citation and Disclaimer

If this demo is used alongside real GPUMD/NEP work, cite the appropriate GPUMD and NEP papers and official documentation. AutoGPUMD is an unofficial learning/demo project and is not affiliated with or endorsed by the GPUMD developers.
