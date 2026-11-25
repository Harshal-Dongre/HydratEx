import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from hydratex.config.system_config import HYDRATEX_SETTINGS
from hydratex.utils.display_symbols import DELTA_MU

logger_base = logging.getLogger(__name__)
logger = logging.LoggerAdapter(logger_base, {"phase": "SOLVER"})

x_tol = HYDRATEX_SETTINGS.x_tol


@dataclass
class ConvergenceResult:
    success: bool
    pressure: float
    method_used: str
    function_calls: int
    iterations: int
    message: str | None
    x_tol: np.float64 = x_tol


class ConvergenceMethod:
    def __init__(
        self,
        pressure_initial,
        pressure_min,
        pressure_max,
        del_mu_pressure_func,
    ):
        self.pressure_initial: float = pressure_initial
        self.pressure_min: float = pressure_min
        self.pressure_max: float = pressure_max
        self.del_mu_pressure_func = del_mu_pressure_func

        self.x_tol: float = x_tol
        self.r_tol: float = 1e-5
        self.method_used = None
        self.message = None
        self.pressure = None

    def default_solver(self) -> ConvergenceResult:

        pressure_min = self.pressure_min
        pressure_max = self.pressure_max
        del_mu_pressure_func = self.del_mu_pressure_func


        product_bracket = del_mu_pressure_func(pressure_min) * del_mu_pressure_func(
            pressure_max
        )

        if product_bracket < 0:
            logger.info(
                f"Product of function evaluation at bracket ends {pressure_min:.4f} MPa, {pressure_max:.4f} MPa is negative ({product_bracket:.6f})\n"
                f"                                      Initiating Brentq solver...\n"
                f"                                      Setting termination criterion {self.x_tol}"
            )

            pressure_converged, convergence_data = self._brentq_call_helper(
                pressure_min,
                pressure_max,
                del_mu_pressure_func(pressure_min),
                del_mu_pressure_func(pressure_max),
            )
            return ConvergenceResult(
                success=True,
                pressure=float(pressure_converged),
                method_used="brentq",
                iterations=convergence_data.iterations,
                function_calls=convergence_data.function_calls,
                message=None,
            )

        elif (
            del_mu_pressure_func(pressure_min) * del_mu_pressure_func(pressure_max)
        ) > 0:
            pressures = self._bracket_maker(
                pressure_min=pressure_min, pressure_max=pressure_max
            )

            del_mu_values = np.array([del_mu_pressure_func(p) for p in pressures])

            # find sign change
            sign_change_index = np.where(np.diff(np.sign(del_mu_values)))[0]

            if len(sign_change_index) > 0:
                idx = sign_change_index[
                    0
                ]  # first index - lowest phase equilibrium pressure

                if idx == len(del_mu_values) - 1:  # last index - unphysical pressure
                    logger.warning(
                        "Pressure converger hit improbable values. Terminating loop"
                    )
                    return ConvergenceResult(
                        success=False,
                        iterations=idx,
                        pressure=pressures[idx],
                        method_used="log bracket",
                        function_calls=idx,
                        message=None,
                    )

                p_low = float(pressures[idx])
                p_high = float(pressures[idx + 1])  # immediately next index

                # default solver - Brentq
                pressure_converged, convergence_data = brentq(
                    del_mu_pressure_func,
                    p_low,
                    p_high,
                    xtol=self.x_tol,
                    full_output=True,
                    disp=False,
                )

                logger.info(
                    f"\nDefault implementation of 'Brentq solver' does not reveal internal convergence steps.\n"
                    f"Printing convergence output data from 'Brentq solver':\n"
                    f"      {convergence_data}"
                )

                return ConvergenceResult(
                    success=True,
                    pressure=float(pressure_converged),
                    method_used="brentq",
                    iterations=convergence_data.iterations,
                    function_calls=convergence_data.function_calls,
                    message=None,
                )

        # function evaluation and iteration counter
        del_mu_pressure_func_counter = 0
        iteration_counter = 0
        pressures = self._bracket_maker(
            pressure_min=pressure_min, pressure_max=pressure_max
        )
        del_mu_values = np.array([del_mu_pressure_func(p) for p in pressures])

        for i in range(20):
            iteration_counter += 1  

            # Fallback recipie 1 - No sign change - dynamic bracketing -> Initial bracketing be good!!
            min_idx = int(np.argmin(np.abs(del_mu_values)))
            pressure_center = pressures[min_idx]

            if (min_idx - 1) <= 0:  # avoid too high or too low pressure hit
                p_low_bound = float(pressures[min_idx] / 1000)
            else:
                p_low_bound = float(pressures[min_idx - 1])

            if (min_idx + 1) >= len(pressures) - 1:
                p_high_bound = float(pressures[min_idx] * 2)
            else:
                p_high_bound = float(pressures[min_idx + 1])

            # immediate neighbours used to refine grid

            if p_low_bound <= 0:  # avoid negative pressure
                p_low_bound = self.x_tol

            delta = (p_high_bound - p_low_bound) / (i + 1)

            # grid update
            pressure_min = pressure_center - delta
            pressure_max = pressure_center + delta

            pressures = self._bracket_maker(
                pressure_min=pressure_min, pressure_max=pressure_max
            )

            for k in range(len(pressures)):
                del_mu_values[k] = np.array([del_mu_pressure_func(pressures[k])])
                del_mu_pressure_func_counter += 1

            differences = [
                del_mu_values[j + 1] - del_mu_values[j]
                for j in range(len(del_mu_values) - 1)
            ]
            least_difference = np.min(
                differences
            )  # min of the difference between consecutive del_mu_values

            if (
                abs(pressure_max - pressure_min) < self.x_tol
                or abs(least_difference) < self.x_tol / 2
            ):
                logger.info(
                    f"Pressure converged (non-sign change) to pressure: {pressure_center:.4f}"
                )

                return ConvergenceResult(
                    success=True,
                    pressure=float(pressure_center),
                    method_used="dynamic bracketing",
                    iterations=iteration_counter,
                    function_calls=del_mu_pressure_func_counter,
                    message=None,
                )

        return ConvergenceResult(
            success=False,
            pressure=float(pressures[-1]),
            method_used="dynamic bracketing",
            iterations=iteration_counter,
            function_calls=del_mu_pressure_func_counter,
            message=None,
        )

    def manual_scan(self) -> ConvergenceResult:
        """
        Performs a brute-force pressure scan to find the minimum absolute value of Δμ.
        Returns the best pressure found, with success if x_tol is achieved.
        """
        step = 0.05
        best_pressure = None
        best_error = float("inf")

        P = self.pressure_min

        iterations = 0
        del_mu_pressure_func_counter = 0

        while P <= self.pressure_max:
            iterations += 1

            val = self.del_mu_pressure_func(P)
            del_mu_pressure_func_counter += 1

            if np.isnan(val):
                P = round(P + step, 10)
                continue

            abs_error = abs(val)

            if abs_error < best_error:
                best_error = abs_error
                best_pressure = P

                # Stop early if tolerance met
                if best_error <= 0.01:
                    return ConvergenceResult(
                        success=True,
                        pressure=best_pressure,
                        method_used="manual",
                        iterations=iterations,
                        function_calls=iterations,
                        message=None,
                    )

            P = round(P + step, 10)

        # Scan complete — return best attempt even if not fully successful
        return ConvergenceResult(
            success=False,
            pressure=P,
            method_used="manual",
            message=f"Manual scan did not meet tolerance. Best error = {best_error:.6f}",
            iterations=iterations,
            function_calls=del_mu_pressure_func_counter,
        )

    def iterative_bi_directional_search(self) -> ConvergenceResult:

        best_pressure = self.pressure_initial
        best_error = abs(self.del_mu_pressure_func(best_pressure))

        step = 0.5
        max_iter = 100
        factor = 0.25
        min_step = self.x_tol / 10

        iteration_number = 0
        del_mu_pressure_func_counter = 0

        for iteration in range(max_iter):
            iteration_number += 1

            pressures_to_try = [best_pressure - step, best_pressure + step]
            found_better = False

            for P in pressures_to_try:
                if P <= 0:
                    continue

                func_val = self.del_mu_pressure_func(P)
                error = abs(func_val)
                del_mu_pressure_func_counter += 1

                if np.isnan(func_val):
                    continue

                if error < best_error:
                    best_error = error
                    best_pressure = P
                    found_better = True

            delta_pressures = abs(pressures_to_try[1] - pressures_to_try[0])

            if delta_pressures < self.x_tol:
                return ConvergenceResult(
                    success=True,
                    pressure=best_pressure,
                    method_used="iterative bi directional search",
                    iterations=iteration_number,
                    function_calls=del_mu_pressure_func_counter,
                    message=None,
                )

            if not found_better:
                step *= factor

            if step < min_step:
                break

        return ConvergenceResult(
            success=False,
            pressure=best_pressure,
            method_used="iterative bi directional search",
            iterations=iteration_number,
            function_calls=del_mu_pressure_func_counter,
            message="Did not converge",
        )

    def _bracket_maker(self, pressure_min, pressure_max, steps=10):

        log_10_p_min = (
            np.log10(pressure_min) if pressure_min > 0 else self.x_tol
        )  # filter non negative pressures and vector spaces

        log_10_p_max = np.log10(pressure_max)

        log_space_array = np.logspace(log_10_p_min, log_10_p_max, steps)

        return log_space_array

    def _brentq_call_helper(self, Pmin, Pmax, F_Pmin, F_Pmax):
        func = self.del_mu_pressure_func
        cache = {}

        def wrapped_function(
            P,
            _Pmin=Pmin,
            _Pmax=Pmax,
            _F_Pmin=F_Pmin,
            _F_Pmax=F_Pmax,
            _xtol=self.x_tol,
            _rtol=self.r_tol,
        ):
            # skip recomputation
            tol_min = max(_xtol, _rtol * abs(_Pmin))

            if abs(P - _Pmin) <= tol_min:
                logger.info(
                    f"[BRENTQ] P=%.6f MPa, {DELTA_MU}=%.3e (endpoint cached) J/mol",
                    P,
                    _F_Pmin,
                )
                return _F_Pmin

            tol_max = max(_xtol, _rtol * abs(_Pmax))
            if abs(P - _Pmax) <= tol_max:
                logger.info(
                    f"[BRENTQ] P=%.6f MPa, {DELTA_MU}=%.3e (endpoint cached) J/mol",
                    P,
                    _F_Pmax,
                )
                return _F_Pmax

            # P iteration 
            key = round(P, 10)
            if key in cache:
                val = cache[key]
                logger.info(
                    f"[BRENTQ] P=%.6f MPa, {DELTA_MU}=%.3e (cache hit) J/mol", P, val
                )
                return val

            # iterate over range
            val = func(P)
            cache[key] = val
            logger.info(f"[BRENTQ] P=%.6f MPa, {DELTA_MU}=%.3e J/mol", P, val)
            return val

        pressure_converged, convergence_data = brentq(
            wrapped_function,
            Pmin,
            Pmax,
            xtol=HYDRATEX_SETTINGS.x_tol,
            rtol=HYDRATEX_SETTINGS.r_tol,
            full_output=True,
            disp=False,
        )
        return pressure_converged, convergence_data
