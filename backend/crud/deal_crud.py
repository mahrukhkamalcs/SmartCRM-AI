from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.deal import Deal


router = APIRouter(prefix="/api/deals", tags=["deals"])


class DealCreate(BaseModel):
	lead_id: Optional[int] = None
	customer_id: Optional[int] = None
	title: str
	value: float
	stage: str
	probability: Optional[float] = None
	expected_close_date: Optional[str] = None


class DealUpdate(BaseModel):
	lead_id: Optional[int] = None
	customer_id: Optional[int] = None
	title: Optional[str] = None
	value: Optional[float] = None
	stage: Optional[str] = None
	probability: Optional[float] = None
	expected_close_date: Optional[str] = None


class DealResponse(DealCreate):
	id: int
	created_at: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
def create_deal(deal_data: DealCreate, db: Session = Depends(get_db)):
	deal = Deal(**deal_data.model_dump())
	db.add(deal)
	db.commit()
	db.refresh(deal)
	return deal


@router.get("", response_model=List[DealResponse])
def get_deals(db: Session = Depends(get_db)):
	return db.query(Deal).all()


@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
	deal = db.query(Deal).filter(Deal.id == deal_id).first()
	if deal is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Deal not found",
		)
	return deal


@router.put("/{deal_id}", response_model=DealResponse)
def update_deal(
	deal_id: int,
	deal_data: DealUpdate,
	db: Session = Depends(get_db),
):
	deal = db.query(Deal).filter(Deal.id == deal_id).first()
	if deal is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Deal not found",
		)

	for field, value in deal_data.model_dump(exclude_unset=True).items():
		setattr(deal, field, value)

	db.commit()
	db.refresh(deal)
	return deal


@router.delete("/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
	deal = db.query(Deal).filter(Deal.id == deal_id).first()
	if deal is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Deal not found",
		)

	db.delete(deal)
	db.commit()
	return {"message": "Deal deleted successfully"}
