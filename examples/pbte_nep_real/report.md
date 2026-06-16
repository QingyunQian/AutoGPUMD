# AutoGPUMD NEP Workflow Report

**Data mode: REAL TUTORIAL OUTPUT**
**Source: official GPUMD-Tutorials / examples/11_NEP_potential_PbTe**

## Overview

This report summarizes imported NEP tutorial-output files. It does not retrain a potential and does not claim that the tutorial potential was produced by AutoGPUMD.

## Data provenance

These files are imported from official GPUMD tutorial outputs for learning and workflow demonstration. They are not original AutoGPUMD simulation results.

## Loss curve

Loss data were parsed from `loss.out` using the official tutorial plotting convention.

![Loss curve](figures/loss_curve.png)

## Energy and force evaluation

- Train energy RMSE: 0.000369 eV/atom
- Test energy RMSE: 0.000454 eV/atom
- Train force RMSE: 0.039186 eV/Angstrom
- Test force RMSE: 0.038860 eV/Angstrom

![Energy parity](figures/energy_test_parity.png)

![Force parity](figures/force_test_parity.png)

## Parser assumptions

- loss.out follows official plot_results.m columns
- energy_*.out columns are NEP energy then DFT energy
- force_*.out columns 1-3 are NEP force components and columns 4-6 are DFT force components

## Limitations

- This is not a replacement for GPUMD, GPUMDkit, NEP training tools, or official tutorials.
- Tutorial outputs are used for learning and workflow demonstration.
- Real NEP training decisions require careful dataset, hyperparameter, and validation review.

## Next steps

- Extend the same workflow to a small real GPUMD run with a traceable user-provided NEP potential.
- Add a compact NEP training mini-demo only after input data provenance and runtime assumptions are clear.
- Compare tutorial-output diagnostics with future A800-generated outputs.
