from agentic_ai.openrouter_client import ask_openrouter
from agentic_ai.gemini_client import ask_gemini
from agentic_ai.utils.fallback import answer_question, is_tool_oriented_question


def answer_crm_question(question, db):
	if is_tool_oriented_question(question):
		return {"result": answer_question(question, db), "source": "fallback"}
	try:
		return {"answer": ask_openrouter(question, db), "source": "openrouter"}
	except RuntimeError:
		try:
			return {"answer": ask_gemini(question, db), "source": "gemini"}
		except RuntimeError:
			return {"result": answer_question(question, db), "source": "fallback"}