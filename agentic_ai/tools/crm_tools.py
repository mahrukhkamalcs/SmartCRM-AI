from datetime import date, datetime, timezone

from backend.ml.lead_scoring.predict import predict_lead_score


def _serialize(model):
	return {
		column.name: getattr(model, column.name)
		for column in model.__table__.columns
	}


def get_leads(db):
	from backend.models.lead import Lead

	return [_serialize(lead) for lead in db.query(Lead).all()]


def get_customers(db):
	from backend.models.customer import Customer

	return [_serialize(customer) for customer in db.query(Customer).all()]


def get_deals(db):
	from backend.models.deal import Deal

	return [_serialize(deal) for deal in db.query(Deal).all()]


def get_interactions(db):
	from backend.models.interaction import Interaction

	return [_serialize(interaction) for interaction in db.query(Interaction).all()]


def _get_lead(db, lead_id):
	from backend.models.lead import Lead

	return db.query(Lead).filter(Lead.id == int(lead_id)).first()


def _lead_features(lead):
	last_interaction = max(
		(
			item
			for item in lead.interactions
			if item.interaction_date
		),
		key=lambda item: item.interaction_date,
		default=None,
	)
	days_since = None
	if last_interaction:
		try:
			interaction_date = datetime.fromisoformat(
				last_interaction.interaction_date.replace("Z", "+00:00")
			)
			now = datetime.now(timezone.utc)
			if interaction_date.tzinfo is None:
				now = now.replace(tzinfo=None)
			days_since = max(0, (now - interaction_date).days)
		except (TypeError, ValueError):
			pass
	return {
		"name": lead.name,
		"email": lead.email,
		"phone": lead.phone,
		"company": lead.company,
		"source": lead.source,
		"status": lead.status,
		"company_size": None,
		"interactions_count": len(lead.interactions),
		"previous_deals": len(lead.deals),
		"deal_value": sum(deal.value or 0 for deal in lead.deals),
		"days_since_last_interaction": days_since,
	}


def score_lead(db, lead_id):
	lead = _get_lead(db, lead_id)
	if lead is None:
		return {"error": "Lead not found."}
	return {"lead_id": lead.id, **predict_lead_score(_lead_features(lead))}


def analyze_churn_risk(db, customer_id=None):
	from backend.models.customer import Customer

	query = db.query(Customer)
	if customer_id is not None:
		query = query.filter(Customer.id == int(customer_id))
	customers = query.all()
	if not customers:
		return {"error": "Customer not found."}

	results = []
	for customer in customers:
		interactions = list(customer.interactions)
		deals = list(customer.deals)
		score = 0
		reasons = []
		if not interactions:
			score += 45
			reasons.append("No recorded interactions")
		if not deals:
			score += 30
			reasons.append("No associated deals")
		if str(customer.status).lower() in {"inactive", "at risk", "churned"}:
			score += 25
			reasons.append(f"Customer status is {customer.status}")
		if len(interactions) == 1:
			score += 10
			reasons.append("Only one recorded interaction")
		score = min(score, 100)
		level = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
		results.append(
			{
				"customer": _serialize(customer),
				"risk_level": level,
				"risk_score": score,
				"reasons": reasons or ["Healthy recent CRM activity"],
				"recommended_action": "Contact the customer this week with a retention check-in."
				if level == "High"
				else "Schedule a proactive check-in and review open opportunities."
				if level == "Medium"
				else "Maintain regular engagement and monitor activity.",
			}
		)
	return results[0] if customer_id is not None else results


def next_best_action(db, lead_id):
	lead = _get_lead(db, lead_id)
	if lead is None:
		return {"error": "Lead not found."}
	status = str(lead.status).lower()
	if status == "new" or not lead.interactions:
		return {
			"action": "Make first contact",
			"reason": "This lead has no recorded interaction yet.",
			"priority": "High",
			"suggested_message": f"Hi {lead.name}, I would like to learn more about your priorities and see how we can help.",
		}
	if status == "qualified" and not lead.deals:
		return {
			"action": "Schedule a proposal call",
			"reason": "The lead is qualified but has no associated deal.",
			"priority": "High",
			"suggested_message": f"Hi {lead.name}, can we schedule time to review the right solution and next steps?",
		}
	return {
		"action": "Follow up on the open opportunity",
		"reason": "Existing activity suggests a direct progress check is appropriate.",
		"priority": "Medium",
		"suggested_message": f"Hi {lead.name}, I wanted to check in and confirm the best next step.",
	}


def follow_up_recommendation(db, entity_type, entity_id):
	model = _get_lead(db, entity_id) if entity_type == "lead" else None
	if entity_type == "customer":
		from backend.models.customer import Customer

		model = db.query(Customer).filter(Customer.id == int(entity_id)).first()
	if model is None:
		return {"error": f"{entity_type.title()} not found."}
	recent = max(
		list(model.interactions),
		key=lambda item: item.interaction_date or "",
		default=None,
	)
	name = model.name
	if recent:
		try:
			days_since = (date.today() - datetime.fromisoformat(recent.interaction_date).date()).days
		except (TypeError, ValueError):
			days_since = 0
	else:
		days_since = 999
	return {
		"last_interaction": _serialize(recent) if recent else None,
		"recommendation": "Re-engage promptly because the last activity is older than two weeks."
		if days_since >= 14
		else "Send a progress check while the conversation is still recent.",
		"suggested_timing": "Today" if days_since >= 14 else "Within 2 business days",
		"suggested_message": f"Hi {name}, I wanted to follow up on our recent conversation and see whether you need anything else from us.",
	}


TOOL_FUNCTIONS = {
	"get_leads": get_leads,
	"get_customers": get_customers,
	"get_deals": get_deals,
	"get_interactions": get_interactions,
	"score_lead": score_lead,
	"analyze_churn_risk": analyze_churn_risk,
	"next_best_action": next_best_action,
	"follow_up_recommendation": follow_up_recommendation,
}


def call_tool(name, arguments, db):
	function = TOOL_FUNCTIONS.get(name)
	if function is None:
		return {"error": f"Unknown CRM tool: {name}"}
	try:
		return function(db=db, **(arguments or {}))
	except (RuntimeError, TypeError, ValueError):
		return {"error": "The CRM tool received invalid arguments."}