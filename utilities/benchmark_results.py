"""
Benchmark results storage and CSV export for TLC LLM Playground.

Handles persistent storage of batch run results with:
- Test items: unique combinations of system prompt + context
- Results: model outputs for each test item with parameters and metrics

Designed to support future SQLite migration via clean data structures.
"""

import csv
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

CONFIG_FILE = "benchmark_results.json"


def generate_test_item_id(prompt_id: str, context_id: str) -> str:
    """
    Generate a stable hash for a prompt+context combination.

    Args:
        prompt_id: The system prompt identifier
        context_id: The context identifier

    Returns:
        8-character hex hash
    """
    combined = f"{prompt_id}|{context_id}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]


def generate_params_hash(params: dict) -> str:
    """
    Generate a hash of generation parameters for cache keying.

    Args:
        params: Dictionary of model parameters (temperature, top_p, etc.)

    Returns:
        6-character hex hash
    """
    # Sort keys for consistency
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()[:6]


def generate_result_key(test_item_id: str, model_id: str, params: dict) -> str:
    """
    Generate a unique key for a specific result.

    Args:
        test_item_id: The test item identifier
        model_id: The model identifier
        params: Generation parameters

    Returns:
        Composite key string
    """
    params_hash = generate_params_hash(params)
    return f"{test_item_id}|{model_id}|{params_hash}"


def load_results() -> Dict:
    """
    Load benchmark results from JSON file.

    Returns:
        Dictionary with structure:
        {
            "test_items": {
                "abc123": {
                    "test_item_id": "abc123",
                    "system_prompt_id": "...",
                    "context_id": "...",
                    "created_at": "..."
                }
            },
            "results": {
                "abc123|model-id|params-hash": {
                    "result_key": "...",
                    "test_item_id": "...",
                    "model_id": "...",
                    "model_display_name": "...",
                    "params": {...},
                    "params_hash": "...",
                    "system_prompt_name": "...",
                    "context_name": "...",
                    "output": "...",
                    "ttft": 1.23,
                    "total_time": 5.67,
                    "token_count": 234,
                    "run_at": "..."
                }
            }
        }
    """
    if not os.path.exists(CONFIG_FILE):
        return {"test_items": {}, "results": {}}

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading benchmark results: {e}")
        return {"test_items": {}, "results": {}}


def save_results(results: Dict) -> bool:
    """
    Save benchmark results to JSON file.

    Args:
        results: Dictionary with test_items and results

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving benchmark results: {e}")
        return False


def get_or_create_test_item(
    data: Dict,
    prompt_id: str,
    context_id: str
) -> tuple[Dict, str]:
    """
    Get an existing test item or create a new one.

    Args:
        data: The full results dictionary
        prompt_id: System prompt identifier
        context_id: Context identifier

    Returns:
        Tuple of (updated data, test_item_id)
    """
    test_item_id = generate_test_item_id(prompt_id, context_id)

    if "test_items" not in data:
        data["test_items"] = {}

    if test_item_id not in data["test_items"]:
        data["test_items"][test_item_id] = {
            "test_item_id": test_item_id,
            "system_prompt_id": prompt_id,
            "context_id": context_id,
            "created_at": datetime.now().isoformat()
        }

    return data, test_item_id


def get_cached_result(
    data: Dict,
    test_item_id: str,
    model_id: str,
    params: dict
) -> Optional[Dict]:
    """
    Check if a result already exists for this combination.

    Args:
        data: The full results dictionary
        test_item_id: The test item identifier
        model_id: The model identifier
        params: Generation parameters

    Returns:
        The cached result dict, or None if not found
    """
    result_key = generate_result_key(test_item_id, model_id, params)
    return data.get("results", {}).get(result_key)


def store_result(
    data: Dict,
    test_item_id: str,
    model_id: str,
    model_display_name: str,
    params: dict,
    system_prompt_name: str,
    context_name: str,
    context_length: int,
    output: str,
    ttft: float,
    total_time: float,
    token_count: int
) -> Dict:
    """
    Store a new result.

    Args:
        data: The full results dictionary
        test_item_id: The test item identifier
        model_id: The model API identifier
        model_display_name: Friendly model name
        params: Generation parameters dict
        system_prompt_name: Friendly prompt name
        context_name: Friendly context name
        context_length: Character count of context
        output: The generated text
        ttft: Time to first token in seconds
        total_time: Total generation time in seconds
        token_count: Approximate token/chunk count

    Returns:
        Updated data dictionary
    """
    if "results" not in data:
        data["results"] = {}

    params_hash = generate_params_hash(params)
    result_key = generate_result_key(test_item_id, model_id, params)

    data["results"][result_key] = {
        "result_key": result_key,
        "test_item_id": test_item_id,
        "model_id": model_id,
        "model_display_name": model_display_name,
        "params": params,
        "params_hash": params_hash,
        "system_prompt_name": system_prompt_name,
        "context_name": context_name,
        "context_length": context_length,
        "output": output,
        "output_length": len(output),
        "ttft": ttft,
        "total_time": total_time,
        "token_count": token_count,
        "run_at": datetime.now().isoformat()
    }

    return data


def get_all_results(data: Dict) -> List[Dict]:
    """
    Get all stored results as a list, sorted by run time (newest first).

    Args:
        data: The full results dictionary

    Returns:
        List of result dicts
    """
    results = list(data.get("results", {}).values())
    return sorted(results, key=lambda x: x.get("run_at", ""), reverse=True)


def clear_all_results(data: Dict) -> Dict:
    """
    Clear all results (but keep test items for reference).

    Args:
        data: The full results dictionary

    Returns:
        Updated data with empty results
    """
    data["results"] = {}
    return data


def export_to_csv(data: Dict, filepath: str) -> bool:
    """
    Export all results to a CSV file.

    Args:
        data: The full results dictionary
        filepath: Path to write the CSV file

    Returns:
        True if export succeeded, False otherwise

    CSV columns:
    - run_at
    - model_id
    - model_display_name
    - temperature
    - top_p
    - other_params (JSON of remaining params)
    - system_prompt_id (from test_item)
    - system_prompt_name
    - context_id (from test_item)
    - context_name
    - context_length
    - output
    - output_length
    - ttft_seconds
    - total_seconds
    - token_count
    """
    results = get_all_results(data)

    if not results:
        return False

    # Build lookup for test items
    test_items = data.get("test_items", {})

    fieldnames = [
        "run_at",
        "model_id",
        "model_display_name",
        "temperature",
        "top_p",
        "other_params",
        "system_prompt_id",
        "system_prompt_name",
        "context_id",
        "context_name",
        "context_length",
        "output",
        "output_length",
        "ttft_seconds",
        "total_seconds",
        "token_count"
    ]

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                # Get test item info
                test_item_id = result.get("test_item_id", "")
                test_item = test_items.get(test_item_id, {})

                # Extract params
                params = result.get("params", {})
                temperature = params.pop("temperature", "")
                top_p = params.pop("top_p", "")
                other_params = json.dumps(params) if params else ""

                row = {
                    "run_at": result.get("run_at", ""),
                    "model_id": result.get("model_id", ""),
                    "model_display_name": result.get("model_display_name", ""),
                    "temperature": temperature,
                    "top_p": top_p,
                    "other_params": other_params,
                    "system_prompt_id": test_item.get("system_prompt_id", ""),
                    "system_prompt_name": result.get("system_prompt_name", ""),
                    "context_id": test_item.get("context_id", ""),
                    "context_name": result.get("context_name", ""),
                    "context_length": result.get("context_length", ""),
                    "output": result.get("output", ""),
                    "output_length": result.get("output_length", ""),
                    "ttft_seconds": result.get("ttft", ""),
                    "total_seconds": result.get("total_time", ""),
                    "token_count": result.get("token_count", "")
                }

                writer.writerow(row)

        return True
    except IOError as e:
        print(f"Error exporting to CSV: {e}")
        return False
