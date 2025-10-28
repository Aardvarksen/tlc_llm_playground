"""
Centralized configuration for TLC LLM Playground.
All settings in one place - modify here instead of scattered across files.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# LM Studio Configuration
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
LM_STUDIO_API_KEY = "lm_studio"  # LM Studio doesn't use real keys, this is just a placeholder

# Available Models and Their Defaults
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

# Default Settings
DEFAULT_MODEL = AVAILABLE_MODELS[0]
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_TEMPERATURE = MODEL_DEFAULTS[DEFAULT_MODEL]["temperature"]

# Queue Server Configuration
QUEUE_SERVER_HOST = os.getenv("QUEUE_HOST", "0.0.0.0")
QUEUE_SERVER_PORT = int(os.getenv("QUEUE_PORT", "8000"))

# Streamlit Configuration
PAGE_TITLE = "LLM Chatbot Playground"
PAGE_ICON = "🤖"
