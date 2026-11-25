import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LoggerInstanceContext:


    sanitized_log_path: str
    timestamp: datetime
    file_name: str | None
    log_path: Path | None


class _EnsurePhase(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "phase"):
            record.phase = "GENERAL"
        return True


class LoggerManager:


    _initialized: bool = False
    _log_path: Path | None = None
    _project_root: Path | None = None
    _run_datetime: datetime
    _run_file_ID: str | None = None

    @classmethod
    def initialize(
            cls,
            temp_bounds: float | tuple[float, ...] | None,
            guest_label: str | tuple[str, ...],
            job_type: str = "run",
            verbose: bool = False,
            save_files: bool = False,
    ):


        if cls._initialized:
            return

        cls._project_root = Path(__file__).resolve().parent.parent
        root_logger = logging.getLogger()

        # Root and file capture INFO when saving; console only prints INFO when verbose=True
        root_logger.setLevel(logging.INFO)
        console_level = logging.INFO if verbose else logging.WARNING

        # Always build run timestamp and file ID so JSON and log share the exact same ID
        cls._run_datetime = datetime.now()
        timestamp_str = cls._run_datetime.strftime("%d%m_%H%M%S")
        if isinstance(temp_bounds, float):
            temp_str = f"{temp_bounds:.2f}K"
        elif isinstance(temp_bounds, tuple):
            temp_str = "_".join(f"{temp:.2f}K" for temp in temp_bounds)
        else:
            raise TypeError("temp_bounds must be a float or a tuple of floats")

        cls._run_file_ID = (
            f"{guest_label}_{job_type}_{temp_str}_{timestamp_str}"
        )

        # File handler (created only if save_files is True)
        if save_files:
            log_dir = cls._project_root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            cls._log_path = log_dir / f"{cls._run_file_ID}.log"

            print(f"Logging to {cls._log_path}")

            file_handler = logging.FileHandler(cls._log_path, mode="a")
            file_formatter = logging.Formatter(
                "%(asctime)s - [%(levelname)s] - [%(phase)s] - %(name)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.INFO)
            file_handler.addFilter(_EnsurePhase())
            root_logger.addHandler(file_handler)

        # Console handler setup (always active, respects verbosity)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "[%(levelname)s] - [%(phase)s] - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(console_level)
        console_handler.addFilter(_EnsurePhase())
        root_logger.addHandler(console_handler)

        cls._initialized = True

    @classmethod
    def get_run_metadata(cls) -> LoggerInstanceContext | None:


        if cls._run_file_ID is None:
            return None

        sanitized_path = (
            str(cls._log_path).replace(str(cls._project_root), "<HydratEx Root>", 1)
            if cls._log_path is not None
            else "'save-files' option disabled"
        )
        return LoggerInstanceContext(
            log_path=cls._log_path,
            sanitized_log_path=sanitized_path,
            timestamp=cls._run_datetime,
            file_name=cls._run_file_ID,
        )

    @classmethod
    def get_phase_logger(cls, phase: str = "GENERAL") -> logging.LoggerAdapter:


        base = logging.getLogger()
        return logging.LoggerAdapter(base, {"phase": phase})
