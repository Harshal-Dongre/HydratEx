import logging
from dataclasses import dataclass

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import ConvergenceError, UnsupportedModelError
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.core.shared.equilibrate_phases import EquilibratePhases, SimulationResults
from hydratex.core.solver.converger import ConvergenceResult
from hydratex.core.solver.pressure_root_solver import PressureSolver
from hydratex.data.create_guest_bundle import GuestBundle

logger = logging.getLogger(__name__)


@dataclass
class PhaseEquilibriumState:
    configuration: SystemConfig
    condition: EquilibriumConditions
    phase: SimulationResults
    convergence_metadata: ConvergenceResult


class EquilibriumSolver:
    """

    Initiates the identification of equilibrium state between co-existing phases based on
    appropriate (temperature / pressure) search method, and returns the estimated phase properties
    if equilibrium state is found.

    This class uses various search methods to identify the equilibrium pressure and temperature
    for a given system configuration and operating conditions.

    Returns:
        EquilibProperty: Phase properties of the equilibrium state if found.

    """

    def __init__(
        self,
        sys_config: SystemConfig,
        sys_condition: SystemConditions,
        guest_bundle_dict: dict[str, GuestBundle],
        search_method: SearchMethod,
    ):
        """

        Args:
            Args:
            sys_config (SystemConfig): Validated hydratex configuration to simulate.
            sys_condition (SystemConditions): Operating condition used to determine equilibrium state.
            guest_bundle_dict (dict[str, GuestBundle]): Property dataset retrieved from database.
            search_method (SearchMethod): Search method used to determine equilibrium state.

        """
        self.sys_config = sys_config
        self.sys_condition = sys_condition
        self.guest_bundle_dict = guest_bundle_dict
        self.search_method = search_method

    def pressure_solver(self, temperature: float) -> ConvergenceResult:
        """
        Handles the pressure search algorithm for a given temperature.

        Args:
            temperature (float): Temperature in Kelvin at which the equilibrium state is to be found.

        Returns:
            ConvergenceResult: Summary of simulation state including success, pressure, temperature,
                convergence method used, error messages if any, number of function calls, and iterations required.

        Raises:
            ValueError: If the temperature is None.

        """

        pressure_solver = PressureSolver(
            temperature=temperature,
            sys_config=self.sys_config,
            guest_bundle_dict=self.guest_bundle_dict,
        )

        return pressure_solver.converge()

    def solve(self) -> PhaseEquilibriumState:
        """
        Executes the equilibrium state solver for given conditions, based on inputs and appropriate search method.

        Returns:
            EquilibProperty: Phase properties of the equilibrium state if found.

        Raises:
            ConvergenceError: If the algorithm fails to converge.
            UnsupportedModelError: If an unsupported search method is provided.

        """

        if self.search_method == SearchMethod.TEMP_SEARCH:
            # solver_output = self.temperature_solver()     # TODO - add temperature solver
            raise UnsupportedModelError(
                "Temperature search method not yet supported. Stay tuned."
            )

        if self.search_method == SearchMethod.PRESSURE_SEARCH:
            temperature = self.sys_condition.temperature

            if temperature is None:
                raise ValueError(
                    "Temperature value can not be None for 'Pressure Search Algorithm'."
                )

            # initiate pressure search algorithm
            convergence_metadata = self.pressure_solver(temperature=temperature)

            if not convergence_metadata.success:
                raise ConvergenceError(
                    f"Equilibrium solver failed to find the equilibrium pressure for the T = {temperature} K."
                )

            logger.info(
                f"Pressure converged at {temperature} to {convergence_metadata.pressure:.4f} MPa",
                extra={"phase": "SOLVER"},
            )

            sys_equilib_condition = EquilibriumConditions(
                temperature=temperature, pressure=convergence_metadata.pressure
            )

            equilib_phases = EquilibratePhases(
                sys_operate_cond=sys_equilib_condition,
                sys_config=self.sys_config,
                guest_bundle_dict=self.guest_bundle_dict,
            )

            equilib_property = equilib_phases.populate_results()

            phase_equilib_state = PhaseEquilibriumState(
                configuration=self.sys_config,
                condition=sys_equilib_condition,
                phase=equilib_property,
                convergence_metadata=convergence_metadata,
            )

            return phase_equilib_state

        raise UnsupportedModelError(
            f"Unsupported search method: {self.search_method}. Please choose from {SearchMethod.TEMP_SEARCH, SearchMethod.PRESSURE_SEARCH}, else raise an issue."
        )
