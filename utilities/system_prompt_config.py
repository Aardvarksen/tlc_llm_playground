"""
System prompt configuration management for TLC LLM Playground.

Handles persistent storage of reusable system prompts.
Each prompt has:
- prompt_id: Unique identifier
- name: Display name for UI
- content: The actual system prompt text
- description: Brief description of what the prompt does
- is_default: Whether this is a built-in Moodle default
- created_at: Timestamp when saved
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

CONFIG_FILE = "system_prompt_config.json"

# Default Moodle prompts (from Moodle 5.1.1 source: moodle/public/lang/en/ai.php)
MOODLE_DEFAULT_PROMPTS = {
    "summarise-default": {
        "prompt_id": "summarise-default",
        "name": "Summarise Text (Moodle)",
        "content": """You will receive a text input from the user. Your task is to summarize the provided text. Follow these guidelines:
    1. Condense: Shorten long passages into key points.
    2. Simplify: Make complex information easier to understand, especially for learners.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the summary is easy to read and effectively conveys the main points of the original text.""",
        "description": "Creates a brief summary of the content in a page.",
        "is_default": True,
        "created_at": "2025-01-01T00:00:00"
    },
    "explain-default": {
        "prompt_id": "explain-default",
        "name": "Explain Text (Moodle)",
        "content": """You will receive a text input from the user. Your task is to explain the provided text. Follow these guidelines:
    1. Elaborate: Expand on key ideas and concepts, ensuring the explanation adds meaningful depth and avoids restating the text verbatim.
    2. Simplify: Break down complex terms or ideas into simpler components, making them easy to understand for a wide audience, including learners.
    3. Provide Context: Explain why something happens, how it works, or what its purpose is. Include relevant examples or analogies to enhance understanding where appropriate.
    4. Organise Logically: Structure your explanation to flow naturally, beginning with fundamental ideas before moving to finer details.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the explanation is easy to read and effectively conveys the main points of the original text.""",
        "description": "Provides an explanation that expands on key ideas, simplifies complex concepts, and adds context.",
        "is_default": True,
        "created_at": "2025-01-01T00:00:00"
    },
    "generate-default": {
        "prompt_id": "generate-default",
        "name": "Generate Text (Moodle)",
        "content": """You will receive a text input from the user. Your task is to generate text based on their request. Follow these important instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.""",
        "description": "Creates text based on a prompt.",
        "is_default": True,
        "created_at": "2025-01-01T00:00:00"
    }
}


def load_config() -> Dict:
    """
    Load system prompt configuration from JSON file.

    Returns:
        Dictionary with prompt configurations. Format:
        {
            "prompts": {
                "prompt-id": {
                    "prompt_id": "string",
                    "name": "Display Name",
                    "content": "The system prompt text...",
                    "description": "Brief description",
                    "is_default": bool,
                    "created_at": "2025-01-21T12:00:00"
                }
            }
        }

    If file doesn't exist, initializes with Moodle defaults.
    """
    if not os.path.exists(CONFIG_FILE):
        # Create with default prompts
        config = initialize_default_prompts({"prompts": {}})
        save_config(config)
        return config

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Ensure defaults exist
            if not config.get("prompts"):
                config = initialize_default_prompts(config)
                save_config(config)
            return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading system prompt config: {e}")
        return initialize_default_prompts({"prompts": {}})


def save_config(config: Dict) -> bool:
    """
    Save system prompt configuration to JSON file.

    Args:
        config: Dictionary with prompt configurations

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving system prompt config: {e}")
        return False


def initialize_default_prompts(config: Dict) -> Dict:
    """
    Initialize config with Moodle default prompts.

    Args:
        config: Config dictionary to add defaults to

    Returns:
        Config with default prompts added
    """
    if "prompts" not in config:
        config["prompts"] = {}

    for prompt_id, prompt_data in MOODLE_DEFAULT_PROMPTS.items():
        if prompt_id not in config["prompts"]:
            config["prompts"][prompt_id] = prompt_data.copy()

    return config


def get_all_prompts(config: Dict) -> List[Dict]:
    """
    Get list of all saved prompts.

    Args:
        config: Prompt configuration dictionary

    Returns:
        List of prompt dicts, sorted by name (defaults first)
    """
    prompts = list(config.get("prompts", {}).values())
    # Sort: defaults first, then by name
    return sorted(
        prompts,
        key=lambda x: (not x.get("is_default", False), x.get("name", "").lower())
    )


def get_prompt(config: Dict, prompt_id: str) -> Optional[Dict]:
    """
    Get a specific prompt by ID.

    Args:
        config: Prompt configuration dictionary
        prompt_id: The prompt ID to look up

    Returns:
        Prompt dict or None if not found
    """
    return config.get("prompts", {}).get(prompt_id)


def add_prompt(
    config: Dict,
    name: str,
    content: str,
    description: str = ""
) -> tuple[Dict, str]:
    """
    Add a new prompt to the configuration.

    Args:
        config: Current config dictionary
        name: Display name for the prompt
        content: The system prompt text
        description: Brief description of what it does

    Returns:
        Tuple of (updated config, new prompt_id)
    """
    if "prompts" not in config:
        config["prompts"] = {}

    prompt_id = str(uuid.uuid4())[:8]  # Short UUID for readability

    config["prompts"][prompt_id] = {
        "prompt_id": prompt_id,
        "name": name,
        "content": content,
        "description": description,
        "is_default": False,
        "created_at": datetime.now().isoformat()
    }

    return config, prompt_id


def update_prompt(
    config: Dict,
    prompt_id: str,
    name: str = None,
    content: str = None,
    description: str = None
) -> Dict:
    """
    Update an existing prompt.

    Args:
        config: Current config dictionary
        prompt_id: The prompt ID to update
        name: New display name (or None to keep existing)
        content: New content (or None to keep existing)
        description: New description (or None to keep existing)

    Returns:
        Updated config dictionary
    """
    if "prompts" not in config or prompt_id not in config["prompts"]:
        return config

    prompt = config["prompts"][prompt_id]

    if name is not None:
        prompt["name"] = name
    if content is not None:
        prompt["content"] = content
    if description is not None:
        prompt["description"] = description

    return config


def delete_prompt(config: Dict, prompt_id: str) -> Dict:
    """
    Delete a prompt from the configuration.

    Note: Default prompts can be deleted but will be re-added on next load.

    Args:
        config: Current config dictionary
        prompt_id: The prompt ID to delete

    Returns:
        Updated config dictionary
    """
    if "prompts" in config and prompt_id in config["prompts"]:
        del config["prompts"][prompt_id]
    return config


def get_prompt_choices(config: Dict) -> List[tuple]:
    """
    Get list of (name, prompt_id) tuples for populating dropdowns.

    Args:
        config: Prompt configuration dictionary

    Returns:
        List of (name, prompt_id) tuples
    """
    choices = []
    for prompt in get_all_prompts(config):
        choices.append((prompt.get("name", "Unnamed"), prompt.get("prompt_id")))
    return choices
