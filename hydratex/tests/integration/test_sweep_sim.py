import pytest

from hydratex.core.services.batch_orchestrate import BatchOrchestrate


def test_sweep_sim(std_sweep_input, std_simulation_flags):
    
    batch = BatchOrchestrate(
        input_params=std_sweep_input,
        sim_flags=std_simulation_flags,
    )

    batch_results = batch.orchestrate()

    assert batch_results[3].pressure == pytest.approx(0.859135, rel=1e-4)
    assert batch_results[5].pressure == pytest.approx(1.10655, rel=1e-4)