import pandas as pd
import plotly.graph_objects as go
import streamlit as st

SEVERITY_COLOR = {"low": "#f4c430", "medium": "#ff8c42", "high": "#e63946"}


def render_timeline(timeline: list[dict], anomalies: list[dict]):
    if not timeline:
        st.info("No readings to show yet.")
        return

    df = pd.DataFrame(timeline)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["kwh"], mode="lines",
        name="Usage (kWh)", line=dict(color="#2a9d8f", width=1.5),
    ))

    for a in anomalies:
        color = SEVERITY_COLOR.get(a["severity"], "#e63946")
        fig.add_vrect(
            x0=a["start"], x1=a["end"],
            fillcolor=color, opacity=0.25, line_width=0,
        )

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="", yaxis_title="kWh",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🟡 low · 🟠 medium · 🔴 high — shaded regions mark detected anomalies")
