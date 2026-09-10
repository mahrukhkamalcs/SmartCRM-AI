from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.db import Base

if TYPE_CHECKING:
	from backend.models.lead import Lead
	from backend.models.customer import Customer


class AIRecommendation(Base):
	__tablename__ = "ai_recommendations"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	lead_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
	)
	customer_id: Mapped[Optional[int]] = mapped_column(
		ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
	)
	recommendation_type: Mapped[str] = mapped_column(String, nullable=False)
	recommendation: Mapped[str] = mapped_column(Text, nullable=False)
	confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	created_at: Mapped[Optional[str]] = mapped_column(
		Text, nullable=False, server_default=text("CURRENT_TIMESTAMP")
	)

	lead: Mapped[Optional["Lead"]] = relationship(back_populates="recommendations")
	customer: Mapped[Optional["Customer"]] = relationship(
		back_populates="recommendations"
	)
