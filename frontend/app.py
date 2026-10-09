import streamlit as st

from components.sidebar import render_sidebar
from components.tab_data import render_data_tab
from components.tab_overview import render_overview_tab
from components.tab_anomalies import render_anomalies_tab
from components.tab_savings import render_savings_tab
from components.tab_chat import render_chat_tab
from components.tab_bill_check import render_bill_check_tab
import api_client as api

st.set_page_config(page_title="EcoEnergy — AI Energy Leak Finder", page_icon="⚡", layout="wide")

selected_dataset_id = render_sidebar()

st.title("⚡ EcoEnergy Dashboard")
st.caption("Find where your electricity is being wasted, and what to do about it.")

tabs = st.tabs(["📊 Overview", "📁 Data", "🚨 Anomalies", "✅ Savings Plan", "🧾 Bill Check", "💬 Ask AI", "⬇️ Export"])

with tabs[0]:
    if selected_dataset_id:
        render_overview_tab(selected_dataset_id)
    else:
        st.info("Upload a CSV or load demo data in the Data tab to get started.")

with tabs[1]:
    render_data_tab(selected_dataset_id)

with tabs[2]:
    if selected_dataset_id:
        render_anomalies_tab(selected_dataset_id)
    else:
        st.info("No dataset selected yet.")

with tabs[3]:
    if selected_dataset_id:
        render_savings_tab(selected_dataset_id)
    else:
        st.info("No dataset selected yet.")

with tabs[4]:
    if selected_dataset_id:
        render_bill_check_tab(selected_dataset_id)
    else:
        st.info("No dataset selected yet.")

with tabs[5]:
    if selected_dataset_id:
        render_chat_tab(selected_dataset_id)
    else:
        st.info("No dataset selected yet.")

with tabs[6]:
    st.subheader("Export report")
    if selected_dataset_id:
        c1, c2 = st.columns(2)
        c1.link_button(
            "⬇️ Download CSV", api.report_url(selected_dataset_id, "csv"),
            use_container_width=True,
        )
        c2.link_button(
            "⬇️ Download PDF", api.report_url(selected_dataset_id, "pdf"),
            use_container_width=True,
        )
    else:
        st.info("No dataset selected yet.")
