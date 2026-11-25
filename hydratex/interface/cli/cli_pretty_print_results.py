# from hydratex.core.shared._simulation_results_delete import SimulationResults
# from rich import box
# from rich.align import Align
# from rich.panel import Panel
# from rich.rule import Rule
# from rich.table import Table
# from rich.text import Text

# from hydratex.core.solver.converger import ConvergenceResult
# from hydratex.utils.console_utils import console
# from hydratex.utils.retrieve_sys_hw_info import retrieve_sys_arch_info

# sys_arch_info = retrieve_sys_arch_info()

# def display_simulation_results(results: SimulationResults, convergence_result: ConvergenceResult):

#     # Title Panel
#     header = Panel(
#         Align.center("[bold cyan] HydratEx Simulation Results[/bold cyan]", vertical="middle"),
#         border_style="blue",
#         padding=(1, 2),
#         box=box.ROUNDED,
#     )
#     console.print(header)

    


#     # # Simulation summary
#     # sim_summary_table = Table().grid(expand=False)
#     # sim_summary_table.add_column(justify="left", style="bold")
#     # sim_summary_table.add_column(justify="center")
#     # sim_summary_table.add_column()
#     # sim_summary_table.add_row("Simulation ID", " : ", " hydratex_xxxxxxxxxx")
#     # sim_summary_table.add_row("Status", " : ", " Converged")
#     # sim_summary_table.add_row("Host", " : ", " harshal")
#     # console.print(sim_summary_table)
#     # console.print(Rule(characters="."))
#     # console.print(Rule(characters=" ~ |  ", style="cyan"))

#     # ==================== HYDRATEX SIMULATION SUMMARY ====================
#     #
#     # Simulation ID     : hydratex_CH4_270K_20250806_120822
#     # Date & Time       : 2025-08-06 12:08:22
#     # User              : harshal
#     # Host              : macOS (Intel) / Python 3.11

#     # this is the file that needs to be updated

#     # Summary Table
#     summary_table = Table.grid(expand=False)
#     summary_table.add_column(justify="left", style="bold")
#     summary_table.add_column()
#     summary_table.add_row("️ Status", " Converged" if results.pressure else "❌ Failed")
#     summary_table.add_row(" Compound", f" {results.compound_name} ({results.compound_id})")
#     summary_table.add_row("️ Temperature", f" {results.temperature:.2f} K")
#     summary_table.add_row("️ Pressure", f" {results.pressure:.4f} MPa")
#     summary_table.add_row("️ Structure", f" {results.hydrate_structure}")
#     console.print(Panel(summary_table, title="Summary", border_style="green", box=box.SQUARE))

#     # TODO add a flag here to verify we want every simulation result along with summary. if not, print summary alone.
#     # Vapor Phase
#     vapor_table = Table(title="Vapor Phase", box=box.MINIMAL_DOUBLE_HEAD)
#     vapor_table.add_column("Property", style="bold")
#     vapor_table.add_column("Value", justify="right")
#     vapor_table.add_row("Fugacity (MPa)", f"{results.fugacity:.5f}")
#     console.print(vapor_table)

#     # Hydrate Phase
#     hydrate_table = Table(title="Hydrate Phase", box=box.MINIMAL_DOUBLE_HEAD)
#     hydrate_table.add_column("Property", style="bold")
#     hydrate_table.add_column("Value", justify="right")
#     hydrate_table.add_row("Hydration Number", f"{results.hydration_number:.3f}")
#     hydrate_table.add_row("Δμ (kJ/mol)", f"{results.delta_chemical_potential:.5f}")
#     console.print(hydrate_table)

#     # Liquid Phase
#     if results.liquid_phase_composition:
#         liquid_table = Table(title="Liquid Phase Composition", box=box.MINIMAL_DOUBLE_HEAD)
#         liquid_table.add_column("Component", style="bold")
#         liquid_table.add_column("Mole Fraction", justify="right")
#         for comp, val in results.liquid_phase_composition.items():
#             liquid_table.add_row(comp, f"{val:.4f}")
#         console.print(liquid_table)

#     # Footer Info
#     # log_info = f" Log File: {convergence_result.log_path or 'N/A'}\n" \
#     #            f" Timestamp: {convergence_result.timestamp or 'N/A'}" \


#     # console.print(Panel(Text(log_info), box=box.SQUARE, border_style="grey37"))

#     # Footer -

#     #TODO - silent simulation - add - condensed information to even more level - only the simulation output - summary alone


# # sample output
# #
# #
# # ==================== HYDRATEX SIMULATION SUMMARY ====================
# #
# # Simulation ID     : hydratex_CH4_270K_20250806_120822
# # Date & Time       : 2025-08-06 12:08:22
# # User              : harshal
# # Host              : macOS (Intel) / Python 3.11
# #
# # ------------------ Input Configuration ------------------
# #
# # Guest Molecule    : CH4
# # Temperature       : 270.0 K
# # EoS Model         : Peng–Robinson (pt)
# # Activity Model    : UNIQUAC
# # Hydrate Structure : sI
# # Max Iterations    : 50
# # Tolerance         : 1e-6
# # Method            : Regula Falsi
# #
# # ------------------ Convergence Info ------------------
# #
# # Initial Pressure Guess  : 5.0 MPa
# # Final Converged Pressure: 8.39 MPa
# # Converged in Iterations : 8
# # Final Fugacity Diff      : 6.2e-5
# #
# # ------------------ Output ------------------
# #
# # Hydrate Phase Mole Fractions:
# #   CH4      : 0.97
# #   H2S      : 0.03
# #
# # Total Cavities Filled    : 0.835
# # Equilibrium Pressure     : 8.39 MPa
# #
# # ------------------ Status ------------------
# #
# # Simulation Status        : ✅ SUCCESS
# # Fallbacks Used           : ❌ No
# # Warnings Encountered     : 0
# # Errors Encountered       : 0
# #
# # ================= END OF SIMULATION SUMMARY =================
