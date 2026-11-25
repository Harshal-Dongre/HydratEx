import re

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from hydratex.utils.console_utils import console


def fmt_comp_dict(d: dict, fmt: str = ".6g") -> str:
    return ", ".join(f"{k.upper()}: {float(v):{fmt}}" for k, v in d.items())

def fmt_comp_lines(d: dict, fmt: str = ".4f") -> str:
    return "\n".join(f"{k.upper()}: {float(v):{fmt}}" for k, v in d.items())

def fmt_sci_compact(val: float, sig_digits: int = 3) -> str:
    s = f"{float(val):.{sig_digits}e}"
    return re.sub(r"e([+-])0(\d+)", r"e\1\2", s)

def display_simulation_summary(
        results         # instance of SimulationSummary
):
    # ================== HEADER PANEL ==================    
    title_text = Text("HydratEx Summary", style="bold white", justify="center")
    header = Panel(
    title_text,
    expand=True,
    padding=(0, 1),
    box=box.DOUBLE,
    border_style="bold bright_cyan",
    )

    # ================== INPUT CONFIGURATION ==================
    cfg = Table(show_header=False, box=box.SIMPLE)

    cfg.add_row("Activity Model", f"{results.ACM_model}")
    cfg.add_row("EoS Model", f"{results.EoS_model}")
    cfg.add_row("Feed Composition", "Pure")
    cfg.add_row("Guest Molecule", f"{results.guest}")

    cfg_panel = Panel(cfg, title="Input Configuration", box=box.ROUNDED)


    # ================== EQUILIBRIUM CONDITIONS ==================
    eq_table = Table(show_header=False, box = box.SIMPLE)

    eq_table.add_row("Hydrate Structure", f"{results.hydrate_structure}")
    eq_table.add_row("Pressure", f"{results.P_MPa:.3f} MPa")
    eq_table.add_row("Temperature", f"{results.T_Kelvin:.3f} K")

    eq_panel = Panel(eq_table, title="Equilibrium Conditions", box=box.ROUNDED)

    # ================== Phases ==================

    # ------------------- Vapor -------------------
    vapor_phase = Table(show_header=False, box = box.SIMPLE)

    vapor_phase.add_row("Compressibility factor", f"{results.z_vapor:.3f}")
    vapor_phase.add_row("Fugacity", f"{results.fugacity_MPa:.3f} MPa")

    vapor_block = Group("[dim]Vapor[/dim]", vapor_phase)

    # ------------------- Aqueous -------------------
    aqueous_phase = Table(show_header=False, box = box.SIMPLE)

    aqueous_phase.add_row("Activity Coefficient",fmt_comp_lines(results.activity_coefficient, ".4f"))
    aqueous_phase.add_row("Bulk delta_mu", f"{results.bulk_chemical_pot:.5f}")
    aqueous_phase.add_row("Composition", fmt_comp_lines(results.aqueous_composition, ".4f"))
    aqueous_phase.add_row("Compressibility factor", f"{results.z_aqueous:.3f}")

    aqueous_block = Group("[dim]Aqeuous[/dim]", aqueous_phase)

    # ------------------- Hydrate -------------------
    hydrate_phase = Table(show_header=False, box = box.SIMPLE)

    hydrate_phase.add_row("Hydrate delta_mu", f"{results.hydrate_chemical_pot:.5f}")
    hydrate_phase.add_row("Hydration number", f"{results.hydration_number:.3f}")
    hydrate_phase.add_row("Occupancy small cage", f"{results.cage_occupancy_small:.3f}")
    hydrate_phase.add_row("Occupancy large cage", f"{results.cage_occupancy_large:.3f}")

    hydrate_block = Group("[dim]Hydrate[/dim]", hydrate_phase)

    phase_contents = Group(vapor_block, Rule(style="dim"),
                           aqueous_block, Rule(style="dim"),
                           hydrate_block,
                           )

    phase_panel = Panel(phase_contents, title="Phase Estimates", box=box.ROUNDED)

    # ================== SOLVER ==================
    conv = Table(show_header=False, box=box.SIMPLE)

    conv.add_row("Final delta_mu", fmt_sci_compact(results.final_chemical_potential_diff))
    # conv.add_row("Execution time", f"{results.elapsed_ms:.3f}")   # TODO 
    conv.add_row("Iterations", f"{results.iterations}")
    conv.add_row("Solver method", f"{results.solver_method}")
    conv.add_row("Solver state", f"{"[green]Converged[/green]" if results.converged else "[red]Not converged[/red]"}")
    conv.add_row("Tolerance", f"{results.tolerance}")
    conv.add_row("Warning", f"{results.warning}")

    conv_panel = Panel(conv, title="Convergence Info", box=box.ROUNDED)

    # ================== METEDATA ==================
    meta_data = Table(show_header=False, box=box.SIMPLE)

    meta_data.add_row("Date & Time", f"{results.date_time}")
    meta_data.add_row("JSON Summary", f"{results.json_summary}")
    meta_data.add_row("Run Hash", f"{results.run_hash}")
    meta_data.add_row("Simulation ID", f"{results.simulation_id}")
    meta_data.add_row("Simulation Log", f"{results.log_path}")

    meta_panel = Panel(meta_data, title="Input Configuration", box=box.ROUNDED)

 
    # ================== RENDER ==================
    
    console.print(header)

    data_group = Group(
        cfg_panel,
        eq_panel,
        phase_panel,
        conv_panel,
        meta_panel
    )

    plot_group = "[dim]Slot for ASCII Plot[/dim]"

    master = Table(show_header=False, box=None, expand=True, padding=(0, 2))
    master.add_column("LHS", ratio=3, no_wrap=False)
    master.add_column("RHS", ratio=2, no_wrap=True)
    master.add_row(data_group, plot_group)

    console.print(Panel(master, box=box.SIMPLE, padding=(0, 1)))
    
    console.print(Rule("END", style="green", characters="="))
