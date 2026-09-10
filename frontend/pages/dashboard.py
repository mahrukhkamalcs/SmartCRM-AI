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


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def render_dashboard():
	load_styles()
	page_header("Overview", "Dashboard", "A live view of your pipeline, relationships, and activity.")
	data = {
		"leads": fetch_records("leads"),
		"customers": fetch_records("customers"),
		"deals": fetch_records("deals"),
		"interactions": fetch_records("interactions"),
	}

	failed_resources = [name for name, records in data.items() if records is None]
	if failed_resources:
		api_error(f"Unable to load {', '.join(failed_resources)}. Please check that the backend is running.")
		return

	leads = data["leads"]
	customers = data["customers"]
	deals = data["deals"]
	interactions = data["interactions"]
	new_leads = sum(str(lead.get("status", "")).lower() == "new" for lead in leads)
	open_deals = sum(str(deal.get("stage", "")).lower() not in {"won", "closed won", "lost", "closed lost"} for deal in deals)
	total_value = sum(float(deal.get("value") or 0) for deal in deals)

	metric_columns = st.columns(4)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Total leads", len(leads), f"{new_leads} new this cycle", "blue"),
		(metric_columns[1], "Customers", len(customers), "Relationship records", "teal"),
		(metric_columns[2], "Open deals", open_deals, f"${total_value:,.0f} total value", "green"),
		(metric_columns[3], "Interactions", len(interactions), "Recorded touchpoints", "amber"),
	]:
		with column:
			metric_card(label, value, detail, tone)

	st.markdown('<div class="section-label">Pipeline pulse</div>', unsafe_allow_html=True)
	left, right = st.columns(2)
	with left:
		st.subheader("Leads by status")
		if leads:
			lead_statuses = pd.Series(
				[lead.get("status") or "Unknown" for lead in leads]
			).value_counts()
			st.bar_chart(lead_statuses, color="#3478f6")
			st.dataframe(
				lead_statuses.rename("Count").reset_index().rename(
					columns={"index": "Status"}
				),
				use_container_width=True,
				hide_index=True,
			)
		else:
			empty_state("No leads yet", "Create a lead to start building the pipeline.")

	with right:
		st.subheader("Deals by stage")
		if deals:
			deal_frame = pd.DataFrame(deals)
			if "stage" in deal_frame:
				stage_counts = deal_frame["stage"].fillna("Unknown").value_counts()
				st.bar_chart(stage_counts, color="#159a8c")
				st.dataframe(
					stage_counts.rename("Count").reset_index().rename(
						columns={"index": "Stage"}
					),
					use_container_width=True,
					hide_index=True,
				)
		else:
			empty_state("No deals yet", "Add an opportunity to see the pipeline take shape.")

	st.markdown('<div class="section-label">Recent records</div>', unsafe_allow_html=True)
	st.subheader("Recent leads")
	if leads:
		st.dataframe(
			[
				{
					"ID": lead.get("id"),
					"Name": lead.get("name"),
					"Status": lead.get("status"),
					"Score": lead.get("score"),
				}
				for lead in leads[:10]
			],
			use_container_width=True,
			hide_index=True,
		)
	else:
		empty_state("Nothing to show", "Recent lead activity will appear here.")


render_dashboard()