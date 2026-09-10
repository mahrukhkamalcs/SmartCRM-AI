from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.db import Base

if TYPE_CHECKING:
	from backend.models.lead import Lead
	from backend.models.customer import Customer


class Interaction(Base):
	__tablename__ = "interactions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	lead_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
	)
	customer_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
	)
	type: Mapped[str] = mapped_column(String, nullable=False)
	subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
	notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	interaction_date: Mapped[str] = mapped_column(Text, nullable=False)

	lead: Mapped[Optional["Lead"]] = relationship(back_populates="interactions")
	customer: Mapped[Optional["Customer"]] = relationship(
		back_populates="interactions"
	)
