import pytest

from hydratex.config.system_config import ACMType
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.data.create_guest_bundle import GuestBundleData


def test_get_guest_bundle(std_guest_ch4, std_sys_config):
    bundle = GuestBundleData(sys_config=std_sys_config, search_method=SearchMethod.PRESSURE_SEARCH)
    guest_bundle = bundle.populate()

    assert guest_bundle.kihara_parameters.core == 3.834e-11
    assert guest_bundle.critical_property.Vc == 98.6
    assert guest_bundle.henry_constant.H3 == 25.0405
    assert guest_bundle.compound_id.name == "Methane"
    assert guest_bundle.initiation_param.param_a == pytest.approx(0.11215677565793201)
    assert guest_bundle.acm_parameters.acm_type == ACMType.UNIQUAC
    assert guest_bundle.acm_parameters.parameters.q_params['ch4'] == 1.12393    # type: ignore


def test_get_guest_bundle_unknown(std_unknown_sys_config):
    bundle = GuestBundleData(sys_config=std_unknown_sys_config, search_method=SearchMethod.PRESSURE_SEARCH)
    with pytest.raises(UnsupportedModelError,
                       match=r"Critical properties for Component 'UNKNOWN_GUEST' not found in database\. Raise a feature request\."):
        bundle.populate()

