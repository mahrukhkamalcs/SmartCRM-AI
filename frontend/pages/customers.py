import sys
from pathlib import Path

import requests
import streamlit as st

frontend_dir = str(Path(__file__).resolve().parents[1])
if frontend_dir not in sys.path:
	sys.path.insert(0, frontend_dir)

from config import BACKEND_URL
from components.ui import api_error, badge, display_value, empty_state, load_styles, metric_card, page_header, render_status_table, tone_for_status


def render_customers_page():
	load_styles()
	page_header("Relationships", "Customers", "Keep every customer relationship visible, current, and actionable.")

	if "customer_created_message" in st.session_state:
		st.success(st.session_state.pop("customer_created_message"))
	submission_handled = st.session_state.pop("customer_submission_handled", False)

	with st.form("add_customer_form", clear_on_submit=True):
		st.markdown('<div class="form-heading">Create a customer</div>', unsafe_allow_html=True)
		st.markdown('<div class="form-help">Keep relationship and contact information ready for the team.</div>', unsafe_allow_html=True)
		left, right = st.columns(2)
		with left:
			name = st.text_input("Name *", placeholder="e.g. Jordan Lee")
			email = st.text_input("Email", placeholder="name@company.com")
			phone = st.text_input("Phone", placeholder="Optional")
		with right:
			company = st.text_input("Company", placeholder="e.g. Acme Inc.")
			status = st.text_input("Status", placeholder="e.g. active")
		submitted = st.form_submit_button("Add Customer")

	if submitted and not submission_handled:
		if not name.strip():
			st.error("Please enter a customer name.")
		elif not email.strip():
			st.error("Please enter a customer email address.")
		elif "@" not in email or "." not in email.split("@")[-1]:
			st.error("Please enter a valid email address.")
		else:
			customer_data = {
				"name": name,
				"email": email,
				"phone": phone,
				"company": company,
				"status": status,
			}
			try:
				response = requests.post(
					f"{BACKEND_URL}/api/customers",
					json=customer_data,
					timeout=5,
				)
				response.raise_for_status()
				st.session_state["customer_submission_handled"] = True
				st.session_state["customer_created_message"] = (
					"Customer added successfully."
				)
				st.rerun()
			except requests.RequestException:
				st.error("Unable to create the customer.")

	try:
		response = requests.get(f"{BACKEND_URL}/api/customers", timeout=5)
		response.raise_for_status()
		customers = response.json()
	except (requests.RequestException, ValueError):
		api_error("Unable to load customers from the backend. Please try again shortly.")
		return

	filter_col, status_col = st.columns([2, 1])
	with filter_col:
		search = st.text_input("Search contacts", placeholder="Search name, company, or email", label_visibility="collapsed")
	with status_col:
		status_filter = st.selectbox("Contact status", ["All statuses"] + sorted({str(customer.get("status") or "Unknown") for customer in customers}), label_visibility="collapsed")
	if search.strip():
		customers = [customer for customer in customers if search.lower() in str(customer).lower()]
	if status_filter != "All statuses":
		customers = [customer for customer in customers if str(customer.get("status") or "Unknown") == status_filter]

	if not customers:
		empty_state("No matching contacts", "Adjust the search or filters, or add a new contact above.")
		return

	st.markdown('<div class="section-label">Relationship snapshot</div>', unsafe_allow_html=True)
	metric_columns = st.columns(3)
	for column, label, value, detail, tone in [
		(metric_columns[0], "Total customers", len(customers), "All customer records", "teal"),
		(metric_columns[1], "Active customers", sum(str(customer.get("status", "")).lower() == "active" for customer in customers), "Marked active", "green"),
		(metric_columns[2], "Needs review", sum(str(customer.get("status", "")).lower() in {"inactive", "at risk", "churned"} for customer in customers), "Inactive or at-risk status", "amber"),
	]:
		with column:
			metric_card(label, value, detail, tone)

	columns = {
		"ID": "id",
		"Name": "name",
		"Email": "email",
		"Phone": "phone",
		"Company": "company",
		"Status": "status",
	}
	table_data = [
		{
			"ID": customer.get("id"), "Name": display_value(customer.get("name")),
			"Email": display_value(customer.get("email")), "Phone": display_value(customer.get("phone")),
			"Company": display_value(customer.get("company")),
			"Status": badge(display_value(customer.get("status"), "Unknown"), tone_for_status(customer.get("status"))),
		}
		for customer in customers
	]
	st.markdown('<div class="section-label">Customer directory</div>', unsafe_allow_html=True)
	render_status_table(table_data)


render_customers_page()
