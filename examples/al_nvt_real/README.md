# Al NVT Real GPUMD Example

This placeholder describes the real-mode path. To use it, provide a valid GPUMD installation and a user-supplied `nep.txt`. AutoGPUMD does not ship or fabricate potentials.

Recommended workflow:

```bash
autogpumd validate configs/al_nvt_real.yaml
autogpumd prepare configs/al_nvt_real.yaml
autogpumd run examples/al_nvt_real --gpumd gpumd
autogpumd analyze examples/al_nvt_real --thermo --rdf --msd
autogpumd report examples/al_nvt_real
```

The default config expects the potential at `potentials/Al/nep.txt`. Use only a traceable user-provided or official potential, and record its source before presenting real results.

Before running production calculations, inspect `run.in` and compare it with the official GPUMD documentation and examples for your installed version.
