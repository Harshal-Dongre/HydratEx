from enum import StrEnum

from hydratex.config.input_parameter import InputParameter


class SearchMethod(StrEnum):
    TEMP_SEARCH = "temperature_search"
    PRESSURE_SEARCH = "pressure_search"



def set_search_method(input_params: InputParameter) -> SearchMethod:
    """
    Identify appropriate equilibrium search method to use based on input parameters.

    Args:
        input_params: Operational state container; evaluates temperature and pressure configurations.

    Returns:
        The target SearchMethod execution mode.

    Raises:
        ValueError: If both conditions are missing.

    """

    temperatures = input_params.temperature
    pressures = input_params.pressure

    # search mode based on which fixed condition    
    if temperatures is not None and pressures is None:
        return SearchMethod.PRESSURE_SEARCH

    if pressures is not None and temperatures is None:
        return SearchMethod.TEMP_SEARCH

    if temperatures is not None and pressures is not None:
        return SearchMethod.PRESSURE_SEARCH

    print(input_params.is_temp)
    if input_params.is_temp:
        return SearchMethod.PRESSURE_SEARCH

    raise ValueError(
        "Invalid operational conditions: At least one of temperature or pressure "
        "must be specified for a single-variable equilibrium search."
    )

