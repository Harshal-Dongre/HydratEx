import logging
from random import random

import numpy as np

from hydratex.config.system_conditions import SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import ConvergenceError
from hydratex.core.shared.equilibrate_phases import EquilibratePhases
from hydratex.core.solver.converger import ConvergenceMethod, ConvergenceResult
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.unwrap_dict_dataclass import unwrap_single

logger_base = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger_base, {"phase": "SOLVER"})

class PressureSolver:
    """
    Manages convergence states and fall-back logic for pressure search algorithm.
    """

    def __init__(self,
                 temperature: float,
                 sys_config: SystemConfig,
                 guest_bundle_dict: dict[str, GuestBundle]
                 ):
        """
        Constructor for pressure search algorithm.

        Args:
            temperature: Temperature at with equilibrium pressure is evaluated.
            sys_config: System configuration for a given simulation instance.
            guest_bundle_dict: Property dictionary with model parameters related to simulation instance.
        """
        self.temperature = temperature
        self.sys_config = sys_config
        self.guest_bundle_dict = guest_bundle_dict

    def converge(self) -> ConvergenceResult:
        """

        Returns:

        """
        del_mu_funct = self._pressure_search_function()
        pressure_initial, pressure_min, pressure_max = self._pressure_search_bracket()

        convergence_class = ConvergenceMethod(
            pressure_initial=pressure_initial,
            pressure_min=pressure_min,
            pressure_max=pressure_max,
            del_mu_pressure_func=del_mu_funct
        )

        converged_pressure = convergence_class.default_solver()

        if converged_pressure.success:
            logger.info(
                f"Pressure converged at {converged_pressure.pressure:.4f} using '{converged_pressure.method_used.title()}' solver in {converged_pressure.iterations:} iterations."
            )
            return converged_pressure

        if not converged_pressure.success:
            logger.info(
                "Default pressure solver did not converge. Attempting to find root using iterative bi-directional search")
            converged_pressure = convergence_class.iterative_bi_directional_search()

        if not converged_pressure.success:
            logger.info(
                "Bi-directional search did not converge. Attempting to find root using manual search algorithm.")
            converged_pressure = convergence_class.manual_scan()

        if not converged_pressure.success:
            logger.info("Pressure did not converge.")

            raise ConvergenceError(
                f"Equilibrium solver failed to find the equilibrium pressure for the T = {self.temperature} K."
            )

        return converged_pressure


    def _pressure_search_function(self):

        def pressure_func(p_iter):
            
            sys_iterate_cond = SystemConditions(
                temperature=self.temperature,
                pressure=p_iter)

            equilib_p_iter = EquilibratePhases(
                sys_operate_cond=sys_iterate_cond,
                guest_bundle_dict=self.guest_bundle_dict,
                sys_config=self.sys_config
            )

            equilib_p_iter_res = equilib_p_iter.chemical_potential_diff()

            return equilib_p_iter_res

        return pressure_func


    def _pressure_search_bracket(self, mode="default"):

        initial_pressure = self._initialization_pressure()

        pressure_min, pressure_max = None, None

        if mode == "default":           # bisection bounds
            pressure_min = initial_pressure * 0.795
            pressure_max = initial_pressure * 1.217

        # only use this to ensure more robust parameter estimation - model do not get stuck in local minima
        elif mode == "challenge":
            pressure_min = initial_pressure * (1 - random())
            pressure_max = initial_pressure * (1 + random())

        logger.info(f"Pressure search bracket identified: [{pressure_min:.4f} MPa, {pressure_max:.4f} MPa]", extra={'phase': "SOLVER"})
        return initial_pressure, pressure_min, pressure_max

    def _initialization_pressure(self):

        bundle = unwrap_single(self.guest_bundle_dict, "Unwrap pure guest bundle")

        param_a = bundle.initiation_param.param_a
        param_b = bundle.initiation_param.param_b

        initial_pressure = np.exp(param_a * self.temperature + param_b)

        logger.info(f"Initializing pressure search with a guess pressure: {initial_pressure:.4f} MPa.", extra={'phase': "SOLVER'})"})

        return initial_pressure
