import re

from agentic_ai.tools.crm_tools import (
	analyze_churn_risk,
	follow_up_recommendation,
	get_customers,
	get_deals,
	get_interactions,
	get_leads,
	next_best_action,
)


def _lead_id(question):
	match = re.search(r"\blead\s+(\d+)\b", question.lower())
	return int(match.group(1)) if match else None


def is_tool_oriented_question(question):
	query = question.lower()
	return any(
		phrase in query
		for phrase in (
			"need immediate attention",
			"needs attention",
			"at risk",
			"churn",
			"high-value",
			"high value",
			"what should i do",
			"next best action",
			"follow-up",
			"follow up",
			"score lead",
		)
	)


def answer_question(question, db):
	query = question.lower().strip()
	leads = get_leads(db)
	customers = get_customers(db)
	deals = get_deals(db)
	interactions = get_interactions(db)
	lead_id = _lead_id(query)

	if "follow-up" in query or "follow up" in query:
		if lead_id is not None:
			return follow_up_recommendation(db, "lead", lead_id)
		return {"answer": "Please include a lead or customer ID for a follow-up recommendation."}
	if "what should i do" in query or "next best action" in query:
		if lead_id is not None:
			return next_best_action(db, lead_id)
		return {"answer": "Please include a lead ID for a next-best-action recommendation."}
	if "churn" in query or "at risk" in query:
		return {"customers_at_risk": analyze_churn_risk(db)}
	if "high-value" in query or "high value" in query:
		high_value = sorted(deals, key=lambda item: item.get("value") or 0, reverse=True)[:5]
		return {"high_value_deals": high_value}
	if "attention" in query:
		attention = [
			lead for lead in leads
			if str(lead.get("status", "")).lower() in {"new", "qualified", "lost"}
		]
		return {"leads_needing_attention": attention}
	if "customer" in query and ("how many" in query or "count" in query):
		return {"answer": f"There are {len(customers)} customers."}
	if "lead" in query and ("how many" in query or "count" in query):
		return {"answer": f"There are {len(leads)} leads."}
	return {
		"answer": "I can help with lead and customer counts, leads needing attention, "
		"churn risk, high-value deals, lead actions, and follow-up messages."
	}