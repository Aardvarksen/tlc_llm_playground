import streamlit as st
import requests
import json

# have some variable set things that will affect the overall browser tab
PAGE_TITLE = "LLM Chatbot Playground" # this defines what will be used as the title of the browser tab
PAGE_ICON = "🤖" # this defines the icon or image that will be used to the left of the title in the browser tab

st.set_page_config(
    page_title = PAGE_TITLE, # this sets the title
    page_icon = PAGE_ICON # this sets the icon
    ,layout="wide" # this sets the layout of the page to use full width
    ,initial_sidebar_state="collapsed"  # this sets the initial state of the sidebar to be collapsed
)
# End of page setup variables

# ----------------------------------------------------

# Some variables that will be used to set default values for the session
QUEUE_SERVER_BASE_URL = "http://localhost:8000"
AVAILABLE_MODELS = ["mistralai/mistral-7b-instruct-v0.3","magistral-small-2509","qwen3-4b","qwen3-8b","qwen3-14b","qwen/qwen3-32b","granite-4.0-h-tiny","granite-4.0-h-small"]
DEFAULT_MODEL = AVAILABLE_MODELS[0]
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."

# Model-specific default parameters
MODEL_DEFAULTS = {
    "mistralai/mistral-7b-instruct-v0.3": {
        "temperature": 0.8,
        "hf_url": "https://hf.co/mistralai/Mistral-7B-Instruct-v0.3",
        "license": "apache-2.0"
    },
    "magistral-small-2509": {
        "temperature": 0.8,
        "hf_url": "https://hf.co/mistralai/Magistral-Small-2509",
        "license": "apache-2.0"
    },
    "qwen3-4b": {
        "temperature": 0.7,
        "hf_url": "https://hf.co/Qwen/Qwen3-4B",
        "license": "apache-2.0"
    },
    "qwen3-8b": {
        "temperature": 0.7,
        "hf_url": "https://hf.co/Qwen/Qwen3-8B",
        "license": "apache-2.0"
    },
    "qwen3-14b": {
        "temperature": 0.7,
        "hf_url": "https://hf.co/Qwen/Qwen3-14B",
        "license": "apache-2.0"
    },
    "qwen/qwen3-32b": {
        "temperature": 0.7,
        "hf_url": "https://hf.co/Qwen/Qwen3-32B",
        "license": "apache-2.0"
    },
    "granite-4.0-h-tiny": {
        "temperature": 0.0,
        "hf_url": "https://hf.co/ibm-granite/granite-4.0-h-tiny",
        "license": "apache-2.0"
    },
    "granite-4.0-h-small": {
        "temperature": 0.0,
        "hf_url": "https://hf.co/ibm-granite/granite-4.0-h-small",
        "license": "apache-2.0"
    },
}

# Session defaults. For key and value in the dictionary, if the key is not in the session state, it will be added with the value.
for k, v in {
    "messages": [],
    "model_name": DEFAULT_MODEL,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "temperature": MODEL_DEFAULTS[DEFAULT_MODEL]["temperature"],
    "added_context": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------------------------------

st.title("Chatbot demo")
st.write("v2.0, now with queue server")

with st.expander("Notes for use", expanded=False):
    st.write("""
             This application is built for demo/exploration purposes only, and is not intended to support widespread use.

             **NEW**: This version uses the queue server instead of direct LM Studio connection.

             Select a model in the sidebar to the left. Modify the 'temperature' parameter as/if desired.

             Modify the 'System Prompt' to change the LLM's behavior and personality if desired.

             Paste text into the 'Added Context' area to simulate context added from some source.

             """)

with st.sidebar:
    st.subheader("Model Selection")
    st.markdown("""
                Changing the selected model will reset/clear the application
                """)
    # Add model selection radio buttons
    selected_model = st.radio(
        "Select Model:",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state["model_name"]),
        help="Choose which AI model to use for responses"
    )

    # Update model and load its defaults if model changed
    if selected_model != st.session_state["model_name"]:
        st.session_state["messages"] = []
        st.session_state["model_name"] = selected_model
        st.session_state["temperature"] = MODEL_DEFAULTS[selected_model]["temperature"]

    # Visual separation between model selection and parameters
    st.divider()

    # Parameters section
    st.subheader("Parameters")

    # Temperature slider
    st.session_state["temperature"] = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state["temperature"],
        step=0.1,
        help="Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."
    )

    # System prompt editor
    st.session_state["system_prompt"] = st.text_area(
        "System Prompt:",
        value=st.session_state["system_prompt"],
        height=100,
        help="This defines the AI's behavior and personality"
    )

    st.divider()

    st.markdown("**Model URL**")
    st.markdown(f"[HuggingFace]({MODEL_DEFAULTS[st.session_state['model_name']]['hf_url']})")

    st.markdown("**License Type**")
    st.markdown(MODEL_DEFAULTS[st.session_state['model_name']]['license'])

prompt = st.chat_input("Say Something")

# Create two columns with custom ratio (30% context, 70% chat)
col1, col2 = st.columns([4, 6], gap="large")

with col1:

    st.header("Added Context")
    st.session_state["added_context"] = st.text_area(
        "Paste additional context here:",
        value=st.session_state["added_context"],
        height=600,
        help="This text will be included as context with every message to the AI",
        label_visibility="collapsed"
    )

with col2:
    st.header("Chat")

    with st.container(height=600, border = True):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Build messages list with system prompt first
                messages_with_system = [
                    {"role": "system", "content": st.session_state["system_prompt"]}
                ]

                # Add context as a user message if it exists
                if st.session_state["added_context"].strip():
                    messages_with_system.append({
                        "role": "user",
                        "content": f"Additional context:\n{st.session_state['added_context']}"
                    })

                # Add conversation history
                messages_with_system.extend([
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ])

                # ============================================================
                # STEP 1: Submit to queue server
                # ============================================================
                response = requests.post(
                    f"{QUEUE_SERVER_BASE_URL}/queue/add",
                    json={
                        "client_id": "streamlit_v2",
                        "messages": messages_with_system,
                        "model": st.session_state["model_name"],
                        "temperature": st.session_state["temperature"],
                    }
                )

                if response.status_code != 200:
                    st.error(f"Failed to submit request: {response.text}")
                    st.stop()

                data = response.json()
                request_id = data["request_id"]
                initial_queue_position = data["queue_position"]  # Store original position

                # Show queue position (will be cleared when streaming starts)
                info_placeholder = st.empty()
                info_placeholder.info(f"Joined queue at position {initial_queue_position}, {initial_queue_position} total generations in queue")

                # ============================================================
                # STEP 2: Stream the response from queue server
                # ============================================================
                message_placeholder = st.empty()
                full_response = ""

                # Open streaming connection
                stream_response = requests.get(
                    f"{QUEUE_SERVER_BASE_URL}/stream/{request_id}",
                    stream=True
                )

                # Read Server-Sent Events (SSE) line by line
                for line in stream_response.iter_lines():
                    if not line:
                        continue

                    # SSE format: "data: {json}"
                    line_text = line.decode('utf-8')
                    if line_text.startswith("data: "):
                        chunk_data = json.loads(line_text[6:])  # Skip "data: " prefix

                        if "position" in chunk_data:
                            # Still waiting in queue - update total count
                            current_total = chunk_data['position']
                            info_placeholder.info(f"Joined queue at position {initial_queue_position}, {current_total} total generations in queue")

                        elif "chunk" in chunk_data:
                            # Got a text chunk! Clear the info message if first chunk
                            if not full_response:
                                info_placeholder.empty()  # Clear the queue position message

                            full_response += chunk_data["chunk"]
                            message_placeholder.markdown(full_response + "▌")  # Show cursor

                        elif "done" in chunk_data:
                            # Stream finished!
                            message_placeholder.markdown(full_response)
                            break

                        elif "error" in chunk_data:
                            # Error during processing
                            info_placeholder.empty()
                            st.error(f"Error: {chunk_data['error']}")
                            break

            st.session_state.messages.append({"role": "assistant", "content": full_response})

with st.expander("Full Context as raw JSON", expanded=False):
    messages_with_system = [
        {"role": "system", "content": st.session_state["system_prompt"]}
    ]

    if st.session_state["added_context"].strip():
        messages_with_system.append({
            "role": "user",
            "content": f"Additional context:\n{st.session_state['added_context']}"
        })

    messages_with_system.extend([
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ])

    st.write(messages_with_system)
