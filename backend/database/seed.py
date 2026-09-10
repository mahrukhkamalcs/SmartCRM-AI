from backend.database.db import Base, engine
from backend.models.ai_recommendation import AIRecommendation
from backend.models.customer import Customer
from backend.models.deal import Deal
from backend.models.interaction import Interaction
from backend.models.lead import Lead
from backend.models.user import User


def main():
	Base.metadata.create_all(bind=engine)
	print("Database tables created successfully.")


if __name__ == "__main__":
	main()
