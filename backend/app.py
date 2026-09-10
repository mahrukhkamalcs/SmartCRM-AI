from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.crud.customer_crud import router as customer_router
from backend.crud.deal_crud import router as deal_router
from backend.crud.interaction_crud import router as interaction_router
from backend.crud.lead_crud import router as lead_router
from backend.database.db import get_db
from agentic_ai.workflows.ask_crm_workflow import answer_crm_question
from backend.ml.lead_scoring.predict import predict_lead_score
from backend.models.lead import Lead


app = FastAPI(title="SmartCRM-AI API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:8501",
		"http://127.0.0.1:8501",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(lead_router)
app.include_router(customer_router)
app.include_router(interaction_router)
app.include_router(deal_router)


class CRMQuestion(BaseModel):
	question: str


@app.get("/health")
def health_check():
	return {"status": "healthy"}


@app.get("/api")
def api_status():
	return {"message": "SmartCRM-AI API is running"}


@app.post("/api/ask-crm")
def ask_crm(question_data: CRMQuestion, db: Session = Depends(get_db)):
	question = question_data.question.strip()
	if not question:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Question is required",
		)
	return answer_crm_question(question, db)


@app.post("/api/leads/{lead_id}/score")
def score_lead(lead_id: int, db: Session = Depends(get_db)):
	lead = db.query(Lead).filter(Lead.id == lead_id).first()
	if lead is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Lead not found",
		)

	last_interaction = None
	if lead.interactions:
		last_interaction = max(
			(
				interaction
				for interaction in lead.interactions
				if interaction.interaction_date
			),
			key=lambda interaction: interaction.interaction_date,
			default=None,
		)
	days_since_last_interaction = None
	if last_interaction is not None:
		try:
			interaction_date = datetime.fromisoformat(
				last_interaction.interaction_date.replace("Z", "+00:00")
			)
			now = datetime.now(timezone.utc)
			if interaction_date.tzinfo is None:
				now = now.replace(tzinfo=None)
			days_since_last_interaction = max(0, (now - interaction_date).days)
		except (TypeError, ValueError):
			days_since_last_interaction = None

	features = {
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
		"days_since_last_interaction": days_since_last_interaction,
	}

	try:
		return predict_lead_score(features)
	except ValueError as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(error),
		) from error
	except RuntimeError as error:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail=str(error),
		) from error
