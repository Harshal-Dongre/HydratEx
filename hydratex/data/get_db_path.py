import os
from pathlib import Path


def get_db_path(custom_path: str | Path | None = None) -> Path:
    if custom_path is not None:
        return Path(custom_path)

    if "HYDRATEX_DB_PATH" in os.environ:
        return Path(os.environ["HYDRATEX_DB_PATH"])

    # 3. Fallback to the default production database
    base_dir = Path(__file__).resolve().parent
    return base_dir / "property_data.db"