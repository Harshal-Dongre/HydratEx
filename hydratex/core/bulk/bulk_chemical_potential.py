from dataclasses import dataclass

import numpy as np
from scipy.constants import gas_constant, zero_Celsius

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.bulk.activity_coefficient import ACMResults, estimate_activity_coeff
from hydratex.core.bulk.liquid_composition import LiquidPhaseComposition
from hydratex.core.hydrate.hydrate_structure import (
    STRUCTURE_REF_DATA,
    HydrateThermoData,
)
from hydratex.core.vapor.equation_of_state import EoSResults
from hydratex.data.create_guest_bundle import GuestBundle


@dataclass
class BulkPhaseEstimates:
    del_chemical_potential : float
    liquid_composition : dict[str, float]
    activity_result : dict[str, float]
    


class BulkPhase:
    def __init__(
            self,
            sys_operate_cond: SystemConditions | EquilibriumConditions,
            guest_bundle_dict: dict[str, GuestBundle],
            sys_config: SystemConfig,
            eos_result_dict: dict[str, EoSResults]):
        
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict
        self.sys_config = sys_config
        self.eos_result_dict = eos_result_dict

    def _estimate_liquid_phase_composition(self):
        liquid_phase_comp_cls = LiquidPhaseComposition(
            sys_config = self.sys_config,
            sys_operate_cond= self.sys_operate_cond,
            guest_bundle_dict= self.guest_bundle_dict,
            eos_result_dict= self.eos_result_dict
        )

        bulk_composition = liquid_phase_comp_cls.estimate()

        return bulk_composition

    def _get_hydrate_thermodynamic_const(self):

        return STRUCTURE_REF_DATA[self.sys_config.hyd_structure]

    def _estimate_activity_coefficients(self, liquid_composition):
        
        return estimate_activity_coeff(
            sys_config = self.sys_config,
            sys_operate_cond = self.sys_operate_cond,
            guest_bundle_dict = self.guest_bundle_dict,
            liquid_phase_composition = liquid_composition
        )

    def _term2(self, hydrate_thermo_constant: HydrateThermoData) -> float:
        """Compute the temperature-corrected enthalpy term. Definite integral calculated and used here.

        Args:
            hydrate_thermo_constant: Hydrate thermodynamic constants.

        Returns:
            float: Temperature-corrected enthalpy term.
        """

        T = self.sys_operate_cond.temperature

        if T is None:
            raise ValueError(
                "Temperature cannot be None for chemical potential estimation."
            )

        T0 = zero_Celsius
 
        if T > T0:
            hW0 = hydrate_thermo_constant.del_hw0_above_ice
        else:
            hW0 = hydrate_thermo_constant.del_hw0_below_ice

        hw_term1 = hW0 +38.12*T0 + 0.0705 * T0**2
        hw_temp_term1 = ((1/T0) - (1/T))
        hw_term2 = 38.12 + 0.141*T0
        hw_temp_term2 = np.log( np.abs(T/T0))
        hw_term3 = 0.0705
        hw_temp_term3 = T-T0

        hw = hw_term1 * hw_temp_term1 -  hw_term2 * hw_temp_term2 + hw_term3 * hw_temp_term3
        return hw/gas_constant

    
    def _term3(self, hydrate_thermo_constant: HydrateThermoData) -> float:
        """Compute the pressure and temperature-corrected volume term.

        Returns:
            float: Temperature- and pressure-corrected volume term.
        """
        vW0 = hydrate_thermo_constant.ref_volume
        P = self.sys_operate_cond.pressure
        T = self.sys_operate_cond.temperature

        if T is None or P is None:
            raise ValueError(
                f"Operating conditions T: {T} or P {P} cannot be None during estimation of bulk phase chemical potential."
            )

        return (vW0 * P + 3.3e-15 * (P**2))/ (gas_constant * T)

    def _term4(self, activity_result: ACMResults, liquid_composition: dict[str, float]) -> float:
        """Compute the logarithmic term for activity coefficient of H2O.

        Args:
            activity_result: Activity coefficients.
            liquid_composition: Liquid phase composition.

        Returns:
            float: Logarithmic term for H2O activity.
        """

        activity_of_interest = activity_result.activity_data["h2o"]
        h2o_composition = liquid_composition['h2o']

        return np.log(activity_of_interest * h2o_composition)
        
    def estimate_chemical_potential(self) -> BulkPhaseEstimates:
        """Calculate the chemical potential of the bulk phase.

        Returns:
            float: Chemical potential value.
        """
        # Estimate liquid composition
        liquid_composition = self._estimate_liquid_phase_composition()

        # Get hydrate thermodynamic constants
        hydrate_thermo_constant = self._get_hydrate_thermodynamic_const()

        # estimate activity coefficients
        activity_result = self._estimate_activity_coefficients(liquid_composition)

        # Compute chemical potential terms

        term1 = hydrate_thermo_constant.ref_chemical_potential / (gas_constant * zero_Celsius)
        term2 = self._term2(hydrate_thermo_constant)
        term3 = self._term3(hydrate_thermo_constant)
        term4 = self._term4(activity_result, liquid_composition)

        chemical_potential = term1 - term2 + term3 - term4

        return BulkPhaseEstimates(
            del_chemical_potential=chemical_potential,
            liquid_composition= liquid_composition,
            activity_result= activity_result.activity_data
        )

