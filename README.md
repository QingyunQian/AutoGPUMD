# AutoGPUMD

**Agent-assisted Molecular Dynamics Workflow with GPUMD/NEP**

AutoGPUMD is a small, unofficial Python v0.1 demo for reproducible atomistic simulation workflows around GPUMD and NEP. It focuses on workflow automation: setup, data import, analysis, plotting, report generation, and agent-style prompts/tools.

The project is designed for a professor-facing research demo. It does not replace GPUMD, gpyumd, GPUMDkit, or official GPUMD tools.

## Why This Matters for AI-Assisted Atomistic Simulation

Computational materials projects often lose time at workflow boundaries: checking inputs, tracking provenance, launching or importing runs, parsing outputs, making figures, and writing short reports. AutoGPUMD demonstrates how a conservative agent-assisted layer can help automate those steps without inventing potentials or overstating results.

The v0.1 goal is to show that the workflow can:

- run a complete mock MD pipeline on a laptop;
- import official GPUMD tutorial outputs;
- analyze thermo/RDF/MSD data;
- generate figures and provenance-aware reports;
- expose `agent/tools.yaml` and prompt templates for future LLM-agent workflows.

## What Works Today

| Mode | Purpose | Requirement | Report label |
| --- | --- | --- | --- |
| Mock workflow | Full local demo and tests | Python only | `Data mode: MOCK` |
| Real tutorial output | Analyze official GPUMD-Tutorials outputs | Cloned tutorial repo | `Data mode: REAL TUTORIAL OUTPUT` |
| Real GPUMD run | Future A800/user run path | GPUMD, GPU, traceable `nep.txt` | `Data mode: REAL GPUMD RUN / USER-PROVIDED NEP` |

Mock data are synthetic. Tutorial outputs are used for learning and workflow demonstration. Real GPUMD results require a valid executable, suitable runtime environment, and user-provided official or traceable NEP potential.

## Demo Results

The repository includes a small set of generated figures for quick preview. They are committed as lightweight demonstration artifacts; raw imported tutorial files and intermediate CSV/JSON outputs remain ignored by default.

### Mock MD Workflow

Mock mode exercises the full local pipeline: synthetic thermo data, RDF, MSD, plots, and a provenance-aware report. These figures are not physical GPUMD simulation results.

| Temperature | Energy |
| --- | --- |
| ![Mock temperature](examples/al_nvt_mock/figures/temperature.png) | ![Mock energy](examples/al_nvt_mock/figures/energy.png) |

| RDF | MSD |
| --- | --- |
| ![Mock RDF](examples/al_nvt_mock/figures/rdf.png) | ![Mock MSD](examples/al_nvt_mock/figures/msd.png) |

### Official Si Diffusion Tutorial Output

The Si diffusion example imports official GPUMD-Tutorials output and analyzes the MSD/SDC files using the same column convention as the tutorial `plot_results.m`.

| MSD | SDC |
| --- | --- |
| ![Si diffusion MSD](examples/si_diffusion_real/figures/msd.png) | ![Si diffusion SDC](examples/si_diffusion_real/figures/sdc.png) |

## Quickstart: Mock Workflow

Use Python 3.10 or newer.

```bash
uv sync --dev
uv run autogpumd init examples/al_nvt_mock --template al-nvt
uv run autogpumd prepare configs/al_nvt.yaml --mock
uv run autogpumd run examples/al_nvt_mock --mock
uv run autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
uv run autogpumd report examples/al_nvt_mock
uv run pytest
```

Fallback without `uv`:

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

- `examples/al_nvt_mock/figures/temperature.png`
- `examples/al_nvt_mock/figures/energy.png`
- `examples/al_nvt_mock/figures/rdf.png`
- `examples/al_nvt_mock/figures/msd.png`
- `examples/al_nvt_mock/report.md`
- `examples/al_nvt_mock/metadata.yaml`
- `examples/al_nvt_mock/analysis/analysis_summary.json`

## Import and Analyze Official GPUMD Tutorial Outputs

v0.1 supports the official GPUMD-Tutorials Si diffusion example as the real-data demonstration path.

```bash
git clone --depth 1 https://github.com/brucefan1983/GPUMD-Tutorials.git external/GPUMD-Tutorials

uv run autogpumd import-example si-diffusion --source external/GPUMD-Tutorials
uv run autogpumd analyze examples/si_diffusion_real --thermo --msd
uv run autogpumd report examples/si_diffusion_real
```

Expected outputs:

- `examples/si_diffusion_real/source.md`
- `examples/si_diffusion_real/metadata.yaml`
- `examples/si_diffusion_real/analysis/analysis_summary.json`
- `examples/si_diffusion_real/figures/msd.png`
- `examples/si_diffusion_real/figures/sdc.png`
- `examples/si_diffusion_real/report.md`

For the Si diffusion tutorial, `msd.out` and `sdc.out` are interpreted consistently with the official `plot_results.m`; MSD is the mean of columns 2-4, and SDC from VAC is the mean of columns 5-7. Thermo figures are generated only when `thermo.out` has recognizable named columns; unsupported anonymous columns are skipped rather than guessed.

## Optional Real GPUMD Run on A800

This is a v0.2 path, not a v0.1 blocker. If you have GPUMD available on an A800 node and a traceable `nep.txt`, the intended workflow is:

```bash
uv run autogpumd prepare configs/al_nvt.yaml
uv run autogpumd run examples/al_nvt_mock --gpumd gpumd
uv run autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
uv run autogpumd report examples/al_nvt_mock
```

Before treating results scientifically, verify the GPUMD version, input syntax, potential source, and output parser assumptions.

## CLI

```bash
autogpumd init PROJECT_DIR --template al-nvt
autogpumd validate CONFIG_PATH
autogpumd prepare CONFIG_PATH [--mock]
autogpumd run WORKDIR [--gpumd gpumd] [--mock]
autogpumd analyze WORKDIR [--thermo] [--rdf] [--msd]
autogpumd report WORKDIR
autogpumd import-example si-diffusion --source PATH
autogpumd agent-tools
```

## Agent Prompts and Tools

The `agent/` folder contains project-facing agent harness artifacts:

- `agent/tools.yaml`
- `agent/prompts/plan_simulation.md`
- `agent/prompts/debug_gpumd_error.md`
- `agent/prompts/write_report.md`
- `agent/mcp_skills.md`

These files describe safe workflow actions. The v0.1 package does not call a real LLM API.

## Repository Structure

```text
autogpumd/       Python package and CLI implementation
configs/         example YAML workflow configs
examples/        mock and tutorial-output example folders
agent/           tool definitions and prompt templates
scripts/         optional scheduler template
tutorials/       planned tutorial notes
tests/           lightweight pytest suite
```

## Limitations

- Mock outputs are synthetic and are not physical GPUMD results.
- Official tutorial outputs are not original AutoGPUMD simulations.
- Real NEP potentials are never fabricated, bundled, or guessed.
- Current parsers support AutoGPUMD mock thermo CSV, simple XYZ/extended XYZ, and the Si diffusion tutorial MSD/SDC table convention.
- Large trajectories, imported raw files, and local external clones are ignored by default.

## Roadmap

### v0.1

- Mock workflow.
- Official Si diffusion tutorial-output import and analysis.
- Professor-facing README and provenance-aware reports.
- Agent prompts/tools.
- Tests without GPUMD/GPU.

### v0.1+

- PbTe NEP tutorial analysis.
- NEP loss and parity plots.
- Improved parser support for official tutorial formats.

### v0.2

- A800 real GPUMD run.
- Official/user-provided traceable `nep.txt`.
- Real NVT MD demo.
- Optional Slurm template validation.

### v0.3

- NEP training mini-demo.
- High-temperature diffusion case study.
- Confined-system toy case study.
- MCP server or skills integration.

## Citation and Disclaimer

If this demo is used alongside real GPUMD/NEP work, cite the appropriate GPUMD and NEP papers and official documentation. AutoGPUMD is an unofficial learning/demo project and is not affiliated with or endorsed by the GPUMD developers.
