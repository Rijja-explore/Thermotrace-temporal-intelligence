"""
config_loader.py – Load and validate YAML configuration files.

Provides a single entry point to load thresholds.yaml and weights.yaml.
Configuration values are accessed via dot-notation-style helpers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default config directory: <package_root>/../../config
_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data)}")
    return data


class Config:
    """
    Unified configuration object that merges thresholds and weights.

    Usage:
        cfg = Config()                    # uses default config/
        cfg = Config("/path/to/config")  # uses custom config dir
        thresh = cfg.thresholds
        weights = cfg.weights
    """

    def __init__(self, config_dir: str | Path | None = None) -> None:
        base = Path(config_dir) if config_dir else _DEFAULT_CONFIG_DIR
        self._thresholds = _load_yaml(base / "thresholds.yaml")
        self._weights = _load_yaml(base / "weights.yaml")
        logger.debug(
            "Loaded config v=%s (thresholds) v=%s (weights)",
            self._thresholds.get("version", "?"),
            self._weights.get("version", "?"),
        )

    @property
    def thresholds(self) -> dict[str, Any]:
        return self._thresholds

    @property
    def weights(self) -> dict[str, Any]:
        return self._weights

    def get_threshold(self, *keys: str, default: Any = None) -> Any:
        """Navigate nested threshold keys. e.g. get_threshold('anomaly', 'frp_zscore_threshold')"""
        node: Any = self._thresholds
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k, default)
        return node

    def get_weight(self, *keys: str, default: Any = None) -> Any:
        """Navigate nested weight keys."""
        node: Any = self._weights
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k, default)
        return node

    @property
    def config_version(self) -> str:
        return str(self._thresholds.get("version", "v1"))


# Singleton-style helper so modules can import a ready-to-use config.
_default_config: Config | None = None


def get_config(config_dir: str | Path | None = None) -> Config:
    """Return a Config instance. Creates a singleton for the default path."""
    global _default_config
    if config_dir is not None:
        return Config(config_dir)
    if _default_config is None:
        _default_config = Config()
    return _default_config
