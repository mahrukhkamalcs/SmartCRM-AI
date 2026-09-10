import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def render_lead_details():
	st.title("Lead Details")
	leads = fetch_records("leads")
	if leads is None:
		st.error("Unable to load leads from the backend.")
		return
	if not leads:
		st.info("No leads found.")
		return

	lead_options = {
		f"{lead.get('id')}: {lead.get('name', 'Unnamed lead')}": lead
		for lead in leads
	}
	selected_label = st.selectbox("Select a lead", list(lead_options))
	lead = lead_options[selected_label]

	st.subheader(lead.get("name", "Lead"))
	info_columns = st.columns(3)
	info_columns[0].write(f"**Email:** {lead.get('email') or 'Not provided'}")
	info_columns[0].write(f"**Phone:** {lead.get('phone') or 'Not provided'}")
	info_columns[1].write(f"**Company:** {lead.get('company') or 'Not provided'}")
	info_columns[1].write(f"**Source:** {lead.get('source') or 'Not provided'}")
	info_columns[2].write(f"**Status:** {lead.get('status') or 'Unknown'}")
	info_columns[2].write(f"**Lead score:** {lead.get('score') or 'Not scored'}")

	if st.button("Score Lead", type="primary"):
		try:
			response = requests.post(
				f"{BACKEND_URL}/api/leads/{lead.get('id')}/score", timeout=10
			)
			response.raise_for_status()
			result = response.json()
			st.session_state["lead_score_result"] = result
		except requests.RequestException as error:
			st.error(f"Unable to score this lead: {error}")

	if "lead_score_result" in st.session_state:
		result = st.session_state["lead_score_result"]
		st.success(
			f"Prediction: {result.get('prediction')} | "
			f"Conversion probability: {result.get('conversion_probability', 0):.1%} | "
			f"Lead score: {result.get('lead_score')} / 100"
		)

	customers = fetch_records("customers")
	interactions = fetch_records("interactions")
	deals = fetch_records("deals")
	if customers is None or interactions is None or deals is None:
		st.warning("Some related CRM records could not be loaded.")
		return

	related_customers = [
		customer
		for customer in customers
		if customer.get("email") == lead.get("email")
		or customer.get("company") == lead.get("company")
	]
	related_interactions = [
		interaction
		for interaction in interactions
		if interaction.get("lead_id") == lead.get("id")
	]
	related_deals = [
		deal for deal in deals if deal.get("lead_id") == lead.get("id")
	]

	st.subheader("Related Customer / Contact")
	if related_customers:
		st.dataframe(related_customers, use_container_width=True, hide_index=True)
	else:
		st.info("No matching customer record found.")

	st.subheader("Related Interactions")
	if related_interactions:
		st.dataframe(related_interactions, use_container_width=True, hide_index=True)
	else:
		st.info("No interactions found for this lead.")

	st.subheader("Related Deals")
	if related_deals:
		st.dataframe(related_deals, use_container_width=True, hide_index=True)
	else:
		st.info("No deals found for this lead.")


render_lead_details()