from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.customer import Customer


router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerCreate(BaseModel):
	name: str
	email: str
	phone: Optional[str] = None
	company: Optional[str] = None
	status: str


class CustomerUpdate(BaseModel):
	name: Optional[str] = None
	email: Optional[str] = None
	phone: Optional[str] = None
	company: Optional[str] = None
	status: Optional[str] = None


class CustomerResponse(CustomerCreate):
	id: int
	created_at: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
	customer_data: CustomerCreate,
	db: Session = Depends(get_db),
):
	customer = Customer(**customer_data.model_dump())
	db.add(customer)
	db.commit()
	db.refresh(customer)
	return customer


@router.get("", response_model=List[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
	return db.query(Customer).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
	customer = db.query(Customer).filter(Customer.id == customer_id).first()
	if customer is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Customer not found",
		)
	return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
	customer_id: int,
	customer_data: CustomerUpdate,
	db: Session = Depends(get_db),
):
	customer = db.query(Customer).filter(Customer.id == customer_id).first()
	if customer is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Customer not found",
		)

	for field, value in customer_data.model_dump(exclude_unset=True).items():
		setattr(customer, field, value)

	db.commit()
	db.refresh(customer)
	return customer


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
	customer = db.query(Customer).filter(Customer.id == customer_id).first()
	if customer is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Customer not found",
		)

	db.delete(customer)
	db.commit()
	return {"message": "Customer deleted successfully"}
