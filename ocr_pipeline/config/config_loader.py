"""
Configuration loader for the OCR Pipeline.
Loads YAML configuration with fallback defaults and environment overrides.
"""

import os
import yaml
from typing import Any, Dict

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

_cached_config: Dict[str, Any] = None


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from yaml file with caching."""
    global _cached_config
    if _cached_config is not None and config_path is None:
        return _cached_config

    path = config_path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config_path is None:
        _cached_config = config

    return config


def get_model_config(model_name: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieve configuration dictionary for a specific model."""
    cfg = config or load_config()
    return cfg.get("models", {}).get(model_name, {})


def get_routing_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieve configuration dictionary for routing."""
    cfg = config or load_config()
    return cfg.get("routing", {})


def get_fusion_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieve configuration dictionary for result fusion."""
    cfg = config or load_config()
    return cfg.get("fusion", {})


def get_layout_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieve configuration dictionary for layout analysis."""
    cfg = config or load_config()
    return cfg.get("layout", {})


def get_preprocessing_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Retrieve configuration dictionary for preprocessing."""
    cfg = config or load_config()
    return cfg.get("preprocessing", {})
