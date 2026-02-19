"""
How-To Guides Page

Dynamically loads and displays markdown guides from the how-to-guides folder.
Add new .md files to that folder and they'll automatically appear here.
"""

import re

import streamlit as st
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

GUIDES_FOLDER = Path("how-to-guides")

# ============================================================================
# Page Header
# ============================================================================

st.title("How-To Guides")
st.caption("Reference guides for using the TLC LLM Playground")

# ============================================================================
# Load Available Guides
# ============================================================================

def get_available_guides() -> list[tuple[str, Path]]:
    """
    Scan the guides folder for .md files.
    Returns list of (display_name, file_path) tuples, sorted by filename.
    """
    guides = []

    if not GUIDES_FOLDER.exists():
        return guides

    for md_file in sorted(GUIDES_FOLDER.glob("*.md")):
        # Convert filename to display name
        # e.g., "01-moodle-bookmarklet.md" -> "Moodle Bookmarklet"
        name = md_file.stem  # Remove .md extension

        # Remove leading numbers and dashes (e.g., "01-")
        if name[0:2].isdigit() and name[2] == "-":
            name = name[3:]
        elif name[0].isdigit() and name[1] == "-":
            name = name[2:]

        # Convert dashes to spaces and title case
        display_name = name.replace("-", " ").title()

        guides.append((display_name, md_file))

    return guides


def load_guide_content(file_path: Path) -> str:
    """Load the content of a markdown file."""
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error loading guide: {e}"


def generate_toc(markdown_content: str) -> str:
    """
    Generate a table of contents from markdown headers.
    Returns a markdown string with anchor links matching Streamlit's
    auto-generated heading IDs. Skips the h1 title and anything
    inside fenced code blocks.
    """
    toc_lines = []
    in_code_block = False

    for line in markdown_content.split("\n"):
        # Track fenced code blocks so we don't pick up # comments in code
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Match ## through ###### headers (skip # which is the page title)
        match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            header_text = match.group(2).strip()

            # Build anchor slug to match Streamlit's generated IDs:
            # lowercase, strip non-alphanumeric (keep spaces/hyphens), spaces→hyphens
            anchor = header_text.lower()
            anchor = re.sub(r"[^\w\s-]", " ", anchor)
            anchor = re.sub(r"\s+", "-", anchor.strip())
            anchor = re.sub(r"-+", "-", anchor)

            indent = "  " * (level - 2)
            toc_lines.append(f"{indent}- [{header_text}](#{anchor})")

    if not toc_lines:
        return ""

    return "**Contents**\n\n" + "\n".join(toc_lines) + "\n\n---\n\n"


def insert_toc(content: str) -> str:
    """Insert a generated TOC before the first ## header in the content."""
    toc = generate_toc(content)
    if not toc:
        return content

    # Find the first ## header and insert the TOC right before it
    first_h2 = re.search(r"^## ", content, re.MULTILINE)
    if first_h2:
        return content[: first_h2.start()] + toc + content[first_h2.start() :]

    return content


# ============================================================================
# Guide Selection and Display
# ============================================================================

guides = get_available_guides()

if not guides:
    st.warning(f"No guides found in `{GUIDES_FOLDER}/`")
    st.info("Add `.md` files to the `how-to-guides` folder to see them here.")
else:
    # Create sidebar navigation for guides
    with st.sidebar:
        st.subheader("Guides")

        # Initialize selected guide in session state
        if "how_to.selected_guide" not in st.session_state:
            st.session_state["how_to.selected_guide"] = guides[0][1]  # Default to first guide

        # Create buttons for each guide
        for display_name, file_path in guides:
            is_selected = st.session_state["how_to.selected_guide"] == file_path

            if st.button(
                display_name,
                key=f"guide_{file_path.stem}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                st.session_state["how_to.selected_guide"] = file_path
                st.rerun()

        st.divider()
        st.caption(f"{len(guides)} guide(s) available")

    # Display the selected guide
    selected_path = st.session_state["how_to.selected_guide"]
    content = load_guide_content(selected_path)

    # Insert table of contents and render the markdown
    content = insert_toc(content)
    st.markdown(content)

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption(f"Guides are loaded from: `{GUIDES_FOLDER.absolute()}`")
st.caption("Add new `.md` files to that folder to create new guides.")
