from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.interaction import Interaction


router = APIRouter(prefix="/api/interactions", tags=["interactions"])


class InteractionCreate(BaseModel):
	lead_id: Optional[int] = None
	customer_id: Optional[int] = None
	type: str
	subject: Optional[str] = None
	notes: Optional[str] = None
	interaction_date: str


class InteractionUpdate(BaseModel):
	lead_id: Optional[int] = None
	customer_id: Optional[int] = None
	type: Optional[str] = None
	subject: Optional[str] = None
	notes: Optional[str] = None
	interaction_date: Optional[str] = None


class InteractionResponse(InteractionCreate):
	id: int

	model_config = ConfigDict(from_attributes=True)


@router.post(
	"",
	response_model=InteractionResponse,
	status_code=status.HTTP_201_CREATED,
)
def create_interaction(
	interaction_data: InteractionCreate,
	db: Session = Depends(get_db),
):
	interaction = Interaction(**interaction_data.model_dump())
	db.add(interaction)
	db.commit()
	db.refresh(interaction)
	return interaction


@router.get("", response_model=List[InteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
	return db.query(Interaction).all()


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
	interaction = (
		db.query(Interaction).filter(Interaction.id == interaction_id).first()
	)
	if interaction is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Interaction not found",
		)
	return interaction


@router.put("/{interaction_id}", response_model=InteractionResponse)
def update_interaction(
	interaction_id: int,
	interaction_data: InteractionUpdate,
	db: Session = Depends(get_db),
):
	interaction = (
		db.query(Interaction).filter(Interaction.id == interaction_id).first()
	)
	if interaction is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Interaction not found",
		)

	for field, value in interaction_data.model_dump(exclude_unset=True).items():
		setattr(interaction, field, value)

	db.commit()
	db.refresh(interaction)
	return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
	interaction = (
		db.query(Interaction).filter(Interaction.id == interaction_id).first()
	)
	if interaction is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Interaction not found",
		)

	db.delete(interaction)
	db.commit()
	return {"message": "Interaction deleted successfully"}
