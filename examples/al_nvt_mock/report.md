# AutoGPUMD Workflow Report

**Data mode: MOCK**

## Overview

AutoGPUMD is an unofficial learning/demo workflow layer around GPUMD/NEP.
It automates setup, execution or import, analysis, plotting, and Markdown reporting.

## Data provenance

These are synthetic mock data generated for workflow testing and are not physical GPUMD simulation results.

## System and inputs

- Example type: `md`
- Source path: `AutoGPUMD deterministic mock generator`
- Original AutoGPUMD simulation results: `False`
- Workdir: `examples/al_nvt_mock`

## Thermodynamic stability

- Samples: 60
- Mean temperature: 300.13 K
- Temperature standard deviation: 5.79 K
- Total energy drift: 0.0110 eV

![Temperature](figures/temperature.png)

![Energy](figures/energy.png)

## RDF observations

RDF data were generated from the mock XYZ trajectory and illustrate the pipeline, not a physical pair-correlation result.

![RDF](figures/rdf.png)

## MSD and diffusion observations

- Estimated diffusion slope proxy: 0.543086 Angstrom^2/ps
- Mock-mode MSD is synthetic and should not be read as a real diffusivity.

![MSD](figures/msd.png)

## Parser assumptions

- thermo_mock.csv uses AutoGPUMD mock thermo columns
- trajectory_mock.xyz uses simple extended XYZ frames

## Limitations

- This is not a replacement for GPUMD, gpyumd, GPUMDkit, or official GPUMD tooling.
- Mock data are synthetic and intended only for workflow validation.
- Official tutorial outputs are used only for learning and workflow demonstration.
- Real NEP potentials are never fabricated by this project.

## Next steps

- PbTe NEP tutorial loss/parity analysis.
- A800 real GPUMD run with a traceable user-provided potential.
- High-temperature diffusion and confined-system case studies.
