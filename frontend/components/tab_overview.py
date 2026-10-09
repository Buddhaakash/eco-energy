import streamlit as st

import api_client as api
from components.kpi_row import render_kpi_row
from components.charts import render_timeline


def render_overview_tab(dataset_id: int):
    analysis = api.safe_call(api.get_analysis, dataset_id, error_prefix="Couldn't load analysis")
    if not analysis:
        return

    render_kpi_row(analysis["kpis"])
    st.divider()
    render_timeline(analysis["timeline"], analysis["anomalies"])
