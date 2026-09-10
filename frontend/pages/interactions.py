import sys
from datetime import date
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, metric_card, page_header


def render_interactions_page():
	load_styles()
	page_header("Activity", "Interactions", "A clear timeline of the conversations moving your CRM forward.")

	if "interaction_created_message" in st.session_state:
		st.success(st.session_state.pop("interaction_created_message"))
	submission_handled = st.session_state.pop(
		"interaction_submission_handled", False
	)

	with st.form("add_interaction_form", clear_on_submit=True):
		st.markdown('<div class="form-heading">Log an interaction</div>', unsafe_allow_html=True)
		st.markdown('<div class="form-help">Record the latest touchpoint so follow-ups stay contextual.</div>', unsafe_allow_html=True)
		left, right = st.columns(2)
		with left:
			lead_id_input = st.number_input("Lead ID (optional)", min_value=0, step=1, value=0)
			customer_id_input = st.number_input("Customer ID (optional)", min_value=0, step=1, value=0)
			interaction_type = st.selectbox("Type", ["call", "email", "meeting", "note"])
		with right:
			subject = st.text_input("Subject", placeholder="e.g. Discovery call")
			interaction_date = st.date_input("Interaction Date", value=date.today())
			notes = st.text_area("Notes", placeholder="Add useful context for the next touchpoint.")
		submitted = st.form_submit_button("Add Interaction")

	if submitted and not submission_handled:
		if lead_id_input == 0 and customer_id_input == 0:
			st.error("Please provide at least a Lead ID or Customer ID.")
		elif interaction_date is None:
			st.error("Interaction Date is required.")
		else:
			interaction_data = {
				"lead_id": int(lead_id_input) if lead_id_input else None,
				"customer_id": int(customer_id_input) if customer_id_input else None,
				"type": interaction_type,
				"subject": subject,
				"notes": notes,
				"interaction_date": interaction_date.isoformat(),
			}
			try:
				response = requests.post(
					f"{BACKEND_URL}/api/interactions",
					json=interaction_data,
					timeout=5,
				)
				response.raise_for_status()
				st.session_state["interaction_submission_handled"] = True
				st.session_state["interaction_created_message"] = (
					"Interaction added successfully."
				)
				st.rerun()
			except requests.RequestException:
				st.error("Unable to create the interaction.")

	try:
		response = requests.get(f"{BACKEND_URL}/api/interactions", timeout=5)
		response.raise_for_status()
		interactions = response.json()
	except (requests.RequestException, ValueError):
		api_error("Unable to load interactions from the backend. Please try again shortly.")
		return

	if not interactions:
		empty_state("No interactions found", "Log a call, email, meeting, or note to begin the activity timeline.")
		return

	st.markdown('<div class="section-label">Activity snapshot</div>', unsafe_allow_html=True)
	metric_columns = st.columns(3)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Total activity", len(interactions), "Recorded interactions", "blue"),
		(metric_columns[1], "Leads touched", len({item.get("lead_id") for item in interactions if item.get("lead_id") is not None}), "Distinct leads", "teal"),
		(metric_columns[2], "Customers touched", len({item.get("customer_id") for item in interactions if item.get("customer_id") is not None}), "Distinct customers", "green"),
	]:
		with column:
			metric_card(label, value, detail, tone)

	columns = {
		"ID": "id",
		"Lead ID": "lead_id",
		"Customer ID": "customer_id",
		"Type": "type",
		"Subject": "subject",
		"Notes": "notes",
		"Interaction Date": "interaction_date",
	}
	table_data = [
		{
			"ID": item.get("id"), "Lead ID": display_value(item.get("lead_id")),
			"Customer ID": display_value(item.get("customer_id")),
			"Type": badge(display_value(item.get("type"), "Unknown"), "blue"),
			"Subject": display_value(item.get("subject")), "Notes": display_value(item.get("notes")),
			"Date": display_value(item.get("interaction_date")),
		}
		for item in interactions
	]
	st.markdown('<div class="section-label">Activity timeline</div>', unsafe_allow_html=True)
	st.dataframe(table_data, use_container_width=True, hide_index=True)


render_interactions_page()
