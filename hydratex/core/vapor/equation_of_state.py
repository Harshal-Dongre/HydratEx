from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from scipy.constants import gas_constant

from hydratex.config.system_conditions import EquilibriumConditions, SystemConditions
from hydratex.config.system_config import EOSType, SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.create_guest_bundle import GuestBundle

# constants 
R = gas_constant


@dataclass
class EoSResults:
    """    
    Data structure holding the computed thermodynamic properties resulting from 
    Equation of State (EoS) evaluation.

    This class encapsulates the output of an EoS model, storing state variables 
    (pressure, temperature) alongside derived thermodynamic properties such as 
    fugacity and compressibility factors for both liquid and vapor phases.

    Attributes:
        compound_id (str): Unique identifier for the compound being evaluated.
        compound_name (str): Human-readable name of the compound.
        pressure (float): System pressure in Mega Pascals.
        temperature (float): System temperature in Kelvin.
        fugacity_liquid (float): Fugacity of the liquid phase (MPa).
        fugacity_vapor (float): Fugacity of the vapor phase (MPa).
        compressibility_liquid (float): Compressibility factor ($Z$) of the liquid phase.
        compressibility_vapor (float): Compressibility factor ($Z$) of the vapor phase.
    """

    type: EOSType
    compound_id: str
    compound_name: str
    pressure: float
    temperature: float
    fugacity_liquid: float
    fugacity_vapor: float
    compressibility_liquid: float
    compressibility_vapor: float


class EoS(ABC):
    """
    Abstract base class for all Equation of State (EoS) models within HydratEx.

    This class defines the standard interface for thermodynamic models used to 
    calculate fluid-phase properties. Subclasses must implement the `evaluate` method 
    to return an `EoSResults` object populated with relevant outputs (e.g., fugacities, 
    compressibility factors) for a specific compound under defined operating conditions.

    All subclasses inherit this interface to ensure consistency in how results are 
    returned and how models are instantiated in the application.

    """

    def __init__(
            self,
            sys_config: SystemConfig,
            sys_operate_cond: SystemConditions,
            guest_bundle_dict: dict[str, GuestBundle]
    ):
        """
        Initialize the Equation of State model with system configuration and data.

        Args:
            sys_config: System configuration containing critical properties and model type.
            sys_operate_cond: Current operating conditions (temperature and pressure).
            guest_bundle_dict: Dictionary mapping guest compound codes to their properties.
        """
        self.sys_config = sys_config
        self.sys_operate_cond = sys_operate_cond
        self.guest_bundle_dict = guest_bundle_dict

        if self.sys_config.is_pure_system:
            self.pure_guest_bundle = guest_bundle_dict[sys_config.primary_guest.code]
            self.crit_property = self.pure_guest_bundle.critical_property

        else:
            raise UnsupportedModelError(
                "Multiple guests are currently not supported. Stay tuned."
            )


    @abstractmethod
    def evaluate(self) -> EoSResults:
        """
        Evaluate the equation of state model and return computed results.

        Returns:
            EoSResults: A structured output containing computed fugacity,
                        compressibility factors, or other model-specific properties.
        """

    

# --- Peng Robinson Equation of State Model Implementation ---
class PengRobinson(EoS):
    """Implementation of the Peng-Robinson Equation of State."""

    def evaluate(self) -> EoSResults:
        """
        Evaluates the Peng-Robinson EoS

        Calculates calculate fugacity coefficients, compressibility factors and other related properties for a given guest
        at a given operating condition.

        Returns:
            A EoSResults object that contains calculated values of pressure, temperature, liquid and vapor fugacity
            coefficients and compressibility factor under the current operating conditions.

        Raises:
            RuntimeError: If no valid real roots for compressibility factor are found.
        """

        if self.sys_operate_cond.temperature is None or self.sys_operate_cond.pressure is None:
            raise ValueError(
                "Temperature or Pressure cannot be 'None' during EOS evaluations"
            )

        T = self.sys_operate_cond.temperature      # temperature 
        P = self.sys_operate_cond.pressure         # pressure 
        
        A, B = self._compute_pr_constants(T, P)
        Z_roots = self._solve_pr_cubic(A, B)

        if len(Z_roots) == 0:
            raise RuntimeError("No valid real roots for compressibility factor.")

        Z_liq = Z_roots.min()
        Z_vap = Z_roots.max()

        ln_phi_liq = self._compute_pr_ln_phi(Z_liq, A, B)
        ln_phi_vap = self._compute_pr_ln_phi(Z_vap, A, B)

        fug_liq = np.exp(ln_phi_liq) * self.sys_operate_cond.pressure
        fug_vap = np.exp(ln_phi_vap) * self.sys_operate_cond.pressure

        results = EoSResults(
            type = self.sys_config.eos_config.eos_type,
            compound_id=self.sys_config.primary_guest.code,
            compound_name=self.sys_config.primary_guest.name,
            pressure=P,
            temperature=T,
            fugacity_liquid=fug_liq,
            fugacity_vapor=fug_vap,
            compressibility_vapor=Z_vap,
            compressibility_liquid=Z_liq
        )

        return results

    def _compute_pr_constants(self, T, P):
        """
        Compute model constant A and B for Peng-Robinson EoS
        """

        Tc = self.crit_property.Tc
        Pc = self.crit_property.Pc
        acentric = self.crit_property.acentric

        # Basic input validation
        if not (Tc > 0 and T > 0):
            raise ValueError("Temperature must be greater than zero")
        if not (Pc > 0 and P >= 0):
            raise ValueError("Pressure must be non-negative")

        Tr = T / Tc  # reduced temperature

        # Peng-Robinson parameters - characteristic constant
        kappa = 0.37464 + 1.54226 * acentric - 0.26992 * acentric ** 2
        alpha = (1 + kappa * (1 - np.sqrt(Tr))) ** 2

        a = 0.45724 * (R ** 2) * (Tc ** 2) * alpha / Pc
        b = 0.07780 * R * Tc / Pc

        A = a * P / (R ** 2 * T ** 2)
        B = b * P / (R * T)

        return A, B

    @staticmethod
    def _solve_pr_cubic(A, B):
        """Solve a cubic equation to find valid roots for compressibility factor.

        Args:
            A (float): First coefficient of the cubic equation.
            B (float): Second coefficient of the cubic equation.

        Returns:
            numpy.ndarray: An array containing real roots where applicable.
        """

        coefficients = [
            1,
            -(1 - B),
            A - 3 * B ** 2 - 2 * B,
            -(A * B - B ** 2 - B ** 3)
        ]
        roots = np.roots(coefficients)
        real_roots = roots[(roots.imag == 0) & (roots.real > 0)].real

        return real_roots

    @staticmethod
    def _compute_pr_ln_phi(Z, A, B):
        """
        Compute natural logarithm of fugacity ratio (phi) using the Peng-Robinson EoS model.

        Args:
            Z (float): Compressibility factor under current operating conditions.
            A (float): Model constant related to critical properties.
            B (float): Model constant related to critical properties.

        Returns:
            float: Natural logarithm of the fugacity ratio for both liquid and vapor phases.
        """
        sqrt2 = np.sqrt(2)
        delta1, delta2 = 1 + sqrt2, 1 - sqrt2

        term1 = Z - 1 - np.log(Z - B)
        term2 = (A / (2 * sqrt2 * B)) * np.log((Z + delta1 * B) / (Z + delta2 * B))

        return term1 - term2


# --- Patel Teja Equation of State Model Implementation ---

class PatelTeja(EoS):
    """Implementation of the Patel-Teja Equation of State."""


    def evaluate(self) -> EoSResults:
        """
        Evaluates the Pate-Teja equation of state.

        Calculates calculate fugacity coefficients, compressibility factors and other related properties for a given guest
        at a given operating condition.

        Returns:
            A EoSResults object that contains calculated values of pressure, temperature, liquid and vapor fugacity
            coefficients and compressibility factor under the current operating conditions.

        Raises:
            RuntimeError: If no valid real roots for compressibility factor are found.
        """

        if self.sys_operate_cond.temperature is None or self.sys_operate_cond.pressure is None:
            raise ValueError(
            "Temperature or Pressure cannot be 'None' during EOS evaluations"
        )

        T = self.sys_operate_cond.temperature      # temperature 
        P = self.sys_operate_cond.pressure         # pressure 

        a, b, c, A, B, C = self._compute_pt_constant(T, P)
        Z_roots = self._compute_pt_compressibility(A, B, C)

        Z_vap = Z_roots.max()
        Z_liq = Z_roots.min()

        ln_phi_vap = self._compute_pt_ln_phi(a, b, c, B, Z_vap, T, P)
        ln_phi_liq = self._compute_pt_ln_phi(a, b, c, B, Z_liq, T, P)

        # fugacity estimates
        fug_vap = np.exp(ln_phi_vap) * P
        fug_liq = np.exp(ln_phi_liq) * P

        # results
        results = EoSResults(
            type = self.sys_config.eos_config.eos_type,
            compound_id=self.sys_config.primary_guest.code,
            compound_name=self.sys_config.primary_guest.name,
            pressure=P,
            temperature=T,
            fugacity_liquid=fug_liq,
            fugacity_vapor=fug_vap,
            compressibility_vapor=Z_vap,
            compressibility_liquid=Z_liq
        )

        return results

    def _compute_pt_constant(self, T, P):
        """Compute model constants for Patel-Teja equation of state."""

        Tc = self.crit_property.Tc
        Pc = self.crit_property.Pc
        acentric = self.crit_property.acentric


        if not (Tc > 0 and T > 0):
            raise ValueError("Temperature must be greater than zero")
        if not (Pc > 0 and P >= 0):
            raise ValueError("Pressure must be non-negative")

        Tr = T / Tc

        # critical compressibility estimates
        kappa = 0.452413 + 1.30982 * acentric - 0.295937 * acentric ** 2  # characteristic constant
        Zc = 0.329032 - 0.076799 * acentric + 0.0211947 * acentric ** 2  # critical compressibility

        alpha = (1 + kappa * (1 - np.sqrt(Tr))) ** 2

        omega_c = 1 - 3 * Zc

        coefficients_b = [
            1,
            (2 - 3 * Zc),
            3 * Zc ** 2,
            -Zc ** 3
        ]
        roots_b = np.roots(coefficients_b)
        omega_b = np.min(roots_b[(roots_b.imag == 0) & (roots_b.real >= 0)].real)  # smallest-real-positive root

        omega_a = (
                3 * Zc ** 2
                + 3 * (1 - 2 * Zc) * omega_b
                + omega_b ** 2
                + 1 - 3 * Zc
        )

        # a, b, c constants
        a = omega_a * alpha * R ** 2 * Tc ** 2 / Pc
        b = omega_b * R * Tc / Pc
        c = omega_c * R * Tc / Pc

        A = a * P / (R ** 2 * T ** 2)
        B = b * P / (R * T)
        C = c * P / (R * T)

        return a, b, c, A, B, C

    @staticmethod
    def _compute_pt_compressibility(A, B, C):
        """Solve a cubic equation to find valid roots for compressibility factor for Patel-Teja equation of state.

        Args:
            A (float): First coefficient of the cubic equation.
            B (float): Second coefficient of the cubic equation.
            C (float): Third coefficient of the cubic equation.

        Returns:
            numpy.ndarray: An array containing real roots where applicable.
        """

        # Cubic compressibility equation
        coefficients = [
            1,
            C - 1,
            A - 2 * B * C - B ** 2 - B - C,
            (B * C + C - A) * B
        ]

        # roots
        roots = np.roots(coefficients)
        real_root = roots[(roots.imag == 0) & (roots.real >= 0)].real

        return real_root

    def _compute_pt_ln_phi(self, a, b, c, B, Z, T, P):
        """
        Compute ln(osmotic coefficient) at a given operating condition for Patel-Teja equation of state.
        """

        # Fugacity coefficient expressions
        N = (b * c + ((b + c) ** 2) / 2) ** (-0.5)
        Q = ((b + c) / 2 + N) * P / (R * T)
        M = ((b + c) / 2 - N) * P / (R * T)

        ln_osmotic_coefficient = (
                Z - 1
                - np.log(Z - B)
                + (a / (2 * R * T * N)) * np.log((Z + M) / (Z + Q))
        )

        return ln_osmotic_coefficient


EOS_CLASS_MAP = {
    EOSType.PT: PatelTeja,
    EOSType.PR: PengRobinson
}



def estimate_vapor_phase_properties(
        sys_config: SystemConfig,
        sys_operate_cond: SystemConditions | EquilibriumConditions,
        guest_bundle_dict: dict[str, GuestBundle] 
) -> EoSResults:

    eos_instance = sys_config.eos_config.eos_type

    if eos_instance not in EOS_CLASS_MAP:
        raise UnsupportedModelError(
            f"EOS Type {eos_instance.value.upper()} currently unsupported. Please raise an issue."
        )

    EoSClass = EOS_CLASS_MAP[eos_instance]

    eos_model_cls = EoSClass(
        sys_config = sys_config,
        sys_operate_cond = sys_operate_cond,
        guest_bundle_dict = guest_bundle_dict
    )

    return eos_model_cls.evaluate()

