# AutoGPUMD Workflow Report

**Data mode: REAL TUTORIAL OUTPUT**
**Source: official GPUMD-Tutorials / examples/09_Silicon_diffusion**

## Overview

AutoGPUMD is an unofficial learning/demo workflow layer around GPUMD/NEP.
It automates setup, execution or import, analysis, plotting, and Markdown reporting.

## Data provenance

These files are imported from official GPUMD tutorial outputs for learning and workflow demonstration. They are not original AutoGPUMD simulation results.

## System and inputs

- Example type: `md`
- Source path: `official GPUMD-Tutorials / examples/09_Silicon_diffusion`
- Original AutoGPUMD simulation results: `False`
- Workdir: `examples/si_diffusion_real`

## Thermodynamic stability

Thermodynamic output was not available or could not be parsed.

## RDF observations

RDF analysis was not available.

## MSD and diffusion observations

- Estimated diffusion slope proxy: 1.010481 Angstrom^2/ps
- Tutorial-output MSD is imported for workflow demonstration.
- SDC data were parsed from the tutorial `sdc.out` file when available.

![MSD](figures/msd.png)

![SDC](figures/sdc.png)

## Skipped analyses

- thermo: thermo.out requires recognizable named columns for ['kinetic_energy_eV', 'potential_energy_eV', 'step', 'temperature_K', 'time_ps', 'total_energy_eV']; unsupported anonymous thermo.out was skipped

## Parser assumptions

- Searches raw/ and workdir root for supported files
- thermo.out must include recognizable named columns to be parsed
- Si diffusion msd.out follows official plot_results.m; time in column 1 and MSD as mean columns 2-4
- Si diffusion sdc.out follows official plot_results.m; time in column 1 and SDC from VAC as mean columns 5-7

## Limitations

- This is not a replacement for GPUMD, gpyumd, GPUMDkit, or official GPUMD tooling.
- Mock data are synthetic and intended only for workflow validation.
- Official tutorial outputs are used only for learning and workflow demonstration.
- Real NEP potentials are never fabricated by this project.

## Next steps

- PbTe NEP tutorial loss/parity analysis.
- A800 real GPUMD run with a traceable user-provided potential.
- High-temperature diffusion and confined-system case studies.
