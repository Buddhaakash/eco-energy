
import streamlit as st

from translation import tr


def render_kpi_row(kpis: dict):
    language = st.session_state.get("app_language", "English")

    cols = st.columns(5)

    cols[0].metric(
        tr("Total usage", language),
        f'{kpis["total_kwh"]:.1f} kWh',
    )

    cols[1].metric(
        tr("Cost so far", language),
        f'₹{kpis["total_cost"]:.0f}',
    )

    cols[2].metric(
        tr("Projected monthly bill", language),
        f'₹{kpis["projected_monthly_cost"]:.0f}',
    )

    cols[3].metric(
        tr("Leaks found", language),
        kpis["leak_count"],
    )

    cols[4].metric(
        tr("Potential savings", language),
        f'₹{kpis["potential_savings"]:.0f}',
    )
