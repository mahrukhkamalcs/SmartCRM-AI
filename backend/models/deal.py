from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.db import Base

if TYPE_CHECKING:
	from backend.models.lead import Lead
	from backend.models.customer import Customer


class Deal(Base):
	__tablename__ = "deals"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	lead_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
	)
	customer_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
	)
	title: Mapped[str] = mapped_column(String, nullable=False)
	value: Mapped[float] = mapped_column(Float, nullable=False)
	stage: Mapped[str] = mapped_column(String, nullable=False)
	probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	expected_close_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	created_at: Mapped[Optional[str]] = mapped_column(
		Text, nullable=False, server_default=text("CURRENT_TIMESTAMP")
	)

	lead: Mapped[Optional["Lead"]] = relationship(back_populates="deals")
	customer: Mapped[Optional["Customer"]] = relationship(back_populates="deals")
