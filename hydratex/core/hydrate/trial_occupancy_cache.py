from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class SimulationState:
    eval_fn: Callable[[float], float]
    current_t: float | None = None
    current_p: float | None = None
    cached_t: float | None = None
    m_value: float | None = None


def get_m(state: SimulationState) -> float:
    if state.current_t is None:
        raise ValueError("current_t must be set before computing M")

    if state.cached_t != state.current_t or state.m_value is None:
        state.m_value = state.eval_fn(state.current_t)
        state.cached_t = state.current_t

    return state.m_value


def step_1_set_t(state: SimulationState, t: float) -> None:
    state.current_t = t


def step_2_adjust_t(state: SimulationState, delta_t: float) -> None:
    if state.current_t is not None:
        state.current_t += delta_t


def deep_step_solve_p(state: SimulationState, p: float) -> tuple[float, float, float]:
    state.current_p = p
    m = get_m(state)
    # Example P-dependent calculation using cached M
    xxxx = m + 0.5 * p
    print(xxxx)
    return state.current_t, state.current_p, m  # type: ignore[return-value]


def run_sample(state: SimulationState) -> list[tuple[float, float, float]]:
    outputs: list[tuple[float, float, float]] = []

    # T = 280.0 -> computes M = 560.0 once, reuses across P = 10, 20, 30
    step_1_set_t(state, 280.0)
    for p in (10.0, 20.0, 30.0):
        outputs.append(deep_step_solve_p(state, p))

    # T changes to 290.0 -> recomputes M = 580.0 once, reuses across P = 10, 20
    step_1_set_t(state, 285.0)
    step_2_adjust_t(state, 5.0)  # effective T = 290.0
    for p in (10.0, 20.0):
        outputs.append(deep_step_solve_p(state, p))

    return outputs


if __name__ == "__main__":
    sim_state = SimulationState(eval_fn=lambda t: 2.0 * t)
    for row in run_sample(sim_state):
        print(row)