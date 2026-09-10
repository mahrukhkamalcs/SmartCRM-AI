import json

from agentic_ai.config import (
	OPENROUTER_BASE_URL,
	OPENROUTER_MODEL,
	get_openrouter_api_key,
)
from agentic_ai.gemini_client import SYSTEM_INSTRUCTION, TOOL_DECLARATIONS
from agentic_ai.tools.crm_tools import call_tool


def _openai_tools():
	return [
		{
			"type": "function",
			"function": {
				"name": declaration["name"],
				"description": declaration["description"],
				"parameters": declaration["parameters"],
			},
		}
		for declaration in TOOL_DECLARATIONS
	]


def ask_openrouter(question, db):
	api_key = get_openrouter_api_key()
	if not api_key:
		raise RuntimeError("OpenRouter API key is not configured.")

	try:
		from openai import OpenAI

		client = OpenAI(
			api_key=api_key,
			base_url=OPENROUTER_BASE_URL,
			timeout=15.0,
			max_retries=0,
		)
		messages = [
			{"role": "system", "content": SYSTEM_INSTRUCTION},
			{"role": "user", "content": question},
		]
		for _ in range(2):
			response = client.chat.completions.create(
				model=OPENROUTER_MODEL,
				messages=messages,
				tools=_openai_tools(),
				tool_choice="auto",
				max_tokens=300,
			)
			message = response.choices[0].message
			tool_calls = message.tool_calls or []
			if not tool_calls:
				return message.content or "OpenRouter returned no answer."

			messages.append(
				{
					"role": "assistant",
					"content": message.content,
					"tool_calls": [
						{
							"id": call.id,
							"type": "function",
							"function": {
								"name": call.function.name,
								"arguments": call.function.arguments,
							},
						}
						for call in tool_calls
					],
				}
			)
			for call in tool_calls:
				try:
					arguments = json.loads(call.function.arguments or "{}")
				except (TypeError, ValueError):
					arguments = {}
				result = call_tool(call.function.name, arguments, db)
				messages.append(
					{
						"role": "tool",
						"tool_call_id": call.id,
						"content": json.dumps(result, default=str),
					}
				)
		raise RuntimeError("OpenRouter did not return a final answer.")
	
	except RuntimeError:
		raise
	except Exception as error:
		raise RuntimeError("OpenRouter request failed.") from error