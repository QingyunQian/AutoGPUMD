# Si Diffusion Real Tutorial Output

This workdir is for imported official GPUMD-Tutorials output from `examples/09_Silicon_diffusion`.

Import the raw tutorial files locally:

```bash
git clone --depth 1 https://github.com/brucefan1983/GPUMD-Tutorials.git external/GPUMD-Tutorials
uv run autogpumd import-example si-diffusion --source external/GPUMD-Tutorials
uv run autogpumd analyze examples/si_diffusion_real --thermo --msd
uv run autogpumd report examples/si_diffusion_real
```

Raw imported files live under `raw/` and are ignored by git by default.
