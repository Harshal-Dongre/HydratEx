import pytest

from hydratex.core.vapor.equation_of_state import estimate_vapor_phase_properties


def test_estimate_fugacity(std_guest_bundle_dict, std_sys_config, std_sys_condition):
    fugacity = estimate_vapor_phase_properties(
        sys_operate_cond=std_sys_condition,
        sys_config=std_sys_config,
        guest_bundle_dict=std_guest_bundle_dict
    )

    assert fugacity.compressibility_liquid == pytest.approx(0.837563976)
    assert fugacity.fugacity_vapor == pytest.approx(7.5473998476)



