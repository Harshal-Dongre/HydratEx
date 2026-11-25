import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from hydratex.core.run_simulation import PhaseEquilibriumState
from hydratex.utils.logging_utils import LoggerInstanceContext
from hydratex.utils.summary_encode_utils import SimulationSummaryContext


@dataclass
class SimulationMetadata:
    logger : LoggerInstanceContext | None
    summary : SimulationSummaryContext


def _json_serializer(value):
    """Convert NumPy scalars and non-standard floats into strict JSON values."""
    if value is None:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {str(k): _json_serializer(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_serializer(v) for v in value]
    return value


@dataclass
class SimulationSummary:
    # simulation configuration
    EoS_model : str
    ACM_model : str
    guest : str
    feed_composition: dict[str, float]

    # simulation information
    simulation_id : str
    date_time : str
    run_hash: str
    json_summary : str
    log_path: str

    # equilibrium conditions
    T_Kelvin: float
    P_MPa: float

    # solver state
    converged: bool = False
    hydrate_formed: bool = False
    hydrate_structure: str | None = None
    solver_method: str = 'brentq'
    iterations: int = 0
    fallback_used: bool = False
    tolerance: float = 1e-8
    elapsed_ms: float = 0.0
    final_chemical_potential_diff: float = 0

    # vapor phase
    fugacity_MPa: float | None = None
    z_vapor: float | None = None
    z_aqueous: float | None = None

    # bulk / aqueous phase
    bulk_chemical_pot: float | None = None
    aqueous_composition: dict[str, float] = field(default_factory=dict)
    activity_coefficient: dict[str, float] = field(default_factory=dict)

    # hydrate phase
    hydrate_chemical_pot: float | None = None
    cage_occupancy_small: float | None = None
    cage_occupancy_large: float | None = None
    langmuir_small_cage: float | None = None
    langmuir_large_cage: float | None = None
    hydration_number: float | None = None

    # warnings - if any
    warning: str | None = None

    def to_dict(self):
        raw = {
            "configuration" :{
                "EoS_model": self.EoS_model,
                "ACM_model": self.ACM_model,
                "guest": self.guest,
                "feed_composition": self.feed_composition,
            },
            "condition": {
                "T_K": self.T_Kelvin,
                "P_MPa": self.P_MPa,
            },
            "outcome": {
                "converged": self.converged,
                "hydrate_formed": self.hydrate_formed,
                "hydrate_structure": self.hydrate_structure,
                "warning": self.warning,
            },
            "solver": {
                "method": self.solver_method,
                "iterations": self.iterations,
                "fallback_used": self.fallback_used,
                "elapsed_ms": self.elapsed_ms,
                "tolerance": self.tolerance,
                "final_chemical_potential_diff": self.final_chemical_potential_diff,
            },
            "phases": {
                "vapor": {
                    "Z": self.z_vapor,
                    "fugacity": self.fugacity_MPa,
                },
                "aqueous": {
                    "Z": self.z_aqueous,
                    "composition": self.aqueous_composition,
                    "chemical_potential": self.bulk_chemical_pot,
                    "activity_coefficient": self.activity_coefficient,
                },
                "hydrate": {
                    "chemical_potential": self.hydrate_chemical_pot,
                    "cage_occupancy_small": self.cage_occupancy_small,
                    "cage_occupancy_large": self.cage_occupancy_large,
                    "langmuir_small_cage": self.langmuir_small_cage,
                    "langmuir_large_cage": self.langmuir_large_cage,
                    "hydration_number": self.hydration_number,
                },
                "metadata": {
                    "simulation_id": self.simulation_id,
                    "date_time": self.date_time,
                    "run_hash": self.run_hash,
                    "json_summary_path": self.json_summary,
                    "log_path": self.log_path,
                }
            },
        }
        return _json_serializer(raw)

    def to_row(self):
        """Flat dictionary tailored for pd.DataFrame / Streamlit tables & charts."""
        row: dict = {
            "T_K": self.T_Kelvin,
            "P_MPa": self.P_MPa,
            "converged": self.converged,
            "hydrate_structure": self.hydrate_structure,
            "method": self.solver_method,
            "fugacity_MPa": self.fugacity_MPa,
            "z_vapor": self.z_vapor,
            "bulk_chemical_pot": self.bulk_chemical_pot,
            "aqueous_composition": self.aqueous_composition,
            "chemical_potential": self.hydrate_chemical_pot,
            "cage_occupancy_small": self.cage_occupancy_small,
            "cage_occupancy_large": self.cage_occupancy_large,
            "hydration_number": self.hydration_number,
        }

        return _json_serializer(row)


def build_summary(equilib: PhaseEquilibriumState,
                  simulation_metadata: SimulationMetadata):

    guest_formatted = f"{equilib.configuration.primary_guest.name} ({equilib.configuration.primary_guest.code.upper()})"
    eos_formatted = f"{equilib.configuration.eos_config.name} ({equilib.configuration.eos_config.code.upper()})"
    acm_formatted = f"{equilib.configuration.acm_config.name} ({equilib.configuration.acm_config.code.upper()})"
    feed_comp_formatted = {equilib.configuration.primary_guest.code.upper(): 1.00}

    bulk_chem_pot = equilib.phase.bulk_phase.del_chemical_potential
    hyd_chem_pot = equilib.phase.hydrate_phase.del_chemical_potential
    chem_pot_diff = hyd_chem_pot-bulk_chem_pot

    
    record = SimulationSummary(
        # simulation configuration
        EoS_model = eos_formatted,
        ACM_model = acm_formatted,
        guest = guest_formatted,
        feed_composition= feed_comp_formatted,

        # equilibrium conditions
        T_Kelvin=equilib.condition.temperature,
        P_MPa=equilib.condition.pressure,

        # simulation information
        simulation_id = simulation_metadata.logger.file_name,
        date_time = str(simulation_metadata.logger.timestamp),
        run_hash = simulation_metadata.summary.short_config_hash,
        json_summary = simulation_metadata.summary.sanitized_path,
        log_path = simulation_metadata.logger.sanitized_log_path,

        # solver state
        converged=equilib.convergence_metadata.success,
        hydrate_formed=equilib.convergence_metadata.success,
        hydrate_structure=equilib.configuration.hyd_structure,
        solver_method=equilib.convergence_metadata.method_used,
        iterations=equilib.convergence_metadata.iterations,
        tolerance=equilib.convergence_metadata.x_tol,
        elapsed_ms=0.0,
        final_chemical_potential_diff=chem_pot_diff,
        # vapor phase
        fugacity_MPa=equilib.phase.vapor_phase.fugacity_vapor,
        z_vapor=equilib.phase.vapor_phase.compressibility_vapor,
        z_aqueous=equilib.phase.vapor_phase.compressibility_liquid,
        # bulk / aqueous phase
        bulk_chemical_pot=bulk_chem_pot,
        aqueous_composition=equilib.phase.bulk_phase.liquid_composition,
        activity_coefficient=equilib.phase.bulk_phase.activity_result,
        # hydrate phase
        hydrate_chemical_pot=hyd_chem_pot,
        cage_occupancy_small=equilib.phase.hydrate_phase.cage_data.small.FractionalOcc,
        cage_occupancy_large=equilib.phase.hydrate_phase.cage_data.large.FractionalOcc,
        langmuir_small_cage=equilib.phase.hydrate_phase.cage_data.small.LangmuirConst,
        langmuir_large_cage=equilib.phase.hydrate_phase.cage_data.large.LangmuirConst,
        hydration_number=equilib.phase.hydrate_phase.hydration_number,
        # warnings - if any
        warning=equilib.convergence_metadata.message,
    )

    return record


def write_summary_json(records: list[SimulationSummary], summary_path: Path) -> None:
    payload = {
        "count": len(records),
        "records": [r.to_dict() for r in records],
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def records_to_dataframe(records: list[SimulationSummary]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame([r.to_row() for r in records])


def process_simulation_results(
    equilib_results: PhaseEquilibriumState, simulation_metadata: SimulationMetadata
):
    summary_context = simulation_metadata.summary
    out_path = summary_context.full_summary_path
    rec_instance = build_summary(
        equilib=equilib_results,
        simulation_metadata=simulation_metadata,
    )  # formatted summary

    write_summary_json(records=[rec_instance], summary_path=out_path)

    if not equilib_results:
            return pd.DataFrame()

    processed_results = pd.DataFrame([r.to_row() for r in [rec_instance]])

    return rec_instance, processed_results   
     
