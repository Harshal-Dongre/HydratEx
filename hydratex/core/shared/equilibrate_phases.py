from dataclasses import dataclass

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.bulk.bulk_chemical_potential import (
    BulkPhase,
    BulkPhaseEstimates,
)
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.core.hydrate.hydrate_chemical_potential import (
    HydratePhase,
    HydratePhaseEstimates,
)
from hydratex.core.vapor.equation_of_state import (
    EoSResults,
    estimate_vapor_phase_properties,
)
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.unwrap_dict_dataclass import unwrap_single


@dataclass
class SimulationResults:
    vapor_phase: EoSResults
    hydrate_phase: HydratePhaseEstimates
    bulk_phase: BulkPhaseEstimates


class EquilibratePhases:
    def __init__(
        self,
        sys_operate_cond: SystemConditions | EquilibriumConditions,
        sys_config: SystemConfig,
        guest_bundle_dict: dict[str, GuestBundle],
    ):

        self.sys_operate_cond = sys_operate_cond
        self.sys_config = sys_config
        self.guest_bundle_dict = guest_bundle_dict

        # initiation : store estimate
        self.eos_result_dict: dict[str, EoSResults] = {}

    def _vapor_phase(self):

        if self.sys_config.is_pure_system:
            guest_code = self.sys_config.primary_guest.code
        else:
            raise UnsupportedModelError(
                "Multiple guests are currently unsupported. Please stay tuned."
            )

        eos_estimates: dict[str, EoSResults] = {guest_code: estimate_vapor_phase_properties(
            sys_config=self.sys_config,
            sys_operate_cond=self.sys_operate_cond,
            guest_bundle_dict=self.guest_bundle_dict,
        )}

        return eos_estimates

    def _bulk_chemical_potential(self) -> BulkPhaseEstimates:

        bulk_phase_cls = BulkPhase(
            sys_operate_cond=self.sys_operate_cond,
            guest_bundle_dict=self.guest_bundle_dict,
            sys_config=self.sys_config,
            eos_result_dict=self.eos_result_dict,
        )

        return bulk_phase_cls.estimate_chemical_potential()

    def _hydrate_chemical_potential(self) -> HydratePhaseEstimates:
        hydrate_phase_cls = HydratePhase(
            sys_config=self.sys_config,
            sys_operate_cond=self.sys_operate_cond,
            eos_estimates_dict=self.eos_result_dict,
            guest_bundle_dict=self.guest_bundle_dict,
        )

        return hydrate_phase_cls.estimate_chemical_potential()

    # def property_run(self):
    def _equilib_phase_properties(self):

        # vapor phase fugacity
        self.eos_result_dict = self._vapor_phase()

        # chemical potential hydrate phase
        self.hydrate_estimates = self._hydrate_chemical_potential()

        # chemical potential bulk phase
        self.bulk_estimates = self._bulk_chemical_potential()

    def chemical_potential_diff(self) -> float:

        self._equilib_phase_properties()

        return (
            self.hydrate_estimates.del_chemical_potential
            - self.bulk_estimates.del_chemical_potential
        )

    def populate_results(self):

        self._equilib_phase_properties()

        eos_estimates = unwrap_single(self.eos_result_dict,"EOS Results unpack")

        return SimulationResults(
            vapor_phase=eos_estimates,
            hydrate_phase=self.hydrate_estimates,
            bulk_phase=self.bulk_estimates,
        )
