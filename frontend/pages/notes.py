import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, empty_state, load_styles, page_header


def render_notes_page():
    load_styles()
    page_header("Workspace", "Notes", "A searchable view of the notes captured during customer interactions.")
    try:
        response = requests.get(f"{BACKEND_URL}/api/interactions", timeout=5)
        response.raise_for_status()
        notes = [item for item in response.json() if str(item.get("type", "")).lower() == "note"]
    except (requests.RequestException, ValueError):
        api_error("Unable to load notes from the backend.")
        return
    search = st.text_input("Search notes", placeholder="Search subjects and note content", label_visibility="collapsed")
    if search.strip():
        notes = [item for item in notes if search.lower() in str(item).lower()]
    if not notes:
        empty_state("No notes found", "Notes are created from the Interactions page using type 'note'.")
        if st.button("Open interactions"):
            st.info("Use Tasks & activity in the sidebar to log a note against a lead or customer.")
        return
    for item in notes:
        st.markdown(
            f'<div class="feature-card"><div class="eyebrow">{item.get("interaction_date") or "Undated"}</div>'
            f'<h3>{item.get("subject") or "Untitled note"}</h3><p>{item.get("notes") or "No note content"}</p>'
            f'<span class="status-badge badge-neutral">Lead {item.get("lead_id") or "-"} · Customer {item.get("customer_id") or "-"}</span></div>',
            unsafe_allow_html=True,
        )


render_notes_page()
