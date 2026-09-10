import requests
import streamlit as st

from config import BACKEND_URL


def render_sidebar(page_groups):
	with st.sidebar:
		st.markdown(
			'<div class="brand"><span class="brand-mark">S</span>'
			'<span class="brand-name">SmartCRM-AI</span>'
			'<div class="brand-sub">Intelligence for every relationship</div></div>',
			unsafe_allow_html=True,
		)
		for group_name, pages in page_groups.items():
			st.markdown(
				f'<div class="section-label">{group_name}</div>',
				unsafe_allow_html=True,
			)
			for page in pages:
				st.page_link(
					page,
					label=page.title,
					icon=page.icon,
					use_container_width=True,
				)

		st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
		st.markdown('<div class="section-label">System</div>', unsafe_allow_html=True)
		if st.button("Check backend health", use_container_width=True):
			try:
				response = requests.get(f"{BACKEND_URL}/health", timeout=5)
				if response.json() == {"status": "healthy"}:
					st.success("Backend connected")
				else:
					st.error("Unexpected backend response")
			except requests.RequestException:
				st.error("Backend unavailable")
		st.markdown(
				'<div class="sidebar-footer"><strong>SmartCRM-AI</strong><br>'
				'<span>AI-powered relationship workspace</span></div>',
				unsafe_allow_html=True,
			)
