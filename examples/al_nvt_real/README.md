# Al NVT Real GPUMD Example

This placeholder describes the real-mode path. To use it, provide a valid GPUMD installation and a user-supplied `nep.txt`. AutoGPUMD does not ship or fabricate potentials.

Recommended workflow:

```bash
autogpumd validate configs/al_nvt.yaml
autogpumd prepare configs/al_nvt.yaml
autogpumd run examples/al_nvt_mock --gpumd gpumd
```

Before running production calculations, inspect `run.in` and compare it with the official GPUMD documentation and examples for your installed version.
