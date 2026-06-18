# Al NVT Mock Example

This folder is the default mock-mode workspace for the quickstart.
It does not correspond to an official GPUMD tutorial and does not contain
physical simulation results.

Run:

```bash
autogpumd prepare configs/al_nvt.yaml --mock
autogpumd run examples/al_nvt_mock --mock
autogpumd analyze examples/al_nvt_mock --thermo --rdf --msd
autogpumd report examples/al_nvt_mock
```

The generated outputs are synthetic and are kept locally in this example
folder for workflow testing.
