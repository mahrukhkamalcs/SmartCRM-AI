import os

from dotenv import load_dotenv


load_dotenv()


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_gemini_api_key():
	return os.getenv("GEMINI_API_KEY")


def get_openrouter_api_key():
	return os.getenv("OPENROUTER_API_KEY")