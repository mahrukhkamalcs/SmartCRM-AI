import streamlit as st

from components.ui import load_styles
from components.sidebar import render_sidebar


st.set_page_config(
	page_title="SmartCRM-AI",
	page_icon="▦",
	layout="wide",
	initial_sidebar_state="expanded",
)
load_styles()

main_pages = [
	st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
	st.Page("pages/leads.py", title="Leads", icon="🎯"),
	st.Page("pages/customers.py", title="Customers", icon="👥"),
	st.Page("pages/deals.py", title="Deals", icon="💼"),
	st.Page("pages/interactions.py", title="Interactions", icon="💬"),
]
ai_pages = [
	st.Page("pages/lead_details.py", title="Lead Details", icon="🔎"),
	st.Page("pages/churn.py", title="Churn Prediction", icon="📉"),
	st.Page("pages/next_best_action.py", title="Next Best Action", icon="💡"),
	st.Page("pages/follow_up.py", title="Follow Up", icon="📅"),
	st.Page("pages/ask_crm.py", title="Ask CRM", icon="🤖"),
]
page_groups = {"Main": main_pages, "AI & Insights": ai_pages}
selected_page = st.navigation(page_groups, position="hidden")
render_sidebar(page_groups)
selected_page.run()
