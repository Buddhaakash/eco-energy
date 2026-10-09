import streamlit as st

from components.sidebar import render_sidebar
from components.tab_data import render_data_tab
from components.tab_overview import render_overview_tab
from components.tab_anomalies import render_anomalies_tab
from components.tab_savings import render_savings_tab
from components.tab_chat import render_chat_tab
from components.tab_bill_check import render_bill_check_tab

import api_client as api
from translation import SUPPORTED_LANGUAGES, tr


# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="EcoEnergy — AI Energy Leak Finder",
    page_icon="⚡",
    layout="wide",
)


# --------------------------------------------------
# Initialize language
# --------------------------------------------------
if "app_language" not in st.session_state:
    st.session_state["app_language"] = "English"

languages = list(SUPPORTED_LANGUAGES.keys())

if st.session_state["app_language"] not in languages:
    st.session_state["app_language"] = "English"


# --------------------------------------------------
# Header and language selector
# --------------------------------------------------
header_left, header_right = st.columns([5, 1])

with header_left:
    st.title(tr("⚡ EcoEnergy Dashboard"))
    st.caption(
        tr(
            "Find where your electricity is being wasted, "
            "and what to do about it."
        )
    )

with header_right:
    with st.popover("🌐 Translate", use_container_width=True):
        st.markdown("### " + tr("Choose your language"))

        current_language = st.session_state["app_language"]

        selected_language = st.selectbox(
            tr("Select language"),
            options=languages,
            index=languages.index(current_language),
            key="translate_language_select",
        )

        if st.button(
            "Translate",
            key="apply_language_button",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["app_language"] = selected_language
            st.rerun()


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
selected_dataset_id = render_sidebar()


# --------------------------------------------------
# Navigation tabs
# --------------------------------------------------
tab_names = [
    tr("📊 Overview"),
    tr("📁 Data"),
    tr("🚨 Anomalies"),
    tr("✅ Savings Plan"),
    tr("🧾 Bill Check"),
    tr("💬 Ask AI"),
    tr("⬇️ Export"),
]

tabs = st.tabs(tab_names)


# --------------------------------------------------
# Overview tab
# --------------------------------------------------
with tabs[0]:
    if selected_dataset_id:
        render_overview_tab(selected_dataset_id)
    else:
        st.info(
            tr(
                "Upload a CSV or load demo data in the Data tab "
                "to get started."
            )
        )


# --------------------------------------------------
# Data tab
# --------------------------------------------------
with tabs[1]:
    render_data_tab(selected_dataset_id)


# --------------------------------------------------
# Anomalies tab
# --------------------------------------------------
with tabs[2]:
    if selected_dataset_id:
        render_anomalies_tab(selected_dataset_id)
    else:
        st.info(tr("No dataset selected yet."))


# --------------------------------------------------
# Savings Plan tab
# --------------------------------------------------
with tabs[3]:
    if selected_dataset_id:
        render_savings_tab(selected_dataset_id)
    else:
        st.info(tr("No dataset selected yet."))


# --------------------------------------------------
# Bill Check tab
# --------------------------------------------------
with tabs[4]:
    if selected_dataset_id:
        render_bill_check_tab(selected_dataset_id)
    else:
        st.info(tr("No dataset selected yet."))


# --------------------------------------------------
# Ask AI tab
# --------------------------------------------------
with tabs[5]:
    if selected_dataset_id:
        render_chat_tab(selected_dataset_id)
    else:
        st.info(tr("No dataset selected yet."))


# --------------------------------------------------
# Export tab
# --------------------------------------------------
with tabs[6]:
    st.subheader(tr("Export report"))

    if selected_dataset_id:
        col1, col2 = st.columns(2)

        with col1:
            st.link_button(
                tr("⬇️ Download CSV"),
                api.report_url(selected_dataset_id, "csv"),
                use_container_width=True,
            )

        with col2:
            st.link_button(
                tr("⬇️ Download PDF"),
                api.report_url(selected_dataset_id, "pdf"),
                use_container_width=True,
            )
    else:
        st.info(tr("No dataset selected yet."))
