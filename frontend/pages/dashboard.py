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
	page_header("Live workspace", "Good morning, team.", "A live view of your pipeline, relationships, and activity.")
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
	weighted_value = sum(float(deal.get("value") or 0) * float(deal.get("probability") or 0) / 100 for deal in deals)
	active_leads = sum(str(lead.get("status", "")).lower() not in {"lost", "converted", "won"} for lead in leads)

	metric_columns = st.columns(5)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Contacts", len(customers), "Customer records", "blue"),
		(metric_columns[1], "Active leads", active_leads, f"{new_leads} new to qualify", "teal"),
		(metric_columns[2], "Open deals", open_deals, f"${total_value:,.0f} pipeline", "green"),
		(metric_columns[3], "Weighted forecast", f"${weighted_value:,.0f}", "Probability-adjusted", "amber"),
		(metric_columns[4], "Activity", len(interactions), "Recorded touchpoints", "red"),
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

	st.markdown('<div class="section-label">Today at a glance</div>', unsafe_allow_html=True)
	activity_col, action_col = st.columns([1.4, 1])
	with activity_col:
		st.subheader("Latest activity")
		if interactions:
			for item in interactions[:5]:
				st.markdown(
					f'<div class="activity-row"><span class="activity-dot"></span>'
					f'<div><strong>{item.get("subject") or item.get("type") or "Interaction"}</strong>'
					f'<div class="muted-copy">{item.get("notes") or "No notes added"}</div></div>'
					f'<time>{item.get("interaction_date") or "Recently"}</time></div>',
					unsafe_allow_html=True,
				)
		else:
			empty_state("No activity yet", "Log an interaction to start your timeline.")
	with action_col:
		st.subheader("Focus this week")
		st.markdown(
			f'<div class="focus-panel"><div class="focus-kicker">AI focus</div>'
			f'<strong>{new_leads} new leads need a first touch</strong>'
			f'<p>Use AI Assistant to prioritize the next best conversation.</p></div>',
			unsafe_allow_html=True,
		)

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