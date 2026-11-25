import numpy as np
from scipy.constants import Boltzmann, pi

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.core.hydrate.hydrate_structure import (
    HydratePureOccupancy,
    OccupancyData,
)
from hydratex.core.hydrate.spherical_cell_potential import (
    compute_del_n_grid,
    safe_cell_potential,
)
from hydratex.core.vapor.equation_of_state import EoSResults
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.unwrap_dict_dataclass import unwrap_single


class CageOccupancy:
    """
    Initialize the HydrateCageOccupancy class.
    """

    def __init__(
        self,
        sys_operate_cond: SystemConditions | EquilibriumConditions,
        sys_config: SystemConfig,
        guest_bundle_dict: dict[str, GuestBundle],
        eos_result_dict: dict[str, EoSResults],
    ):

        self.sys_config = sys_config
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict
        self.eos_result_dict = eos_result_dict

    def evaluate(self):
        """
        Evaluate the cage occupancy for both small and large cavities in the hydrate. This method:
            - Retrieves cavity properties for small and large cavities.
            - Computes radial grid values for integration.
            - Evaluates the cell potential using 'safe_cell_potential'.
            - Computes Langmuir constant and occupancy.
            - Stores results in 'cavity_data' dictionary.

        Returns
        -------
        dict:
            A nested dictionary containing occupancy data_not_needed_DELETE for each compound,
            temperature, and cavity type. Structure:
                {
                    compound: str,
                    temperature: float,
                    cavity_type: 'small' | 'large',
                    cage_occupancy: float
                }

        """

        # TODO - if bool is fitting - the from the optimizer or from SQL database. - do not complicate this function - build a new one ....

        temperature = self.sys_operate_cond.temperature

        if temperature is None:
            raise ValueError("Temperature cannot be None for Cage Occupancy compute.")

        eos_result = unwrap_single(self.eos_result_dict, label = "pure system EOS results")
        vapor_fugacity = eos_result.fugacity_vapor

        bundle = unwrap_single(self.guest_bundle_dict, label="pure system bundle")

        core = bundle.kihara_parameters.core
        sigma = bundle.kihara_parameters.sigma
        epsilon = bundle.kihara_parameters.epsilon

        if not self.sys_config.is_pure_system:
            raise UnsupportedModelError(
                "Multiple guests are currenly unsupported by HydratEx. Stay tuned."
            )

        crystal_data = bundle.hydrate_lattice

        computed_occupancy: dict[str, OccupancyData] = {}

        for cage_name, cage in (
            ("small", crystal_data.small),
            ("large", crystal_data.large),
        ):
            radius = cage.radius  # cavity radius
            coordination = cage.coordination  # cavity coordination

            r_range = np.arange(0.0001e-18, radius - core, 0.5e-13)

            del_nr_grid = compute_del_n_grid(
                r_values=r_range, guest_core=core, cavity_radius=radius
            )

            integral = safe_cell_potential(
                r_values=r_range,
                guest_core=core,
                guest_sigma=sigma,
                guest_epsilon=epsilon,
                cavity_radius=radius,
                cavity_coordination=coordination,
                temperature=temperature,
                del_n_r_grid=del_nr_grid,
            )

            langmuir_const = 4 * pi * integral / (Boltzmann * temperature) * 1e6

            occupancy = (
                langmuir_const * vapor_fugacity / (1 + langmuir_const * vapor_fugacity)
            )

            computed_occupancy[cage_name] = OccupancyData(
                LangmuirConst=langmuir_const, FractionalOcc=occupancy
            )

        crystal_occupancy = HydratePureOccupancy(
            structure=self.sys_config.hyd_structure,
            guest=self.sys_config.primary_guest,
            small=computed_occupancy["small"],
            large=computed_occupancy["large"],
        )

        return crystal_occupancy

