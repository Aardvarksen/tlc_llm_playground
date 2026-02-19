"""
Batch Runner Page

Automated testing across models x prompts x contexts with CSV export.
Supports caching to avoid re-running identical combinations.
"""

import streamlit as st
import httpx
import json
import time
import os
from datetime import datetime
from typing import Optional, List, Dict

import utilities.model_config as model_config
import utilities.context_config as context_config
import utilities.system_prompt_config as prompt_config
import utilities.benchmark_results as benchmark

# ============================================================================
# Page Header
# ============================================================================

st.title("Batch Runner")
st.caption("Automated testing across models, prompts, and contexts")

# ============================================================================
# Load Configurations
# ============================================================================

queue_server_url = st.session_state.get("app.queue_server_url", "http://localhost:8001")

# Load model config
if "app.model_config" not in st.session_state:
    st.session_state["app.model_config"] = model_config.load_config()
model_cfg = st.session_state["app.model_config"]
enabled_models = model_config.get_enabled_models(model_cfg)

# Load context config
if "app.context_config" not in st.session_state:
    st.session_state["app.context_config"] = context_config.load_config()
context_cfg = st.session_state["app.context_config"]
all_contexts = context_config.get_all_contexts(context_cfg)

# Load prompt config
if "app.prompt_config" not in st.session_state:
    st.session_state["app.prompt_config"] = prompt_config.load_config()
prompt_cfg = st.session_state["app.prompt_config"]
all_prompts = prompt_config.get_all_prompts(prompt_cfg)

# Load benchmark results
if "batch.results_data" not in st.session_state:
    st.session_state["batch.results_data"] = benchmark.load_results()
results_data = st.session_state["batch.results_data"]

# ============================================================================
# Check Prerequisites
# ============================================================================

if not enabled_models:
    st.warning("No models enabled. Please configure models in Model Configuration page.")
    st.stop()

if not all_contexts:
    st.warning("No saved contexts found. Please add contexts in Saved Contexts page.")
    st.stop()

if not all_prompts:
    st.warning("No saved prompts found. Please add prompts in Saved Prompts page.")
    st.stop()

# ============================================================================
# Selection UI
# ============================================================================

st.subheader("Selection")

col_models, col_prompts = st.columns(2)

with col_models:
    st.markdown("**Models**")

    # Create checkboxes for models
    # Use index to ensure unique keys (same model_id can have multiple configs)
    selected_model_entries = []
    for idx, model in enumerate(enabled_models):
        display_name = model.get("display_name", model.get("model_id"))
        key = f"batch_runner.model_{idx}"

        if st.checkbox(display_name, key=key):
            selected_model_entries.append(model)

with col_prompts:
    st.markdown("**System Prompts**")

    # Create checkboxes for prompts
    selected_prompt_ids = []
    for idx, prompt in enumerate(all_prompts):
        name = prompt.get("name", "Unnamed")
        prompt_id = prompt.get("prompt_id")
        is_default = prompt.get("is_default", False)
        label = f"{name}" + (" (Default)" if is_default else "")
        key = f"batch_runner.prompt_{idx}"

        if st.checkbox(label, key=key):
            selected_prompt_ids.append(prompt_id)

st.markdown("**Contexts**")

# Create checkboxes for contexts in columns
context_cols = st.columns(3)
selected_context_ids = []
for idx, ctx in enumerate(all_contexts):
    name = ctx.get("name", "Unnamed")
    context_id = ctx.get("context_id")
    char_count = len(ctx.get("content", ""))
    label = f"{name} ({char_count:,} chars)"
    key = f"batch_runner.context_{idx}"

    with context_cols[idx % 3]:
        if st.checkbox(label, key=key):
            selected_context_ids.append(context_id)

# ============================================================================
# Preview Matrix
# ============================================================================

st.divider()
st.subheader("Preview")

# Count selections
num_models = len(selected_model_entries)
num_prompts = len(selected_prompt_ids)
num_contexts = len(selected_context_ids)
total_combinations = num_models * num_prompts * num_contexts

if total_combinations == 0:
    st.info("Select at least one model, prompt, and context to see the test matrix.")
else:
    st.markdown(
        f"**{num_models} models x {num_prompts} prompts x {num_contexts} contexts = "
        f"{total_combinations} combinations**"
    )

    # Build test items and check cache
    test_items = []
    cached_count = 0
    new_count = 0

    for prompt_id in selected_prompt_ids:
        prompt_entry = prompt_config.get_prompt(prompt_cfg, prompt_id)
        prompt_name = prompt_entry.get("name", "Unknown") if prompt_entry else "Unknown"

        for context_id in selected_context_ids:
            ctx_entry = context_config.get_context(context_cfg, context_id)
            ctx_name = ctx_entry.get("name", "Unknown") if ctx_entry else "Unknown"

            test_item_id = benchmark.generate_test_item_id(prompt_id, context_id)

            models_to_run = []
            models_cached = []

            for model_entry in selected_model_entries:
                model_id = model_entry.get("model_id")
                display_name = model_entry.get("display_name", model_id)
                params = {
                    "temperature": model_entry.get("temperature", 0.7),
                    "top_p": model_entry.get("top_p", 1.0),
                    "frequency_penalty": model_entry.get("frequency_penalty", 0.0),
                    "presence_penalty": model_entry.get("presence_penalty", 0.0),
                }

                # Check if cached
                cached_result = benchmark.get_cached_result(
                    results_data, test_item_id, model_id, params
                )

                if cached_result:
                    models_cached.append(display_name)
                    cached_count += 1
                else:
                    models_to_run.append({
                        "model_id": model_id,
                        "display_name": display_name,
                        "params": params
                    })
                    new_count += 1

            test_items.append({
                "test_item_id": test_item_id,
                "prompt_id": prompt_id,
                "prompt_name": prompt_name,
                "context_id": context_id,
                "context_name": ctx_name,
                "models_to_run": models_to_run,
                "models_cached": models_cached
            })

    # Show preview table
    if test_items:
        preview_data = []
        for item in test_items:
            run_models = ", ".join([m["display_name"] for m in item["models_to_run"]]) or "-"
            cached_models = ", ".join(item["models_cached"]) or "-"
            preview_data.append({
                "Test Item": f"{item['prompt_name']} + {item['context_name']}",
                "To Run": run_models,
                "Cached": cached_models
            })

        st.dataframe(preview_data, use_container_width=True, hide_index=True)

    # Show counts
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cached (skip)", cached_count)
    with col2:
        st.metric("New (to generate)", new_count)

# ============================================================================
# Run Button
# ============================================================================

st.divider()

run_disabled = total_combinations == 0
run_button = st.button(
    "Start Batch Run",
    type="primary",
    disabled=run_disabled,
    help="Run all new (non-cached) combinations"
)

# Progress placeholder
progress_placeholder = st.empty()
status_placeholder = st.empty()

# ============================================================================
# Batch Execution
# ============================================================================


def submit_to_queue(
    model_id: str,
    params: dict,
    system_prompt: str,
    content: str,
    client: httpx.Client
) -> Optional[dict]:
    """Submit a request to the queue server."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content}
    ]

    payload = {
        "client_id": "tlc_playground_batch_runner",
        "model": model_id,
        "messages": messages,
        "temperature": params.get("temperature", 0.7),
        "top_p": params.get("top_p", 1.0),
        "frequency_penalty": params.get("frequency_penalty", 0.0),
        "presence_penalty": params.get("presence_penalty", 0.0),
    }

    max_tokens = params.get("max_tokens")
    if max_tokens:
        payload["max_tokens"] = max_tokens

    try:
        response = client.post(
            f"{queue_server_url}/queue/add",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Submit error: {e}")
    return None


def stream_from_queue(request_id: str) -> tuple[Optional[str], float, float, int]:
    """
    Stream a response from the queue server.
    Returns (output_text, ttft, total_time, token_count) or (None, 0, 0, 0) on error.
    """
    full_content = ""
    start_time = time.time()
    first_token_time = None
    token_count = 0

    try:
        with httpx.Client(timeout=300) as client:
            with client.stream("GET", f"{queue_server_url}/stream/{request_id}") as response:
                if response.status_code != 200:
                    return None, 0, 0, 0

                for line in response.iter_lines():
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            chunk_data = json.loads(data_str)

                            if "chunk" in chunk_data:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                full_content += chunk_data["chunk"]
                                token_count += 1

                            elif "done" in chunk_data:
                                break

                            elif "error" in chunk_data:
                                return None, 0, 0, 0

                        except json.JSONDecodeError:
                            continue

    except Exception as e:
        print(f"Stream error: {e}")
        return None, 0, 0, 0

    end_time = time.time()
    total_time = end_time - start_time
    ttft = first_token_time - start_time if first_token_time else 0

    return full_content, ttft, total_time, token_count


if run_button and total_combinations > 0:
    # Collect all items to run
    items_to_run = []
    for item in test_items:
        for model_info in item["models_to_run"]:
            items_to_run.append({
                "test_item_id": item["test_item_id"],
                "prompt_id": item["prompt_id"],
                "prompt_name": item["prompt_name"],
                "context_id": item["context_id"],
                "context_name": item["context_name"],
                "model_id": model_info["model_id"],
                "display_name": model_info["display_name"],
                "params": model_info["params"]
            })

    if not items_to_run:
        st.info("All combinations are already cached. Nothing to run.")
    else:
        total_to_run = len(items_to_run)
        completed = 0

        progress_bar = progress_placeholder.progress(0, text=f"Running 0/{total_to_run}...")

        with httpx.Client() as client:
            for run_item in items_to_run:
                # Get prompt content
                prompt_entry = prompt_config.get_prompt(prompt_cfg, run_item["prompt_id"])
                system_prompt_content = prompt_entry.get("content", "") if prompt_entry else ""

                # Get context content
                ctx_entry = context_config.get_context(context_cfg, run_item["context_id"])
                context_content = ctx_entry.get("content", "") if ctx_entry else ""
                context_length = len(context_content)

                status_placeholder.info(
                    f"Running: {run_item['display_name']} + {run_item['prompt_name']} + {run_item['context_name']}"
                )

                # Submit to queue
                result = submit_to_queue(
                    model_id=run_item["model_id"],
                    params=run_item["params"],
                    system_prompt=system_prompt_content,
                    content=context_content,
                    client=client
                )

                if result:
                    request_id = result.get("request_id")

                    # Stream response
                    output, ttft, total_time, token_count = stream_from_queue(request_id)

                    if output is not None:
                        # Ensure test item exists
                        results_data, test_item_id = benchmark.get_or_create_test_item(
                            results_data,
                            run_item["prompt_id"],
                            run_item["context_id"]
                        )

                        # Store result
                        results_data = benchmark.store_result(
                            data=results_data,
                            test_item_id=test_item_id,
                            model_id=run_item["model_id"],
                            model_display_name=run_item["display_name"],
                            params=run_item["params"],
                            system_prompt_name=run_item["prompt_name"],
                            context_name=run_item["context_name"],
                            context_length=context_length,
                            output=output,
                            ttft=ttft,
                            total_time=total_time,
                            token_count=token_count
                        )

                        # Save after each result
                        benchmark.save_results(results_data)
                        st.session_state["batch.results_data"] = results_data

                completed += 1
                progress_bar.progress(
                    completed / total_to_run,
                    text=f"Running {completed}/{total_to_run}..."
                )

        progress_placeholder.empty()
        status_placeholder.success(f"Batch complete! {completed} results generated.")
        st.rerun()

# ============================================================================
# Results Table
# ============================================================================

st.divider()
st.subheader("Results")

all_results = benchmark.get_all_results(results_data)

if not all_results:
    st.info("No results yet. Run a batch to generate results.")
else:
    # Build display table
    table_data = []
    for r in all_results:
        table_data.append({
            "Model": r.get("model_display_name", ""),
            "Prompt": r.get("system_prompt_name", ""),
            "Context": r.get("context_name", ""),
            "TTFT (s)": f"{r.get('ttft', 0):.1f}",
            "Total (s)": f"{r.get('total_time', 0):.1f}",
            "Tokens": r.get("token_count", 0),
            "Output Length": r.get("output_length", 0),
            "Run At": r.get("run_at", "")[:16]  # Truncate timestamp
        })

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Expandable output viewer
    st.markdown("**View Full Outputs**")
    for i, r in enumerate(all_results[:20]):  # Limit to 20 most recent
        label = f"{r.get('model_display_name', '')} | {r.get('system_prompt_name', '')} | {r.get('context_name', '')}"
        with st.expander(label):
            st.text(r.get("output", ""))

# ============================================================================
# Export and Clear
# ============================================================================

st.divider()

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Export to CSV", disabled=len(all_results) == 0):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"benchmark_export_{timestamp}.csv"

        if benchmark.export_to_csv(results_data, filepath):
            st.success(f"Exported to {filepath}")

            # Offer download
            with open(filepath, 'r', encoding='utf-8') as f:
                csv_content = f.read()

            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=filepath,
                mime="text/csv"
            )
        else:
            st.error("Export failed")

with col2:
    if st.button("Clear All Results", type="secondary", disabled=len(all_results) == 0):
        results_data = benchmark.clear_all_results(results_data)
        benchmark.save_results(results_data)
        st.session_state["batch.results_data"] = results_data
        st.success("All results cleared")
        st.rerun()

# ============================================================================
# Summary Stats
# ============================================================================

st.divider()

total_results = len(all_results)
unique_models = len(set(r.get("model_id", "") for r in all_results))
unique_prompts = len(set(r.get("system_prompt_name", "") for r in all_results))

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Results", total_results)
with col2:
    st.metric("Unique Models", unique_models)
with col3:
    st.metric("Unique Prompts", unique_prompts)
