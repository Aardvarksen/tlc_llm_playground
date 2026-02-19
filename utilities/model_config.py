"""
Model configuration management for TLC LLM Playground.

Handles persistent storage of model configurations including:
- Display names (friendly names for UI)
- Model IDs (actual model reference for API calls)
- Generation parameters (temperature, top_p, max_tokens, etc.)
- Enabled/disabled status

Supports multiple configurations per model (e.g., same model with different temps).
"""

import json
import os
import uuid
from typing import Dict, List, Optional

CONFIG_FILE = "model_config.json"

# ============================================================================
# APPROVED MODELS - Developer-controlled list of models available to TLC users
# ============================================================================
# Only models in this list will be visible in the TLC LLM Playground.
# Add/remove models here to control what TLC users can access.

APPROVED_MODELS = {
    # Mistral / Ministral models
    "mistralai/mistral-7b-instruct-v0.3": {
        "display_name": "Mistral 7B Instruct v0.3",
        "default_temperature": 0.8,
    },
    "magistral-small-2509": {
        "display_name": "Magistral Small 2509",
        "default_temperature": 0.8,
    },
    "ministral-3-8b-instruct-2512": {
        "display_name": "Ministral 3 8B Instruct",
        "default_temperature": 0.15,
    },
    "ministral-3-8b-reasoning-2512": {
        "display_name": "Ministral 3 8B Reasoning",
        "default_temperature": 0.7,
    },
    "ministral-3-14b-instruct-2512": {
        "display_name": "Ministral 3 14B Instruct",
        "default_temperature": 0.15,
    },
    "ministral-3-14b-reasoning-2512": {
        "display_name": "Ministral 3 14B Reasoning",
        "default_temperature": 0.7,
    },
    # Meta Llama models
    "llama-3.1-8b-instruct": {
        "display_name": "Llama 3.1 8B Instruct",
        "default_temperature": 0.6,
    },
    # Qwen models
    "qwen3-4b": {
        "display_name": "Qwen 3 4B",
        "default_temperature": 0.7,
    },
    "qwen3-8b": {
        "display_name": "Qwen 3 8B",
        "default_temperature": 0.7,
    },
    "qwen3-14b": {
        "display_name": "Qwen 3 14B",
        "default_temperature": 0.7,
    },
    "qwen/qwen3-32b": {
        "display_name": "Qwen 3 32B",
        "default_temperature": 0.7,
    },
    # IBM Granite models
    "granite-4.0-h-tiny": {
        "display_name": "Granite 4.0 Tiny",
        "default_temperature": 0.0,
    },
    "granite-4.0-h-small": {
        "display_name": "Granite 4.0 Small",
        "default_temperature": 0.0,
    },
}

# Default parameters for new configurations
DEFAULT_PARAMS = {
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": None,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
}


def load_config() -> Dict:
    """
    Load model configuration from JSON file.

    Returns:
        Dictionary with model configurations. Format:
        {
            "models": {
                "model-id": {
                    "display_name": "Friendly Name",
                    "model_id": "model-id",
                    "enabled": True/False,
                    "temperature": 0.7,
                    "top_p": 1.0,
                    "max_tokens": None,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                }
            }
        }

    If file doesn't exist, returns empty config.
    """
    if not os.path.exists(CONFIG_FILE):
        return {"models": {}}

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading model config: {e}")
        return {"models": {}}


def save_config(config: Dict) -> bool:
    """
    Save model configuration to JSON file.

    Args:
        config: Dictionary with model configurations

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving model config: {e}")
        return False


def get_enabled_models(config: Dict) -> List[Dict]:
    """
    Get list of enabled model configurations.

    Args:
        config: Model configuration dictionary

    Returns:
        List of model config dicts that are enabled
    """
    enabled = []
    models = config.get("models", {})

    for model_id, model_info in models.items():
        if model_info.get("enabled", True):
            enabled.append(model_info)

    return enabled


def get_model_choices(config: Dict) -> List[tuple]:
    """
    Get list of (display_name, model_id) tuples for enabled models.
    Useful for populating dropdowns.

    Args:
        config: Model configuration dictionary

    Returns:
        List of (display_name, model_id) tuples
    """
    choices = []
    for model_info in get_enabled_models(config):
        display_name = model_info.get("display_name", model_info.get("model_id", "Unknown"))
        model_id = model_info.get("model_id", "")
        choices.append((display_name, model_id))
    return choices


def get_model_config(config: Dict, model_id: str) -> Optional[Dict]:
    """
    Get the full configuration for a specific model.

    Args:
        config: Model configuration dictionary
        model_id: The model ID to look up

    Returns:
        Model config dict or None if not found
    """
    return config.get("models", {}).get(model_id)


def update_model_config(
    config: Dict,
    model_id: str,
    display_name: str = None,
    enabled: bool = None,
    temperature: float = None,
    top_p: float = None,
    max_tokens: int = None,
    frequency_penalty: float = None,
    presence_penalty: float = None,
) -> Dict:
    """
    Update the configuration for a model.

    Args:
        config: Current config dictionary
        model_id: The model ID to update
        display_name: Friendly name for the model
        enabled: Whether the model should appear in selection
        temperature: Generation temperature
        top_p: Top-p sampling parameter
        max_tokens: Maximum tokens to generate
        frequency_penalty: Frequency penalty parameter
        presence_penalty: Presence penalty parameter

    Returns:
        Updated config dictionary
    """
    if "models" not in config:
        config["models"] = {}

    # Get existing or create new entry
    if model_id not in config["models"]:
        config["models"][model_id] = {
            "model_id": model_id,
            "display_name": display_name or model_id,
            "enabled": True,
            **DEFAULT_PARAMS
        }

    model = config["models"][model_id]

    # Update only provided values
    if display_name is not None:
        model["display_name"] = display_name
    if enabled is not None:
        model["enabled"] = enabled
    if temperature is not None:
        model["temperature"] = temperature
    if top_p is not None:
        model["top_p"] = top_p
    if max_tokens is not None:
        model["max_tokens"] = max_tokens
    if frequency_penalty is not None:
        model["frequency_penalty"] = frequency_penalty
    if presence_penalty is not None:
        model["presence_penalty"] = presence_penalty

    return config


def ensure_models_in_config(config: Dict, model_ids: List[str]) -> Dict:
    """
    Ensure all models from a list are in the config.
    New models get default parameters and enabled=True.

    Args:
        config: Current config dictionary
        model_ids: List of model IDs to ensure exist

    Returns:
        Updated config dictionary
    """
    if "models" not in config:
        config["models"] = {}

    for model_id in model_ids:
        if model_id not in config["models"]:
            config["models"][model_id] = {
                "model_id": model_id,
                "display_name": model_id,  # Default to ID as display name
                "enabled": True,
                **DEFAULT_PARAMS
            }

    return config


def remove_model_from_config(config: Dict, config_key: str) -> Dict:
    """
    Remove a model configuration.

    Args:
        config: Current config dictionary
        config_key: The config key to remove

    Returns:
        Updated config dictionary
    """
    if "models" in config and config_key in config["models"]:
        del config["models"][config_key]
    return config


def generate_config_key(model_id: str, suffix: str = "") -> str:
    """
    Generate a unique config key for a model configuration.

    Args:
        model_id: The model ID
        suffix: Optional suffix (e.g., "temp-0", "creative")

    Returns:
        A unique config key string
    """
    # Simplify model_id for key (remove slashes, lowercase)
    base = model_id.replace("/", "-").lower()
    if suffix:
        return f"{base}-{suffix}"
    return base


def copy_model_config(config: Dict, source_key: str, new_display_name: str) -> tuple[Dict, str]:
    """
    Copy an existing model configuration with a new display name.

    Args:
        config: Current config dictionary
        source_key: The config key to copy from
        new_display_name: Display name for the new configuration

    Returns:
        Tuple of (updated config, new config key) or (config, None) if source not found
    """
    if "models" not in config or source_key not in config["models"]:
        return config, None

    source = config["models"][source_key]

    # Generate a unique key for the copy
    base_key = generate_config_key(source["model_id"])
    new_key = f"{base_key}-{uuid.uuid4().hex[:6]}"

    # Create the copy
    config["models"][new_key] = {
        **source,
        "display_name": new_display_name,
    }

    return config, new_key


def get_approved_models() -> Dict:
    """
    Get the list of developer-approved models.

    Returns:
        Dictionary of approved models with their default settings
    """
    return APPROVED_MODELS.copy()


def initialize_default_configs(config: Dict) -> Dict:
    """
    Ensure all approved models have a default configuration.
    Creates "(default)" configs for any missing approved models.

    Args:
        config: Current config dictionary

    Returns:
        Updated config dictionary
    """
    if "models" not in config:
        config["models"] = {}

    for model_id, model_info in APPROVED_MODELS.items():
        default_key = generate_config_key(model_id, "default")

        if default_key not in config["models"]:
            config["models"][default_key] = {
                "model_id": model_id,
                "display_name": f"{model_info['display_name']} (default)",
                "enabled": True,
                "temperature": model_info.get("default_temperature", 0.7),
                "top_p": 1.0,
                "max_tokens": None,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }

    return config
