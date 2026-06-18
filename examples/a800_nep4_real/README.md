# A800 NEP4 Real GPUMD Demo

These are real GPUMD v5.5 runs executed on NVIDIA A800 GPUs using official GPUMD-Tutorials NEP4 inputs.
Raw `*.out` files are kept in `runs/` and are not committed; this folder keeps lightweight figures and run inputs for the README demo.

## Runs

- LLZO ionic conductivity at 1000 K: 12288 atoms, 1000000 steps, 3244.39 s wall time.
- Li3PS4 CodeCheck HAC: 6144 atoms, 400000 total steps, 931.64 s wall time.

## Key Outputs

- LLZO `thermo.out`: 10000 rows; mean temperature 999.89 K.
- LLZO `msd.out`: 1000 rows; final Li running diffusivity proxy 9.687e-06 cm^2/s.
- Li3PS4 `hac.out`: 10000 rows; A800 `kz` mean over the second half 0.309 W/mK.
- Official bundled Li3PS4 reference `kz` mean over the second half: 0.780 W/mK.

The LLZO diffusivity proxy agrees with the official tutorial README. The Li3PS4 CodeCheck figure is a stochastic single-run sanity check; it should be compared by trend and workflow, not read as a converged thermal conductivity estimate. The A800 `kz` mean is lower than the official bundled reference because Green-Kubo/HAC estimates have high finite-trajectory variance, depend on the sampled random trajectory, and are sensitive to noisy long-time integration tails.

## Figures

Each figure is generated as a README-friendly 600 dpi PNG.

- `ionic_1000K/figures/ionic_temperature.png`: equilibrated LLZO temperature samples with a 20 ps rolling mean and 1000 K target line.
- `ionic_1000K/figures/ionic_energy_drift.png`: equilibrated NPT kinetic, potential, and total energy fluctuations around their post-transient means.
- `ionic_1000K/figures/ionic_group_msd.png`: Li MSD and final Li diffusivity proxy in the main panel, with La/Zr/O small-scale MSD in the inset.
- `li3ps4_codecheck/figures/li3ps4_hac_components.png`: raw HAC component signals from the A800 single CodeCheck run.
- `li3ps4_codecheck/figures/li3ps4_integrated_hac.png`: integrated HAC signals from the A800 single CodeCheck run.
- `li3ps4_codecheck/figures/li3ps4_kz_reference_comparison.png`: A800 `kz` compared with official bundled `hac.out` and independent GK references.
