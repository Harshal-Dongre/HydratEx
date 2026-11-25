
from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_conditions import SystemConditions
from hydratex.config.system_config import SimulationFlags, SystemConfig
from hydratex.core.exceptions import (
    ConvergenceError,
    UnsupportedModelError,
    UnsupportedRangeError,
)
from hydratex.core.methods.search_methods import set_search_method
from hydratex.core.run_simulation import EquilibriumSolver
from hydratex.core.services.result_postprocess import (
    SimulationMetadata,
    process_simulation_results,
)
from hydratex.data.create_guest_bundle import GuestBundle, GuestBundleData
from hydratex.data.input_validation import validate_input_params
from hydratex.utils.logging_utils import LoggerManager
from hydratex.utils.summary_encode_utils import summary_context_generator


class Orchestrate:
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

        # Initialize globally based on config flags
        LoggerManager.initialize(
            guest_label=guest_list,
            job_type="sgl",
            temp_bounds=self.input_params.temperature,
            verbose=self.sim_flags.verbose,
            save_files=self.sim_flags.save_files,
        )

        # standard phase logger and context
        self.logger = LoggerManager.get_phase_logger("START")
        self.logger.info("Initiating simulation metadata")
        logger_metadata = LoggerManager.get_run_metadata()

        return logger_metadata

    def _set_sys_condition(self):

        # single point simulation - so no need of upper and lower bounds
        self.sys_condition = SystemConditions(
            temperature=self.input_params.temperature,
            pressure=self.input_params.pressure,
        )

    def _simulation_metadata(self):

        logger_context = self._logger_options()

        assert self.logger is not None

        summary_context = summary_context_generator(
            sys_config=self.sys_config, sys_condition=self.sys_condition
        )

        self.logger.info(
            f"Starting HydratEx simulation... at {self.sys_condition.temperature} Kelvin", extra={"phase": "SIMULATION"}
        )
        self.logger.info(
            "Pressure search algorithm initiated...", extra={"phase": "SIMULATION"}
        )

        simulation_metadata = SimulationMetadata(
            logger = logger_context,
            summary = summary_context
        )

        return simulation_metadata

    @staticmethod
    def _process_sim_results(phase_equilib_state, simulation_metadata):
        processed_result_cls, processed_result_df = process_simulation_results(
            equilib_results=phase_equilib_state,
            simulation_metadata=simulation_metadata
        )

        return processed_result_cls, processed_result_df


class SinglePoint(Orchestrate):

    def orchestrate(self):

        try:

            self._validate_inputs()

            self._set_sys_condition()

            self._set_search_method()

            simulation_metadata = self._simulation_metadata()

            self._build_guest_bundle()

            # Run Simulation
            equilibrium_state = EquilibriumSolver(
                sys_config=self.sys_config,
                sys_condition=self.sys_condition,
                guest_bundle_dict=self.guest_bundle_dict, 
                search_method=self.search_method,
            )

            phase_equilib_state = equilibrium_state.solve()

            processed_result_cls, _ = self._process_sim_results(
                phase_equilib_state=phase_equilib_state,
                simulation_metadata = simulation_metadata
            )
            return processed_result_cls

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