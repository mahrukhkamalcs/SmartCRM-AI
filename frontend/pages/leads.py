import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, metric_card, page_header, render_status_table, score_label, tone_for_status


def render_leads_page():
	load_styles()
	page_header("Pipeline", "Leads", "Capture, qualify, and prioritize every opportunity.")

	if "lead_created_message" in st.session_state:
		st.success(st.session_state.pop("lead_created_message"))
	submission_handled = st.session_state.pop("lead_submission_handled", False)

	with st.form("add_lead_form", clear_on_submit=True):
		st.markdown('<div class="form-heading">Create a lead</div>', unsafe_allow_html=True)
		st.markdown('<div class="form-help">Capture the contact details needed for the next conversation.</div>', unsafe_allow_html=True)
		left, right = st.columns(2)
		with left:
			name = st.text_input("Name *", placeholder="e.g. Alex Morgan")
			email = st.text_input("Email", placeholder="name@company.com")
			phone = st.text_input("Phone", placeholder="Optional")
		with right:
			company = st.text_input("Company", placeholder="e.g. Northstar Labs")
			source = st.text_input("Source", placeholder="e.g. Website, referral")
			status = st.selectbox(
				"Status",
				["new", "contacted", "qualified", "lost", "converted"],
			)
		submitted = st.form_submit_button("Add Lead")

	if submitted and not submission_handled:
		if not name.strip():
			st.error("Please enter a lead name.")
		elif not email.strip():
			st.error("Please enter a lead email address.")
		elif "@" not in email or "." not in email.split("@")[-1]:
			st.error("Please enter a valid email address.")
		else:
			lead_data = {
				"name": name,
				"email": email,
				"phone": phone,
				"company": company,
				"source": source,
				"status": status,
			}
			try:
				response = requests.post(
					f"{BACKEND_URL}/api/leads",
					json=lead_data,
					timeout=5,
				)
				response.raise_for_status()
				st.session_state["lead_submission_handled"] = True
				st.session_state["lead_created_message"] = "Lead added successfully."
				st.rerun()
			except requests.RequestException:
				st.error("Unable to create the lead.")

	try:
		response = requests.get(f"{BACKEND_URL}/api/leads", timeout=5)
		response.raise_for_status()
		leads = response.json()
	except (requests.RequestException, ValueError):
		api_error("Unable to load leads from the backend. Please try again shortly.")
		return

	filter_col, status_col = st.columns([2, 1])
	with filter_col:
		search = st.text_input("Search leads", placeholder="Search name, company, or email", label_visibility="collapsed")
	with status_col:
		status_filter = st.selectbox("Lead status", ["All statuses"] + sorted({str(lead.get("status") or "Unknown") for lead in leads}), label_visibility="collapsed")
	if search.strip():
		leads = [lead for lead in leads if search.lower() in str(lead).lower()]
	if status_filter != "All statuses":
		leads = [lead for lead in leads if str(lead.get("status") or "Unknown") == status_filter]

	if not leads:
		empty_state("No matching leads", "Adjust the search or filters, or add a new opportunity above.")
		return

	st.markdown('<div class="section-label">Pipeline snapshot</div>', unsafe_allow_html=True)
	metric_columns = st.columns(3)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Total leads", len(leads), "All captured opportunities", "blue"),
		(metric_columns[1], "New leads", sum(lead.get("status") == "new" for lead in leads), "Awaiting first touch", "amber"),
		(metric_columns[2], "Qualified", sum(lead.get("status") == "qualified" for lead in leads), "Ready for progression", "green"),
	]:
		with column:
			metric_card(label, value, detail, tone)

	columns = {
		"ID": "id",
		"Name": "name",
		"Email": "email",
		"Phone": "phone",
		"Company": "company",
		"Source": "source",
		"Status": "status",
		"Score": "score",
	}
	table_data = []
	for lead in leads:
		score, score_tone = score_label(lead.get("score"))
		table_data.append({
			"ID": lead.get("id"), "Name": display_value(lead.get("name")),
			"Email": display_value(lead.get("email")), "Company": display_value(lead.get("company")),
			"Status": badge(display_value(lead.get("status"), "Unknown"), tone_for_status(lead.get("status"))),
			"Lead score": badge(score, score_tone), "Source": display_value(lead.get("source")),
		})
	st.markdown('<div class="section-label">All opportunities</div>', unsafe_allow_html=True)
	render_status_table(table_data)


render_leads_page()
