# Plan Simulation

Given a YAML AutoGPUMD config, produce a safe execution plan.

Rules:

- Validate required fields before proposing execution.
- Do not invent files, potentials, or GPUMD syntax.
- If `potential.path` is missing in real mode, ask the user to provide a valid `nep.txt` or switch to mock mode.
- Clearly separate preparation, execution, analysis, plotting, and reporting steps.
- Mention that mock mode is synthetic and suitable for CI/laptop workflow checks.
