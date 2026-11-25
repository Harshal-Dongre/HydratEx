import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# paths - sys_operate_cond configuration and property database
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
default_config_path = project_root / "config" / "config.yaml"


def load_default_config(path: Path = default_config_path) -> dict:
    logger.debug(f"Loading default config from Path:'{path}'")
    logger.info(f"Loading default config from Path: '{str(path).replace(str(project_root), '<HydratEx Root>', 1)}'", extra={'phase': "SETUP"})
    with open(path, "r") as f:
        return yaml.safe_load(f)


config = load_default_config()

#TODO -  run a simulation from the config file itself