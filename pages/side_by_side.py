"""
Side-by-Side Model Comparison Page

Compare multiple models' responses to the same prompt and content.
Simulates Moodle's LLM functions (Explain, Summarize, Generate) for validation.
"""

import streamlit as st
import httpx
import json
import time
from typing import Optional

import utilities.model_config as model_config

# ============================================================================
# Moodle Function System Prompts (from Moodle 5.1.1 source)
# Source: moodle/public/lang/en/ai.php
# ============================================================================

MOODLE_FUNCTIONS = {
    "Summarise Text": {
        "description": "Creates a brief summary of the content in a page.",
        "system_prompt": """You will receive a text input from the user. Your task is to summarize the provided text. Follow these guidelines:
    1. Condense: Shorten long passages into key points.
    2. Simplify: Make complex information easier to understand, especially for learners.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the summary is easy to read and effectively conveys the main points of the original text."""
    },
    "Explain Text": {
        "description": "Provides an explanation that expands on key ideas, simplifies complex concepts, and adds context.",
        "system_prompt": """You will receive a text input from the user. Your task is to explain the provided text. Follow these guidelines:
    1. Elaborate: Expand on key ideas and concepts, ensuring the explanation adds meaningful depth and avoids restating the text verbatim.
    2. Simplify: Break down complex terms or ideas into simpler components, making them easy to understand for a wide audience, including learners.
    3. Provide Context: Explain why something happens, how it works, or what its purpose is. Include relevant examples or analogies to enhance understanding where appropriate.
    4. Organise Logically: Structure your explanation to flow naturally, beginning with fundamental ideas before moving to finer details.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the explanation is easy to read and effectively conveys the main points of the original text."""
    },
#    "Generate Text": {
#        "description": "Creates text based on a prompt.",
#        "system_prompt": """You will receive a text input from the user. Your task is to generate text based on their request. Follow these important instructions:
#    1. Return the summary in plain text only.
#    2. Do not include any markdown formatting, greetings, or platitudes."""
#    },
    "Custom": {
        "description": "Enter your own system prompt.",
        "system_prompt": ""
    }
}

# ============================================================================
# Page Setup
# ============================================================================

st.title("Side-by-Side Comparison")
st.caption("Compare model responses to the same prompt")

# Get config from session state
queue_server_url = st.session_state.get("app.queue_server_url", "http://localhost:8001")
config = st.session_state.get("app.model_config", {"models": {}})
enabled_models = model_config.get_enabled_models(config)

# Build model choices list - map display_name to the full config entry
model_choices = ["(None)"] + [m.get("display_name", m.get("model_id")) for m in enabled_models]
# Map display_name -> full config dict (contains model_id and all parameters)
model_config_map = {m.get("display_name", m.get("model_id")): m for m in enabled_models}

# ============================================================================
# Function and Content Selection
# ============================================================================

st.subheader("Input")

col_func, col_content = st.columns([1, 2])

with col_func:
    # Function selector
    selected_function = st.selectbox(
        "Moodle Function",
        options=list(MOODLE_FUNCTIONS.keys()),
        help="Select the type of task to perform"
    )

    st.caption(MOODLE_FUNCTIONS[selected_function]["description"])

    # Custom system prompt (only if Custom selected)
    if selected_function == "Custom":
        system_prompt = st.text_area(
            "Custom System Prompt",
            value="You are a helpful assistant.",
            height=150,
            key="custom_system_prompt"
        )
    else:
        system_prompt = MOODLE_FUNCTIONS[selected_function]["system_prompt"]
        with st.expander("View System Prompt"):
            st.code(system_prompt, language=None)

with col_content:
    # Content paste area
    content = st.text_area(
        "Content (paste from bookmarklet)",
        height=200,
        placeholder="Paste the page content here...",
        key="comparison_content"
    )

st.divider()

# ============================================================================
# Model Selection Columns
# ============================================================================

st.subheader("Models to Compare")

NUM_COLUMNS = 3

# Create column containers
cols = st.columns(NUM_COLUMNS)

# Model selection for each column
selected_models = []
for i, col in enumerate(cols):
    with col:
        selection = st.selectbox(
            f"Model {i + 1}",
            options=model_choices,
            index=0,
            key=f"model_select_{i}"
        )
        selected_models.append(selection)

# Generate button
st.divider()

generate_clicked = st.button(
    "Generate All",
    type="primary",
    disabled=not content.strip(),
    help="Generate responses from all selected models"
)

# ============================================================================
# Response Display Columns
# ============================================================================

st.divider()
st.subheader("Results")

# Create output columns
output_cols = st.columns(NUM_COLUMNS)

# Create placeholders for each column
status_placeholders = []
content_placeholders = []
metrics_placeholders = []

for i, col in enumerate(output_cols):
    with col:
        st.markdown(f"**{selected_models[i]}**")
        status_placeholders.append(st.empty())
        # Container for visual styling, empty() inside for replaceable content
        with st.container(height=700, border=True):
            content_placeholders.append(st.empty())
        metrics_placeholders.append(st.empty())


# ============================================================================
# Generation Logic (Two-phase: submit all, then stream all)
# ============================================================================

def submit_to_queue(
    model_id: str,
    model_config_entry: dict,
    system_prompt: str,
    content: str,
    client: httpx.Client
) -> Optional[dict]:
    """
    Submit a request to the queue server.
    Returns {"request_id": ..., "queue_position": ...} or None on error.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content}
    ]

    payload = {
        "client_id": "tlc_playground_side_by_side",
        "model": model_id,
        "messages": messages,
        "temperature": model_config_entry.get("temperature", 0.7),
        "top_p": model_config_entry.get("top_p", 1.0),
        "frequency_penalty": model_config_entry.get("frequency_penalty", 0.0),
        "presence_penalty": model_config_entry.get("presence_penalty", 0.0),
    }

    max_tokens = model_config_entry.get("max_tokens")
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


def stream_from_queue(
    request_id: str,
    status_placeholder,
    content_placeholder,
    metrics_placeholder
) -> Optional[str]:
    """
    Stream a response from /stream/{request_id}.
    Returns the full response text, or None if error.
    """
    full_content = ""
    start_time = time.time()
    first_token_time = None
    token_count = 0

    try:
        with httpx.Client(timeout=300) as client:
            with client.stream(
                "GET",
                f"{queue_server_url}/stream/{request_id}"
            ) as response:

                if response.status_code != 200:
                    status_placeholder.error(f"HTTP {response.status_code}")
                    return None

                for line in response.iter_lines():
                    if not line:
                        continue

                    # SSE format: "data: {json}"
                    if line.startswith("data: "):
                        data_str = line[6:]

                        try:
                            chunk_data = json.loads(data_str)

                            # Queue position update
                            if "position" in chunk_data:
                                pos = chunk_data["position"]
                                if pos > 0:
                                    status_placeholder.info(f"Queue position: {pos}")
                                else:
                                    status_placeholder.success("Generating...")

                            # Content chunk
                            elif "chunk" in chunk_data:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    status_placeholder.success("Generating...")

                                full_content += chunk_data["chunk"]
                                token_count += 1
                                content_placeholder.markdown(full_content + "...")

                            # Done
                            elif "done" in chunk_data:
                                content_placeholder.markdown(full_content)
                                status_placeholder.empty()
                                break

                            # Error
                            elif "error" in chunk_data:
                                status_placeholder.error(f"Error: {chunk_data['error']}")
                                return None

                        except json.JSONDecodeError:
                            continue

    except httpx.ConnectError:
        status_placeholder.error("Connection failed")
        return None
    except httpx.ReadTimeout:
        status_placeholder.error("Timeout")
        return None
    except Exception as e:
        status_placeholder.error(f"Error: {str(e)[:50]}")
        return None

    # Calculate metrics
    end_time = time.time()
    total_time = end_time - start_time
    ttft = first_token_time - start_time if first_token_time else 0

    metrics_placeholder.caption(
        f"TTFT: {ttft:.1f}s | Total: {total_time:.1f}s | ~{token_count} chunks"
    )

    return full_content


# ============================================================================
# Execute Generation
# ============================================================================

if generate_clicked and content.strip():
    # Collect models to run
    models_to_run = []
    for i, selection in enumerate(selected_models):
        if selection != "(None)":
            model_entry = model_config_map.get(selection)
            if model_entry:
                models_to_run.append({
                    "index": i,
                    "model_id": model_entry.get("model_id"),
                    "config": model_entry,
                    "display_name": selection
                })

    if not models_to_run:
        st.warning("Please select at least one model to compare.")
    else:
        # ============================================================
        # PHASE 1: Submit ALL requests to queue first
        # ============================================================
        st.info(f"Submitting {len(models_to_run)} request(s) to queue...")

        submitted_requests = []

        with httpx.Client() as client:
            for model_info in models_to_run:
                idx = model_info["index"]
                status_placeholders[idx].info("Submitting...")

                result = submit_to_queue(
                    model_id=model_info["model_id"],
                    model_config_entry=model_info["config"],
                    system_prompt=system_prompt,
                    content=content,
                    client=client
                )

                if result:
                    queue_pos = result.get("queue_position", "?")
                    request_id = result.get("request_id")
                    status_placeholders[idx].info(f"Queued at position {queue_pos}")
                    submitted_requests.append({
                        **model_info,
                        "request_id": request_id,
                        "queue_position": queue_pos
                    })
                else:
                    status_placeholders[idx].error("Failed to submit")

        # ============================================================
        # PHASE 2: Stream responses (requests are already queued)
        # ============================================================
        if submitted_requests:
            results = {}

            for req_info in submitted_requests:
                idx = req_info["index"]
                request_id = req_info["request_id"]

                result = stream_from_queue(
                    request_id=request_id,
                    status_placeholder=status_placeholders[idx],
                    content_placeholder=content_placeholders[idx],
                    metrics_placeholder=metrics_placeholders[idx]
                )

                results[req_info["display_name"]] = result

            # Summary
            successful = sum(1 for r in results.values() if r is not None)
            st.success(f"Complete! {successful}/{len(submitted_requests)} models responded successfully.")
