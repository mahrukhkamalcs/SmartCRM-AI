import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, empty_state, load_styles, metric_card, page_header


def fetch(resource):
    try:
        response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def render_reports_page():
    load_styles()
    page_header("Intelligence", "Reports", "Live performance signals from the records in your CRM.")
    leads, deals, interactions = fetch("leads"), fetch("deals"), fetch("interactions")
    if any(item is None for item in (leads, deals, interactions)):
        api_error("Unable to load report data from the backend.")
        return
    won = sum(str(item.get("stage", "")).lower() in {"won", "closed won"} for item in deals)
    conversion = won / len(deals) * 100 if deals else 0
    value = sum(float(item.get("value") or 0) for item in deals)
    columns = st.columns(4)
    for column, label, value_text, detail, tone in [
        (columns[0], "Lead conversion", f"{conversion:.0f}%", f"{won} won deals", "blue"),
        (columns[1], "Pipeline value", f"${value:,.0f}", "Across all deals", "green"),
        (columns[2], "Average deal", f"${value / len(deals):,.0f}" if deals else "$0", "Current deal set", "teal"),
        (columns[3], "Touchpoints", len(interactions), "Logged interactions", "amber"),
    ]:
        with column:
            metric_card(label, value_text, detail, tone)
    left, right = st.columns(2)
    with left:
        st.subheader("Lead conversion by status")
        if leads:
            status_counts = pd.Series([item.get("status") or "Unknown" for item in leads]).value_counts()
            st.bar_chart(status_counts, color="#3478f6")
        else:
            empty_state("No leads yet", "Add leads to populate this report.")
    with right:
        st.subheader("Revenue by deal stage")
        if deals:
            frame = pd.DataFrame(deals)
            revenue = frame.groupby(frame["stage"].fillna("Unknown"))["value"].sum()
            st.bar_chart(revenue, color="#159a8c")
        else:
            empty_state("No deals yet", "Add deals to populate this report.")


render_reports_page()
