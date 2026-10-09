
import streamlit as st

import api_client as api
from components.kpi_row import render_kpi_row
from components.charts import render_timeline
from translation import tr


def render_overview_tab(dataset_id: int):
    language = st.session_state.get("app_language", "English")

    st.subheader(tr("Energy Overview", language))

    analysis = api.safe_call(
        api.get_analysis,
        dataset_id,
        error_prefix=tr("Couldn't load analysis", language),
    )

    if not analysis:
        st.info(tr("No analysis available for this dataset yet.", language))
        return

    render_kpi_row(analysis["kpis"])
    st.divider()
    render_timeline(analysis["timeline"], analysis["anomalies"])
