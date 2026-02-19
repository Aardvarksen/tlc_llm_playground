"""
Saved Contexts Page

Save and manage content snippets for reuse in testing.
These can be used in Side-by-Side comparisons and future batch testing.
"""

import streamlit as st
import utilities.context_config as context_config

# ============================================================================
# Page Header
# ============================================================================

st.title("Saved Contexts")
st.caption("Save Moodle page content for reuse in testing")

# ============================================================================
# Load Context Configuration
# ============================================================================

# Load config into session state if not present
if "app.context_config" not in st.session_state:
    st.session_state["app.context_config"] = context_config.load_config()

config = st.session_state["app.context_config"]

# ============================================================================
# Add New Context
# ============================================================================

st.subheader("Save New Context")

with st.form("add_context_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        new_name = st.text_input(
            "Name",
            placeholder="e.g., Python Quiz Intro Page",
            help="A descriptive name for this content"
        )

    with col2:
        new_url = st.text_input(
            "Source URL (optional)",
            placeholder="https://moodle.example.com/...",
            help="Where this content came from"
        )

    new_content = st.text_area(
        "Content",
        height=200,
        placeholder="Paste content here (from bookmarklet or manual copy)...",
        help="The page content to save"
    )

    # Show character count
    if new_content:
        st.caption(f"{len(new_content):,} characters")

    submitted = st.form_submit_button("Save Context", type="primary")

    if submitted:
        if not new_name.strip():
            st.error("Please enter a name for this context")
        elif not new_content.strip():
            st.error("Please enter some content to save")
        else:
            config, context_id = context_config.add_context(
                config,
                name=new_name.strip(),
                content=new_content.strip(),
                url=new_url.strip()
            )
            context_config.save_config(config)
            st.session_state["app.context_config"] = config
            st.success(f"Saved '{new_name}' (ID: {context_id})")
            st.rerun()

# ============================================================================
# List Saved Contexts
# ============================================================================

st.divider()
st.subheader("Saved Contexts")

contexts = context_config.get_all_contexts(config)

if not contexts:
    st.info("No saved contexts yet. Use the form above to save some content.")
else:
    # Initialize edit state
    if "contexts.editing" not in st.session_state:
        st.session_state["contexts.editing"] = None

    for ctx in contexts:
        context_id = ctx.get("context_id")
        name = ctx.get("name", "Unnamed")
        content = ctx.get("content", "")
        url = ctx.get("url", "")
        created_at = ctx.get("created_at", "")

        # Check if we're editing this context
        is_editing = st.session_state["contexts.editing"] == context_id

        with st.expander(f"**{name}** ({len(content):,} chars)", expanded=is_editing):
            if is_editing:
                # Edit mode
                with st.form(f"edit_form_{context_id}"):
                    edit_name = st.text_input("Name", value=name, key=f"edit_name_{context_id}")
                    edit_url = st.text_input("Source URL", value=url, key=f"edit_url_{context_id}")
                    edit_content = st.text_area(
                        "Content",
                        value=content,
                        height=300,
                        key=f"edit_content_{context_id}"
                    )

                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        save_edit = st.form_submit_button("Save", type="primary")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")

                    if save_edit:
                        config = context_config.update_context(
                            config,
                            context_id,
                            name=edit_name.strip(),
                            content=edit_content.strip(),
                            url=edit_url.strip()
                        )
                        context_config.save_config(config)
                        st.session_state["app.context_config"] = config
                        st.session_state["contexts.editing"] = None
                        st.success("Saved changes")
                        st.rerun()

                    if cancel_edit:
                        st.session_state["contexts.editing"] = None
                        st.rerun()

            else:
                # View mode
                if url:
                    st.caption(f"Source: {url}")

                if created_at:
                    # Format the timestamp nicely
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at)
                        st.caption(f"Saved: {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.caption(f"Saved: {created_at}")

                # Show preview (first 500 chars)
                preview_len = 500
                if len(content) > preview_len:
                    st.text(content[:preview_len] + "...")
                    st.caption(f"... and {len(content) - preview_len:,} more characters")
                else:
                    st.text(content)

                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 4])

                with col1:
                    if st.button("Edit", key=f"edit_btn_{context_id}"):
                        st.session_state["contexts.editing"] = context_id
                        st.rerun()

                with col2:
                    if st.button("Delete", key=f"delete_btn_{context_id}"):
                        config = context_config.delete_context(config, context_id)
                        context_config.save_config(config)
                        st.session_state["app.context_config"] = config
                        st.success(f"Deleted '{name}'")
                        st.rerun()

# ============================================================================
# Summary Stats
# ============================================================================

st.divider()

total_contexts = len(contexts)
total_chars = sum(len(c.get("content", "")) for c in contexts)

col1, col2 = st.columns(2)
with col1:
    st.metric("Saved Contexts", total_contexts)
with col2:
    st.metric("Total Characters", f"{total_chars:,}")
