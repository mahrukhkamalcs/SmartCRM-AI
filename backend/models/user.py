from typing import Optional

from sqlalchemy import Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.db import Base


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String, nullable=False)
	email: Mapped[str] = mapped_column(String, nullable=False)
	password: Mapped[str] = mapped_column(String, nullable=False)
	role: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[Optional[str]] = mapped_column(
		Text, nullable=False, server_default=text("CURRENT_TIMESTAMP")
	)
