from html import escape
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]


def safe_text(value, fallback=""):
	return escape(str(value if value is not None else fallback))


def load_styles():
	css_path = ROOT / "styles" / "style.css"
	st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_header(eyebrow, title, description):
	st.markdown(
		f"""
		<div class="page-header">
			<div class="eyebrow">{safe_text(eyebrow)}</div>
			<h1>{safe_text(title)}</h1>
			<p>{safe_text(description)}</p>
		</div>
		""",
		unsafe_allow_html=True,
	)


def metric_card(label, value, detail="", tone="blue"):
	st.markdown(
		f"""
		<div class="metric-card metric-{tone}">
			<div class="metric-label">{safe_text(label)}</div>
			<div class="metric-value">{safe_text(value)}</div>
			<div class="metric-detail">{safe_text(detail)}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def badge(label, tone="neutral"):
	return f'<span class="status-badge badge-{safe_text(tone)}">{safe_text(label)}</span>'


def render_status_table(rows):
	if not rows:
		return
	headers = list(rows[0].keys())
	headers_html = "".join(f"<th>{safe_text(header)}</th>" for header in headers)
	body_html = []
	for row in rows:
		cells = []
		for header in headers:
			value = row.get(header, "")
			if isinstance(value, str) and value.startswith('<span class="status-badge '):
				cell = value
			else:
				cell = safe_text(value, "—")
			cells.append(f"<td>{cell}</td>")
			tbody_html.append(f"<tr>{''.join(cells)}</tr>")
	st.markdown(
		f'<div class="status-table-wrap"><table class="status-table">'
		f'<thead><tr>{headers_html}</tr></thead><tbody>{"".join(tbody_html)}</tbody>'
		f'</table></div>',
		unsafe_allow_html=True,
	)


def display_value(value, fallback="—"):
	return fallback if value is None or value == "" else value


def score_label(score):
	if score is None or score == "":
		return "Not scored", "neutral"
	try:
		score = float(score)
	except (TypeError, ValueError):
		return "Not scored", "neutral"
	if score >= 70:
		return f"{score:g} / 100", "success"
	if score >= 40:
		return f"{score:g} / 100", "warning"
	return f"{score:g} / 100", "danger"


def tone_for_status(status):
	status = str(status or "").lower()
	if status in {"converted", "qualified", "active", "won", "closed won", "low"}:
		return "success"
	if status in {"contacted", "new", "open", "medium", "at risk"}:
		return "warning"
	if status in {"lost", "inactive", "churned", "high", "closed lost"}:
		return "danger"
	return "neutral"


def api_error(message="Unable to connect to the CRM backend."):
	st.markdown(
		f'<div class="state-panel error-panel"><strong>Connection issue</strong><br>{safe_text(message)}</div>',
		unsafe_allow_html=True,
	)


def empty_state(title, detail):
	st.markdown(
		f'<div class="state-panel"><strong>{safe_text(title)}</strong><br><span>{safe_text(detail)}</span></div>',
		unsafe_allow_html=True,
	)


def render_crm_response(result):
	"""Render known Ask CRM payloads without exposing Python dictionary syntax."""
	if not isinstance(result, dict):
		st.markdown(
			f'<div class="feature-card"><h3>CRM Assistant</h3><p>{result}</p></div>',
			unsafe_allow_html=True,
		)
		return

	if result.get("answer"):
		st.markdown(
			f'<div class="feature-card"><h3>CRM Assistant</h3><p>{result["answer"]}</p></div>',
			unsafe_allow_html=True,
		)
		return
	if result.get("customers_at_risk") is not None:
		st.subheader("🚨 Customers at High Churn Risk")
		risk_rows = result["customers_at_risk"]
		if isinstance(risk_rows, dict):
			risk_rows = [risk_rows]
		for item in risk_rows:
			customer = item.get("customer", {})
			risk_badge = badge(
				f'{item.get("risk_score", 0)} / 100',
				tone_for_status(item.get("risk_level")),
			)
			reasons = "; ".join(item.get("reasons", []))
			st.markdown(
				f'<div class="feature-card"><h3>{display_value(customer.get("name"))}</h3>'
				f'<p>{display_value(customer.get("company"))}</p>{risk_badge}'
				f'<p><strong>Why:</strong> {display_value(reasons)}</p>'
				f'<p><strong>Recommended action:</strong> '
				f'{display_value(item.get("recommended_action"))}</p></div>',
				unsafe_allow_html=True,
			)
		return
	if result.get("leads_needing_attention") is not None:
		st.subheader("⚠️ Leads Needing Attention")
		rows = []
		for lead in result["leads_needing_attention"]:
			score, _ = score_label(lead.get("score"))
			rows.append({"Name": display_value(lead.get("name")), "Company": display_value(lead.get("company")), "Status": display_value(lead.get("status")), "Lead score": score, "Email": display_value(lead.get("email")), "Phone": display_value(lead.get("phone"))})
		if rows:
			st.dataframe(rows, use_container_width=True, hide_index=True)
		else:
			empty_state("No leads need attention", "The current attention rules found no matching leads.")
		return
	if result.get("high_value_deals") is not None:
		st.subheader("💼 High-Value Deals")
		rows = [{"Title": display_value(deal.get("title")), "Value": f'${float(deal.get("value") or 0):,.2f}', "Stage": display_value(deal.get("stage")), "Lead ID": display_value(deal.get("lead_id")), "Customer ID": display_value(deal.get("customer_id"))} for deal in result["high_value_deals"]]
		if rows:
			st.dataframe(rows, use_container_width=True, hide_index=True)
		else:
			empty_state("No deals found", "There are no deals to display.")
		return
	if result.get("action") or result.get("recommendation"):
		st.subheader("🎯 Recommendation")
		for label, key in [("Recommended action", "action"), ("Follow-up recommendation", "recommendation"), ("Priority", "priority"), ("Reason", "reason"), ("Suggested timing", "suggested_timing"), ("Suggested message", "suggested_message")]:
			if result.get(key):
				st.markdown(f"**{label}:** {result[key]}")
		return
	if result.get("error"):
		st.info(result["error"])
		return
	st.markdown('<div class="feature-card"><h3>CRM Assistant</h3><p>Here is the latest CRM result.</p></div>', unsafe_allow_html=True)
