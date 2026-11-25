from concurrent.futures import ProcessPoolExecutor

import numpy as np

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_conditions import SystemConditions
from hydratex.config.system_config import SimulationFlags, SystemConfig
from hydratex.core.exceptions import (
    ConvergenceError,
    UnsupportedModelError,
    UnsupportedRangeError,
)
from hydratex.core.methods.search_methods import SearchMethod, set_search_method
from hydratex.core.run_simulation import EquilibriumSolver
from hydratex.core.services.result_postprocess import SimulationMetadata
from hydratex.data.create_guest_bundle import GuestBundle, GuestBundleData
from hydratex.data.input_validation import validate_input_params
from hydratex.utils.logging_utils import LoggerManager
from hydratex.utils.summary_encode_utils import summary_context_generator


def worker_function(
    sys_config: SystemConfig,
    sys_condition: SystemConditions,
    guest_bundle_dict: dict[str, GuestBundle],
    search_method: SearchMethod,
):
    try:

        equilibrium_state = EquilibriumSolver(
            sys_config=sys_config,
            sys_condition=sys_condition,
            guest_bundle_dict=guest_bundle_dict,
            search_method=search_method,
        )

        phase_equilib_state = equilibrium_state.solve()

        return phase_equilib_state

    except UnsupportedModelError as e:
        print(e)

    except UnsupportedRangeError as e:
        print(e)

    except ConvergenceError as e:
        print(e)

    except ValueError as e:
        print(e)

    except NotImplementedError as e:
        print(e)


class BatchOrchestrate:
    def __init__(
        self,
        input_params: InputParameter,
        sim_flags: SimulationFlags,
    ):
        self.input_params = input_params
        self.sim_flags = sim_flags

        self.sys_config: SystemConfig
        self.guest_bundle_dict: dict[str, GuestBundle]
        self.sys_condition: SystemConditions
        self.method = None
        self.logger = None

    def _validate_inputs(self):
        self.sys_config = validate_input_params(self.input_params)

    def _set_search_method(self):
        self.search_method = set_search_method(self.input_params)

    def _build_guest_bundle(self):
        bundle = GuestBundleData(
            sys_config=self.sys_config, search_method=self.search_method
        )
        guest_bundle = bundle.populate()

        key = guest_bundle.compound_id.code
        self.guest_bundle_dict = {key: guest_bundle}

    def _logger_options(self):

        # list of components
        if not self.sys_config.is_pure_system:
            raise NotImplementedError(
                "Multiple guests are currently not implemented within Hydratex. Stay tuned."
            )

        guest_list = self.sys_config.primary_guest.code

        if (
            self.input_params.lower_bound is None
            or self.input_params.upper_bound is None
        ):
            raise ValueError("Lower or upper bounds cannot be None")

        bounded_temp_range = (
            self.input_params.lower_bound,
            self.input_params.upper_bound,
        )

        # Global log
        LoggerManager.initialize(
            guest_label=guest_list,
            job_type="swp",
            temp_bounds=bounded_temp_range,
            verbose=self.sim_flags.verbose,
            save_files=self.sim_flags.save_files,
        )

        # standard phase logger and context
        self.logger = LoggerManager.get_phase_logger("START")
        self.logger.info("Initiating simulation metadata")
        logger_metadata = LoggerManager.get_run_metadata()
        return logger_metadata

    def _sweep_parameters(self):

        param_name = "temperature" if self.input_params.is_temp else "pressure"

        if (
            self.input_params.lower_bound is None
            or self.input_params.upper_bound is None
        ):
            raise ValueError(
                f"Lower and Upper {param_name.capitalize()} bounds needed for sweep functionality."
            )

        values = np.round(
            np.arange(
                self.input_params.lower_bound,
                self.input_params.upper_bound + 1,
                self.input_params.step_size,
            ),
            3,
        )

        print(f"number of simulation points : {len(values)}")

        sweep_params = [
            SystemConditions(temperature=value, pressure=None) for value in values
        ]

        return sweep_params

    def _simulation_metadata(self):

        logger_context = self._logger_options()

        assert self.logger is not None

        summary_context = summary_context_generator(
            sys_config=self.sys_config, sys_condition=self.sys_condition
        )

        self.logger.info(
            f"Starting HydratEx simulation... at {self.sys_condition.temperature} Kelvin",
            extra={"phase": "SIMULATION"},
        )
        self.logger.info(
            "Pressure search algorithm initiated...", extra={"phase": "SIMULATION"}
        )

        simulation_metadata = SimulationMetadata(
            logger=logger_context, summary=summary_context
        )
        return simulation_metadata


    def orchestrate(self):
        self._validate_inputs()

        self._set_search_method()

        self._build_guest_bundle()

        self._logger_options()

        sweep_conditions = self._sweep_parameters()

        # self._simulation_metadata()   #  TODO - fix this for sweep

        results = []

        if len(sweep_conditions) > 100:
            with ProcessPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        worker_function,
                        sys_config=self.sys_config,
                        sys_condition=condition,
                        guest_bundle_dict=self.guest_bundle_dict,
                        search_method=self.search_method,
                    )
                    for condition in sweep_conditions
                ]

                results = [f.result() for f in futures]

        else:
            for condition in sweep_conditions:
                res = worker_function(
                        sys_config=self.sys_config,
                        sys_condition=condition,
                        guest_bundle_dict=self.guest_bundle_dict,
                        search_method=self.search_method, 
                    )
                results.append(res)

        # TODO - post process results 

        quick_results = [res.condition for res in results] 

        return quick_results

        # TODO - CLI output
        