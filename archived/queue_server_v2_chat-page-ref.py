"""
Test Chat 3 - RTXBox Queue Server Client

A simple Streamlit chat that connects to the RTXBox queue server over Tailscale.
Demonstrates queue position feedback via SSE comments.

No local LLM, no model manager, no TTS - just queue-aware streaming chat.
"""

import streamlit as st
import httpx
import json

# ============================================================================
# Configuration - RTXBox Connection
# ============================================================================

RTXBOX_BASE_URL = "http://desktop-toeaoij.tail1ef175.ts.net:8001"

AVAILABLE_MODELS = [
    "mistralai/mistral-7b-instruct-v0.3",
    "magistral-small-2509",
    "qwen3-4b",
    "qwen3-8b",
    "qwen3-14b",
    "qwen/qwen3-32b",
    "granite-4.0-h-tiny",
    "granite-4.0-h-small"
]

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

# ============================================================================
# Page Setup
# ============================================================================

st.title("Test Chat 3 - RTXBox Queue Client")
st.caption(f"Connected to: {RTXBOX_BASE_URL}")

# Initialize session state
st.session_state.setdefault("test_chat3.messages", [])
st.session_state.setdefault("test_chat3.selected_model", AVAILABLE_MODELS[4])  # qwen3-14b
st.session_state.setdefault("test_chat3.system_prompt", DEFAULT_SYSTEM_PROMPT)

# ============================================================================
# Sidebar Configuration
# ============================================================================

with st.sidebar:
    st.header("Configuration")

    # Model selection
    selected_model = st.selectbox(
        "Model",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state["test_chat3.selected_model"]),
        key="test_chat3.model_selector"
    )
    st.session_state["test_chat3.selected_model"] = selected_model

    # System prompt
    system_prompt = st.text_area(
        "System Prompt",
        value=st.session_state["test_chat3.system_prompt"],
        height=100,
        key="test_chat3.system_prompt_input"
    )
    st.session_state["test_chat3.system_prompt"] = system_prompt

    st.divider()

    # Connection test
    if st.button("Test Connection", key="test_chat3.test_conn"):
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{RTXBOX_BASE_URL}/health")
                if response.status_code == 200:
                    health = response.json()
                    st.success(f"Connected! Queue size: {health.get('queue_size', '?')}")
                else:
                    st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

    st.divider()

    # Clear chat
    if st.button("Clear Chat", key="test_chat3.clear"):
        st.session_state["test_chat3.messages"] = []
        st.rerun()

# ============================================================================
# Chat Display
# ============================================================================

for msg in st.session_state["test_chat3.messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============================================================================
# Chat Input and Streaming Response
# ============================================================================

if prompt := st.chat_input("Message the RTXBox...", key="test_chat3.input"):
    # Add user message
    st.session_state["test_chat3.messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Build messages for API
    messages = [{"role": "system", "content": st.session_state["test_chat3.system_prompt"]}]
    for msg in st.session_state["test_chat3.messages"]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Prepare request
    payload = {
        "model": selected_model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7
    }

    # Stream response with queue feedback
    with st.chat_message("assistant"):
        # Status placeholder for queue position
        status_placeholder = st.empty()
        # Content placeholder for streaming text
        content_placeholder = st.empty()

        full_content = ""
        queue_entered = None
        queue_position = None
        is_processing = False

        try:
            with httpx.Client(timeout=300) as client:
                with client.stream(
                    "POST",
                    f"{RTXBOX_BASE_URL}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:

                    if response.status_code != 200:
                        st.error(f"Error: {response.status_code} - {response.text}")
                    else:
                        for line in response.iter_lines():
                            if not line:
                                continue

                            # Parse SSE comments (queue position feedback)
                            if line.startswith(': queue_entered='):
                                queue_entered = int(line.split('=')[1])
                                status_placeholder.info(f"Entered queue at position {queue_entered}")

                            elif line.startswith(': queue_position='):
                                queue_position = int(line.split('=')[1])
                                if queue_position == 0:
                                    is_processing = True
                                    status_placeholder.success("Processing...")
                                else:
                                    status_placeholder.info(f"Queue position: {queue_position}")

                            # Parse data chunks (actual content)
                            elif line.startswith('data: '):
                                data_str = line[6:]  # Remove 'data: ' prefix

                                if data_str == '[DONE]':
                                    # Stream complete
                                    status_placeholder.empty()
                                    continue

                                try:
                                    chunk = json.loads(data_str)

                                    # Check for error
                                    if 'error' in chunk:
                                        st.error(f"Server error: {chunk['error']}")
                                        continue

                                    # Extract content delta
                                    if 'choices' in chunk and chunk['choices']:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            full_content += delta['content']
                                            content_placeholder.markdown(full_content + "...")

                                        # Check for finish
                                        if chunk['choices'][0].get('finish_reason'):
                                            content_placeholder.markdown(full_content)

                                except json.JSONDecodeError:
                                    # Skip malformed JSON
                                    continue

        except httpx.ConnectError:
            st.error(f"Could not connect to RTXBox at {RTXBOX_BASE_URL}")
            st.info("Is the queue server running? Is Tailscale connected?")
        except httpx.ReadTimeout:
            st.error("Request timed out (300s)")
        except Exception as e:
            st.error(f"Error: {e}")

        # Save assistant message if we got content
        if full_content:
            st.session_state["test_chat3.messages"].append({
                "role": "assistant",
                "content": full_content
            })

# ============================================================================
# Footer
# ============================================================================

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption(f"Model: {selected_model}")
with col2:
    st.caption(f"Messages: {len(st.session_state['test_chat3.messages'])}")
