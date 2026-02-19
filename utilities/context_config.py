"""
Context configuration management for TLC LLM Playground.

Handles persistent storage of saved content snippets for reuse in testing.
Each context has:
- context_id: Unique identifier
- name: Display name for UI
- content: The actual text content
- url: Optional source URL (where it came from)
- created_at: Timestamp when saved
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

CONFIG_FILE = "context_config.json"


def load_config() -> Dict:
    """
    Load context configuration from JSON file.

    Returns:
        Dictionary with context configurations. Format:
        {
            "contexts": {
                "context-id": {
                    "context_id": "uuid-string",
                    "name": "Display Name",
                    "content": "The actual content...",
                    "url": "https://... or empty string",
                    "created_at": "2025-01-21T12:00:00"
                }
            }
        }

    If file doesn't exist, returns empty config.
    """
    if not os.path.exists(CONFIG_FILE):
        return {"contexts": {}}

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading context config: {e}")
        return {"contexts": {}}


def save_config(config: Dict) -> bool:
    """
    Save context configuration to JSON file.

    Args:
        config: Dictionary with context configurations

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving context config: {e}")
        return False


def get_all_contexts(config: Dict) -> List[Dict]:
    """
    Get list of all saved contexts.

    Args:
        config: Context configuration dictionary

    Returns:
        List of context dicts, sorted by name
    """
    contexts = list(config.get("contexts", {}).values())
    return sorted(contexts, key=lambda x: x.get("name", "").lower())


def get_context(config: Dict, context_id: str) -> Optional[Dict]:
    """
    Get a specific context by ID.

    Args:
        config: Context configuration dictionary
        context_id: The context ID to look up

    Returns:
        Context dict or None if not found
    """
    return config.get("contexts", {}).get(context_id)


def add_context(
    config: Dict,
    name: str,
    content: str,
    url: str = ""
) -> tuple[Dict, str]:
    """
    Add a new context to the configuration.

    Args:
        config: Current config dictionary
        name: Display name for the context
        content: The actual text content
        url: Optional source URL

    Returns:
        Tuple of (updated config, new context_id)
    """
    if "contexts" not in config:
        config["contexts"] = {}

    context_id = str(uuid.uuid4())[:8]  # Short UUID for readability

    config["contexts"][context_id] = {
        "context_id": context_id,
        "name": name,
        "content": content,
        "url": url,
        "created_at": datetime.now().isoformat()
    }

    return config, context_id


def update_context(
    config: Dict,
    context_id: str,
    name: str = None,
    content: str = None,
    url: str = None
) -> Dict:
    """
    Update an existing context.

    Args:
        config: Current config dictionary
        context_id: The context ID to update
        name: New display name (or None to keep existing)
        content: New content (or None to keep existing)
        url: New URL (or None to keep existing)

    Returns:
        Updated config dictionary
    """
    if "contexts" not in config or context_id not in config["contexts"]:
        return config

    context = config["contexts"][context_id]

    if name is not None:
        context["name"] = name
    if content is not None:
        context["content"] = content
    if url is not None:
        context["url"] = url

    return config


def delete_context(config: Dict, context_id: str) -> Dict:
    """
    Delete a context from the configuration.

    Args:
        config: Current config dictionary
        context_id: The context ID to delete

    Returns:
        Updated config dictionary
    """
    if "contexts" in config and context_id in config["contexts"]:
        del config["contexts"][context_id]
    return config


def get_context_choices(config: Dict) -> List[tuple]:
    """
    Get list of (name, context_id) tuples for populating dropdowns.

    Args:
        config: Context configuration dictionary

    Returns:
        List of (name, context_id) tuples
    """
    choices = []
    for context in get_all_contexts(config):
        choices.append((context.get("name", "Unnamed"), context.get("context_id")))
    return choices
