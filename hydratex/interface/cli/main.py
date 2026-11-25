from pprint import pprint

import typer
from rich.panel import Panel

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import SimulationFlags
from hydratex.core.services.batch_orchestrate import BatchOrchestrate
from hydratex.core.services.point_orchestrate import SinglePoint
from hydratex.interface.cli.cli_print_results import display_simulation_summary
from hydratex.utils.console_utils import console

app = typer.Typer()

"""
HydratEx Simulation Driver

This module implements the primary execution flow for hydrate equilibrium calculations in HydratEx.
It coordinates phase model selection, equation-of-state evaluation, and nonlinear convergence routines 
to compute hydrate stability conditions under specified thermodynamic states. 
 
The module does not implement thermodynamic models directly. All phase behavior, property evaluation, 
and hydrate-specific formulations are delegated to specialized submodules. Solver behavior is configurable
but bounded by assumptions and numerical limits of the selected models. 

This file is intended to act as the central orchestration layer for a single simulation run. It exposes
structured simulation state and convergence metadata for use by command-line interfaces and visualization tools.

Assumptions:
- The use provides physically meaningful thermodynamic inputs.
- Selected models are internally consistent over the specified state range.
- Convergence behavior is solver-depended and may fail for ill-conditioned systems.

Scope:
- Supports pure guest hydrate systems only.
- Mixed guest systems, electrolyte effects, and advanced solver heuristics are outside the scope of this module. 

Intended use:
- Internal use by the HydratEx CLI and Streamlit interface.
- Not designed as a standalone API entry point.
"""


def show_banner():
    width = 42

    lines = [
        "HydratEx",
        "Gas Hydrate Thermodynamic Simulator",
        "Developed by Harshal J. Dongre"
    ]

    padded_lines = [
        line.center(width) for line in lines
    ]
    banner_text = "\n".join(padded_lines)

    panel = Panel(
        banner_text,
        padding=(1, 0),
        expand=False,
        border_style="blue"
    )

    console.print(panel)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        show_banner()
        typer.echo("Use `hydratex --help` to explore available commands.")


@app.command(name='sim')
def simulate(
        guest: str = typer.Argument(
            ...,
            help="Guest molecules, e.g., CH4"
        ),
        temperature: float = typer.Option(
            298.15,
            "--temp", "-T",
            help="Temperature (K)"
        ),
        eos_instance: str = typer.Option(
            None,
            "--eos", "-E",
            help="Equation of state model"
        ),
        acm_instance: str = typer.Option(
            None,
            "--acm", "-A",
            help="Activity coefficient model"
        ),
        save_files: bool = typer.Option(
            False,
            "--save_files", "-sf",
            help="Save simulation files"
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose", "-v",
            help="Verbose output"
        )
):


    input_params = InputParameter(
        guest_input=safe_lower(guest),
        temperature=temperature,
        eos_input=safe_lower(eos_instance),
        acm_input=safe_lower(acm_instance),
    )

    sim_flags = SimulationFlags(
        save_files=save_files,
        verbose=verbose,
    )

    point = SinglePoint(input_params=input_params,
                             sim_flags=sim_flags)
    processed_results = point.orchestrate()

    display_simulation_summary(
        results = processed_results
    )


@app.command(name='sweep')
def batch_simulate(
        guest: str = typer.Argument(
            ...,
            help="Guest molecules, e.g., CH4"
        ),
        low: float = typer.Option(
            ...,
            "--low", "-L",
            help="Lower sweep bound"
        ),
        high: float = typer.Option(
            ...,
            "--high", "-H",
            help="Upper sweep bound"
        ),
        step: float = typer.Option(
            ...,
            "--step", "-S",
            help="Step size"
        ),
        is_temp: bool = typer.Option(
            True,
            "--temp/--pressure",
            help = "Sweep temperature (K) if true, else pressure (MPa)"
        ),
        eos_instance: str = typer.Option(
            None,
            "--eos", "-E",
            help="Equation of state model"
        ),
        acm_instance: str = typer.Option(
            None,
            "--acm", "-A",
            help="Activity coefficient model"
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose", "-v",
            help="Generate detailed logs"
        ),  # TODO Show detailed logs in Streamlit console
        save_files: bool = typer.Option(
            False,
            "--save_files", "-sf",
            help="Save simulation files"
        )
):

    if low >= high:
        raise typer.BadParameter("--low must be less than --high")

    batch_input = InputParameter(
        guest_input = safe_lower(guest),
        eos_input= safe_lower(eos_instance),
        acm_input=safe_lower(acm_instance),
        is_temp= is_temp,
        lower_bound=low,
        upper_bound=high,
        step_size=step)

    sim_flags = SimulationFlags(
        verbose=verbose,
        save_files=save_files
    )

    batch = BatchOrchestrate(
        input_params=batch_input,
        sim_flags=sim_flags,
    )

    batch_results = batch.orchestrate()
    pprint(batch_results)

    
def safe_lower(value: str | None):
    return value.lower() if isinstance(value, str) else None

if __name__ == '__main__':
    app()
