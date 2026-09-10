import sys
from datetime import date, datetime
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, page_header, tone_for_status


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def render_follow_up():
	load_styles()
	page_header("AI Signals", "Follow Up", "Keep momentum with timely, context-aware outreach suggestions.")
	st.caption("MVP follow-up assistant using deterministic templates and CRM activity")
	leads = fetch_records("leads")
	customers = fetch_records("customers")
	interactions = fetch_records("interactions")
	if leads is None or customers is None or interactions is None:
		api_error("Unable to load CRM data from the backend.")
		return

	entity_options = {
		**{f"Lead {item.get('id')}: {item.get('name')}": ("lead", item) for item in leads},
		**{
			f"Customer {item.get('id')}: {item.get('name')}": ("customer", item)
			for item in customers
		},
	}
	if not entity_options:
		empty_state("No contacts found", "Add a lead or customer to create a follow-up plan.")
		return

	entity_type, entity = entity_options[st.selectbox("Select a lead or customer", list(entity_options))]
	entity_id = entity.get("id")
	related = [
		item
		for item in interactions
		if item.get(f"{entity_type}_id") == entity_id
	]
	recent = max(related, key=lambda item: item.get("interaction_date", ""), default=None)

	st.markdown(f'<div class="feature-card"><div class="eyebrow">Outreach workspace</div><h3>Follow-up for {display_value(entity.get("name"))}</h3><p>{display_value(entity.get("company"))}</p></div>', unsafe_allow_html=True)
	if recent:
		st.write(f"**Last interaction:** {recent.get('interaction_date')} ({recent.get('type')})")
		st.write(f"**Subject:** {recent.get('subject') or 'No subject'}")
	else:
		st.info("No prior interaction is recorded.")

	if recent:
		try:
			days_since = (date.today() - datetime.fromisoformat(recent["interaction_date"]).date()).days
		except (KeyError, TypeError, ValueError):
			days_since = 0
	else:
		days_since = 999

	if days_since >= 14:
		timing = "Today"
		recommendation = "Re-engage promptly because the last activity is older than two weeks."
	elif days_since >= 5:
		timing = "Within 2 business days"
		recommendation = "Send a progress check while the conversation is still recent."
	else:
		timing = "At the next agreed milestone"
		recommendation = "Keep the conversation warm and confirm the next milestone."

	message = (
		f"Hi {entity.get('name')}, I wanted to follow up on our recent conversation "
		"and see whether there is anything else you need from us. "
		"Would a short check-in this week be useful?"
	)
	st.markdown(f'<div class="feature-card"><h3>Recommended follow-up</h3><p><strong>Action:</strong> {recommendation}</p><p><strong>Timing:</strong> {badge(timing, "warning")}</p><p><strong>Priority:</strong> {badge("High" if days_since >= 14 else "Medium", tone_for_status("High" if days_since >= 14 else "Medium"))}</p></div>', unsafe_allow_html=True)
	st.text_area("Suggested follow-up message", message, height=140)

render_follow_up()