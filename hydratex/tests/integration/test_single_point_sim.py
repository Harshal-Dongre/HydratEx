import pytest

from hydratex.core.services.point_orchestrate import SinglePoint


def test_single_point_simulation(std_single_sim_input, std_simulation_flags):
    
    single_point_cls = SinglePoint(
        input_params=std_single_sim_input,
        sim_flags=std_simulation_flags)
    
    results = single_point_cls.orchestrate()

    assert results.P_MPa == pytest.approx(8.909, rel=1e-3)
    assert results.bulk_chemical_pot == pytest.approx(0.6687, rel=1e-3)
    assert results.z_vapor == pytest.approx(0.83917, rel = 1e-4)

