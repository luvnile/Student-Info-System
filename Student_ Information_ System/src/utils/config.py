"""Configuration loading and access."""

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Config:
    """Load application settings from a JSON configuration file."""

    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config_file = Path(config_file) if config_file else (
            PROJECT_ROOT / "config" / "config.json"
        )
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            with self.config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}"
            ) from error
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid configuration file {self.config_file}: {error}"
            ) from error
        except OSError as error:
            raise OSError(
                f"Unable to read configuration file {self.config_file}: {error}"
            ) from error

        if not isinstance(config, dict):
            raise ValueError("Configuration root must be a JSON object.")
        return config

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Return a setting, using default when its section or key is absent."""
        section_config = self.config.get(section, {})
        if not isinstance(section_config, dict):
            raise ValueError(f"Configuration section '{section}' must be an object.")
        return section_config.get(key, default)
