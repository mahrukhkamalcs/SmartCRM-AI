import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, load_styles, page_header, tone_for_status


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def recommend(lead, interactions, deals):
	lead_interactions = [item for item in interactions if item.get("lead_id") == lead.get("id")]
	lead_deals = [item for item in deals if item.get("lead_id") == lead.get("id")]
	status = str(lead.get("status", "")).lower()
	if status == "new" or not lead_interactions:
		return (
			"Make first contact",
			"This lead has no recorded interaction yet.",
			"High",
			f"Hi {lead.get('name')}, I would like to learn more about your priorities and see how we can help.",
		)
	if status == "qualified" and not lead_deals:
		return (
			"Schedule a proposal call",
			"The lead is qualified but has no associated deal.",
			"High",
			f"Hi {lead.get('name')}, can we schedule time to review the right solution and next steps?",
		)
	if status == "lost":
		return (
			"Re-engage with a targeted offer",
			"The lead is marked lost and may need a new reason to reconsider.",
			"Medium",
			f"Hi {lead.get('name')}, we have a few updates that may address your earlier concerns. Would you be open to reconnecting?",
		)
	return (
		"Follow up on the open opportunity",
		"Existing activity suggests a direct progress check is appropriate.",
		"Medium",
		f"Hi {lead.get('name')}, I wanted to check in on our conversation and confirm the best next step.",
	)


def render_next_best_action():
	load_styles()
	page_header("AI Signals", "Next Best Action", "Turn current activity into a clear, practical next move.")
	st.caption("MVP deterministic recommendation engine based on current CRM activity")
	leads = fetch_records("leads")
	interactions = fetch_records("interactions")
	deals = fetch_records("deals")
	if leads is None or interactions is None or deals is None:
		api_error("Unable to load CRM data from the backend.")
		return
	if not leads:
		st.info("No leads found. Add an opportunity to generate recommendations.")
		return

	options = {f"{lead.get('id')}: {lead.get('name')}": lead for lead in leads}
	lead = options[st.selectbox("Select a lead", list(options))]
	action, reason, priority, message = recommend(lead, interactions, deals)
	st.markdown(f'<div class="feature-card"><div class="eyebrow">Recommendation for {lead.get("name")}</div><h3>{action}</h3><p><strong>Priority</strong> {badge(priority, tone_for_status(priority))}</p><p><strong>Reason</strong> {reason}</p></div>', unsafe_allow_html=True)
	st.text_area("Suggested message / action", message, height=120)


render_next_best_action()