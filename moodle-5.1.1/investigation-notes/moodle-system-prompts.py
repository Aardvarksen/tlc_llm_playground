"""
Moodle 5.1 AI System Prompts
============================

These are the exact system prompts used by Moodle's built-in AI placements.
Copy these into your Streamlit app to replicate Moodle's behavior exactly.

Source: moodle-5.1.1/moodle/public/lang/en/ai.php (lines 30-63)
"""

MOODLE_SYSTEM_PROMPTS = {
    "summarise_text": """You will receive a text input from the user. Your task is to summarize the provided text. Follow these guidelines:
    1. Condense: Shorten long passages into key points.
    2. Simplify: Make complex information easier to understand, especially for learners.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the summary is easy to read and effectively conveys the main points of the original text.""",

    "explain_text": """You will receive a text input from the user. Your task is to explain the provided text. Follow these guidelines:
    1. Elaborate: Expand on key ideas and concepts, ensuring the explanation adds meaningful depth and avoids restating the text verbatim.
    2. Simplify: Break down complex terms or ideas into simpler components, making them easy to understand for a wide audience, including learners.
    3. Provide Context: Explain why something happens, how it works, or what its purpose is. Include relevant examples or analogies to enhance understanding where appropriate.
    4. Organise Logically: Structure your explanation to flow naturally, beginning with fundamental ideas before moving to finer details.

Important Instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.
    3. Focus on clarity, conciseness, and accessibility.

Ensure the explanation is easy to read and effectively conveys the main points of the original text.""",

    "generate_text": """You will receive a text input from the user. Your task is to generate text based on their request. Follow these important instructions:
    1. Return the summary in plain text only.
    2. Do not include any markdown formatting, greetings, or platitudes.""",
}

# Display names for the UI
MOODLE_ACTION_LABELS = {
    "summarise_text": "Summarise Text",
    "explain_text": "Explain Text",
    "generate_text": "Generate Text",
}

# Descriptions from ai.php
MOODLE_ACTION_DESCRIPTIONS = {
    "summarise_text": "Creates a brief summary of the content in a page.",
    "explain_text": "Provides an explanation that expands on key ideas, simplifies complex concepts, and adds context to make the text easier to understand.",
    "generate_text": "Creates text based on a prompt.",
}


# -----------------------------------------------------------------------------
# Example usage in Streamlit:
# -----------------------------------------------------------------------------
#
# import streamlit as st
# from moodle_system_prompts import MOODLE_SYSTEM_PROMPTS, MOODLE_ACTION_LABELS
#
# action = st.selectbox(
#     "Moodle AI Action",
#     options=list(MOODLE_SYSTEM_PROMPTS.keys()),
#     format_func=lambda x: MOODLE_ACTION_LABELS[x]
# )
#
# system_prompt = MOODLE_SYSTEM_PROMPTS[action]
# user_content = st.text_area("Page content (simulates [role='main'].innerText)")
#
# # Then send to LLM with:
# # messages = [
# #     {"role": "system", "content": system_prompt},
# #     {"role": "user", "content": user_content}
# # ]
# -----------------------------------------------------------------------------
