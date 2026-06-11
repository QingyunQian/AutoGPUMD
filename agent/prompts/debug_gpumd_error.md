# Debug GPUMD Error

Given GPUMD stdout/stderr and the files present in a workdir, suggest likely causes.

Rules:

- Quote only the relevant short error snippets.
- Check for missing `run.in`, missing `nep.txt`, missing structure files, and executable/path issues.
- Do not hallucinate undocumented GPUMD behavior.
- Recommend consulting official GPUMD documentation or examples when syntax is unclear.
- Provide concrete next commands where possible.
