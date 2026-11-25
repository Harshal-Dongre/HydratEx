import pytest

from hydratex.config.input_parameter import InputParameter
from hydratex.core.methods.search_methods import SearchMethod, set_search_method


def test_set_search_method_pressure_search():
    input_parameter = InputParameter(temperature=298.15, pressure=None)
    method = set_search_method(input_parameter)

    assert method == SearchMethod.PRESSURE_SEARCH


def test_set_search_method_temperature_search():
    input_parameter = InputParameter(temperature=None, pressure=5.0)
    method = set_search_method(input_parameter)

    assert method == SearchMethod.TEMP_SEARCH


def test_set_search_method_empty_inputs():
    input_parameter = InputParameter(temperature=None, pressure=None)

    with pytest.raises(ValueError,
                       match="Invalid operational conditions: At least one of temperature or pressure must be specified for a single-variable equilibrium search."):
        set_search_method(input_parameter)


def test_set_search_method_both_inputs():
    input_parameter = InputParameter(temperature=298.15, pressure=5.0)
    method = set_search_method(input_parameter)

    assert method == SearchMethod.PRESSURE_SEARCH

