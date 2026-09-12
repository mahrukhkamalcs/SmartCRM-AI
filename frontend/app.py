import streamlit as st

from components.ui import load_styles
from components.sidebar import render_sidebar


st.set_page_config(
	page_title="SmartCRM AI | Relationship workspace",
	page_icon="S",
	layout="wide",
	initial_sidebar_state="expanded",
)
load_styles()

main_pages = [
	st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
	st.Page("pages/customers.py", title="Contacts", icon="👥"),
	st.Page("pages/companies.py", title="Companies", icon="🏢"),
	st.Page("pages/leads.py", title="Leads", icon="🎯"),
	st.Page("pages/deals.py", title="Deals", icon="💼"),
	st.Page("pages/interactions.py", title="Tasks & activity", icon="✅"),
]
ai_pages = [
	st.Page("pages/ask_crm.py", title="AI Assistant", icon="🤖"),
	st.Page("pages/lead_details.py", title="Lead Details", icon="🔎"),
	st.Page("pages/churn.py", title="Churn Prediction", icon="📉"),
	st.Page("pages/next_best_action.py", title="Next Best Action", icon="💡"),
	st.Page("pages/follow_up.py", title="Follow Up", icon="📅"),
	st.Page("pages/reports.py", title="Reports", icon="📈"),
	st.Page("pages/notes.py", title="Notes", icon="📝"),
	st.Page("pages/settings.py", title="Settings", icon="🔧"),
]
page_groups = {"Workspace": main_pages, "Intelligence": ai_pages}
selected_page = st.navigation(page_groups, position="hidden")
render_sidebar(page_groups)
selected_page.run()
