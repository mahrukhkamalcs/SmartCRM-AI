from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.db import Base

if TYPE_CHECKING:
	from backend.models.interaction import Interaction
	from backend.models.deal import Deal
	from backend.models.ai_recommendation import AIRecommendation


class Customer(Base):
	__tablename__ = "customers"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String, nullable=False)
	email: Mapped[str] = mapped_column(String, nullable=False)
	phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
	company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
	status: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[Optional[str]] = mapped_column(
		Text, nullable=False, server_default=text("CURRENT_TIMESTAMP")
	)

	interactions: Mapped[List["Interaction"]] = relationship(
		back_populates="customer"
	)
	deals: Mapped[List["Deal"]] = relationship(back_populates="customer")
	recommendations: Mapped[List["AIRecommendation"]] = relationship(
		back_populates="customer"
	)
