# AutoGPUMD Agent Notes

This repository is a professor-facing demo for agent-assisted GPUMD/NEP workflows. Keep changes simple, reproducible, and clearly labeled by data provenance.

## Core Rules

- Do not fabricate NEP potentials, structures, or scientific claims.
- Distinguish clearly between mock data, imported official tutorial outputs, and original local GPUMD runs.
- Prefer small, readable scripts over large abstractions.
- Keep raw simulation artifacts out of git unless explicitly requested.

## Current Real GPUMD Demo

- The validated A800 demo lives in `examples/a800_nep4_real`.
- Raw run outputs live under `runs/` and are intentionally ignored.
- Regenerate README figures and summaries with:

```bash
uv run python scripts/plot_a800_nep4_results.py
```

- Figures should be committed as PNG only. Do not generate or commit PDF figures unless explicitly requested.
- The LLZO ionic-conductivity run agrees with the official tutorial README scale.
- The Li3PS4 CodeCheck run is a stochastic workflow sanity check; compare it against the official bundled reference, but do not present it as a converged thermal-conductivity result.

## Figure Semantics

- LLZO temperature: plot only the equilibrated region after the initial thermostat transient, with raw 100-step samples plus a 20 ps rolling mean. This shows both noise and stability near 1000 K without overclaiming precision.
- LLZO energy: show equilibrated NPT energy fluctuations around the post-transient mean. Do not label this as conserved energy or energy drift, because NPT dynamics are not an NVE energy-conservation test.
- LLZO MSD: emphasize Li diffusion because Li is the mobile species and matches the tutorial diffusivity scale. Use an inset for La/Zr/O because their MSD values are much smaller and would be visually flattened on the Li scale.
- Li3PS4 HAC: include the official bundled `hac.out`/`kappa_ee.txt` reference comparison. The A800 single run differs in the long-time `kz` mean, so present it as a real-run workflow check, not as a reproduced converged thermal conductivity.
- Keep figure styling publication-oriented: 600 dpi PNG, consistent colors, clear units, panel labels, minimal legends, and no decorative chart clutter.

## GPUMD Notes

- The installed real-run path uses GPUMD v5.5 and NEP4 inputs.
- Old silicon examples using `Si_2022_NEP3_*` are not compatible with GPUMD v5.5.
- Use official GPUMD-Tutorials NEP4 examples for current real-run demos.

## Validation

Before handing off demo changes, run:

```bash
uv run ruff check scripts/plot_a800_nep4_results.py
uv run pytest
```

Also check that README image links point to existing files.
