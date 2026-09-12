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


def render_companies_page():
    load_styles()
    page_header("Relationships", "Companies", "See the organizations behind your contacts and pipeline.")
    customers = fetch("customers")
    deals = fetch("deals")
    if customers is None or deals is None:
        api_error("Unable to load company data from the backend.")
        return

    company_names = sorted({item.get("company") for item in customers if item.get("company")})
    st.markdown('<div class="section-label">Company directory</div>', unsafe_allow_html=True)
    search = st.text_input("Search companies", placeholder="Search by company name", label_visibility="collapsed")
    selected = [name for name in company_names if not search.strip() or search.lower() in name.lower()]
    rows = []
    for company in selected:
        company_contacts = [item for item in customers if item.get("company") == company]
        related_ids = {item.get("id") for item in company_contacts}
        company_deals = [item for item in deals if item.get("customer_id") in related_ids]
        rows.append({
            "Company": company,
            "Contacts": len(company_contacts),
            "Active deals": sum(str(item.get("stage", "")).lower() not in {"won", "lost", "closed won", "closed lost"} for item in company_deals),
            "Pipeline value": f"${sum(float(item.get('value') or 0) for item in company_deals):,.0f}",
            "Status": ", ".join(sorted({str(item.get("status") or "unknown") for item in company_contacts})),
        })
    metric_columns = st.columns(3)
    for column, label, value, detail, tone in [
        (metric_columns[0], "Companies", len(company_names), "Derived from contact records", "blue"),
        (metric_columns[1], "Contacts", len(customers), "Across all organizations", "teal"),
        (metric_columns[2], "Company pipeline", f"${sum(float(item.get('value') or 0) for item in deals):,.0f}", "All linked deal value", "green"),
    ]:
        with column:
            metric_card(label, value, detail, tone)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        empty_state("No companies found", "Add a company name to a customer record to see it here.")


render_companies_page()
