# MCP / Agent Skill Notes

AutoGPUMD can be used as a small command-line toolset for an agent-assisted scientific workflow. The MVP keeps this deliberately simple:

- tools are described in `agent/tools.yaml`;
- prompts live in `agent/prompts/`;
- no LLM API calls are made by the package;
- all agent suggestions must preserve scientific provenance and avoid fabricating potentials or results.
