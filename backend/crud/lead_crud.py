from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.ai_recommendation import AIRecommendation
from backend.models.customer import Customer
from backend.models.deal import Deal
from backend.models.interaction import Interaction
from backend.models.lead import Lead


router = APIRouter(prefix="/api/leads", tags=["leads"])


class LeadCreate(BaseModel):
	name: str
	email: str
	phone: Optional[str] = None
	company: Optional[str] = None
	source: Optional[str] = None
	status: str


class LeadUpdate(BaseModel):
	name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None
	company: Optional[str] = None
	source: Optional[str] = None
	status: Optional[str] = None


class LeadResponse(LeadCreate):
	id: int
	score: Optional[float] = None
	created_at: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead_data: LeadCreate, db: Session = Depends(get_db)):
	lead = Lead(**lead_data.model_dump())
	db.add(lead)
	db.commit()
	db.refresh(lead)
	return lead


@router.get("", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db)):
	return db.query(Lead).all()


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
	lead = db.query(Lead).filter(Lead.id == lead_id).first()
	if lead is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Lead not found",
		)
	return lead


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
	lead_id: int,
	lead_data: LeadUpdate,
	db: Session = Depends(get_db),
):
	lead = db.query(Lead).filter(Lead.id == lead_id).first()
	if lead is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Lead not found",
		)

	for field, value in lead_data.model_dump(exclude_unset=True).items():
		setattr(lead, field, value)

	db.commit()
	db.refresh(lead)
	return lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
	lead = db.query(Lead).filter(Lead.id == lead_id).first()
	if lead is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Lead not found",
		)

	db.delete(lead)
	db.commit()
	return {"message": "Lead deleted successfully"}
