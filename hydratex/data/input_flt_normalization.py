"""
Float Input Normalization and Validation Module for HydratEx.

This module acts as one of the gateway layer between raw user-supplied float configurations
and core thermodynamic model instances. It queries the local SQLite registry database to
validate supported ranges before initiating simulation.

Core Operations:
    - Resolve appropriate hydrate structure for a given hydrate system.
    - Perform validity of input operation range.
"""
import sqlite3

import numpy as np

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import Guest
from hydratex.core.exceptions import UnsupportedRangeError
from hydratex.core.hydrate.hydrate_structure import StructureType
from hydratex.data.get_db_path import get_db_path

db_path = get_db_path()


def validate_float_input(guest: Guest, input_params: InputParameter):
    """
    Validates if the input float parameters are within the HydratEx supported ranges.

    Args:
        guest: An instance of Guest container for the given system.
        input_params: An instance of InputParameter container holding raw string and float values to be validated.

    Returns:
        hydratex_structure: Equilibrium hydrate structure based on literature findings
        t_min_k: Minimum temperature in Kelvin currently validated and supported by HydratEx.
        t_max_k: Maximum temperature in Kelvin currently validated and supported by HydratEx.

    Raises:
        UnsupportedRangeError: If input float parameters are not within the supported ranges.
    """

    ref_structure, t_min_k, t_max_k = recover_supported_ranges(guest)

    validate_temperature_range(
            input_params=input_params,
            guest=guest,
            ref_t_min_k=t_min_k,
            ref_t_max_k=t_max_k,
        )

    if ref_structure == 'sI':
        hydrate_structure = StructureType.SI
    elif ref_structure == 'sII':
        hydrate_structure = StructureType.SII
    elif ref_structure == 'sH':
        hydrate_structure = StructureType.SH
    else:
        raise UnsupportedRangeError(
            f"Equilibrium hydrate structure must be one of '{StructureType.SI, StructureType.SII, StructureType.SH}' and is missing in the database"
        )

    return hydrate_structure


def recover_supported_ranges(guest: Guest):
    """
    Support function that performs a database query to recover system ranges supported by HydratEx
    simulation engine.

    Args:
        guest: An instance of Guest container, to look for in the database

    Returns:
        hydrate_structure: reference hydrate structure for a particular guest gas hydrate
        t_min_k: minimum temperature in kelvin supported by HydratEx
        t_max_k: maximum temperature in kelvin supported by HydratEx

    Raises:
        UnsupportedRangeError: If the requested simulation range is outside the scope
        of HydratEx validated range.

    """
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("""
        SELECT
            hydrate_structure,
            t_min_k,
            t_max_k
        FROM 
            guest_validity_ranges
        WHERE
            guest_code = ?
        """, (guest.code.lower(),))

        row = cursor.fetchone()

        if row is None:
            raise UnsupportedRangeError(
                f"System ranges for Guest code '{guest.code.upper()}' not found in database. Please raise an issue."
            )

        return row['hydrate_structure'], row['t_min_k'], row['t_max_k']


def validate_temperature_range(
        input_params: InputParameter,
        guest: Guest,
        ref_t_min_k: float,
        ref_t_max_k: float):
    """
    Support function for validating temperature ranges supported by HydratEx.

    Args:
        input_params: InputParameter instance containing temperature input
        guest: Guest instance that needs to be validated
        ref_t_min_k: Reference minimum temperature in kelvin retrieved from database
        ref_t_max_k: Reference maximum temperature in kelvin retrieved from database

    Raises:
        UnsupportedRangeError if any of the requested temperature ranges are outside the scope of HydratEx

    """
    if input_params.temperature is not None:
        temp_bounds = np.atleast_1d(input_params.temperature)
    else:
        bounds = [input_params.lower_bound, input_params.upper_bound]
        temp_bounds = np.array([b for b in bounds if b is not None])

    if temp_bounds.size == 0:
        return

    if ref_t_min_k is not None and np.any(temp_bounds < ref_t_min_k):
        raise UnsupportedRangeError(
            f"Temperature = {temp_bounds} K is below supported minimum [{ref_t_min_k}] K for {guest.code.upper()} system."
        )

    if ref_t_max_k is not None and np.any(temp_bounds > ref_t_max_k):
        raise UnsupportedRangeError(
            f"Temperature = {temp_bounds} K is above supported maximum [{ref_t_max_k}] K for {guest.code.upper()} system."
        )
