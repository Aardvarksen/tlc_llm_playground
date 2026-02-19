import streamlit as st
import requests

st.title("testing queue server")
fastapi_base_url = "http://localhost:8000"
queue_add = "/queue/add"
request_status = "/request/{request_id}"

model = "mistralai/mistral-7b-instruct-v0.3"
temperature = 0.8

system_prompt = "You are a writer of very very long stories based on user prompts. The story should take approximately 10 minutes to read aloud."

for k, v in {
    "messages": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Say something..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    # ========================================================================
    # STEP 1: Build the full messages array (system prompt + conversation)
    # ========================================================================
    messages_for_llm = [
        {"role": "system", "content": system_prompt}
    ] + st.session_state.messages

    # ========================================================================
    # STEP 2: Submit to queue server
    # ========================================================================
    with st.spinner("Submitting to queue..."):
        response = requests.post(
            f"{fastapi_base_url}/queue/add",
            json={
                "client_id": "streamlit_test",
                "messages": messages_for_llm,
                "model": model,
                "temperature": temperature,
            }
        )

        if response.status_code != 200:
            st.error(f"Failed to submit request: {response.text}")
            st.stop()

        data = response.json()
        request_id = data["request_id"]
        queue_position = data["queue_position"]

        st.info(f"Request submitted! ID: {request_id}, Queue position: {queue_position}")

    # ========================================================================
    # STEP 3: Connect to streaming endpoint and receive chunks
    # ========================================================================
    import json

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Open streaming connection
        stream_response = requests.get(
            f"{fastapi_base_url}/stream/{request_id}",
            stream=True  # CRITICAL: keeps connection open
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
                    # Still waiting in queue
                    message_placeholder.info(f"⏳ Position in queue: {chunk_data['position']}")

                elif "chunk" in chunk_data:
                    # Got a text chunk!
                    full_response += chunk_data["chunk"]
                    message_placeholder.markdown(full_response + "▌")  # Show cursor

                elif "done" in chunk_data:
                    # Stream finished!
                    message_placeholder.markdown(full_response)
                    break

                elif "error" in chunk_data:
                    # Error during processing
                    st.error(f"Error: {chunk_data['error']}")
                    break

    # Save assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})

