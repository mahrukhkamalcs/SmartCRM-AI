import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, metric_card, page_header, render_status_table, tone_for_status


def render_deals_page():
	load_styles()
	page_header("Revenue", "Deals", "Manage the pipeline from first opportunity to close.")

	if "deal_created_message" in st.session_state:
		st.success(st.session_state.pop("deal_created_message"))
	submission_handled = st.session_state.pop("deal_submission_handled", False)

	with st.form("add_deal_form", clear_on_submit=True):
		st.markdown('<div class="form-heading">Create a deal</div>', unsafe_allow_html=True)
		st.markdown('<div class="form-help">Add the commercial context behind an opportunity.</div>', unsafe_allow_html=True)
		left, right = st.columns(2)
		with left:
			title = st.text_input("Title *", placeholder="e.g. Enterprise renewal")
			value = st.number_input("Value", min_value=0.0, step=0.01, format="%.2f")
			stage = st.text_input("Stage *", placeholder="e.g. discovery, proposal, won")
		with right:
			lead_id_input = st.number_input("Lead ID (optional)", min_value=0, step=1, value=0)
			customer_id_input = st.number_input("Customer ID (optional)", min_value=0, step=1, value=0)
			probability_input = st.text_input("Probability (optional)", placeholder="e.g. 60")
			expected_close_date = st.text_input("Expected Close Date (optional)", placeholder="YYYY-MM-DD")
		submitted = st.form_submit_button("Add Deal")

	if submitted and not submission_handled:
		if not title.strip():
			st.error("Please enter a deal title.")
		elif not stage.strip():
			st.error("Please select or enter a deal stage.")
		else:
			probability = None
			probability_valid = True
			try:
				if probability_input.strip():
					probability = float(probability_input)
			except ValueError:
				st.error("Probability must be a number.")
				probability_valid = False

			if probability_valid:
				deal_data = {
					"lead_id": int(lead_id_input) if lead_id_input else None,
					"customer_id": int(customer_id_input) if customer_id_input else None,
					"title": title,
					"value": value,
					"stage": stage,
					"probability": probability,
					"expected_close_date": expected_close_date or None,
				}
				try:
					response = requests.post(
						f"{BACKEND_URL}/api/deals",
						json=deal_data,
						timeout=5,
					)
					response.raise_for_status()
					st.session_state["deal_submission_handled"] = True
					st.session_state["deal_created_message"] = (
						"Deal added successfully."
					)
					st.rerun()
				except requests.RequestException:
					st.error("Unable to create the deal.")

	try:
		response = requests.get(f"{BACKEND_URL}/api/deals", timeout=5)
		response.raise_for_status()
		deals = response.json()
	except (requests.RequestException, ValueError):
		api_error("Unable to load deals from the backend. Please try again shortly.")
		return

	filter_col, stage_col = st.columns([2, 1])
	with filter_col:
		search = st.text_input("Search deals", placeholder="Search title or linked record ID", label_visibility="collapsed")
	with stage_col:
		stage_filter = st.selectbox("Deal stage", ["All stages"] + sorted({str(deal.get("stage") or "Unknown") for deal in deals}), label_visibility="collapsed")
	if search.strip():
		deals = [deal for deal in deals if search.lower() in str(deal).lower()]
	if stage_filter != "All stages":
		deals = [deal for deal in deals if str(deal.get("stage") or "Unknown") == stage_filter]

	if not deals:
		empty_state("No matching deals", "Adjust the search or filters, or create a new deal above.")
		return

	total_value = sum(float(deal.get("value") or 0) for deal in deals)
	st.markdown('<div class="section-label">Revenue snapshot</div>', unsafe_allow_html=True)
	metric_columns = st.columns(3)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Total deals", len(deals), "All opportunities", "blue"),
		(metric_columns[1], "Pipeline value", f"${total_value:,.0f}", "Combined deal value", "green"),
		(metric_columns[2], "Stages", len({deal.get("stage") for deal in deals if deal.get("stage")}), "Distinct pipeline stages", "teal"),
	]:
		with column:
			metric_card(label, value, detail, tone)

	columns = {
		"ID": "id",
		"Lead ID": "lead_id",
		"Customer ID": "customer_id",
		"Title": "title",
		"Value": "value",
		"Stage": "stage",
		"Probability": "probability",
		"Expected Close Date": "expected_close_date",
	}
	table_data = [
		{
			"ID": deal.get("id"), "Lead ID": display_value(deal.get("lead_id")),
			"Customer ID": display_value(deal.get("customer_id")), "Title": display_value(deal.get("title")),
			"Value": f"${float(deal.get('value') or 0):,.2f}",
			"Stage": badge(display_value(deal.get("stage"), "Unknown"), tone_for_status(deal.get("stage"))),
			"Probability": f"{float(deal.get('probability')):.0f}%" if deal.get("probability") is not None else "—",
			"Expected close": display_value(deal.get("expected_close_date")),
		}
		for deal in deals
	]
	st.markdown('<div class="section-label">Pipeline register</div>', unsafe_allow_html=True)
	render_status_table(table_data)


render_deals_page()
