import sys
from pathlib import Path

import streamlit as st
import requests

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, metric_card, page_header, tone_for_status


def fetch_records(resource):
	try:
		response = requests.get(f"{BACKEND_URL}/api/{resource}", timeout=5)
		response.raise_for_status()
		return response.json()
	except (requests.RequestException, ValueError):
		return None


def calculate_risk(customer, interactions, deals):
	risk_score = 0
	reasons = []
	customer_interactions = [
		item for item in interactions if item.get("customer_id") == customer.get("id")
	]
	customer_deals = [
		item for item in deals if item.get("customer_id") == customer.get("id")
	]

	if not customer_interactions:
		risk_score += 45
		reasons.append("No recorded interactions")
	if not customer_deals:
		risk_score += 30
		reasons.append("No associated deals")
	if str(customer.get("status", "")).lower() in {"inactive", "at risk", "churned"}:
		risk_score += 25
		reasons.append(f"Customer status is {customer.get('status')}")
	if len(customer_interactions) == 1:
		risk_score += 10
		reasons.append("Only one recorded interaction")

	risk_score = min(risk_score, 100)
	if risk_score >= 60:
		risk_level = "High"
		action = "Contact the customer this week with a retention check-in."
	elif risk_score >= 30:
		risk_level = "Medium"
		action = "Schedule a proactive check-in and review open opportunities."
	else:
		risk_level = "Low"
		action = "Maintain regular engagement and monitor activity."

	return risk_level, risk_score, reasons or ["Healthy recent CRM activity"], action


def render_churn():
	load_styles()
	page_header("AI Signals", "Churn Risk", "Prioritize retention work with transparent, rule-based customer risk signals.")
	st.caption("MVP rule-based assessment · no trained churn model is available")
	customers = fetch_records("customers")
	interactions = fetch_records("interactions")
	deals = fetch_records("deals")
	if customers is None or interactions is None or deals is None:
		api_error("Unable to load customer activity from the backend.")
		return
	if not customers:
		empty_state("No customers found", "Risk analysis will appear once customer activity exists.")
		return

	results = []
	for customer in customers:
		level, score, reasons, action = calculate_risk(customer, interactions, deals)
		results.append(
			{
				"Customer": customer.get("name"),
				"Risk level": level,
				"Risk score": score,
				"Reasons": "; ".join(reasons),
				"Recommended action": action,
			}
		)

	st.markdown('<div class="section-label">Risk distribution</div>', unsafe_allow_html=True)
	metric_columns = st.columns(3)
	for column, level, tone in [(metric_columns[0], "High", "red"), (metric_columns[1], "Medium", "amber"), (metric_columns[2], "Low", "green")]:
		with column:
			metric_card(f"{level} risk", sum(item["Risk level"] == level for item in results), "Customers in this band", tone)
	st.bar_chart(__import__("pandas").Series([item["Risk level"] for item in results]).value_counts(), color="#c44d51")
	st.markdown('<div class="section-label">Customer risk register</div>', unsafe_allow_html=True)
	st.dataframe(results, use_container_width=True, hide_index=True)
	selected_name = st.selectbox("Inspect customer", [item["Customer"] for item in results])
	selected = next(item for item in results if item["Customer"] == selected_name)
	st.metric("Risk score", f"{selected['Risk score']} / 100")
	st.markdown(f"**Risk level:** {badge(selected['Risk level'], tone_for_status(selected['Risk level']))}", unsafe_allow_html=True)
	st.write(f"**Reasons:** {selected['Reasons']}")
	st.write(f"**Recommended retention action:** {selected['Recommended action']}")


render_churn()