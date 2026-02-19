"""
Saved Prompts Page

Save and manage reusable system prompts.
These can be used in Side-by-Side comparisons and Batch Runner testing.
"""

import streamlit as st
import utilities.system_prompt_config as prompt_config

# ============================================================================
# Page Header
# ============================================================================

st.title("Saved Prompts")
st.caption("Manage reusable system prompts for LLM testing")

# ============================================================================
# Load Prompt Configuration
# ============================================================================

# Load config into session state if not present
if "app.prompt_config" not in st.session_state:
    st.session_state["app.prompt_config"] = prompt_config.load_config()

config = st.session_state["app.prompt_config"]

# ============================================================================
# Add New Prompt
# ============================================================================

st.subheader("Add New Prompt")

with st.form("add_prompt_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        new_name = st.text_input(
            "Name",
            placeholder="e.g., Technical Documentation Writer",
            help="A descriptive name for this prompt"
        )

    with col2:
        new_description = st.text_input(
            "Description (optional)",
            placeholder="Brief description of purpose...",
            help="What this prompt is designed to do"
        )

    new_content = st.text_area(
        "System Prompt Content",
        height=200,
        placeholder="Enter the system prompt text here...",
        help="The full system prompt to send to the LLM"
    )

    # Show character count
    if new_content:
        st.caption(f"{len(new_content):,} characters")

    submitted = st.form_submit_button("Save Prompt", type="primary")

    if submitted:
        if not new_name.strip():
            st.error("Please enter a name for this prompt")
        elif not new_content.strip():
            st.error("Please enter the prompt content")
        else:
            config, prompt_id = prompt_config.add_prompt(
                config,
                name=new_name.strip(),
                content=new_content.strip(),
                description=new_description.strip()
            )
            prompt_config.save_config(config)
            st.session_state["app.prompt_config"] = config
            st.success(f"Saved '{new_name}' (ID: {prompt_id})")
            st.rerun()

# ============================================================================
# List Saved Prompts
# ============================================================================

st.divider()
st.subheader("Saved Prompts")

prompts = prompt_config.get_all_prompts(config)

if not prompts:
    st.info("No saved prompts yet. Use the form above to create some, or default Moodle prompts will be loaded on refresh.")
else:
    # Initialize edit state
    if "prompts.editing" not in st.session_state:
        st.session_state["prompts.editing"] = None

    for prompt in prompts:
        prompt_id = prompt.get("prompt_id")
        name = prompt.get("name", "Unnamed")
        content = prompt.get("content", "")
        description = prompt.get("description", "")
        is_default = prompt.get("is_default", False)
        created_at = prompt.get("created_at", "")

        # Check if we're editing this prompt
        is_editing = st.session_state["prompts.editing"] == prompt_id

        # Build expander label
        label_parts = [f"**{name}**"]
        if is_default:
            label_parts.append("(Default)")
        label_parts.append(f"({len(content):,} chars)")
        expander_label = " ".join(label_parts)

        with st.expander(expander_label, expanded=is_editing):
            if is_editing:
                # Edit mode
                with st.form(f"edit_form_{prompt_id}"):
                    edit_name = st.text_input(
                        "Name",
                        value=name,
                        key=f"edit_name_{prompt_id}"
                    )
                    edit_description = st.text_input(
                        "Description",
                        value=description,
                        key=f"edit_description_{prompt_id}"
                    )
                    edit_content = st.text_area(
                        "System Prompt Content",
                        value=content,
                        height=300,
                        key=f"edit_content_{prompt_id}"
                    )

                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        save_edit = st.form_submit_button("Save", type="primary")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")

                    if save_edit:
                        config = prompt_config.update_prompt(
                            config,
                            prompt_id,
                            name=edit_name.strip(),
                            content=edit_content.strip(),
                            description=edit_description.strip()
                        )
                        prompt_config.save_config(config)
                        st.session_state["app.prompt_config"] = config
                        st.session_state["prompts.editing"] = None
                        st.success("Saved changes")
                        st.rerun()

                    if cancel_edit:
                        st.session_state["prompts.editing"] = None
                        st.rerun()

            else:
                # View mode
                if description:
                    st.caption(f"**Purpose:** {description}")

                if is_default:
                    st.caption("*This is a built-in Moodle default prompt*")

                if created_at and not is_default:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at)
                        st.caption(f"Saved: {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.caption(f"Saved: {created_at}")

                # Show preview (first 500 chars)
                preview_len = 500
                st.markdown("**Prompt Content:**")
                if len(content) > preview_len:
                    st.text(content[:preview_len] + "...")
                    st.caption(f"... and {len(content) - preview_len:,} more characters")
                else:
                    st.text(content)

                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 4])

                with col1:
                    if st.button("Edit", key=f"edit_btn_{prompt_id}"):
                        st.session_state["prompts.editing"] = prompt_id
                        st.rerun()

                with col2:
                    delete_label = "Delete"
                    if is_default:
                        delete_label = "Delete (will restore on reload)"

                    if st.button(delete_label, key=f"delete_btn_{prompt_id}"):
                        config = prompt_config.delete_prompt(config, prompt_id)
                        prompt_config.save_config(config)
                        st.session_state["app.prompt_config"] = config
                        st.success(f"Deleted '{name}'")
                        st.rerun()

# ============================================================================
# Summary Stats
# ============================================================================

st.divider()

total_prompts = len(prompts)
default_count = sum(1 for p in prompts if p.get("is_default", False))
custom_count = total_prompts - default_count

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Prompts", total_prompts)
with col2:
    st.metric("Default (Moodle)", default_count)
with col3:
    st.metric("Custom", custom_count)
