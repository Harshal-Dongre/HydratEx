import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent


from hydratex.config.system_conditions import SystemConditions
from hydratex.config.system_config import SystemConfig

logger = logging.getLogger(__name__)


@dataclass
class SimulationSummaryContext:
    full_config_hash: str
    short_config_hash: str
    canonical_string: str
    readable_string: str
    full_summary_path: Path
    sanitized_path: str


def summary_context_generator(
    sys_config: SystemConfig, sys_condition: SystemConditions
) -> SimulationSummaryContext:
    """Configuration hash generator for a simulation instance.

    Returns: (config_hash, short_hash, canonical_string, readable_string)
    """

    config_dict = {}

    config_dict["components"] = tuple(sorted(sys_config.all_guests_codes))
    config_dict["structure_id"] = sys_config.hyd_structure.value
    config_dict["eos_instance"] = sys_config.eos_config.code
    config_dict["activity_instance"] = sys_config.acm_config.code
    config_dict["temperature"] = sys_condition.temperature

    # Canonical string and JSON
    canonical_string = json.dumps(
        config_dict,
        sort_keys=True,
        separators=(",", ":"),
    )

    config_hash = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
    short_hash = config_hash[:20]

    readable_string = "_".join(
        [
            ",".join(sys_config.all_guests_codes),
            # sys_config.hyd_structure.value,
            sys_config.eos_config.code,
            sys_config.acm_config.code,
            f"{sys_condition.temperature:.4f}",
        ]
    )

    full_summary_path, sanitized_summary_pth = generate_summary_path(readable_string)


    logger.info(f"Simulation metadata created with the name '{short_hash}.json'")

    return SimulationSummaryContext(
        full_config_hash=config_hash,
        short_config_hash=short_hash,
        canonical_string=canonical_string,
        readable_string=readable_string,
        full_summary_path=full_summary_path,
        sanitized_path=sanitized_summary_pth
    )


def _generate_json_summary_path(config_hash: str) -> Path:

    short_hash = config_hash[:20]
    file_name = f"{short_hash}.json"

    summary_directory = project_root / "logs" / "simulation_summary"
    summary_directory.mkdir(parents=True, exist_ok=True)

    json_file = summary_directory / file_name

    # create empty JSON if not exist
    if not json_file.exists():
        json_file.write_text(json.dumps({}, indent=4))

    return json_file


def _sanitize_json_path(json_path: Path) -> str:

    if json_path is None:
        raise RuntimeError(f"File {json_path} does not exist")

    path_resolved = str(json_path.resolve())
    root_resolved = str(project_root.resolve())

    json_path.resolve().relative_to(project_root.resolve())
    return path_resolved.replace(root_resolved, "<HydratEx Root>")


def generate_summary_path(config_hash: str):
    full_path = _generate_json_summary_path(config_hash)
    sanitized_path = _sanitize_json_path(full_path)


    return full_path, sanitized_path

