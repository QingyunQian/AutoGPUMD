"""Typer command-line interface for AutoGPUMD."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from autogpumd.config import ConfigError, load_config, summarize_config
from autogpumd.import_examples import ImportExampleError, import_example
from autogpumd.runner import WorkflowError, prepare_workdir, run_workdir
from autogpumd.templates import init_project

app = typer.Typer(help="AutoGPUMD workflow helper for GPUMD/NEP demos.")


@app.command()
def init(
    project_dir: Path,
    template: str = typer.Option("al-nvt", "--template", help="Template name."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing template files."),
) -> None:
    """Create a minimal workflow folder."""
    try:
        paths = init_project(project_dir, template=template, force=force)
    except (ValueError, FileExistsError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Initialized {project_dir}")
    for path in paths:
        typer.echo(f"  {path}")


@app.command()
def validate(config_path: Path) -> None:
    """Validate a YAML workflow config."""
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(summarize_config(config))


@app.command()
def prepare(config_path: Path, mock: bool = typer.Option(False, "--mock")) -> None:
    """Generate structure and run template files."""
    try:
        config = load_config(config_path)
        outputs = prepare_workdir(config, mock=mock)
    except (ConfigError, WorkflowError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(summarize_config(config, mock=mock))
    typer.echo("Prepared files:")
    for name, path in outputs.items():
        typer.echo(f"  {name}: {path}")


@app.command()
def run(
    workdir: Path,
    gpumd: str = typer.Option("gpumd", "--gpumd", help="GPUMD executable name or path."),
    mock: bool = typer.Option(False, "--mock", help="Generate deterministic mock outputs."),
) -> None:
    """Run GPUMD or generate deterministic mock outputs."""
    try:
        outputs = run_workdir(workdir, gpumd=gpumd, mock=mock)
    except WorkflowError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo("Run completed:")
    for name, path in outputs.items():
        typer.echo(f"  {name}: {path}")


@app.command()
def analyze(
    workdir: Path,
    thermo: bool = typer.Option(False, "--thermo"),
    rdf: bool = typer.Option(False, "--rdf"),
    msd: bool = typer.Option(False, "--msd"),
) -> None:
    """Analyze supported output files and generate figures."""
    if not any((thermo, rdf, msd)):
        thermo = rdf = msd = True
    try:
        from autogpumd.analysis import analyze_workdir
        from autogpumd.plotting import plot_workdir

        outputs = analyze_workdir(workdir, thermo=thermo, rdf=rdf, msd=msd)
        figures = plot_workdir(workdir, thermo=thermo, rdf=rdf, msd=msd)
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo("Analysis completed:")
    for name, path in outputs.items():
        typer.echo(f"  {name}: {path}")
    for name, path in figures.items():
        typer.echo(f"  figure_{name}: {path}")


@app.command("import-example")
def import_example_command(
    name: str,
    source: Annotated[
        Path,
        typer.Option("--source", help="Path to a cloned GPUMD-Tutorials repo."),
    ],
) -> None:
    """Import a supported official tutorial-output example."""
    try:
        outputs = import_example(name, source=source)
    except ImportExampleError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Imported example: {name}")
    for key, path in outputs.items():
        typer.echo(f"  {key}: {path}")


@app.command()
def report(workdir: Path) -> None:
    """Generate a Markdown report."""
    from autogpumd.report import generate_report

    path = generate_report(workdir)
    typer.echo(f"Wrote report: {path}")


@app.command("analyze-nep")
def analyze_nep(workdir: Path) -> None:
    """Analyze supported NEP tutorial-output files and generate figures."""
    from autogpumd.nep_analysis import analyze_nep_workdir
    from autogpumd.plotting import plot_nep_workdir

    try:
        outputs = analyze_nep_workdir(workdir)
        figures = plot_nep_workdir(workdir)
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo("NEP analysis completed:")
    for name, path in outputs.items():
        typer.echo(f"  {name}: {path}")
    for name, path in figures.items():
        typer.echo(f"  figure_{name}: {path}")


@app.command("agent-tools")
def agent_tools() -> None:
    """Print the agent tool harness definition."""
    path = Path(__file__).resolve().parent.parent / "agent" / "tools.yaml"
    if not path.exists():
        raise typer.BadParameter(f"Missing agent tools file: {path}")
    typer.echo(path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    app()
