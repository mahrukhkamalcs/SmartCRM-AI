import streamlit as st

from components.ui import load_styles, page_header

load_styles()
page_header("Workspace", "Settings", "Review the workspace configuration and connected intelligence services.")

st.markdown('<div class="feature-card"><h3>Workspace profile</h3><p>SmartCRM AI · Relationship intelligence workspace</p><p class="muted-copy">Profile and authentication settings are managed by the current deployment.</p></div>', unsafe_allow_html=True)
st.markdown('<div class="feature-card"><h3>AI assistant</h3><p>Ask CRM uses the existing agentic workflow with provider fallbacks and deterministic CRM tools.</p></div>', unsafe_allow_html=True)
st.markdown('<div class="feature-card"><h3>Data & privacy</h3><p>Records are loaded from the configured backend API. No credentials or secrets are stored in the frontend.</p></div>', unsafe_allow_html=True)
