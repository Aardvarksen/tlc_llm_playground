"""
TLC LLM Playground - Main Application Entry Point

A multi-page Streamlit application for testing and validating LLM capabilities
before Moodle integration.

Run with:
    streamlit run app.py
"""

import streamlit as st
import utilities.model_config as model_config
import utilities.context_config as context_config
import utilities.system_prompt_config as prompt_config

# ============================================================================
# Configuration
# ============================================================================

# Queue server URL - connects to queue_server_v2.py
QUEUE_SERVER_URL = "http://localhost:8001"

# Page configuration
PAGE_TITLE = "TLC LLM Playground"
PAGE_ICON = "🧪"

# ============================================================================
# Page Setup (runs once at app start)
# ============================================================================

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Shared State Initialization
# ============================================================================

# Store queue server URL in session state for access by all pages
if "app.queue_server_url" not in st.session_state:
    st.session_state["app.queue_server_url"] = QUEUE_SERVER_URL

# Load model configuration from JSON file
if "app.model_config" not in st.session_state:
    config = model_config.load_config()
    # Ensure all approved models have default configs (adds any new ones)
    config = model_config.initialize_default_configs(config)
    model_config.save_config(config)
    st.session_state["app.model_config"] = config

# Cache enabled models for quick access
if "app.enabled_models" not in st.session_state:
    st.session_state["app.enabled_models"] = model_config.get_enabled_models(
        st.session_state["app.model_config"]
    )

# Load context configuration (saved content snippets)
if "app.context_config" not in st.session_state:
    st.session_state["app.context_config"] = context_config.load_config()

# Load system prompt configuration (reusable prompts)
if "app.prompt_config" not in st.session_state:
    st.session_state["app.prompt_config"] = prompt_config.load_config()

# ============================================================================
# Multi-Page Navigation Setup
# ============================================================================

# Define pages
model_config_page = st.Page(
    "pages/model_config.py",
    title="Model Configuration",
    icon="⚙️"
)

# Side-by-side comparison page
side_by_side_page = st.Page(
    "pages/side_by_side.py",
    title="Side-by-Side",
    icon="⚖️"
)

# Saved contexts page
saved_contexts_page = st.Page("pages/saved_contexts.py",title="Saved Contexts",icon="📋")

# How-To guides page
how_to_page = st.Page(
    "pages/how_to.py",
    title="How-To Guides",
    icon="📖"
)

# Saved prompts page
saved_prompts_page = st.Page("pages/saved_prompts.py",title="Saved Prompts",icon="💬")

# Batch runner page
batch_runner_page = st.Page("pages/batch_runner.py",title="Batch Runner",icon="🧪")

# Create navigation
pg = st.navigation([
    side_by_side_page,
    saved_contexts_page,
    saved_prompts_page,
    batch_runner_page,
    model_config_page,
    how_to_page,
])

# Run the selected page
pg.run()
