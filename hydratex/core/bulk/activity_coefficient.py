import logging
from abc import ABC, abstractmethod

import numpy as np
from attr import dataclass
from scipy.constants import gas_constant

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import ACMType, SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.data.retreive_acm_parameters import UniQuacParams
from hydratex.utils.unwrap_dict_dataclass import unwrap_single

logger = logging.getLogger(__name__)

@dataclass
class ACMResults:
    type: ACMType
    activity_data: dict[str, float]


class ActivityCoefficient(ABC):
    """
    An abstract class that represents the activity coefficient of all the components in a system.

    This class defines the interface for thermodynamic models that compute
    activity coefficient of components present in the bulk aqueous phase. Particularly, important to estimate
    the non-ideality introduced into the bulk aqueous phase (water) due to the presence of guest molecules.
    All subclasses must implement the `evaluate` method, which returns an `ActivityResults` object containing
    relevant outputs for a given compound under specified conditions.
    """
    def __init__(
            self, 
            sys_config: SystemConfig,
            sys_operate_cond: SystemConditions | EquilibriumConditions,
            guest_bundle_dict: dict[str, GuestBundle],
            liquid_phase_composition: dict[str, float]):

        self.sys_config = sys_config
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict
        self.liquid_phase_composition = liquid_phase_composition

    @abstractmethod
    def evaluate(self) -> ACMResults:
        pass


class UNIQUAC(ActivityCoefficient):
    """
    An implementation of the UNIQUAC activity coefficient.
    """

    def evaluate(self) -> ACMResults:

        if not self.sys_config.is_pure_system:
            raise NotImplementedError(
                "Multiple guests are not currently implemented in HydratEx. Stay tuned. "
            )

        bundle = unwrap_single(self.guest_bundle_dict, "Unwrap pure guest bundle.")
        acm_parameters = bundle.acm_parameters.parameters
        if not isinstance(acm_parameters, UniQuacParams):
            raise TypeError(f"Expected UniQuacParams, got {type(acm_parameters).__name__}")

        temperature = self.sys_operate_cond.temperature
        if temperature is None:
            raise ValueError(
                "Temperature cannot be None in ACM estimates."
            )

        ordered_components = list(self.liquid_phase_composition.keys())     # retain same order ***

        # uniquac structure parameters 
        r = np.array([acm_parameters.r_params[component] for component in ordered_components])
        q = np.array([acm_parameters.q_params[component] for component in ordered_components])
        x = np.array([self.liquid_phase_composition[component] for component in ordered_components])        # composition

        interaction = np.zeros((len(ordered_components), len(ordered_components)), dtype= float)

        bip_map = acm_parameters.tau_ij

        # bip = self.activity_coeff_params.uniquac_bip

        for i, comp_i in enumerate(ordered_components):
            for j, comp_j in enumerate(ordered_components):
                if i == j:
                    continue                    # leave diagonal as 0.0 
                val = bip_map.get((comp_i, comp_j))
                if val is None:
                    raise KeyError(f"Missing binary interaction parameter for {(comp_i, comp_j)}")
                interaction[i, j] = val


        # binary interaction scales to temperature
        tau = np.exp(-interaction / (gas_constant * temperature))

        # activity computations using UNIQUAC model
        phi = x * r / (np.dot(x, r))  # volume fraction
        theta = x * q / (np.dot(x, q))  # surface area fraction

        # combinatorial terms
        l = 5 * (r - q) - (r - 1)
        ln_gamma_comb = np.log(phi / x) + 5 * q * np.log(theta / phi) + l - (phi / x) * np.sum(x * l)

        # residual terms
        ln_gamma_res = np.zeros(2)
        for i in range(2):
            sum1 = np.sum(theta * tau[:, i])
            sum2 = np.sum((theta * tau[i, :]) / np.sum(theta * tau, axis=1))
            ln_gamma_res[i] = q[i] * (1 - np.log(sum1) - sum2)

        ln_gamma = ln_gamma_comb + ln_gamma_res
        gamma = np.exp(ln_gamma)

        if len(ordered_components) != len(gamma):
            raise ValueError(
        f"Length mismatch: {len(ordered_components)} components vs {len(gamma)} gamma values"
        )

        activity_results: dict[str, float] = dict(zip(ordered_components, gamma.tolist()))

        return ACMResults(
            type = self.sys_config.acm_config.acm_type,
            activity_data= activity_results
        ) 


class IDEAL(ActivityCoefficient):

    def evaluate(self) -> ACMResults:
        ordered_components = list(self.liquid_phase_composition.keys())
        gamma = np.ones(len(ordered_components))

        if len(ordered_components) != len(gamma):
            raise ValueError(
        f"Length mismatch: {len(ordered_components)} components vs {len(gamma)} gamma values"
        )

        activity_results: dict[str, float] = dict(zip(ordered_components, gamma.tolist()))


        return ACMResults(
            type = self.sys_config.acm_config.acm_type,
            activity_data=activity_results
        )

ACM_CLASS_MAP = {
    ACMType.UNIQUAC: UNIQUAC,
    ACMType.IDEAL: IDEAL,
}


def estimate_activity_coeff(
        sys_config: SystemConfig,
        sys_operate_cond: SystemConditions | EquilibriumConditions,
        guest_bundle_dict: dict[str, GuestBundle],
        liquid_phase_composition: dict[str, float],
) -> ACMResults:

    acm_instance = sys_config.acm_config.acm_type

    if acm_instance not in ACM_CLASS_MAP:
        raise UnsupportedModelError(
            f"EOS Type {acm_instance.value.upper()} currently unsupported. Please raise an issue."
        )

    ACMClass = ACM_CLASS_MAP[acm_instance]

    acm_model_cls = ACMClass(
        sys_config = sys_config,
        sys_operate_cond = sys_operate_cond,
        guest_bundle_dict = guest_bundle_dict,
        liquid_phase_composition = liquid_phase_composition
    )

    return acm_model_cls.evaluate()
