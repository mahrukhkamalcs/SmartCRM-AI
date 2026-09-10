import json

from agentic_ai.config import GEMINI_MODEL, get_gemini_api_key
from agentic_ai.tools.crm_tools import call_tool


TOOL_DECLARATIONS = [
	{
		"name": "get_leads",
		"description": "Get all CRM leads.",
		"parameters": {"type": "object", "properties": {}},
	},
	{
		"name": "get_customers",
		"description": "Get all CRM customers.",
		"parameters": {"type": "object", "properties": {}},
	},
	{
		"name": "get_deals",
		"description": "Get all CRM deals.",
		"parameters": {"type": "object", "properties": {}},
	},
	{
		"name": "get_interactions",
		"description": "Get all CRM interactions.",
		"parameters": {"type": "object", "properties": {}},
	},
	{
		"name": "score_lead",
		"description": "Score one lead with the existing lead scoring model.",
		"parameters": {
			"type": "object",
			"properties": {"lead_id": {"type": "integer"}},
			"required": ["lead_id"],
		},
	},
	{
		"name": "analyze_churn_risk",
		"description": "Analyze rule-based churn risk for all customers or one customer.",
		"parameters": {
			"type": "object",
			"properties": {"customer_id": {"type": "integer"}},
		},
	},
	{
		"name": "next_best_action",
		"description": "Recommend the next action for one lead.",
		"parameters": {
			"type": "object",
			"properties": {"lead_id": {"type": "integer"}},
			"required": ["lead_id"],
		},
	},
	{
		"name": "follow_up_recommendation",
		"description": "Create a follow-up recommendation and message for a lead or customer.",
		"parameters": {
			"type": "object",
			"properties": {
				"entity_type": {"type": "string", "enum": ["lead", "customer"]},
				"entity_id": {"type": "integer"},
			},
			"required": ["entity_type", "entity_id"],
		},
	},
]


SYSTEM_INSTRUCTION = (
	"You are SmartCRM's CRM assistant. Use CRM tools for factual answers. "
	"Do not invent records or fields. Give concise, practical answers and mention "
	"when a result is rule-based or unavailable."
)


def _tool_config(types):
	return types.Tool(function_declarations=TOOL_DECLARATIONS)


def ask_gemini(question, db):
	api_key = get_gemini_api_key()
	if not api_key:
		raise RuntimeError("Gemini API key is not configured.")

	try:
		from google import genai
		from google.genai import types

		client = genai.Client(api_key=api_key)
		contents = [question]
		config = types.GenerateContentConfig(
			system_instruction=SYSTEM_INSTRUCTION,
			tools=[_tool_config(types)],
		)
		for _ in range(4):
			response = client.models.generate_content(
				model=GEMINI_MODEL,
				contents=contents,
				config=config,
			)
			candidate = response.candidates[0].content
			function_calls = [part.function_call for part in candidate.parts if part.function_call]
			if not function_calls:
				return response.text or "Gemini returned no answer."
			contents.append(candidate)
			for function_call in function_calls:
				result = call_tool(
					function_call.name,
					dict(function_call.args or {}),
					db,
				)
				contents.append(
					types.Content(
						role="tool",
						parts=[
							types.Part.from_function_response(
								name=function_call.name,
								response={"result": result},
							)
						],
					)
				)
		raise RuntimeError("Gemini did not return a final answer.")
	except RuntimeError:
		raise
	except Exception as error:
		raise RuntimeError("Gemini request failed.") from error