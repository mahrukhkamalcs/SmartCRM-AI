import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()

default_database_url = (
	"sqlite:////tmp/smartcrm.db"
	if os.getenv("VERCEL")
	else "sqlite:///./smartcrm.db"
)
DATABASE_URL = os.getenv("DATABASE_URL", default_database_url)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
