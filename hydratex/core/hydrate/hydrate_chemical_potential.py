import numpy as np
from attr import dataclass

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.hydrate.cage_occupancy import CageOccupancy
from hydratex.core.hydrate.hydrate_structure import (
    STRUCTURE_REF_DATA,
    HydratePureOccupancy,
)
from hydratex.core.vapor.equation_of_state import EoSResults
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.estimate_hydration_number import calculate_hydration_number

"""
Calculate the chemical potential of water in the hydrate phase.
"""


@dataclass
class HydratePhaseEstimates:
    del_chemical_potential: float
    cage_data: HydratePureOccupancy
    hydration_number: float 


class HydratePhase:
    def __init__(
        self,
        sys_operate_cond: SystemConditions | EquilibriumConditions,
        sys_config: SystemConfig,
        eos_estimates_dict: dict[str, EoSResults],
        guest_bundle_dict:  dict[str, GuestBundle],
    ):
        """
        This class computes the chemical potential of water in the hydrate phase
        based on guest properties and sys_operate_cond conditions.

        Attributes
        ----------
        sys_operate_cond : SystemConditions
            System operating conditions including temperature, pressure, and composition.

        molecular_bip : MolecularInteractionParams
            Guest-host interaction parameters such as sigma and epsilon values.
            vapor_fugacity (float): Vapor fugacity coefficient representing the deviation from ideal gas behavior for the hydrate cage occupancy calculation.
            structure_id (str): Identifier of the hydrate cage structure type, such as "sI" for small or large cavity types.

        Methods
        -------
            evaluate(): Computes and returns the Langmuir-type occupancy for each temperature under different cage structures based on guest properties and sys_operate_cond conditions.
        """
        self.eos_estimates_dict = eos_estimates_dict
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict
        self.sys_config = sys_config

    def estimate_chemical_potential(self) -> HydratePhaseEstimates:
        """
        Estimates the Langmuir-type occupancy of a hydrate cage for various temperatures and cavity types.
        """

        # occupancy estimates - based on Langmuir adsorption theory
        cage_occupancy_cls = CageOccupancy(
            sys_operate_cond=self.sys_operate_cond,
            sys_config=self.sys_config,
            eos_result_dict=self.eos_estimates_dict,
            guest_bundle_dict=self.guest_bundle_dict,
        )

        cavity_occupancy = cage_occupancy_cls.evaluate()

        cage_occupancy = np.array(
            [cavity_occupancy.small.FractionalOcc, cavity_occupancy.large.FractionalOcc]
        )

        ref_hydrate_property = STRUCTURE_REF_DATA[self.sys_config.hyd_structure]

        # number of cages of a particular type per H2O in hydrate lattice
        cage_factor = np.array(ref_hydrate_property.cage_per_water, dtype=np.float64)

        # chemical potential of hydrate phase
        chemical_potential = -np.sum(cage_factor * np.log(1 - cage_occupancy))

        hydration_num = calculate_hydration_number(
            cavity_occupancy=cavity_occupancy,
            guest_bundle_dict=self.guest_bundle_dict,
        )

        return HydratePhaseEstimates(
            del_chemical_potential=chemical_potential, 
            cage_data=cavity_occupancy,
            hydration_number=hydration_num
        )
