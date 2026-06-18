# AutoGPUMD

**Agent-assisted Molecular Dynamics Workflow with GPUMD/NEP**

AutoGPUMD is a small, unofficial Python v0.1 demo for reproducible atomistic simulation workflows around GPUMD and NEP. It focuses on workflow automation: setup, data import, analysis, plotting, report generation, and agent-style prompts/tools.

The project is designed for a professor-facing research demo. It does not replace GPUMD, gpyumd, GPUMDkit, or official GPUMD tools.

## Why This Matters for AI-Assisted Atomistic Simulation

Computational materials projects often lose time at workflow boundaries: checking inputs, tracking provenance, launching or importing runs, parsing outputs, making figures, and writing short reports. AutoGPUMD demonstrates how a conservative agent-assisted layer can help automate those steps without inventing potentials or overstating results.

The v0.1 goal is to show that the workflow can:

- run a complete mock MD pipeline on a laptop;
- import official GPUMD tutorial outputs for Si diffusion;
- run selected official NEP4 GPUMD-Tutorials examples on an A800 node;
- analyze thermo/RDF/MSD data;
- generate figures and provenance-aware reports;
- expose `agent/tools.yaml` and prompt templates for future LLM-agent workflows.

## What Works Today

| Mode | Purpose | Requirement | Report label |
| --- | --- | --- | --- |
| Mock workflow | Full local demo and tests | Python only | `Data mode: MOCK` |
| Real tutorial output | Analyze official Si diffusion GPUMD-Tutorials outputs | Cloned tutorial repo | `Data mode: REAL TUTORIAL OUTPUT` |
| Optional NEP tutorial preview | Analyze official PbTe NEP loss/parity outputs | Cloned tutorial repo | `Data mode: REAL TUTORIAL OUTPUT` |
| Real GPUMD run | A800 direct-run demo using official NEP4 tutorial inputs | GPUMD 5.5, GPU, traceable `nep.txt` | `Data mode: REAL GPUMD RUN / OFFICIAL TUTORIAL NEP4 INPUT` |

Mock data are synthetic. Imported tutorial outputs are used for learning and workflow demonstration. Real GPUMD results require a valid executable, suitable runtime environment, and official or otherwise traceable NEP potential.

## Demo Results

The repository includes a small set of generated figures for quick preview. They are committed as lightweight demonstration artifacts; raw imported tutorial files and intermediate CSV/JSON outputs remain ignored by default.

### Mock MD Workflow

Mock mode exercises the full local pipeline: synthetic thermo data, RDF, MSD, plots, and a provenance-aware report. These figures are not physical GPUMD simulation results. The energy panel shows drift relative to the initial value, which makes stability easier to inspect than plotting absolute potential, kinetic, and total energies on one axis.

| Temperature | Energy drift |
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

### Optional PbTe NEP Tutorial-Output Preview

The PbTe example imports official GPUMD-Tutorials NEP evaluation outputs and plots the loss curve plus energy/force parity diagnostics. These are tutorial outputs, not AutoGPUMD-trained potentials. In the parity plots, the horizontal axis is the DFT reference value and the vertical axis is the NEP prediction; the diagonal line marks perfect agreement.

| Loss curve | Energy parity |
| --- | --- |
| ![PbTe NEP loss curve](examples/pbte_nep_real/figures/loss_curve.png) | ![PbTe NEP energy parity](examples/pbte_nep_real/figures/energy_test_parity.png) |

| Force parity |
| --- |
| ![PbTe NEP force parity](examples/pbte_nep_real/figures/force_test_parity.png) |

### A800 Real GPUMD NEP4 Runs

To verify the real-GPUMD path, two official GPUMD-Tutorials NEP4 examples were run on NVIDIA A800 GPUs with GPUMD v5.5. The raw `*.out` files are local runtime artifacts under `runs/`; the repository keeps lightweight figures, `run.in` copies, and summaries in `examples/a800_nep4_real`.

| Run | System | Official parameters | Wall time | Key output |
| --- | --- | --- | --- | --- |
| Ionic conductivity | LLZO, 12,288 atoms, 1000 K NPT | 1,000,000 MD steps | 3244 s | `thermo.out` 10,000 rows, `msd.out` 1,000 rows |
| Li3PS4 CodeCheck | Li3PS4, 6,144 atoms, HAC | 200,000 + 200,000 MD steps | 932 s | `hac.out` 10,000 rows |

The LLZO run held the temperature near the 1000 K target, with a mean sampled temperature of 999.89 K. The final Li running self-diffusion proxy from the GPUMD `msd.out` table is `9.687e-06 cm^2/s`, consistent with the tutorial-scale result shown for this input.

| LLZO temperature | LLZO energy components |
| --- | --- |
| ![A800 LLZO temperature](examples/a800_nep4_real/ionic_1000K/figures/ionic_temperature.png)<br><sub>Equilibrated 100-step temperature samples with a 20 ps rolling mean; the dashed line marks the 1000 K target.</sub> | ![A800 LLZO energy components](examples/a800_nep4_real/ionic_1000K/figures/ionic_energy_drift.png)<br><sub>Post-transient NPT kinetic, potential, and total energy fluctuations around their own equilibrated means; this is not an NVE energy-drift test.</sub> |

| LLZO group MSD | Li3PS4 HAC |
| --- | --- |
| ![A800 LLZO group MSD](examples/a800_nep4_real/ionic_1000K/figures/ionic_group_msd.png)<br><sub>Li is the mobile species, so its MSD and running diffusivity are shown in the main panel; La/Zr/O are shown in the inset because their MSD scale is much smaller.</sub> | ![A800 Li3PS4 HAC](examples/a800_nep4_real/li3ps4_codecheck/figures/li3ps4_hac_components.png)<br><sub>Heat-current autocorrelation components from one real A800 CodeCheck trajectory; the panel checks output shape and signal behavior.</sub> |

| Li3PS4 integrated HAC signals |
| --- |
| ![A800 Li3PS4 integrated HAC](examples/a800_nep4_real/li3ps4_codecheck/figures/li3ps4_integrated_hac.png)<br><sub>Integrated HAC components from the same single trajectory; these curves are noisy finite-sampling estimates, not final converged thermal conductivities.</sub> |

The Li3PS4 CodeCheck run is stochastic and should be treated as a workflow sanity check rather than a converged thermal-conductivity result. Green-Kubo/HAC estimates have high finite-trajectory variance: a single run samples one initial velocity/random trajectory, the `kz` integral is sensitive to noisy long-time correlation tails, and the official bundled reference represents a separate reference trajectory/post-processing result. For reference, the official bundled `hac.out` and `kappa_ee.txt` curves agree with each other, while this single A800 run has a lower second-half `kz` mean (`0.309 W/mK` vs official `0.780 W/mK`).

| Li3PS4 A800 run vs official bundled reference |
| --- |
| ![A800 Li3PS4 reference comparison](examples/a800_nep4_real/li3ps4_codecheck/figures/li3ps4_kz_reference_comparison.png)<br><sub>A800 single-run `kz` compared with the official bundled `hac.out` and independent GK reference. The difference is why this demo reports workflow validity, not reproduced convergence.</sub> |

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

Optional PbTe NEP tutorial-output preview:

```bash
uv run autogpumd import-example pbte-nep --source external/GPUMD-Tutorials
uv run autogpumd analyze-nep examples/pbte_nep_real
uv run autogpumd report examples/pbte_nep_real
```

This parses the official tutorial loss/parity output files. It does not run NEP training and does not claim the tutorial potential was produced by AutoGPUMD.

## Real GPUMD Run on A800

If GPUMD is available on an A800 node and a traceable `nep.txt` is provided by the user, the AutoGPUMD-owned workflow remains:

```bash
uv run autogpumd validate configs/al_nvt_real.yaml
uv run autogpumd prepare configs/al_nvt_real.yaml
uv run autogpumd run examples/al_nvt_real --gpumd gpumd
uv run autogpumd analyze examples/al_nvt_real --thermo --rdf --msd
uv run autogpumd report examples/al_nvt_real
```

Place a traceable user-provided potential at `potentials/Al/nep.txt` or edit the config path before `prepare`. Before treating results scientifically, verify the GPUMD version, input syntax, potential source, and output parser assumptions.

For the current professor-facing demo, the validated real-run artifacts are in `examples/a800_nep4_real`, generated from official GPUMD-Tutorials NEP4 inputs rather than AutoGPUMD-trained potentials:

```bash
uv run python scripts/plot_a800_nep4_results.py
```

## CLI

```bash
autogpumd init PROJECT_DIR --template al-nvt
autogpumd validate CONFIG_PATH
autogpumd prepare CONFIG_PATH [--mock]
autogpumd run WORKDIR [--gpumd gpumd] [--mock]
autogpumd analyze WORKDIR [--thermo] [--rdf] [--msd]
autogpumd report WORKDIR
autogpumd import-example si-diffusion --source PATH
autogpumd import-example pbte-nep --source PATH
autogpumd analyze-nep WORKDIR
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
tutorials/       planned tutorial notes
tests/           lightweight pytest suite
```

## Limitations

- Mock outputs are synthetic and are not physical GPUMD results.
- Imported official tutorial outputs are not original AutoGPUMD simulations.
- The A800 NEP4 examples are original local GPUMD runs, but their input structures and NEP potentials come from official GPUMD-Tutorials examples.
- Real NEP potentials are never fabricated, bundled, or guessed.
- Current parsers support AutoGPUMD mock thermo CSV, simple XYZ/extended XYZ, the Si diffusion tutorial MSD/SDC table convention, and the PbTe NEP tutorial loss/parity table convention.
- Large trajectories, imported raw files, and local external clones are ignored by default.

## Citation and Disclaimer

If this demo is used alongside real GPUMD/NEP work, cite the appropriate GPUMD and NEP papers and official documentation. AutoGPUMD is an unofficial learning/demo project and is not affiliated with or endorsed by the GPUMD developers.
