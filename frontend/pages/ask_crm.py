import re
import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, load_styles, page_header, render_crm_response


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def answer_question(question, leads, customers, deals, interactions):
	normalized = question.lower().strip()
	if re.search(r"how many .*lead|count .*lead", normalized):
		return f"There are {len(leads)} leads."
	if re.search(r"how many .*customer|count .*customer", normalized):
		return f"There are {len(customers)} customers."
	if "high-value" in normalized or "high value" in normalized:
		high_value = sorted(deals, key=lambda deal: deal.get("value") or 0, reverse=True)[:5]
		if not high_value:
			return "There are no deals to display."
		return "High-value deals:\n" + "\n".join(
			f"- {deal.get('title', 'Untitled')} (${deal.get('value', 0):,.2f})"
			for deal in high_value
		)
	if "attention" in normalized:
		needs_attention = [
			lead for lead in leads if str(lead.get("status", "")).lower() in {"new", "lost"}
		]
		return "Leads needing attention:\n" + "\n".join(
			f"- {lead.get('name')} ({lead.get('status')})" for lead in needs_attention
		) if needs_attention else "No leads currently match the attention rules."
	if "risk" in normalized or "churn" in normalized:
		at_risk = [
			customer for customer in customers
			if not any(item.get("customer_id") == customer.get("id") for item in interactions)
		]
		return "Customers with no recorded interactions:\n" + "\n".join(
			f"- {customer.get('name')}" for customer in at_risk
		) if at_risk else "All customers have at least one recorded interaction."
	return (
		"I can answer questions about lead/customer counts, leads needing attention, "
		"high-value deals, and customers at risk."
	)


def render_ask_crm():
	load_styles()
	page_header("Intelligence", "Ask CRM", "Ask questions in plain language and get answers grounded in your live records.")
	st.markdown('<div class="ai-form-card"><div class="form-heading">Ask SmartCRM AI</div><div class="form-help">Ask about leads, customers, deals, churn risk, and follow-ups.</div>', unsafe_allow_html=True)
	question = st.text_area("Your question", placeholder="e.g. Which customers are at risk of churn?", height=100, label_visibility="collapsed")
	ask_clicked = st.button("✦ Ask SmartCRM AI", type="primary")
	st.markdown('</div>', unsafe_allow_html=True)
	if ask_clicked and question.strip():
		with st.spinner("Working through your CRM data..."):
			try:
				response = requests.post(
					f"{BACKEND_URL}/api/ask-crm",
					json={"question": question},
					timeout=30,
				)
				response.raise_for_status()
				result = response.json()
				st.session_state["crm_answer"] = result.get("answer") if result.get("answer") else result.get("result", result)
				st.session_state["crm_answer_source"] = {"openrouter": "OpenRouter", "gemini": "Gemini", "fallback": "Deterministic fallback"}.get(result.get("source"), "CRM")
			except (requests.RequestException, ValueError):
				leads = fetch_records("leads")
				customers = fetch_records("customers")
				deals = fetch_records("deals")
				interactions = fetch_records("interactions")
				if any(records is None for records in [leads, customers, deals, interactions]):
					st.error("Unable to connect to the CRM assistant or load CRM data.")
				else:
					st.session_state["crm_answer"] = answer_question(
						question, leads, customers, deals, interactions
					)
					st.session_state["crm_answer_source"] = "Deterministic fallback"
	if "crm_answer" in st.session_state:
		st.caption(f"Answer source · {st.session_state.get('crm_answer_source', 'CRM')}")
		render_crm_response(st.session_state["crm_answer"])
	else:
		st.markdown('<div class="state-panel"><strong>Start with a question</strong><br><span>Try “How many leads do we have?” or “Which customers are at risk of churn?”</span></div>', unsafe_allow_html=True)

render_ask_crm()