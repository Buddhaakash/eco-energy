import streamlit as st


def render_kpi_row(kpis: dict):
    cols = st.columns(5)
    cols[0].metric("Total usage", f'{kpis["total_kwh"]:.1f} kWh')
    cols[1].metric("Cost so far", f'₹{kpis["total_cost"]:.0f}')
    cols[2].metric("Projected monthly bill", f'₹{kpis["projected_monthly_cost"]:.0f}')
    cols[3].metric("Leaks found", kpis["leak_count"])
    cols[4].metric("Potential savings", f'₹{kpis["potential_savings"]:.0f}')
