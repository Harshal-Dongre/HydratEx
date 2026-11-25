import logging

import numpy as np
from scipy.constants import gas_constant

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import SystemConfig
from hydratex.core.vapor.equation_of_state import EoSResults
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.unwrap_dict_dataclass import unwrap_single

logger = logging.getLogger(__name__)

class LiquidPhaseComposition:
    def __init__(
            self,
            sys_config: SystemConfig,
            sys_operate_cond: SystemConditions | EquilibriumConditions,
            guest_bundle_dict: dict[str, GuestBundle],
            eos_result_dict: dict[str, EoSResults]
            ):
        self.sys_config = sys_config
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict
        self.eos_result_dict = eos_result_dict

        self.bundle = unwrap_single(self.guest_bundle_dict, label = "simplified pure system bundle")

    def _op_temperature(self):
        if self.sys_operate_cond.temperature is None:
            raise ValueError(
                "Temperature cannot be None for 'Henry Constant' estimates."
            )
        self.temperature = self.sys_operate_cond.temperature


    def _estimate_henry_const(self):

        henry_param = self.bundle.henry_constant


        henry_const = np.exp(-(
                henry_param.H1
                + henry_param.H2 / self.temperature
                + henry_param.H3 * np.log(self.temperature)
                + henry_param.H4 * self.temperature)) * 101325       # [1/Pa]

        return henry_const

    def _estimate_vol_inf_dilution(self):
        """
        Source: [https: // pubs.acs.org / doi / 10.1021 / je000215o] - volume in [cc/mol]
        """

        return 10.74 + 0.2683 * self.bundle.critical_property.Vc

    def _estimate_water_sat_pressure(self):
            
        if self.temperature < 273.15:
            a, b, c, d = 4.6056, -5501.1243, 2.9446, -8.1431e-3
        else:
            a, b, c, d = 4.1539, -5500.9332, 7.6537, -16.1277e-3

        water_saturation_pressure: float = np.exp(
            a * np.log(self.temperature) + 
            b / self.temperature + 
            c + 
            d * self.temperature
        )                               # [Pa]

        return water_saturation_pressure

    @staticmethod
    def _safe_exponent(exponent_term):
        MAX_EXPONENT_TERM = 700
        if exponent_term > MAX_EXPONENT_TERM:
            logger.warning(f"Exponent term {exponent_term} is too large. Capping to {MAX_EXPONENT_TERM}")
            exponent_term = MAX_EXPONENT_TERM

        return np.exp(exponent_term)

    def estimate(self):

        # unpack important variable 
        pressure = self.sys_operate_cond.pressure 
        self._op_temperature()
        
        eos_result = unwrap_single(self.eos_result_dict, "Unpack EOS Result for pure component system.")
        liquid_fugacity = eos_result.fugacity_liquid
        guest_code = self.sys_config.primary_guest.code

        liquid_composition: dict[str, float] = {}

        if pressure is None:
            raise ValueError("Pressure cannot be 'None' for liquid phase composition estimates.")

        henry_constant = self._estimate_henry_const()
        inf_dilution_vol = self._estimate_vol_inf_dilution()
        water_sat_pressure = self._estimate_water_sat_pressure()

        exponent_term = inf_dilution_vol * ((pressure * 1e6) - water_sat_pressure) / (
            gas_constant * 1e6 * self.temperature)

        guest_liq_frac = liquid_fugacity * 1e6 / (
            henry_constant * self._safe_exponent(exponent_term))

        liquid_composition = {guest_code: guest_liq_frac,
                          'h2o': 1 - guest_liq_frac}

        return liquid_composition

        