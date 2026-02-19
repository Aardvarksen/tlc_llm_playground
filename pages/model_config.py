"""
Model Configuration Page

Manage model configurations and their default parameters.
- View/edit model configurations
- Copy configurations to create variants (e.g., different temperatures)
- Enable/disable configurations for selection lists
"""

import streamlit as st
import utilities.model_config as model_config

# ============================================================================
# Page Header
# ============================================================================

st.title("Model Configuration")
st.caption("Manage model configurations and their default parameters")

# ============================================================================
# Queue Server Connection (collapsed by default)
# ============================================================================

queue_server_url = st.session_state.get("app.queue_server_url", "http://localhost:8001")

with st.expander("Queue Server Connection", expanded=False):
    st.write(f"**Connected to:** `{queue_server_url}`")

    if st.button("Test Connection"):
        import httpx
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{queue_server_url}/health")
                if response.status_code == 200:
                    health = response.json()
                    st.success(f"Connected! Queue size: {health.get('queue_size', 0)}")
                else:
                    st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# ============================================================================
# Copy Configuration Feature
# ============================================================================

st.divider()
st.subheader("Create Configuration Variant")
st.caption("Copy an existing configuration to test different parameters")

config = st.session_state["app.model_config"]
models = config.get("models", {})

if models:
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Source config to copy from
        source_options = list(models.keys())
        source_display = {k: models[k].get("display_name", k) for k in source_options}
        source_key = st.selectbox(
            "Copy from",
            options=source_options,
            format_func=lambda x: source_display[x],
            key="copy_source"
        )

    with col2:
        # New display name
        new_name = st.text_input(
            "New configuration name",
            placeholder="e.g., Mistral 7B (temp 0.0)",
            key="copy_new_name"
        )

    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        copy_clicked = st.button("Copy", type="secondary", disabled=not new_name.strip())

    if copy_clicked and new_name.strip():
        config, new_key = model_config.copy_model_config(config, source_key, new_name.strip())
        if new_key:
            model_config.save_config(config)
            st.session_state["app.model_config"] = config
            st.session_state["app.enabled_models"] = model_config.get_enabled_models(config)
            st.success(f"Created '{new_name}' - edit it below!")
            st.rerun()
        else:
            st.error("Failed to copy configuration")

# ============================================================================
# Model Configuration Editor
# ============================================================================

st.divider()
st.subheader("Configured Models")

# Refresh config after potential copy
config = st.session_state["app.model_config"]
models = config.get("models", {})

if not models:
    st.info("No models configured.")
else:
    # Create a form for all model edits
    with st.form("model_config_form"):
        for config_key, model_info in models.items():
            model_id = model_info.get("model_id", config_key)
            display_name = model_info.get("display_name", config_key)

            with st.expander(f"**{display_name}**", expanded=False):

                col1, col2 = st.columns([3, 1])

                with col1:
                    # Display Name
                    new_display_name = st.text_input(
                        "Display Name",
                        value=display_name,
                        key=f"display_name_{config_key}",
                        help="Friendly name shown in model selection dropdowns"
                    )

                    # Model ID (read-only display)
                    st.text_input(
                        "Model ID (API)",
                        value=model_id,
                        disabled=True,
                        key=f"model_id_{config_key}",
                        help="The actual model identifier used in API calls"
                    )

                with col2:
                    # Enabled checkbox
                    new_enabled = st.checkbox(
                        "Enabled",
                        value=model_info.get("enabled", True),
                        key=f"enabled_{config_key}",
                        help="Disabled configs won't appear in selection lists"
                    )

                st.markdown("**Default Parameters**")

                param_col1, param_col2, param_col3 = st.columns(3)

                with param_col1:
                    new_temperature = st.number_input(
                        "Temperature",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(model_info.get("temperature", 0.7)),
                        step=0.1,
                        key=f"temp_{config_key}",
                        help="Higher = more random, Lower = more focused"
                    )

                    new_top_p = st.number_input(
                        "Top P",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(model_info.get("top_p", 1.0)),
                        step=0.05,
                        key=f"top_p_{config_key}",
                        help="Nucleus sampling threshold"
                    )

                with param_col2:
                    new_freq_penalty = st.number_input(
                        "Frequency Penalty",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(model_info.get("frequency_penalty", 0.0)),
                        step=0.1,
                        key=f"freq_{config_key}",
                        help="Penalize repeated tokens"
                    )

                    new_pres_penalty = st.number_input(
                        "Presence Penalty",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(model_info.get("presence_penalty", 0.0)),
                        step=0.1,
                        key=f"pres_{config_key}",
                        help="Penalize tokens that have appeared"
                    )

                with param_col3:
                    # Max tokens - use 0 as "unlimited/None"
                    current_max = model_info.get("max_tokens")
                    new_max_tokens = st.number_input(
                        "Max Tokens (0 = unlimited)",
                        min_value=0,
                        max_value=32768,
                        value=current_max if current_max else 0,
                        step=256,
                        key=f"max_tok_{config_key}",
                        help="Maximum tokens to generate (0 = no limit)"
                    )

                # Store new values back into the model_info dict
                model_info["display_name"] = new_display_name
                model_info["enabled"] = new_enabled
                model_info["temperature"] = new_temperature
                model_info["top_p"] = new_top_p
                model_info["frequency_penalty"] = new_freq_penalty
                model_info["presence_penalty"] = new_pres_penalty
                model_info["max_tokens"] = new_max_tokens if new_max_tokens > 0 else None

        # Save button
        st.divider()
        submitted = st.form_submit_button("Save Configuration", type="primary")

        if submitted:
            # Save to file
            if model_config.save_config(config):
                # Update session state
                st.session_state["app.model_config"] = config
                st.session_state["app.enabled_models"] = model_config.get_enabled_models(config)
                st.success("Configuration saved!")
            else:
                st.error("Failed to save configuration")

# ============================================================================
# Delete Configuration (outside the form)
# ============================================================================

st.divider()
st.subheader("Delete Configuration")
st.caption("Remove a non-default configuration variant")

# Only allow deleting non-default configs
deletable = [k for k in models.keys() if not k.endswith("-default")]

if deletable:
    col1, col2 = st.columns([3, 1])

    with col1:
        delete_key = st.selectbox(
            "Select configuration to delete",
            options=deletable,
            format_func=lambda x: models[x].get("display_name", x),
            key="delete_select"
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("Delete", type="secondary"):
            config = model_config.remove_model_from_config(config, delete_key)
            model_config.save_config(config)
            st.session_state["app.model_config"] = config
            st.session_state["app.enabled_models"] = model_config.get_enabled_models(config)
            st.success(f"Deleted configuration")
            st.rerun()
else:
    st.info("No custom configurations to delete. Default configurations cannot be removed.")

# ============================================================================
# Summary Stats
# ============================================================================

st.divider()

total_configs = len(models)
enabled_count = len([m for m in models.values() if m.get("enabled", True)])
default_count = len([k for k in models.keys() if k.endswith("-default")])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Configs", total_configs)
with col2:
    st.metric("Enabled", enabled_count)
with col3:
    st.metric("Defaults", default_count)
with col4:
    st.metric("Variants", total_configs - default_count)
